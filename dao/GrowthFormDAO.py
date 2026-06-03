"""
GrowthForm DAO Module
=====================
Data Access Object for GrowthForm table operations.
Handles retrieval of coral growth form reference data.
"""

import mysql.connector
from util.DBConnection import getConnection


# ============================================================================
# 1. READ OPERATIONS (Single Records)
# ============================================================================

def getGrowthFormByID(growthFormID: int) -> dict | None:
    """
    Retrieve a growth form record by its ID.
    
    Args:
        growthFormID: ID of the growth form to retrieve
    
    Returns:
        Dictionary containing growth form data, or None if not found
        
    Example:
        >>> form = getGrowthFormByID(1)
        >>> print(form['growthFormName'])
        'Branching'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM GrowthForm WHERE growthFormID = %s LIMIT 1",
            (growthFormID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getGrowthFormByID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getGrowthFormByName(growthFormName: str) -> dict | None:
    """
    Retrieve a growth form record by its name.
    
    Args:
        growthFormName: Name of the growth form (e.g., 'Branching', 'Massive')
    
    Returns:
        Dictionary containing growth form data, or None if not found
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM GrowthForm WHERE growthFormName = %s LIMIT 1",
            (growthFormName,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getGrowthFormByName: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 2. READ OPERATIONS (Multiple Records)
# ============================================================================

def getAllGrowthForms() -> list[dict]:
    """
    Retrieve all growth forms, ordered alphabetically by name.
    
    Returns:
        List of dictionaries containing growth form data (empty list if none found)
        
    Example:
        >>> forms = getAllGrowthForms()
        >>> for form in forms:
        ...     print(form['growthFormName'])
        'Branching'
        'Encrusting'
        'Massive'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM GrowthForm ORDER BY growthFormName"
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getAllGrowthForms: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getGrowthFormsByCoralCount(limit: int = 10) -> list[dict]:
    """
    Retrieve growth forms with their coral count, ordered by popularity.
    
    Args:
        limit: Maximum number of records to return (default 10)
    
    Returns:
        List of dictionaries containing growth form data with coralCount
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT 
                gf.growthFormID,
                gf.growthFormName,
                COUNT(c.coralID) as coralCount
            FROM GrowthForm gf
            LEFT JOIN Coral c ON gf.growthFormID = c.growthFormID
            GROUP BY gf.growthFormID, gf.growthFormName
            ORDER BY coralCount DESC, gf.growthFormName
            LIMIT %s
            """,
            (limit,)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getGrowthFormsByCoralCount: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 3. VALIDATION & UTILITY FUNCTIONS
# ============================================================================

def growthFormExists(growthFormID: int) -> bool:
    """
    Check if a growth form exists in the database.
    
    Args:
        growthFormID: ID of the growth form to check
    
    Returns:
        True if growth form exists, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM GrowthForm WHERE growthFormID = %s",
            (growthFormID,)
        )
        result = cursor.fetchone()
        return result[0] > 0 if result else False
    except mysql.connector.Error as e:
        print(f"Database error in growthFormExists: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getGrowthFormIDMap() -> dict[str, int]:
    """
    Get a mapping of growth form names to their IDs.
    Useful for form dropdowns and validation.
    
    Returns:
        Dictionary mapping growthFormName to growthFormID
        
    Example:
        >>> mapping = getGrowthFormIDMap()
        >>> print(mapping)
        {'Branching': 1, 'Massive': 2, 'Encrusting': 3}
    """
    conn = getConnection()
    cursor = None
    result = {}
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT growthFormID, growthFormName FROM GrowthForm")
        rows = cursor.fetchall()
        for row in rows:
            result[row['growthFormName']] = row['growthFormID']
        return result
    except mysql.connector.Error as e:
        print(f"Database error in getGrowthFormIDMap: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 4. BATCH OPERATIONS
# ============================================================================

def getGrowthFormsByIDs(growthFormIDs: list[int]) -> list[dict]:
    """
    Retrieve multiple growth forms by their IDs.
    
    Args:
        growthFormIDs: List of growth form IDs to retrieve
    
    Returns:
        List of dictionaries containing growth form data
        
    Example:
        >>> forms = getGrowthFormsByIDs([1, 2, 3])
        >>> len(forms)
        3
    """
    if not growthFormIDs:
        return []
    
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        placeholders = ','.join(['%s'] * len(growthFormIDs))
        query = f"""
            SELECT * FROM GrowthForm
            WHERE growthFormID IN ({placeholders})
            ORDER BY growthFormName
        """
        cursor.execute(query, growthFormIDs)
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getGrowthFormsByIDs: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 5. STATISTICS & AGGREGATION
# ============================================================================

def getTotalGrowthFormCount() -> int:
    """
    Get the total number of growth forms in the database.
    
    Returns:
        Total count of growth forms
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM GrowthForm")
        result = cursor.fetchone()
        return result[0] if result else 0
    except mysql.connector.Error as e:
        print(f"Database error in getTotalGrowthFormCount: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getMostCommonGrowthForm() -> dict | None:
    """
    Get the growth form that appears most frequently in coral records.
    
    Returns:
        Dictionary containing growth form data with coralCount, or None if no corals
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT 
                gf.growthFormID,
                gf.growthFormName,
                COUNT(c.coralID) as coralCount
            FROM GrowthForm gf
            JOIN Coral c ON gf.growthFormID = c.growthFormID
            GROUP BY gf.growthFormID, gf.growthFormName
            ORDER BY coralCount DESC
            LIMIT 1
            """
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getMostCommonGrowthForm: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 6. ADMIN OPERATIONS (Optional - for managing reference data)
# ============================================================================

def createGrowthForm(growthFormName: str, description: str = None) -> int | None:
    """
    Create a new growth form (admin function).
    
    Args:
        growthFormName: Name of the growth form
        description: Optional description of the growth form
    
    Returns:
        The ID of the newly created growth form, or None if failed
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO GrowthForm (growthFormName, description)
            VALUES (%s, %s)
            """,
            (growthFormName, description)
        )
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error as e:
        print(f"Database error in createGrowthForm: {e}")
        conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def updateGrowthForm(growthFormID: int, growthFormName: str, description: str = None) -> bool:
    """
    Update an existing growth form (admin function).
    
    Args:
        growthFormID: ID of the growth form to update
        growthFormName: New name for the growth form
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
            UPDATE GrowthForm
            SET growthFormName = %s,
                description = %s
            WHERE growthFormID = %s
            """,
            (growthFormName, description, growthFormID)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in updateGrowthForm: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def deleteGrowthForm(growthFormID: int) -> bool:
    """
    Delete a growth form (admin function).
    Note: May fail if growth form is referenced by existing corals.
    
    Args:
        growthFormID: ID of the growth form to delete
    
    Returns:
        True if deletion successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM GrowthForm WHERE growthFormID = %s",
            (growthFormID,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in deleteGrowthForm: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()