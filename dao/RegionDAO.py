"""
Region DAO Module
=================
Data Access Object for Region table operations.
Handles retrieval of geographic region reference data for coral locations.
"""

import mysql.connector
from util.DBConnection import getConnection


# ============================================================================
# 1. READ OPERATIONS (Single Records)
# ============================================================================

def getRegionByID(regionID: int) -> dict | None:
    """
    Retrieve a region record by its ID.
    
    Args:
        regionID: ID of the region to retrieve
    
    Returns:
        Dictionary containing region data, or None if not found
        
    Example:
        >>> region = getRegionByID(1)
        >>> print(region['regionName'])
        'Tioman Island'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM Region WHERE regionID = %s LIMIT 1",
            (regionID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getRegionByID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getRegionByName(regionName: str) -> dict | None:
    """
    Retrieve a region record by its name.
    
    Args:
        regionName: Name of the region to retrieve (e.g., 'Tioman Island')
    
    Returns:
        Dictionary containing region data, or None if not found
        
    Example:
        >>> region = getRegionByName('Redang Island')
        >>> print(region['regionID'])
        2
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM Region WHERE regionName = %s LIMIT 1",
            (regionName,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getRegionByName: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getRegionByCoordinates(latitude: float, longitude: float, tolerance: float = 0.01) -> dict | None:
    """
    Retrieve a region by geographic coordinates within a tolerance.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        tolerance: Tolerance for coordinate matching (default 0.01 degrees ~ 1km)
    
    Returns:
        Dictionary containing region data, or None if not found
        
    Example:
        >>> region = getRegionByCoordinates(2.8, 104.2)
        >>> print(region['regionName'])
        'Tioman Island'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM Region
            WHERE ABS(latitude - %s) <= %s
              AND ABS(longitude - %s) <= %s
            LIMIT 1
            """,
            (latitude, tolerance, longitude, tolerance)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getRegionByCoordinates: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 2. READ OPERATIONS (Multiple Records)
# ============================================================================

def getAllRegions() -> list[dict]:
    """
    Retrieve all regions, ordered alphabetically by name.
    
    Returns:
        List of dictionaries containing region data (empty list if none found)
        
    Example:
        >>> regions = getAllRegions()
        >>> for r in regions:
        ...     print(f"{r['regionName']}: {r['latitude']}, {r['longitude']}")
        'Perhentian Islands': 5.9167, 102.7333
        'Redang Island': 5.7667, 103.0167
        'Tioman Island': 2.8000, 104.2000
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Region ORDER BY regionName")
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getAllRegions: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getRegionsByCoralCount(minCorals: int = 0, limit: int = 50) -> list[dict]:
    """
    Retrieve regions with their coral count, ordered by coral density.
    
    Args:
        minCorals: Minimum number of corals to include
        limit: Maximum number of records to return
    
    Returns:
        List of dictionaries containing region data with coralCount
        
    Example:
        >>> regions = getRegionsByCoralCount(minCorals=5)
        >>> for r in regions:
        ...     print(f"{r['regionName']}: {r['coralCount']} corals")
        'Tioman Island': 45
        'Redang Island': 32
        'Perhentian Islands': 28
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
                r.latitude,
                r.longitude,
                COUNT(c.coralID) as coralCount
            FROM Region r
            LEFT JOIN Coral c ON r.regionID = c.regionID
            GROUP BY r.regionID, r.regionName, r.latitude, r.longitude
            HAVING coralCount >= %s
            ORDER BY coralCount DESC
            LIMIT %s
            """,
            (minCorals, limit)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getRegionsByCoralCount: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getRegionsByStatus(alertLevel: str = None, isActive: bool = True) -> list[dict]:
    """
    Retrieve regions filtered by alert status.
    
    Args:
        alertLevel: Optional alert level filter (e.g., 'No Stress', 'Bleaching Watch')
        isActive: Filter by active status
    
    Returns:
        List of dictionaries containing region data
        
    Example:
        >>> regions = getRegionsByStatus(alertLevel='Bleaching Watch')
        >>> for r in regions:
        ...     print(f"{r['regionName']}: {r['alertLevel']}")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Base query with SST join for status
        query = """
            SELECT DISTINCT
                r.regionID,
                r.regionName,
                r.latitude,
                r.longitude,
                r.isActive,
                s.sstValue,
                s.status as alertLevel
            FROM Region r
            LEFT JOIN SSTReading s ON r.regionID = s.regionID
            WHERE r.isActive = %s
        """
        params = [isActive]
        
        if alertLevel:
            query += " AND s.status = %s"
            params.append(alertLevel)
        
        query += " ORDER BY r.regionName"
        
        cursor.execute(query, params)
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getRegionsByStatus: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getNearbyRegions(latitude: float, longitude: float, radiusKm: float = 50) -> list[dict]:
    """
    Retrieve regions within a certain radius (approximate using latitude/longitude).
    
    Args:
        latitude: Center latitude
        longitude: Center longitude
        radiusKm: Search radius in kilometers
    
    Returns:
        List of dictionaries containing nearby region data
        
    Note:
        This is an approximation. 1 degree latitude ≈ 111 km
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        # Approximate: 1 degree = 111 km
        degree_range = radiusKm / 111.0
        
        cursor.execute(
            """
            SELECT * FROM Region
            WHERE ABS(latitude - %s) <= %s
              AND ABS(longitude - %s) <= %s
            ORDER BY regionName
            """,
            (latitude, degree_range, longitude, degree_range)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getNearbyRegions: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 3. VALIDATION & UTILITY FUNCTIONS
# ============================================================================

def regionExists(regionID: int) -> bool:
    """
    Check if a region exists in the database.
    
    Args:
        regionID: ID of the region to check
    
    Returns:
        True if region exists, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM Region WHERE regionID = %s",
            (regionID,)
        )
        result = cursor.fetchone()
        return result[0] > 0 if result else False
    except mysql.connector.Error as e:
        print(f"Database error in regionExists: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def isValidRegion(regionName: str) -> bool:
    """
    Validate if a region name exists in the database.
    
    Args:
        regionName: Name of the region to validate
    
    Returns:
        True if region is valid, False otherwise
    """
    region = getRegionByName(regionName)
    return region is not None


def getRegionIDMap() -> dict[str, int]:
    """
    Get a mapping of region names to their IDs.
    Useful for form dropdowns and validation.
    
    Returns:
        Dictionary mapping regionName to regionID
        
    Example:
        >>> mapping = getRegionIDMap()
        >>> print(mapping)
        {'Tioman Island': 1, 'Redang Island': 2, 'Perhentian Islands': 3}
    """
    conn = getConnection()
    cursor = None
    result = {}
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT regionID, regionName FROM Region")
        rows = cursor.fetchall()
        for row in rows:
            result[row['regionName']] = row['regionID']
        return result
    except mysql.connector.Error as e:
        print(f"Database error in getRegionIDMap: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getRegionCoordinatesDict() -> dict[int, tuple[float, float]]:
    """
    Get a dictionary of region coordinates by region ID.
    Useful for map visualizations.
    
    Returns:
        Dictionary mapping regionID to (latitude, longitude) tuple
        
    Example:
        >>> coords = getRegionCoordinatesDict()
        >>> print(coords[1])
        (2.8, 104.2)
    """
    conn = getConnection()
    cursor = None
    result = {}
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT regionID, latitude, longitude FROM Region")
        rows = cursor.fetchall()
        for row in rows:
            result[row['regionID']] = (row['latitude'], row['longitude'])
        return result
    except mysql.connector.Error as e:
        print(f"Database error in getRegionCoordinatesDict: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 4. STATISTICS & AGGREGATION
# ============================================================================

def getRegionStatistics() -> list[dict]:
    """
    Get comprehensive statistics for each region.
    
    Returns:
        List of dictionaries containing region statistics:
        - coralCount: Total corals in region
        - approvedCount: Approved corals
        - pendingCount: Pending reviews
        - bleachingCount: Corals with bleaching status
        
    Example:
        >>> stats = getRegionStatistics()
        >>> for s in stats:
        ...     print(f"{s['regionName']}: {s['coralCount']} corals")
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
                COUNT(DISTINCT c.coralID) as coralCount,
                SUM(CASE WHEN rev.reviewStatus = 'approved' THEN 1 ELSE 0 END) as approvedCount,
                SUM(CASE WHEN rev.reviewStatus = 'pending' THEN 1 ELSE 0 END) as pendingCount,
                SUM(CASE WHEN h.healthName = 'Bleaching' THEN 1 ELSE 0 END) as bleachingCount
            FROM Region r
            LEFT JOIN Coral c ON r.regionID = c.regionID
            LEFT JOIN CoralImage ci ON c.coralID = ci.coralID
            LEFT JOIN Classification cl ON ci.imageID = cl.imageID
            LEFT JOIN HealthStatus h ON cl.healthID = h.healthID
            LEFT JOIN Review rev ON cl.classID = rev.classID
            GROUP BY r.regionID, r.regionName
            ORDER BY r.regionName
            """
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getRegionStatistics: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getTotalRegionCount() -> int:
    """
    Get the total number of regions in the database.
    
    Returns:
        Total count of regions
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Region")
        result = cursor.fetchone()
        return result[0] if result else 0
    except mysql.connector.Error as e:
        print(f"Database error in getTotalRegionCount: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getRegionWithMostCorals() -> dict | None:
    """
    Get the region with the highest number of coral records.
    
    Returns:
        Dictionary containing region data with coralCount, or None if no corals
        
    Example:
        >>> region = getRegionWithMostCorals()
        >>> print(f"{region['regionName']}: {region['coralCount']} corals")
        'Tioman Island: 45 corals'
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
                COUNT(c.coralID) as coralCount
            FROM Region r
            JOIN Coral c ON r.regionID = c.regionID
            GROUP BY r.regionID, r.regionName
            ORDER BY coralCount DESC
            LIMIT 1
            """
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getRegionWithMostCorals: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 5. ADMIN OPERATIONS (Optional - for managing reference data)
# ============================================================================

def createRegion(
    regionName: str,
    latitude: float,
    longitude: float,
    description: str = None,
    isActive: bool = True
) -> int | None:
    """
    Create a new region (admin function).
    
    Args:
        regionName: Name of the region
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        description: Optional description
        isActive: Whether the region is active (default True)
    
    Returns:
        The ID of the newly created region, or None if failed
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Region (regionName, latitude, longitude, description, isActive)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (regionName, latitude, longitude, description, isActive)
        )
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error as e:
        print(f"Database error in createRegion: {e}")
        conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def updateRegion(
    regionID: int,
    regionName: str = None,
    latitude: float = None,
    longitude: float = None,
    description: str = None,
    isActive: bool = None
) -> bool:
    """
    Update an existing region (admin function).
    
    Args:
        regionID: ID of the region to update
        regionName: New region name (optional)
        latitude: New latitude (optional)
        longitude: New longitude (optional)
        description: New description (optional)
        isActive: New active status (optional)
    
    Returns:
        True if update successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        
        # Build dynamic update query
        updates = []
        params = []
        
        if regionName is not None:
            updates.append("regionName = %s")
            params.append(regionName)
        if latitude is not None:
            updates.append("latitude = %s")
            params.append(latitude)
        if longitude is not None:
            updates.append("longitude = %s")
            params.append(longitude)
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        if isActive is not None:
            updates.append("isActive = %s")
            params.append(isActive)
        
        if not updates:
            return False
        
        params.append(regionID)
        query = f"UPDATE Region SET {', '.join(updates)} WHERE regionID = %s"
        
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in updateRegion: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def deleteRegion(regionID: int) -> bool:
    """
    Delete a region (admin function).
    Note: May fail if region has associated corals.
    
    Args:
        regionID: ID of the region to delete
    
    Returns:
        True if deletion successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM Region WHERE regionID = %s",
            (regionID,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in deleteRegion: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()