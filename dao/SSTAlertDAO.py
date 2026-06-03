"""
SSTAlert DAO Module
===================
Data Access Object for SSTAlert table operations.
Handles tracking of coral bleaching alerts sent for Sea Surface Temperature events.
"""

import mysql.connector
from datetime import datetime
from util.DBConnection import getConnection


# ============================================================================
# 1. CREATE OPERATIONS
# ============================================================================

def createAlert(regionID: int, alertLevel: str, sentAt: datetime = None) -> int | None:
    """
    Create a new SST alert record.
    
    Args:
        regionID: ID of the region where alert was triggered
        alertLevel: Alert level ('Alert Level 1', 'Alert Level 2')
        sentAt: Timestamp when alert was sent (defaults to current time)
    
    Returns:
        The ID of the newly created alert, or None if failed
        
    Example:
        >>> alert_id = createAlert(1, 'Alert Level 1')
        >>> print(f"Alert {alert_id} created")
    """
    if sentAt is None:
        sentAt = datetime.now()
    
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO sstalert (regionID, alertLevel, sentAt)
            VALUES (%s, %s, %s)
            """,
            (regionID, alertLevel, sentAt)
        )
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error as e:
        print(f"Database error in createAlert: {e}")
        conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 2. READ OPERATIONS (Single Records)
# ============================================================================

def getAlertByID(alertID: int) -> dict | None:
    """
    Retrieve an alert record by its ID.
    
    Args:
        alertID: ID of the alert to retrieve
    
    Returns:
        Dictionary containing alert data, or None if not found
        
    Example:
        >>> alert = getAlertByID(123)
        >>> print(alert['alertLevel'])
        'Alert Level 1'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM sstalert WHERE alertID = %s LIMIT 1",
            (alertID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getAlertByID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getLastAlert(regionID: int) -> dict | None:
    """
    Get the most recent alert for a specific region.
    
    Args:
        regionID: ID of the region to check
    
    Returns:
        Dictionary containing the latest alert data, or None if no alerts found
        
    Example:
        >>> last_alert = getLastAlert(1)
        >>> if last_alert:
        ...     print(f"Last alert: {last_alert['alertLevel']} on {last_alert['sentAt']}")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM sstalert
            WHERE regionID = %s
            ORDER BY sentAt DESC
            LIMIT 1
            """,
            (regionID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getLastAlert: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getLatestAlertByLevel(alertLevel: str) -> dict | None:
    """
    Get the most recent alert of a specific level across all regions.
    
    Args:
        alertLevel: Alert level to filter by ('Alert Level 1' or 'Alert Level 2')
    
    Returns:
        Dictionary containing the latest alert data, or None if not found
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM sstalert
            WHERE alertLevel = %s
            ORDER BY sentAt DESC
            LIMIT 1
            """,
            (alertLevel,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getLatestAlertByLevel: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 3. READ OPERATIONS (Multiple Records)
# ============================================================================

def getAlertsByRegion(regionID: int, limit: int = None) -> list[dict]:
    """
    Get all alerts for a specific region, ordered newest first.
    
    Args:
        regionID: ID of the region to check
        limit: Maximum number of alerts to return (optional)
    
    Returns:
        List of dictionaries containing alert data (empty list if none found)
        
    Example:
        >>> alerts = getAlertsByRegion(1, limit=10)
        >>> for a in alerts:
        ...     print(f"{a['alertLevel']} - {a['sentAt']}")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM sstalert
            WHERE regionID = %s
            ORDER BY sentAt DESC
        """
        params = [regionID]
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        cursor.execute(query, params)
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getAlertsByRegion: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getAlertsByDateRange(start_date: datetime, end_date: datetime) -> list[dict]:
    """
    Get alerts sent within a specific date range.
    
    Args:
        start_date: Start of date range
        end_date: End of date range
    
    Returns:
        List of dictionaries containing alert data
        
    Example:
        >>> from datetime import datetime, timedelta
        >>> start = datetime.now() - timedelta(days=7)
        >>> alerts = getAlertsByDateRange(start, datetime.now())
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM sstalert
            WHERE sentAt BETWEEN %s AND %s
            ORDER BY sentAt DESC
            """,
            (start_date, end_date)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getAlertsByDateRange: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getAllAlerts(limit: int = 100) -> list[dict]:
    """
    Get all alerts across all regions, ordered newest first.
    
    Args:
        limit: Maximum number of alerts to return (default 100)
    
    Returns:
        List of dictionaries containing alert data
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT a.*, r.regionName
            FROM sstalert a
            JOIN Region r ON a.regionID = r.regionID
            ORDER BY a.sentAt DESC
            LIMIT %s
            """,
            (limit,)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getAllAlerts: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getAlertsByLevel(alertLevel: str) -> list[dict]:
    """
    Get all alerts of a specific level across all regions.
    
    Args:
        alertLevel: Alert level to filter by ('Alert Level 1' or 'Alert Level 2')
    
    Returns:
        List of dictionaries containing alert data
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT a.*, r.regionName
            FROM sstalert a
            JOIN Region r ON a.regionID = r.regionID
            WHERE a.alertLevel = %s
            ORDER BY a.sentAt DESC
            """,
            (alertLevel,)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getAlertsByLevel: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 4. VALIDATION & UTILITY FUNCTIONS
# ============================================================================

def wasAlertSentToday(regionID: int) -> bool:
    """
    Check if an alert was sent for a region in the last 24 hours.
    Prevents duplicate alerts being sent too frequently.
    
    Args:
        regionID: ID of the region to check
    
    Returns:
        True if an alert was sent in the last 24 hours, False otherwise
        
    Example:
        >>> if not wasAlertSentToday(1):
        ...     send_alert(1)
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM sstalert
            WHERE regionID = %s
              AND sentAt >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER BY sentAt DESC
            LIMIT 1
            """,
            (regionID,)
        )
        return cursor.fetchone() is not None
    except mysql.connector.Error as e:
        print(f"Database error in wasAlertSentToday: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def wasAlertSentInLastHours(regionID: int, hours: int = 24) -> bool:
    """
    Check if an alert was sent for a region within a specified time window.
    
    Args:
        regionID: ID of the region to check
        hours: Number of hours to check back (default 24)
    
    Returns:
        True if an alert was sent in the specified time window, False otherwise
        
    Example:
        >>> if not wasAlertSentInLastHours(1, hours=48):
        ...     send_alert(1)
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            f"""
            SELECT * FROM sstalert
            WHERE regionID = %s
              AND sentAt >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            ORDER BY sentAt DESC
            LIMIT 1
            """,
            (regionID, hours)
        )
        return cursor.fetchone() is not None
    except mysql.connector.Error as e:
        print(f"Database error in wasAlertSentInLastHours: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getAlertCountByRegion(regionID: int) -> int:
    """
    Get total number of alerts sent for a specific region.
    
    Args:
        regionID: ID of the region
    
    Returns:
        Total alert count for the region
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM sstalert WHERE regionID = %s",
            (regionID,)
        )
        result = cursor.fetchone()
        return result[0] if result else 0
    except mysql.connector.Error as e:
        print(f"Database error in getAlertCountByRegion: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getRegionAlertFrequency(regionID: int) -> dict:
    """
    Get alert frequency statistics for a region.
    
    Args:
        regionID: ID of the region
    
    Returns:
        Dictionary containing alert frequency statistics
        
    Example:
        >>> stats = getRegionAlertFrequency(1)
        >>> print(f"Level 1 alerts: {stats['level1_count']}")
        >>> print(f"Level 2 alerts: {stats['level2_count']}")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT 
                alertLevel,
                COUNT(*) as count,
                MIN(sentAt) as first_alert,
                MAX(sentAt) as last_alert
            FROM sstalert
            WHERE regionID = %s
            GROUP BY alertLevel
            """,
            (regionID,)
        )
        results = cursor.fetchall()
        
        stats = {
            'total': 0,
            'level1_count': 0,
            'level2_count': 0,
            'first_alert': None,
            'last_alert': None
        }
        
        for row in results:
            stats['total'] += row['count']
            if row['alertLevel'] == 'Alert Level 1':
                stats['level1_count'] = row['count']
            elif row['alertLevel'] == 'Alert Level 2':
                stats['level2_count'] = row['count']
            
            if not stats['first_alert'] or row['first_alert'] < stats['first_alert']:
                stats['first_alert'] = row['first_alert']
            if not stats['last_alert'] or row['last_alert'] > stats['last_alert']:
                stats['last_alert'] = row['last_alert']
        
        return stats
    except mysql.connector.Error as e:
        print(f"Database error in getRegionAlertFrequency: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 5. STATISTICS & AGGREGATION
# ============================================================================

def getAlertStatistics() -> dict:
    """
    Get global alert statistics across all regions.
    
    Returns:
        Dictionary containing alert statistics
        
    Example:
        >>> stats = getAlertStatistics()
        >>> print(f"Total alerts: {stats['total_alerts']}")
        >>> print(f"Regions affected: {stats['regions_affected']}")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_alerts,
                COUNT(DISTINCT regionID) as regions_affected,
                SUM(CASE WHEN alertLevel = 'Alert Level 1' THEN 1 ELSE 0 END) as level1_count,
                SUM(CASE WHEN alertLevel = 'Alert Level 2' THEN 1 ELSE 0 END) as level2_count,
                MIN(sentAt) as first_alert,
                MAX(sentAt) as last_alert
            FROM sstalert
            """
        )
        return cursor.fetchone() or {}
    except mysql.connector.Error as e:
        print(f"Database error in getAlertStatistics: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getAlertsByMonth(year: int = None, month: int = None) -> list[dict]:
    """
    Get alerts grouped by month for trend analysis.
    
    Args:
        year: Specific year to filter (optional)
        month: Specific month to filter (optional, requires year)
    
    Returns:
        List of dictionaries containing monthly alert counts
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        where_clause = ""
        params = []
        
        if year:
            where_clause += " AND YEAR(sentAt) = %s"
            params.append(year)
        if month and year:
            where_clause += " AND MONTH(sentAt) = %s"
            params.append(month)
        
        query = f"""
            SELECT 
                DATE_FORMAT(sentAt, '%Y-%m') as month,
                COUNT(*) as alert_count,
                COUNT(DISTINCT regionID) as regions_affected
            FROM sstalert
            WHERE 1=1 {where_clause}
            GROUP BY DATE_FORMAT(sentAt, '%Y-%m')
            ORDER BY month DESC
        """
        
        cursor.execute(query, params)
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getAlertsByMonth: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getMostAffectedRegion() -> dict | None:
    """
    Get the region with the most alerts.
    
    Returns:
        Dictionary containing region data with alert count, or None if no alerts
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT 
                r.regionID,
                r.regionName,
                COUNT(a.alertID) as alert_count
            FROM sstalert a
            JOIN Region r ON a.regionID = r.regionID
            GROUP BY r.regionID, r.regionName
            ORDER BY alert_count DESC
            LIMIT 1
            """
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getMostAffectedRegion: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 6. DELETE OPERATIONS
# ============================================================================

def deleteAlert(alertID: int) -> bool:
    """
    Delete an alert record.
    
    Args:
        alertID: ID of the alert to delete
    
    Returns:
        True if deletion successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM sstalert WHERE alertID = %s",
            (alertID,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in deleteAlert: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def deleteAlertsByRegion(regionID: int) -> int:
    """
    Delete all alerts for a specific region.
    
    Args:
        regionID: ID of the region whose alerts should be deleted
    
    Returns:
        Number of alerts deleted
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM sstalert WHERE regionID = %s",
            (regionID,)
        )
        conn.commit()
        return cursor.rowcount
    except mysql.connector.Error as e:
        print(f"Database error in deleteAlertsByRegion: {e}")
        conn.rollback()
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def deleteOldAlerts(days: int = 30) -> int:
    """
    Delete alerts older than a specified number of days.
    
    Args:
        days: Number of days to keep alerts for (alerts older than this are deleted)
    
    Returns:
        Number of alerts deleted
        
    Example:
        >>> deleted = deleteOldAlerts(days=90)
        >>> print(f"Deleted {deleted} old alerts")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM sstalert
            WHERE sentAt < DATE_SUB(NOW(), INTERVAL %s DAY)
            """,
            (days,)
        )
        conn.commit()
        return cursor.rowcount
    except mysql.connector.Error as e:
        print(f"Database error in deleteOldAlerts: {e}")
        conn.rollback()
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()