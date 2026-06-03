"""
SSTReading DAO Module
=====================
Data Access Object for SSTReading table operations.
Handles storage and retrieval of Sea Surface Temperature readings for coral reef monitoring.
"""

import mysql.connector
from datetime import datetime
from util.DBConnection import getConnection


# ============================================================================
# 1. CREATE OPERATIONS
# ============================================================================

def createSSTReading(regionID: int, sstValue: float, recordedAt: datetime = None) -> int | None:
    """
    Create a new SST reading record.
    
    Args:
        regionID: ID of the region where reading was taken
        sstValue: Sea Surface Temperature value in Celsius
        recordedAt: Timestamp when reading was recorded (defaults to current time)
    
    Returns:
        The ID of the newly created SST reading, or None if failed
        
    Example:
        >>> reading_id = createSSTReading(1, 29.5)
        >>> print(f"SST reading {reading_id} created")
    """
    if recordedAt is None:
        recordedAt = datetime.now()
    
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO SSTReading (regionID, sstValue, recordedAt)
            VALUES (%s, %s, %s)
            """,
            (regionID, sstValue, recordedAt)
        )
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error as e:
        print(f"Database error in createSSTReading: {e}")
        conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def bulkCreateSSTReadings(readings: list[tuple]) -> list[int]:
    """
    Create multiple SST reading records in batch.
    
    Args:
        readings: List of tuples, each containing (regionID, sstValue, recordedAt)
    
    Returns:
        List of created reading IDs (empty list if failed)
        
    Example:
        >>> readings = [(1, 29.5, datetime.now()), (2, 30.1, datetime.now())]
        >>> ids = bulkCreateSSTReadings(readings)
    """
    conn = getConnection()
    cursor = None
    created_ids = []
    
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO SSTReading (regionID, sstValue, recordedAt)
            VALUES (%s, %s, %s)
        """
        cursor.executemany(sql, readings)
        conn.commit()
        
        # Get the last inserted IDs
        first_id = cursor.lastrowid
        for i in range(len(readings)):
            created_ids.append(first_id + i)
        
        return created_ids
    except mysql.connector.Error as e:
        print(f"Database error in bulkCreateSSTReadings: {e}")
        conn.rollback()
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 2. READ OPERATIONS (Single Records)
# ============================================================================

def getReadingByID(sstID: int) -> dict | None:
    """
    Retrieve an SST reading record by its ID.
    
    Args:
        sstID: ID of the SST reading to retrieve
    
    Returns:
        Dictionary containing SST reading data, or None if not found
        
    Example:
        >>> reading = getReadingByID(123)
        >>> print(f"SST: {reading['sstValue']}°C")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM SSTReading WHERE sstID = %s LIMIT 1",
            (sstID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getReadingByID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getLatestReadingByRegion(regionID: int) -> dict | None:
    """
    Get the most recent SST reading for a specific region.
    
    Args:
        regionID: ID of the region
    
    Returns:
        Dictionary containing the latest reading data, or None if no readings
        
    Example:
        >>> latest = getLatestReadingByRegion(1)
        >>> if latest:
        ...     print(f"Latest SST: {latest['sstValue']}°C at {latest['recordedAt']}")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM SSTReading
            WHERE regionID = %s
            ORDER BY recordedAt DESC
            LIMIT 1
            """,
            (regionID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getLatestReadingByRegion: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getTodayReadingByRegion(regionID: int) -> dict | None:
    """
    Get today's SST reading for a specific region.
    
    Args:
        regionID: ID of the region
    
    Returns:
        Dictionary containing today's reading data, or None if no reading today
        
    Example:
        >>> today = getTodayReadingByRegion(1)
        >>> if today:
        ...     print(f"Today's SST: {today['sstValue']}°C")
        ... else:
        ...     print("No reading recorded today")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM SSTReading
            WHERE regionID = %s AND DATE(recordedAt) = CURDATE()
            LIMIT 1
            """,
            (regionID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getTodayReadingByRegion: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 3. READ OPERATIONS (Multiple Records)
# ============================================================================

def getReadingsByRegion(regionID: int, startDate: datetime = None, limit: int = None) -> list[dict]:
    """
    Get SST readings for a specific region, ordered newest first.
    
    Args:
        regionID: ID of the region
        startDate: Optional start date filter (get readings after this date)
        limit: Maximum number of readings to return (optional)
    
    Returns:
        List of dictionaries containing SST reading data (empty list if none found)
        
    Example:
        >>> readings = getReadingsByRegion(1, limit=10)
        >>> for r in readings:
        ...     print(f"{r['recordedAt']}: {r['sstValue']}°C")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if startDate is None:
            query = """
                SELECT * FROM SSTReading
                WHERE regionID = %s
                ORDER BY recordedAt DESC
            """
            params = [regionID]
        else:
            query = """
                SELECT * FROM SSTReading
                WHERE regionID = %s AND recordedAt >= %s
                ORDER BY recordedAt DESC
            """
            params = [regionID, startDate]
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        cursor.execute(query, params)
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getReadingsByRegion: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getRecentReadings(regionID: int, weeks: int = 12) -> list[dict]:
    """
    Get recent SST readings for DHW (Degree Heating Week) calculation.
    
    Args:
        regionID: ID of the region
        weeks: Number of weeks to look back (default 12 weeks for DHW)
    
    Returns:
        List of dictionaries containing SST readings in the time window
        
    Example:
        >>> readings = getRecentReadings(1, weeks=12)
        >>> print(f"Found {len(readings)} readings for DHW calculation")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM SSTReading
            WHERE regionID = %s
              AND recordedAt >= DATE_SUB(NOW(), INTERVAL %s WEEK)
            ORDER BY recordedAt DESC
            """,
            (regionID, weeks)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getRecentReadings: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getReadingsByDateRange(startDate: datetime, endDate: datetime, regionID: int = None) -> list[dict]:
    """
    Get SST readings within a specific date range.
    
    Args:
        startDate: Start of date range
        endDate: End of date range
        regionID: Optional region ID to filter by
    
    Returns:
        List of dictionaries containing SST readings
        
    Example:
        >>> from datetime import datetime, timedelta
        >>> start = datetime.now() - timedelta(days=30)
        >>> readings = getReadingsByDateRange(start, datetime.now())
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if regionID:
            query = """
                SELECT * FROM SSTReading
                WHERE regionID = %s
                  AND recordedAt BETWEEN %s AND %s
                ORDER BY recordedAt DESC
            """
            cursor.execute(query, (regionID, startDate, endDate))
        else:
            query = """
                SELECT * FROM SSTReading
                WHERE recordedAt BETWEEN %s AND %s
                ORDER BY recordedAt DESC
            """
            cursor.execute(query, (startDate, endDate))
        
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getReadingsByDateRange: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getAllReadingsForRegion(regionID: int) -> list[dict]:
    """
    Get all SST readings for a region (no date filters).
    
    Args:
        regionID: ID of the region
    
    Returns:
        List of all SST readings for the region, ordered newest first
    """
    return getReadingsByRegion(regionID, startDate=None, limit=None)


# ============================================================================
# 4. STATISTICS & AGGREGATION
# ============================================================================

def getAverageSSTByRegion(regionID: int, days: int = 30) -> float | None:
    """
    Calculate average SST for a region over a specified period.
    
    Args:
        regionID: ID of the region
        days: Number of days to average over (default 30)
    
    Returns:
        Average SST value, or None if no readings found
        
    Example:
        >>> avg = getAverageSSTByRegion(1, days=7)
        >>> print(f"Weekly average SST: {avg}°C")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT AVG(sstValue) as avg_sst
            FROM SSTReading
            WHERE regionID = %s
              AND recordedAt >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """,
            (regionID, days)
        )
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else None
    except mysql.connector.Error as e:
        print(f"Database error in getAverageSSTByRegion: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getMaxSSTByRegion(regionID: int, days: int = 30) -> float | None:
    """
    Get maximum SST for a region over a specified period.
    
    Args:
        regionID: ID of the region
        days: Number of days to look back (default 30)
    
    Returns:
        Maximum SST value, or None if no readings found
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT MAX(sstValue) as max_sst
            FROM SSTReading
            WHERE regionID = %s
              AND recordedAt >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """,
            (regionID, days)
        )
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else None
    except mysql.connector.Error as e:
        print(f"Database error in getMaxSSTByRegion: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getMinSSTByRegion(regionID: int, days: int = 30) -> float | None:
    """
    Get minimum SST for a region over a specified period.
    
    Args:
        regionID: ID of the region
        days: Number of days to look back (default 30)
    
    Returns:
        Minimum SST value, or None if no readings found
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT MIN(sstValue) as min_sst
            FROM SSTReading
            WHERE regionID = %s
              AND recordedAt >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """,
            (regionID, days)
        )
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else None
    except mysql.connector.Error as e:
        print(f"Database error in getMinSSTByRegion: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getSSTTrend(regionID: int, days: int = 30) -> dict:
    """
    Analyze SST trend for a region.
    
    Args:
        regionID: ID of the region
        days: Number of days to analyze (default 30)
    
    Returns:
        Dictionary containing trend analysis:
        - current: Most recent SST
        - average: Average SST over period
        - max: Maximum SST
        - min: Minimum SST
        - change_rate: Rate of change per day
        
    Example:
        >>> trend = getSSTTrend(1, days=7)
        >>> print(f"Current: {trend['current']}°C")
        >>> print(f"Change rate: {trend['change_rate']}°C/day")
    """
    readings = getReadingsByRegion(regionID, limit=days)
    
    if not readings:
        return {}
    
    sst_values = [r['sstValue'] for r in readings]
    
    # Calculate simple linear regression for trend
    n = len(sst_values)
    if n > 1:
        x = list(range(n))
        mean_x = sum(x) / n
        mean_y = sum(sst_values) / n
        
        numerator = sum((x[i] - mean_x) * (sst_values[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
    else:
        slope = 0
    
    return {
        'current': readings[0]['sstValue'],
        'average': sum(sst_values) / n,
        'max': max(sst_values),
        'min': min(sst_values),
        'change_rate': slope,
        'readings_count': n,
        'period_days': days
    }


def getHotspotCount(regionID: int, threshold: float = 29.0) -> int:
    """
    Count number of readings above a threshold (hotspots).
    
    Args:
        regionID: ID of the region
        threshold: Temperature threshold in Celsius (default 29.0°C)
    
    Returns:
        Number of hotspot readings
        
    Example:
        >>> hotspot_count = getHotspotCount(1, threshold=29.0)
        >>> print(f"Hotspots detected: {hotspot_count}")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) as hotspot_count
            FROM SSTReading
            WHERE regionID = %s AND sstValue > %s
            """,
            (regionID, threshold)
        )
        result = cursor.fetchone()
        return result[0] if result else 0
    except mysql.connector.Error as e:
        print(f"Database error in getHotspotCount: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 5. VALIDATION & UTILITY FUNCTIONS
# ============================================================================

def readingExists(sstID: int) -> bool:
    """
    Check if an SST reading exists in the database.
    
    Args:
        sstID: ID of the SST reading to check
    
    Returns:
        True if reading exists, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM SSTReading WHERE sstID = %s",
            (sstID,)
        )
        result = cursor.fetchone()
        return result[0] > 0 if result else False
    except mysql.connector.Error as e:
        print(f"Database error in readingExists: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def hasReadingsToday(regionID: int) -> bool:
    """
    Check if there are any SST readings for today.
    
    Args:
        regionID: ID of the region
    
    Returns:
        True if reading exists for today, False otherwise
    """
    reading = getTodayReadingByRegion(regionID)
    return reading is not None


def getReadingCountByRegion(regionID: int) -> int:
    """
    Get total number of SST readings for a region.
    
    Args:
        regionID: ID of the region
    
    Returns:
        Total reading count for the region
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM SSTReading WHERE regionID = %s",
            (regionID,)
        )
        result = cursor.fetchone()
        return result[0] if result else 0
    except mysql.connector.Error as e:
        print(f"Database error in getReadingCountByRegion: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 6. UPDATE OPERATIONS
# ============================================================================

def updateSSTReading(sstID: int, sstValue: float) -> bool:
    """
    Update an SST reading value.
    
    Args:
        sstID: ID of the reading to update
        sstValue: New SST value
    
    Returns:
        True if update successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE SSTReading
            SET sstValue = %s
            WHERE sstID = %s
            """,
            (sstValue, sstID)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in updateSSTReading: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 7. DELETE OPERATIONS
# ============================================================================

def deleteReading(sstID: int) -> bool:
    """
    Delete an SST reading record.
    
    Args:
        sstID: ID of the reading to delete
    
    Returns:
        True if deletion successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM SSTReading WHERE sstID = %s",
            (sstID,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in deleteReading: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def deleteReadingsByRegion(regionID: int) -> int:
    """
    Delete all SST readings for a specific region.
    
    Args:
        regionID: ID of the region whose readings should be deleted
    
    Returns:
        Number of readings deleted
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM SSTReading WHERE regionID = %s",
            (regionID,)
        )
        conn.commit()
        return cursor.rowcount
    except mysql.connector.Error as e:
        print(f"Database error in deleteReadingsByRegion: {e}")
        conn.rollback()
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def deleteOldReadings(days: int = 90) -> int:
    """
    Delete SST readings older than a specified number of days.
    
    Args:
        days: Number of days to keep readings for (older than this are deleted)
    
    Returns:
        Number of readings deleted
        
    Example:
        >>> deleted = deleteOldReadings(days=180)
        >>> print(f"Deleted {deleted} old SST readings")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM SSTReading
            WHERE recordedAt < DATE_SUB(NOW(), INTERVAL %s DAY)
            """,
            (days,)
        )
        conn.commit()
        return cursor.rowcount
    except mysql.connector.Error as e:
        print(f"Database error in deleteOldReadings: {e}")
        conn.rollback()
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()