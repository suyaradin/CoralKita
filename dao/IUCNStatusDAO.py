"""
IUCNStatus DAO Module
=====================
Data Access Object for IUCNStatus table operations.
Handles retrieval of IUCN conservation status reference data 
(e.g., 'Least Concern', 'Endangered', 'Critically Endangered').
"""

import mysql.connector
from util.DBConnection import getConnection


# ============================================================================
# 1. READ OPERATIONS (Single Records)
# ============================================================================

def getIUCNStatusByID(iucnID: int) -> dict | None:
    """
    Retrieve an IUCN status record by its ID.
    
    Args:
        iucnID: ID of the IUCN status to retrieve
    
    Returns:
        Dictionary containing IUCN status data, or None if not found
        
    Example:
        >>> status = getIUCNStatusByID(1)
        >>> print(status['iucnName'])
        'Least Concern'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM IUCNStatus WHERE iucnID = %s LIMIT 1",
            (iucnID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getIUCNStatusByID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getIUCNStatusByName(iucnName: str) -> dict | None:
    """
    Retrieve an IUCN status record by its name.
    
    Args:
        iucnName: Name of the IUCN status (e.g., 'Endangered', 'Vulnerable')
    
    Returns:
        Dictionary containing IUCN status data, or None if not found
        
    Example:
        >>> status = getIUCNStatusByName('Critically Endangered')
        >>> print(status['iucnID'])
        5
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM IUCNStatus WHERE iucnName = %s LIMIT 1",
            (iucnName,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getIUCNStatusByName: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getIUCNStatusByCode(code: str) -> dict | None:
    """
    Retrieve an IUCN status record by its short code.
    
    Args:
        code: Short code for IUCN status (e.g., 'LC', 'EN', 'CR')
    
    Returns:
        Dictionary containing IUCN status data, or None if not found
        
    Example:
        >>> status = getIUCNStatusByCode('CR')
        >>> print(status['iucnName'])
        'Critically Endangered'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM IUCNStatus WHERE code = %s LIMIT 1",
            (code,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getIUCNStatusByCode: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 2. READ OPERATIONS (Multiple Records)
# ============================================================================

def getAllIUCNStatuses() -> list[dict]:
    """
    Retrieve all IUCN status records, ordered alphabetically by name.
    
    Returns:
        List of dictionaries containing IUCN status data (empty list if none found)
        
    Example:
        >>> statuses = getAllIUCNStatuses()
        >>> for s in statuses:
        ...     print(f"{s['code']}: {s['iucnName']}")
        'CR': 'Critically Endangered'
        'EN': 'Endangered'
        'LC': 'Least Concern'
        'VU': 'Vulnerable'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM IUCNStatus ORDER BY iucnName")
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getAllIUCNStatuses: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getIUCNStatusesByThreatLevel() -> list[dict]:
    """
    Retrieve IUCN statuses ordered by threat level (most threatened first).
    
    Returns:
        List of dictionaries containing IUCN status data ordered by threat level
        
    Example:
        >>> statuses = getIUCNStatusesByThreatLevel()
        >>> for s in statuses:
        ...     print(s['iucnName'])
        'Extinct'
        'Extinct in the Wild'
        'Critically Endangered'
        'Endangered'
        'Vulnerable'
        'Near Threatened'
        'Least Concern'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Order by threat level (most severe first)
        threat_order = """
            CASE iucnName
                WHEN 'Extinct' THEN 1
                WHEN 'Extinct in the Wild' THEN 2
                WHEN 'Critically Endangered' THEN 3
                WHEN 'Endangered' THEN 4
                WHEN 'Vulnerable' THEN 5
                WHEN 'Near Threatened' THEN 6
                WHEN 'Least Concern' THEN 7
                WHEN 'Data Deficient' THEN 8
                WHEN 'Not Evaluated' THEN 9
                ELSE 10
            END
        """
        
        cursor.execute(f"""
            SELECT * FROM IUCNStatus
            ORDER BY {threat_order}
        """)
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getIUCNStatusesByThreatLevel: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getThreatenedIUCNStatuses() -> list[dict]:
    """
    Retrieve only threatened IUCN statuses (Vulnerable, Endangered, Critically Endangered).
    
    Returns:
        List of dictionaries containing threatened IUCN status data
        
    Example:
        >>> threatened = getThreatenedIUCNStatuses()
        >>> for s in threatened:
        ...     print(s['iucnName'])
        'Vulnerable'
        'Endangered'
        'Critically Endangered'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM IUCNStatus
            WHERE iucnName IN ('Vulnerable', 'Endangered', 'Critically Endangered')
            ORDER BY 
                CASE iucnName
                    WHEN 'Critically Endangered' THEN 1
                    WHEN 'Endangered' THEN 2
                    WHEN 'Vulnerable' THEN 3
                END
            """
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getThreatenedIUCNStatuses: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 3. VALIDATION & UTILITY FUNCTIONS
# ============================================================================

def iucnStatusExists(iucnID: int) -> bool:
    """
    Check if an IUCN status exists in the database.
    
    Args:
        iucnID: ID of the IUCN status to check
    
    Returns:
        True if IUCN status exists, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM IUCNStatus WHERE iucnID = %s",
            (iucnID,)
        )
        result = cursor.fetchone()
        return result[0] > 0 if result else False
    except mysql.connector.Error as e:
        print(f"Database error in iucnStatusExists: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def isValidIUCNStatus(iucnName: str) -> bool:
    """
    Validate if an IUCN status name is valid.
    
    Args:
        iucnName: Name of the IUCN status to validate
    
    Returns:
        True if IUCN status is valid, False otherwise
    """
    status = getIUCNStatusByName(iucnName)
    return status is not None


def isThreatenedStatus(iucnID: int) -> bool:
    """
    Check if an IUCN status is considered threatened.
    
    Args:
        iucnID: ID of the IUCN status to check
    
    Returns:
        True if status is threatened (Vulnerable, Endangered, or Critically Endangered), 
        False otherwise
    """
    status = getIUCNStatusByID(iucnID)
    if not status:
        return False
    
    threatened_names = ['Vulnerable', 'Endangered', 'Critically Endangered']
    return status['iucnName'] in threatened_names


def getIUCNStatusIDMap() -> dict[str, int]:
    """
    Get a mapping of IUCN status names to their IDs.
    Useful for form dropdowns and validation.
    
    Returns:
        Dictionary mapping iucnName to iucnID
        
    Example:
        >>> mapping = getIUCNStatusIDMap()
        >>> print(mapping)
        {'Least Concern': 1, 'Near Threatened': 2, 'Vulnerable': 3, 
         'Endangered': 4, 'Critically Endangered': 5}
    """
    conn = getConnection()
    cursor = None
    result = {}
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT iucnID, iucnName FROM IUCNStatus")
        rows = cursor.fetchall()
        for row in rows:
            result[row['iucnName']] = row['iucnID']
        return result
    except mysql.connector.Error as e:
        print(f"Database error in getIUCNStatusIDMap: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getIUCNStatusCodeMap() -> dict[str, int]:
    """
    Get a mapping of IUCN status codes to their IDs.
    
    Returns:
        Dictionary mapping code to iucnID
        
    Example:
        >>> mapping = getIUCNStatusCodeMap()
        >>> print(mapping)
        {'LC': 1, 'NT': 2, 'VU': 3, 'EN': 4, 'CR': 5}
    """
    conn = getConnection()
    cursor = None
    result = {}
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT iucnID, code FROM IUCNStatus WHERE code IS NOT NULL")
        rows = cursor.fetchall()
        for row in rows:
            result[row['code']] = row['iucnID']
        return result
    except mysql.connector.Error as e:
        print(f"Database error in getIUCNStatusCodeMap: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 4. STATISTICS & AGGREGATION
# ============================================================================

def getIUCNStatusDistribution() -> list[dict]:
    """
    Get distribution of corals by IUCN status.
    
    Returns:
        List of dictionaries containing iucnID, iucnName, and coralCount
        
    Example:
        >>> stats = getIUCNStatusDistribution()
        >>> for s in stats:
        ...     print(f"{s['iucnName']}: {s['coralCount']} corals")
        'Least Concern': 45
        'Vulnerable': 12
        'Endangered': 8
        'Critically Endangered': 3
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT 
                i.iucnID,
                i.iucnName,
                COUNT(DISTINCT c.coralID) as coralCount
            FROM IUCNStatus i
            LEFT JOIN Review r ON i.iucnID = r.iucnID
            LEFT JOIN Classification cl ON r.classID = cl.classID
            LEFT JOIN CoralImage ci ON cl.imageID = ci.imageID
            LEFT JOIN Coral c ON ci.coralID = c.coralID
            WHERE r.reviewStatus = 'approved'
            GROUP BY i.iucnID, i.iucnName
            ORDER BY coralCount DESC
            """
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getIUCNStatusDistribution: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getTotalIUCNStatusCount() -> int:
    """
    Get the total number of IUCN status records.
    
    Returns:
        Total count of IUCN status types
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM IUCNStatus")
        result = cursor.fetchone()
        return result[0] if result else 0
    except mysql.connector.Error as e:
        print(f"Database error in getTotalIUCNStatusCount: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getMostCommonIUCNStatus() -> dict | None:
    """
    Get the IUCN status that appears most frequently in approved coral records.
    
    Returns:
        Dictionary containing IUCN status data with coralCount, or None if no corals
        
    Example:
        >>> status = getMostCommonIUCNStatus()
        >>> print(f"{status['iucnName']}: {status['coralCount']} corals")
        'Least Concern': 45 corals
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT 
                i.iucnID,
                i.iucnName,
                COUNT(DISTINCT c.coralID) as coralCount
            FROM IUCNStatus i
            JOIN Review r ON i.iucnID = r.iucnID
            JOIN Classification cl ON r.classID = cl.classID
            JOIN CoralImage ci ON cl.imageID = ci.imageID
            JOIN Coral c ON ci.coralID = c.coralID
            WHERE r.reviewStatus = 'approved'
            GROUP BY i.iucnID, i.iucnName
            ORDER BY coralCount DESC
            LIMIT 1
            """
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getMostCommonIUCNStatus: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 5. ADMIN OPERATIONS (Optional - for managing reference data)
# ============================================================================

def createIUCNStatus(iucnName: str, code: str = None, description: str = None) -> int | None:
    """
    Create a new IUCN status (admin function).
    
    Args:
        iucnName: Name of the IUCN status
        code: Short code for the status (e.g., 'LC', 'EN')
        description: Optional description of the status
    
    Returns:
        The ID of the newly created IUCN status, or None if failed
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO IUCNStatus (iucnName, code, description)
            VALUES (%s, %s, %s)
            """,
            (iucnName, code, description)
        )
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error as e:
        print(f"Database error in createIUCNStatus: {e}")
        conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def updateIUCNStatus(iucnID: int, iucnName: str, code: str = None, description: str = None) -> bool:
    """
    Update an existing IUCN status (admin function).
    
    Args:
        iucnID: ID of the IUCN status to update
        iucnName: New name for the IUCN status
        code: New short code (optional)
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
            UPDATE IUCNStatus
            SET iucnName = %s,
                code = %s,
                description = %s
            WHERE iucnID = %s
            """,
            (iucnName, code, description, iucnID)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in updateIUCNStatus: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def deleteIUCNStatus(iucnID: int) -> bool:
    """
    Delete an IUCN status (admin function).
    Note: May fail if status is referenced by existing reviews.
    
    Args:
        iucnID: ID of the IUCN status to delete
    
    Returns:
        True if deletion successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM IUCNStatus WHERE iucnID = %s",
            (iucnID,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in deleteIUCNStatus: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()