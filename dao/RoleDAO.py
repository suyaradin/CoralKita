"""
Role DAO Module
===============
Data Access Object for Role table operations.
Handles retrieval of user role reference data (e.g., Admin, Marine Biologist, Educator).
"""

import mysql.connector
from util.DBConnection import getConnection


# ============================================================================
# 1. READ OPERATIONS (Single Records)
# ============================================================================

def getRoleByID(roleID: int) -> dict | None:
    """
    Retrieve a role record by its ID.
    
    Args:
        roleID: ID of the role to retrieve (1=Admin, 2=Marine Biologist, 3=Educator)
    
    Returns:
        Dictionary containing role data, or None if not found
        
    Example:
        >>> role = getRoleByID(1)
        >>> print(role['roleName'])
        'Scientific Reviewer'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM Role WHERE roleID = %s LIMIT 1",
            (roleID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getRoleByID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getRoleByName(roleName: str) -> dict | None:
    """
    Retrieve a role record by its name (case-insensitive).
    
    Args:
        roleName: Name of the role (e.g., 'Scientific Reviewer', 'Marine Biologist', 'Educator')
    
    Returns:
        Dictionary containing role data, or None if not found
        
    Example:
        >>> role = getRoleByName('Marine Biologist')
        >>> print(role['roleID'])
        2
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM Role WHERE LOWER(roleName) = LOWER(%s) LIMIT 1",
            (roleName,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getRoleByName: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getRoleNameByID(roleID: int) -> str | None:
    """
    Get role name by ID (convenience function).
    
    Args:
        roleID: ID of the role
    
    Returns:
        Role name string, or None if not found
        
    Example:
        >>> role_name = getRoleNameByID(3)
        >>> print(role_name)
        'Educator'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT roleName FROM Role WHERE roleID = %s LIMIT 1",
            (roleID,)
        )
        result = cursor.fetchone()
        return result['roleName'] if result else None
    except mysql.connector.Error as e:
        print(f"Database error in getRoleNameByID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getRoleIDByName(roleName: str) -> int | None:
    """
    Get role ID by name (case-insensitive).
    
    Args:
        roleName: Name of the role
    
    Returns:
        Role ID integer, or None if not found
        
    Example:
        >>> role_id = getRoleIDByName('Educator')
        >>> print(role_id)
        3
    """
    role = getRoleByName(roleName)
    return role['roleID'] if role else None


# ============================================================================
# 2. READ OPERATIONS (Multiple Records)
# ============================================================================

def getAllRoles() -> list[dict]:
    """
    Retrieve all roles, ordered by role ID.
    
    Returns:
        List of dictionaries containing role data (empty list if none found)
        
    Example:
        >>> roles = getAllRoles()
        >>> for r in roles:
        ...     print(f"{r['roleID']}: {r['roleName']}")
        1: Scientific Reviewer
        2: Marine Biologist
        3: Educator
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Role ORDER BY roleID")
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getAllRoles: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getActiveRoles() -> list[dict]:
    """
    Retrieve only active roles (where isActive = 1).
    
    Returns:
        List of dictionaries containing active role data
        
    Example:
        >>> active = getActiveRoles()
        >>> print(len(active))
        3
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM Role WHERE isActive = 1 ORDER BY roleID"
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getActiveRoles: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getRolesByUserCount() -> list[dict]:
    """
    Retrieve roles with the number of users assigned to each.
    
    Returns:
        List of dictionaries containing role data with userCount
        
    Example:
        >>> role_stats = getRolesByUserCount()
        >>> for r in role_stats:
        ...     print(f"{r['roleName']}: {r['userCount']} users")
        'Scientific Reviewer: 3 users'
        'Marine Biologist: 12 users'
        'Educator: 45 users'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT 
                r.roleID,
                r.roleName,
                COUNT(u.userID) as userCount
            FROM Role r
            LEFT JOIN Users u ON r.roleID = u.roleID
            GROUP BY r.roleID, r.roleName
            ORDER BY userCount DESC
            """
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getRolesByUserCount: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 3. VALIDATION & UTILITY FUNCTIONS
# ============================================================================

def roleExists(roleID: int) -> bool:
    """
    Check if a role exists in the database.
    
    Args:
        roleID: ID of the role to check
    
    Returns:
        True if role exists, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM Role WHERE roleID = %s",
            (roleID,)
        )
        result = cursor.fetchone()
        return result[0] > 0 if result else False
    except mysql.connector.Error as e:
        print(f"Database error in roleExists: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def isValidRole(roleName: str) -> bool:
    """
    Validate if a role name is valid.
    
    Args:
        roleName: Name of the role to validate
    
    Returns:
        True if role is valid, False otherwise
    """
    role = getRoleByName(roleName)
    return role is not None


def getRoleIDMap() -> dict[str, int]:
    """
    Get a mapping of role names to their IDs.
    Useful for form dropdowns and validation.
    
    Returns:
        Dictionary mapping roleName to roleID
        
    Example:
        >>> mapping = getRoleIDMap()
        >>> print(mapping)
        {'Scientific Reviewer': 1, 'Marine Biologist': 2, 'Educator': 3}
    """
    conn = getConnection()
    cursor = None
    result = {}
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT roleID, roleName FROM Role")
        rows = cursor.fetchall()
        for row in rows:
            result[row['roleName']] = row['roleID']
        return result
    except mysql.connector.Error as e:
        print(f"Database error in getRoleIDMap: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def isAdminRole(roleID: int) -> bool:
    """
    Check if a role has administrative privileges.
    
    Args:
        roleID: ID of the role to check
    
    Returns:
        True if role is admin (Scientific Reviewer), False otherwise
    """
    role = getRoleByID(roleID)
    if not role:
        return False
    
    # Assuming roleID 1 is Scientific Reviewer/Admin
    admin_role_ids = [1]
    return roleID in admin_role_ids


def isMarineBiologistRole(roleID: int) -> bool:
    """
    Check if a role is Marine Biologist.
    
    Args:
        roleID: ID of the role to check
    
    Returns:
        True if role is Marine Biologist, False otherwise
    """
    # Assuming roleID 2 is Marine Biologist
    return roleID == 2


def isEducatorRole(roleID: int) -> bool:
    """
    Check if a role is Educator.
    
    Args:
        roleID: ID of the role to check
    
    Returns:
        True if role is Educator, False otherwise
    """
    # Assuming roleID 3 is Educator
    return roleID == 3


def getRoleHierarchy() -> dict:
    """
    Get role hierarchy with permission levels.
    
    Returns:
        Dictionary containing role hierarchy information
        
    Example:
        >>> hierarchy = getRoleHierarchy()
        >>> print(hierarchy[1]['permission_level'])
        'high'
    """
    roles = getAllRoles()
    hierarchy = {}
    
    # Define permission levels (higher number = more permissions)
    permission_levels = {
        'Scientific Reviewer': 3,
        'Marine Biologist': 2,
        'Educator': 1
    }
    
    for role in roles:
        role_name = role['roleName']
        hierarchy[role['roleID']] = {
            'name': role_name,
            'permission_level': permission_levels.get(role_name, 0),
            'can_approve': role_name == 'Scientific Reviewer',
            'can_submit': role_name in ['Scientific Reviewer', 'Marine Biologist'],
            'can_view': True  # All roles can view approved content
        }
    
    return hierarchy


# ============================================================================
# 4. CONSTANTS (Role IDs for easier reference in code)
# ============================================================================

class RoleConstants:
    """Centralized role ID constants for use across the application."""
    
    SCIENTIFIC_REVIEWER = 1
    MARINE_BIOLOGIST = 2
    EDUCATOR = 3
    
    @classmethod
    def get_role_name(cls, role_id: int) -> str | None:
        """Get role name from constant ID."""
        mapping = {
            cls.SCIENTIFIC_REVIEWER: 'Scientific Reviewer',
            cls.MARINE_BIOLOGIST: 'Marine Biologist',
            cls.EDUCATOR: 'Educator'
        }
        return mapping.get(role_id)
    
    @classmethod
    def get_all_role_ids(cls) -> list[int]:
        """Get list of all role IDs."""
        return [cls.SCIENTIFIC_REVIEWER, cls.MARINE_BIOLOGIST, cls.EDUCATOR]
    
    @classmethod
    def is_valid_role_id(cls, role_id: int) -> bool:
        """Check if role ID is valid."""
        return role_id in cls.get_all_role_ids()


# ============================================================================
# 5. STATISTICS & AGGREGATION
# ============================================================================

def getRoleDistribution() -> list[dict]:
    """
    Get distribution of users across roles.
    
    Returns:
        List of dictionaries containing role distribution statistics
        
    Example:
        >>> dist = getRoleDistribution()
        >>> for d in dist:
        ...     print(f"{d['roleName']}: {d['percentage']}%")
        'Scientific Reviewer: 5.0%'
        'Marine Biologist: 20.0%'
        'Educator: 75.0%'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT 
                r.roleID,
                r.roleName,
                COUNT(u.userID) as userCount,
                ROUND(COUNT(u.userID) * 100.0 / (SELECT COUNT(*) FROM Users), 2) as percentage
            FROM Role r
            LEFT JOIN Users u ON r.roleID = u.roleID
            GROUP BY r.roleID, r.roleName
            ORDER BY userCount DESC
            """
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getRoleDistribution: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getTotalRoleCount() -> int:
    """
    Get the total number of role types in the database.
    
    Returns:
        Total count of role types
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Role")
        result = cursor.fetchone()
        return result[0] if result else 0
    except mysql.connector.Error as e:
        print(f"Database error in getTotalRoleCount: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 6. ADMIN OPERATIONS (Optional - for managing reference data)
# ============================================================================

def createRole(roleName: str, description: str = None, isActive: bool = True) -> int | None:
    """
    Create a new role (admin function).
    
    Args:
        roleName: Name of the role
        description: Optional description of the role
        isActive: Whether the role is active (default True)
    
    Returns:
        The ID of the newly created role, or None if failed
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Role (roleName, description, isActive)
            VALUES (%s, %s, %s)
            """,
            (roleName, description, isActive)
        )
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error as e:
        print(f"Database error in createRole: {e}")
        conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def updateRole(roleID: int, roleName: str = None, description: str = None, isActive: bool = None) -> bool:
    """
    Update an existing role (admin function).
    
    Args:
        roleID: ID of the role to update
        roleName: New role name (optional)
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
        
        if roleName is not None:
            updates.append("roleName = %s")
            params.append(roleName)
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        if isActive is not None:
            updates.append("isActive = %s")
            params.append(isActive)
        
        if not updates:
            return False
        
        params.append(roleID)
        query = f"UPDATE Role SET {', '.join(updates)} WHERE roleID = %s"
        
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in updateRole: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def deleteRole(roleID: int) -> bool:
    """
    Delete a role (admin function).
    Note: May fail if role has associated users.
    
    Args:
        roleID: ID of the role to delete
    
    Returns:
        True if deletion successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM Role WHERE roleID = %s",
            (roleID,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in deleteRole: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()