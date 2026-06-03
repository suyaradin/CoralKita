"""
SST (Sea Surface Temperature) Monitoring Module
=================================================
Handles NOAA CoralTemp data fetching, DHW computation, alert generation,
and Gmail notifications for coral bleaching monitoring.
"""
from flask import Blueprint, jsonify, session, request, render_template

import os
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from flask import Blueprint, jsonify, session, request

# DAO Imports
from dao.SSTReadingDAO import (
    createSSTReading,
    getRecentReadings,
    getTodayReadingByRegion
)
from dao.SSTAlertDAO import createAlert, wasAlertSentToday
from dao.RegionDAO import getAllRegions
from dao.UserDAO import getNotificationRecipients
from dao.CoralDAO import getCoralCountByRegion
from util.gmail_notify import send_email_to_recipients


# ============================================================================
# 1. BLUEPRINT & CONSTANTS
# ============================================================================

sst_bp = Blueprint("sst", __name__)

# NOAA Coral Reef Watch DHW thresholds
DHW_ALERT_LEVEL1 = 4   # Alert Level 1 threshold (DHW >= 4)
DHW_ALERT_LEVEL2 = 8   # Alert Level 2 threshold (DHW >= 8)
MAX_MONTHLY_MEAN = 29.0  # Maximum monthly mean temperature (°C)

# NOAA ERDDAP endpoints (primary + mirror for redundancy)
NOAA_ENDPOINTS = [
    "https://oceanwatch.pifsc.noaa.gov/erddap/griddap/CRW_sst_v3_1.json",
    "https://pae-paha.pacioos.hawaii.edu/erddap/griddap/CRW_sst_v3_1.json",
]

# In-memory cache for SST data
_sst_cache = {
    "data": None,
    "date": None
}

# TEST MODE
# Set to True for local testing to:
# 1) bypass daily alert suppression, and
# 2) force fresh processing each /api/sst call.
# IMPORTANT: set True only for local alert/email testing.
SST_TEST_MODE = False


# ============================================================================
# 2. NOAA DATA FETCHING
# ============================================================================

def fetchNOAASST(latitude: float, longitude: float) -> float | None:
    """
    Fetch SST value from NOAA CoralTemp API for given coordinates.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    
    Returns:
        SST value in Celsius, or None if fetch fails
    """
    headers = {"User-Agent": "CoralKita/1.0 (SST Monitor)"}
    
    for endpoint in NOAA_ENDPOINTS:
        url = (
            f"{endpoint}"
            f"?analysed_sst[(last)][({latitude:.4f})][({longitude:.4f})]"
        )
        
        for attempt in range(2):  # Retry each endpoint once
            try:
                response = requests.get(url, timeout=15, headers=headers)
                response.raise_for_status()
                data = response.json()
                rows = data["table"]["rows"]
                
                if rows and rows[0][3] is not None:
                    return float(rows[0][3])
                return None
                
            except Exception as e:
                print(
                    f"[SST] NOAA fetch error for ({latitude}, {longitude}) "
                    f"via {endpoint}, attempt {attempt + 1}: {e}"
                )
    
    return None


# ============================================================================
# 3. DHW (Degree Heating Week) COMPUTATION
# ============================================================================

def computeDHW(regionID: int) -> tuple[float, int]:
    """
    Compute Degree Heating Weeks for a region.
    
    DHW accumulates thermal stress (hotspots >= 1°C) over a 12-week period.
    
    Args:
        regionID: Database ID of the region
    
    Returns:
        Tuple of (DHW_value, days_accumulated)
    """
    readings = getRecentReadings(regionID, weeks=12)
    
    if not readings:
        return 0.0, 0
    
    hotspot_sum = 0.0
    days_accumulated = 0
    
    for reading in readings:
        sst = float(reading["sstValue"])
        hotspot = sst - MAX_MONTHLY_MEAN
        
        if hotspot >= 1.0:
            hotspot_sum += hotspot
            days_accumulated += 1
    
    dhw = hotspot_sum / 7.0
    return round(dhw, 2), days_accumulated


def getStatusLabel(dhw: float, hotspot: float) -> str:
    """
    Determine bleaching status label based on DHW and hotspot values.
    
    Args:
        dhw: Degree Heating Weeks value
        hotspot: Current hotspot value (SST - MMM)
    
    Returns:
        Status label string
    """
    if dhw >= DHW_ALERT_LEVEL2:
        return "Alert Level 2"
    elif dhw >= DHW_ALERT_LEVEL1:
        return "Alert Level 1"
    elif dhw > 0:
        return "Bleaching Warning"
    elif hotspot > 0:
        return "Bleaching Watch"
    return "No Stress"


def getAlertLevel(dhw: float) -> str | None:
    """
    Determine alert level for email notifications.
    
    Args:
        dhw: Degree Heating Weeks value
    
    Returns:
        Alert level string, or None if no alert needed
    """
    if dhw >= DHW_ALERT_LEVEL2:
        return "Alert Level 2"
    elif dhw >= DHW_ALERT_LEVEL1:
        return "Alert Level 1"
    return None


# ============================================================================
# 4. CORE SST PROCESSING LOGIC
# ============================================================================

def processRegionSST(
    region: dict,
    coralCounts: dict,
    bypass_daily_alert_lock: bool = False
) -> dict | None:
    """
    Process SST data for a single region.
    
    Args:
        region: Region dictionary with coordinates and metadata
        coralCounts: Dictionary mapping regionID to coral count
    
    Returns:
        Processed region data dict, or None if processing fails
    """
    regionID = region["regionID"]
    regionName = region["regionName"]
    latitude = float(region["latitude"])
    longitude = float(region["longitude"])
    
    # Fetch SST from NOAA (with fallback to database)
    sstValue = fetchNOAASST(latitude, longitude)
    
    if sstValue is None:
        # Fallback: use latest stored reading
        recent = getRecentReadings(regionID, weeks=2)
        if recent:
            sstValue = float(recent[0]["sstValue"])
            print(f"[SST] Using fallback DB reading for {regionName}")
        else:
            print(f"[SST] Skipping {regionName} — NOAA fetch failed and no fallback data")
            return None
    
    # Save reading if not already saved today
    alreadySavedToday = getTodayReadingByRegion(regionID) is not None
    if not alreadySavedToday:
        createSSTReading(regionID, sstValue)
    
    # Compute metrics
    dhw, daysAccumulated = computeDHW(regionID)
    hotspot = sstValue - MAX_MONTHLY_MEAN
    alertLevel = getAlertLevel(dhw)
    status = getStatusLabel(dhw, hotspot)
    
    # Send alerts if needed
    alert_sent_recently = wasAlertSentToday(regionID)
    should_send_alert = bool(alertLevel) and (bypass_daily_alert_lock or not alert_sent_recently)

    pending_alert = None
    if should_send_alert:
        recipients = getNotificationRecipients()
        if not recipients:
            print("[SST] No notification recipients found for roleID 1 or 2")
        else:
            subject = f"[CoralKita] Bleaching {alertLevel} - {regionName}"
            body = (
                f"Dear CoralKita User,\n\n"
                f"A coral bleaching {alertLevel.lower()} has been detected at {regionName}.\n\n"
                f"Current DHW: {dhw} °C-weeks\n"
                f"Alert Level: {alertLevel}\n"
                f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n\n"
                f"Please log in to CoralKita to review the latest SST data and take necessary action.\n\n"
                f"- CoralKita Team"
            )
            emails = [u["email"] for u in recipients if u.get("email")]
            pending_alert = {"emails": emails, "subject": subject, "body": body}
        createAlert(regionID, alertLevel)
        print(
            f"[SST] Alert triggered for {regionName}: "
            f"dhw={dhw}, level={alertLevel}, bypass_lock={bypass_daily_alert_lock}"
        )
    elif alertLevel:
        print(
            f"[SST] Alert suppressed for {regionName}: "
            f"dhw={dhw}, level={alertLevel}, alert_sent_recently={alert_sent_recently}"
        )
    else:
        print(
            f"[SST] No alert for {regionName}: dhw={dhw}, hotspot={round(hotspot, 2)}"
        )
    
    result = {
        "regionID": regionID,
        "regionName": regionName,
        "sstValue": sstValue,
        "dhw": dhw,
        "daysAccumulated": daysAccumulated,
        "hotspot": round(hotspot, 2),
        "alertLevel": alertLevel,
        "status": status,
        "coralCount": coralCounts.get(regionID, 0),
        "latitude": latitude,
        "longitude": longitude
    }
    if pending_alert:
        result["_pending_alert"] = pending_alert
    return result


def _dispatch_alert_emails(pending_alerts: list[dict]) -> None:
    """Send alert emails on a background thread so /api/sst can respond quickly."""
    for item in pending_alerts:
        try:
            send_email_to_recipients(
                item["emails"],
                item["subject"],
                item["body"],
                log_prefix="[SST]",
            )
        except Exception as e:
            print(f"[SST] Background email dispatch failed: {e}")


def processSSTForAllRegions(bypass_daily_alert_lock: bool = False) -> list:
    """
    Process SST data for all regions in parallel.
    
    Returns:
        List of processed region data dictionaries
    """
    regions = getAllRegions()
    coralCounts = getCoralCountByRegion()
    results = []
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(processRegionSST, region, coralCounts, bypass_daily_alert_lock)
            for region in regions
        ]
        
        pending_alerts: list[dict] = []
        for future in as_completed(futures):
            result = future.result()
            if result is None:
                continue
            pending = result.pop("_pending_alert", None)
            if pending:
                pending_alerts.append(pending)
            results.append(result)

    if pending_alerts:
        threading.Thread(
            target=_dispatch_alert_emails,
            args=(pending_alerts,),
            daemon=True,
            name="sst-alert-email",
        ).start()

    return results


# ============================================================================
# 6. CACHE MANAGEMENT
# ============================================================================

def getCachedSST(bypass_daily_alert_lock: bool = False) -> list:
    """
    Get cached SST data or fetch fresh if cache is stale.
    
    Cache resets daily at midnight.
    
    Returns:
        List of processed region data dictionaries
    """
    today = datetime.now().date()
    
    if _sst_cache["data"] is not None and _sst_cache["date"] == today:
        print("[SST] Returning cached data")
        return _sst_cache["data"]
    
    print("[SST] Cache miss — fetching from NOAA")
    results = processSSTForAllRegions(bypass_daily_alert_lock=bypass_daily_alert_lock)
    _sst_cache["data"] = results
    _sst_cache["date"] = today
    return results


def clearSSTCache() -> None:
    """Force clear the SST cache."""
    global _sst_cache
    _sst_cache = {"data": None, "date": None}
    print("[SST] Cache cleared")


# ============================================================================
# 7. API ROUTES
# ============================================================================

@sst_bp.route("/api/sst")
def sstData():
    """
    GET endpoint for SST monitoring data.
    
    Returns JSON array of processed region data with SST, DHW, and alert status.
    Requires user authentication.
    """
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    # Testing helper: /api/sst?refresh=1 will force reprocessing (including alert logic).
    # In SST_TEST_MODE, always refresh.
    if SST_TEST_MODE or request.args.get("refresh") == "1":
        clearSSTCache()
    bypass_daily_alert_lock = SST_TEST_MODE or (request.args.get("force_alert") == "1")

    try:
        results = getCachedSST(bypass_daily_alert_lock=bypass_daily_alert_lock)
        return jsonify(results)
    except Exception as e:
        print(f"[SST] /api/sst error: {e}")
        return jsonify({"error": "Failed to load SST data"}), 500