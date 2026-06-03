"""
HealthStatus DAO Module
=======================
Data Access Object for HealthStatus table operations.
Handles retrieval of coral health status reference data (e.g., Healthy, Bleaching, Dead).
"""

import mysql.connector
from util.DBConnection import getConnection


# ============================================================================
# 1. READ OPERATIONS (Single Records)
# ============================================================================

def getHealthStatusByID(healthID: int) -> dict | None:
    """
    Retrieve a health status record by its ID.
    
    Args:
        healthID: ID of the health status to retrieve
    
    Returns:
        Dictionary containing health status data, or None if not found
        
    Example:
        >>> status = getHealthStatusByID(1)
        >>> print(status['healthName'])
        'Healthy'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM HealthStatus WHERE healthID = %s LIMIT 1",
            (healthID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getHealthStatusByID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getHealthStatusByName(healthName: str) -> dict | None:
    """
    Get health status by name (e.g., 'Healthy', 'Bleaching', 'Dead').
    
    Args:
        healthName: Name of the health status (case-sensitive as in database)
    
    Returns:
        Dictionary containing health status data, or None if not found
        
    Example:
        >>> status = getHealthStatusByName('Bleaching')
        >>> print(status['healthID'])
        3
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM HealthStatus WHERE healthName = %s LIMIT 1",
            (healthName,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getHealthStatusByName: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getHealthStatusByConfidenceRange(minConfidence: float = 0, maxConfidence: float = 100) -> dict | None:
    """
    Get health status that typically corresponds to a confidence range.
    Note: This is a utility function based on common confidence thresholds.
    
    Args:
        minConfidence: Minimum confidence score
        maxConfidence: Maximum confidence score
    
    Returns:
        Dictionary containing health status data, or None if no match
    
    Example:
        >>> status = getHealthStatusByConfidenceRange(75, 100)
        >>> print(status['healthName'])
        'Healthy'
    """
    # Default confidence-based mapping
    if minConfidence >= 75:
        return getHealthStatusByName('Healthy')
    elif minConfidence >= 50:
        return getHealthStatusByName('Stressed')
    elif minConfidence >= 25:
        return getHealthStatusByName('Bleaching')
    else:
        return getHealthStatusByName('Dead')


# ============================================================================
# 2. READ OPERATIONS (Multiple Records)
# ============================================================================

def getAllHealthStatus() -> list[dict]:
    """
    Retrieve all health status records, ordered alphabetically by name.
    
    Returns:
        List of dictionaries containing health status data (empty list if none found)
        
    Example:
        >>> statuses = getAllHealthStatus()
        >>> for s in statuses:
        ...     print(f"{s['healthID']}: {s['healthName']}")
        1: Bleaching
        2: Dead
        3: Healthy
        4: Stressed
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM HealthStatus ORDER BY healthName")
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getAllHealthStatus: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getHealthStatusBySeverity(includeCritical: bool = True) -> list[dict]:
    """
    Retrieve health statuses ordered by severity (most severe first).
    
    Args:
        includeCritical: Whether to include critical/dead statuses
    
    Returns:
        List of dictionaries containing health status data ordered by severity
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Order by severity: Dead > Bleaching > Stressed > Healthy
        severity_order = """
            CASE healthName
                WHEN 'Dead' THEN 1
                WHEN 'Bleaching' THEN 2
                WHEN 'Stressed' THEN 3
                WHEN 'Healthy' THEN 4
                ELSE 5
            END
        """
        
        where_clause = ""
        if not includeCritical:
            where_clause = "WHERE healthName NOT IN ('Dead')"
        
        query = f"""
            SELECT * FROM HealthStatus
            {where_clause}
            ORDER BY {severity_order}
        """
        
        cursor.execute(query)
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getHealthStatusBySeverity: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 3. VALIDATION & UTILITY FUNCTIONS
# ============================================================================

def healthStatusExists(healthID: int) -> bool:
    """
    Check if a health status exists in the database.
    
    Args:
        healthID: ID of the health status to check
    
    Returns:
        True if health status exists, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM HealthStatus WHERE healthID = %s",
            (healthID,)
        )
        result = cursor.fetchone()
        return result[0] > 0 if result else False
    except mysql.connector.Error as e:
        print(f"Database error in healthStatusExists: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def isValidHealthStatus(healthName: str) -> bool:
    """
    Validate if a health status name is valid.
    
    Args:
        healthName: Name of the health status to validate
    
    Returns:
        True if health status is valid, False otherwise
    """
    status = getHealthStatusByName(healthName)
    return status is not None


def getHealthStatusIDMap() -> dict[str, int]:
    """
    Get a mapping of health status names to their IDs.
    Useful for form dropdowns and validation.
    
    Returns:
        Dictionary mapping healthName to healthID
        
    Example:
        >>> mapping = getHealthStatusIDMap()
        >>> print(mapping)
        {'Healthy': 1, 'Stressed': 2, 'Bleaching': 3, 'Dead': 4}
    """
    conn = getConnection()
    cursor = None
    result = {}
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT healthID, healthName FROM HealthStatus")
        rows = cursor.fetchall()
        for row in rows:
            result[row['healthName']] = row['healthID']
        return result
    except mysql.connector.Error as e:
        print(f"Database error in getHealthStatusIDMap: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 4. STATISTICS & AGGREGATION
# ============================================================================

def getHealthStatusDistribution() -> list[dict]:
    """
    Get distribution of corals by health status.
    
    Returns:
        List of dictionaries containing healthID, healthName, and coralCount
        
    Example:
        >>> stats = getHealthStatusDistribution()
        >>> for s in stats:
        ...     print(f"{s['healthName']}: {s['coralCount']} corals")
        Healthy: 45
        Stressed: 12
        Bleaching: 8
        Dead: 3
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT 
                hs.healthID,
                hs.healthName,
                COUNT(DISTINCT c.coralID) as coralCount
            FROM HealthStatus hs
            LEFT JOIN Classification cl ON hs.healthID = cl.healthID
            LEFT JOIN CoralImage ci ON cl.imageID = ci.imageID
            LEFT JOIN Coral c ON ci.coralID = c.coralID
            GROUP BY hs.healthID, hs.healthName
            ORDER BY coralCount DESC
            """
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getHealthStatusDistribution: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getTotalHealthStatusCount() -> int:
    """
    Get the total number of health status records.
    
    Returns:
        Total count of health status types
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM HealthStatus")
        result = cursor.fetchone()
        return result[0] if result else 0
    except mysql.connector.Error as e:
        print(f"Database error in getTotalHealthStatusCount: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getAverageConfidenceByHealthStatus(healthID: int = None) -> list[dict] | dict | None:
    """
    Get average confidence scores for health statuses.
    
    Args:
        healthID: Optional specific health ID to get average for
    
    Returns:
        If healthID provided: Dictionary with avgConfidence or None
        If no healthID: List of dictionaries with healthName and avgConfidence
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if healthID:
            cursor.execute(
                """
                SELECT 
                    AVG(cl.confidenceScore) as avgConfidence
                FROM Classification cl
                WHERE cl.healthID = %s
                """,
                (healthID,)
            )
            result = cursor.fetchone()
            return result if result else None
        else:
            cursor.execute(
                """
                SELECT 
                    hs.healthName,
                    AVG(cl.confidenceScore) as avgConfidence,
                    COUNT(cl.classID) as classificationCount
                FROM HealthStatus hs
                LEFT JOIN Classification cl ON hs.healthID = cl.healthID
                GROUP BY hs.healthID, hs.healthName
                ORDER BY hs.healthName
                """
            )
            return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getAverageConfidenceByHealthStatus: {e}")
        return None if healthID else []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 5. ADMIN OPERATIONS (Optional - for managing reference data)
# ============================================================================

def createHealthStatus(healthName: str, description: str = None) -> int | None:
    """
    Create a new health status (admin function).
    
    Args:
        healthName: Name of the health status
        description: Optional description of the health status
    
    Returns:
        The ID of the newly created health status, or None if failed
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO HealthStatus (healthName, description)
            VALUES (%s, %s)
            """,
            (healthName, description)
        )
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error as e:
        print(f"Database error in createHealthStatus: {e}")
        conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def updateHealthStatus(healthID: int, healthName: str, description: str = None) -> bool:
    """
    Update an existing health status (admin function).
    
    Args:
        healthID: ID of the health status to update
        healthName: New name for the health status
        description: New description (optional)
    
    Returns:
        True if update successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE HealthStatus
            SET healthName = %s,
                description = %s
            WHERE healthID = %s
            """,
            (healthName, description, healthID)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in updateHealthStatus: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def deleteHealthStatus(healthID: int) -> bool:
    """
    Delete a health status (admin function).
    Note: May fail if health status is referenced by existing classifications.
    
    Args:
        healthID: ID of the health status to delete
    
    Returns:
        True if deletion successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM HealthStatus WHERE healthID = %s",
            (healthID,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in deleteHealthStatus: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()