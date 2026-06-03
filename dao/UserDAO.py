"""
User DAO Module
===============
Data Access Object for Users table operations.
Handles user authentication, profile management, and role-based user retrieval.
"""

import mysql.connector
from util.DBConnection import getConnection


# ============================================================================
# 1. CREATE OPERATIONS
# ============================================================================

def createUser(name: str, email: str, password: str, roleID: int) -> int | None:
    """
    Create a new user account.
    
    Args:
        name: User's full name
        email: User's email address (must be unique)
        password: Hashed password
        roleID: Role ID (1=Scientific Reviewer, 2=Marine Biologist, 3=Educator)
    
    Returns:
        The ID of the newly created user, or None if failed
        
    Example:
        >>> user_id = createUser('John Doe', 'john@example.com', 'hashed_pw', 2)
        >>> print(f"Created user {user_id}")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO Users (username, email, password, roleID)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (name, email, password, roleID))
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error as e:
        print(f"Database error in createUser: {e}")
        conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def bulkCreateUsers(users: list[tuple]) -> list[int]:
    """
    Create multiple user accounts in batch.
    
    Args:
        users: List of tuples, each containing (name, email, password, roleID)
    
    Returns:
        List of created user IDs (empty list if failed)
        
    Example:
        >>> users = [('User1', 'user1@example.com', 'hash1', 3), ...]
        >>> ids = bulkCreateUsers(users)
    """
    conn = getConnection()
    cursor = None
    created_ids = []
    
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO Users (username, email, password, roleID)
            VALUES (%s, %s, %s, %s)
        """
        cursor.executemany(sql, users)
        conn.commit()
        
        # Get the last inserted IDs
        first_id = cursor.lastrowid
        for i in range(len(users)):
            created_ids.append(first_id + i)
        
        return created_ids
    except mysql.connector.Error as e:
        print(f"Database error in bulkCreateUsers: {e}")
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

def getByID(userID: int) -> dict | None:
    """
    Retrieve a user record by their ID.
    
    Args:
        userID: ID of the user to retrieve
    
    Returns:
        Dictionary containing user data, or None if not found
        
    Example:
        >>> user = getByID(123)
        >>> print(user['username'])
        'John Doe'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM Users WHERE userID = %s LIMIT 1",
            (userID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getByID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getByEmail(email: str) -> dict | None:
    """
    Retrieve a user record by their email address.
    
    Args:
        email: User's email address
    
    Returns:
        Dictionary containing user data, or None if not found
        
    Example:
        >>> user = getByEmail('john@example.com')
        >>> print(user['userID'])
        123
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM Users WHERE email = %s LIMIT 1",
            (email,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getByEmail: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getUserWithRole(userID: int) -> dict | None:
    """
    Get user with their role name joined.
    
    Args:
        userID: ID of the user
    
    Returns:
        Dictionary containing user data with roleName, or None if not found
        
    Example:
        >>> user = getUserWithRole(123)
        >>> print(f"{user['username']} - {user['roleName']}")
        'John Doe - Marine Biologist'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT u.*, r.roleName
            FROM Users u
            JOIN Role r ON u.roleID = r.roleID
            WHERE u.userID = %s
            LIMIT 1
            """,
            (userID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getUserWithRole: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 3. READ OPERATIONS (Multiple Records)
# ============================================================================

def getAllUsers() -> list[dict]:
    """
    Get all users with their role names joined.
    Used by the User Management panel for administrators.
    
    Returns:
        List of dictionaries containing user data with role information
        
    Example:
        >>> users = getAllUsers()
        >>> for u in users:
        ...     print(f"{u['username']} - {u['roleName']}")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT u.userID, u.username, u.email, u.roleID, r.roleName
            FROM Users u
            JOIN Role r ON u.roleID = r.roleID
            ORDER BY u.userID
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getAllUsers: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Roles that receive system alert / submission emails (Scientific Reviewer + Marine Biologist)
NOTIFICATION_ROLE_IDS = (1, 2)


def getNotificationRecipients(role_ids: tuple[int, ...] = NOTIFICATION_ROLE_IDS) -> list[dict]:
    """
    Get distinct users (by email) for outbound CoralKita notifications.

    Args:
        role_ids: Role IDs to include (default: 1=Scientific Reviewer, 2=Marine Biologist)

    Returns:
        List of user dicts with a non-empty email, one entry per unique email.
    """
    if not role_ids:
        return []

    conn = getConnection()
    cursor = None

    try:
        cursor = conn.cursor(dictionary=True)
        placeholders = ", ".join(["%s"] * len(role_ids))
        cursor.execute(
            f"""
            SELECT userID, username, email, roleID
            FROM Users
            WHERE roleID IN ({placeholders})
              AND email IS NOT NULL
              AND TRIM(email) <> ''
            ORDER BY roleID, username
            """,
            tuple(role_ids),
        )
        rows = cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getNotificationRecipients: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    seen_emails: set[str] = set()
    recipients: list[dict] = []
    for row in rows:
        email = (row.get("email") or "").strip()
        key = email.lower()
        if email and key not in seen_emails:
            seen_emails.add(key)
            recipients.append(row)
    return recipients


def getUsersByRole(roleID: int) -> list[dict]:
    """
    Get all users with a specific role ID.
    
    Args:
        roleID: Role ID (1=Scientific Reviewer, 2=Marine Biologist, 3=Educator)
    
    Returns:
        List of dictionaries containing user data for the specified role
        
    Example:
        >>> reviewers = getUsersByRole(1)
        >>> print(f"Found {len(reviewers)} scientific reviewers")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM Users WHERE roleID = %s ORDER BY username",
            (roleID,)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getUsersByRole: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getUsersByRoleName(roleName: str) -> list[dict]:
    """
    Get all users with a specific role name.
    
    Args:
        roleName: Role name ('Scientific Reviewer', 'Marine Biologist', 'Educator')
    
    Returns:
        List of dictionaries containing user data for the specified role
        
    Example:
        >>> educators = getUsersByRoleName('Educator')
        >>> for e in educators:
        ...     print(e['email'])
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT u.*
            FROM Users u
            JOIN Role r ON u.roleID = r.roleID
            WHERE r.roleName = %s
            ORDER BY u.username
            """,
            (roleName,)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getUsersByRoleName: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def searchUsers(search_term: str) -> list[dict]:
    """
    Search users by name or email.
    
    Args:
        search_term: Term to search for in username or email
    
    Returns:
        List of dictionaries containing matching user data
        
    Example:
        >>> results = searchUsers('john')
        >>> print(f"Found {len(results)} users")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        pattern = f"%{search_term}%"
        cursor.execute(
            """
            SELECT u.userID, u.username, u.email, u.roleID, r.roleName
            FROM Users u
            JOIN Role r ON u.roleID = r.roleID
            WHERE u.username LIKE %s OR u.email LIKE %s
            ORDER BY u.username
            """,
            (pattern, pattern)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in searchUsers: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getRecentlyJoinedUsers(days: int = 30, limit: int = 10) -> list[dict]:
    """
    Get users who joined within the specified number of days.
    
    Args:
        days: Number of days to look back (default 30)
        limit: Maximum number of users to return (default 10)
    
    Returns:
        List of dictionaries containing recent user data
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT u.userID, u.username, u.email, u.roleID, r.roleName, u.createdAt
            FROM Users u
            JOIN Role r ON u.roleID = r.roleID
            WHERE u.createdAt >= DATE_SUB(NOW(), INTERVAL %s DAY)
            ORDER BY u.createdAt DESC
            LIMIT %s
            """,
            (days, limit)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getRecentlyJoinedUsers: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 4. ROLE HELPER FUNCTIONS
# ============================================================================

def getRoleByName(roleName: str) -> int | None:
    """
    Returns the roleID integer for a given roleName string.
    Used during registration to resolve role name to ID.
    
    Args:
        roleName: Name of the role (case-insensitive)
    
    Returns:
        Role ID integer, or None if not found
        
    Example:
        >>> role_id = getRoleByName('Marine Biologist')
        >>> print(role_id)
        2
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT roleID FROM Role WHERE LOWER(roleName) = LOWER(%s) LIMIT 1",
            (roleName,)
        )
        row = cursor.fetchone()
        return row['roleID'] if row else None
    except mysql.connector.Error as e:
        print(f"Database error in getRoleByName: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getRoleNameByID(roleID: int) -> dict | None:
    """
    Returns a dictionary with roleName for a given roleID.
    Used during login to populate session['user_role'].
    
    Args:
        roleID: Role ID
    
    Returns:
        Dictionary containing roleName, or None if not found
        
    Example:
        >>> role = getRoleNameByID(2)
        >>> print(role['roleName'])
        'Marine Biologist'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT roleName FROM Role WHERE roleID = %s LIMIT 1",
            (roleID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getRoleNameByID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getRoleIDMap() -> dict[str, int]:
    """
    Get a mapping of role names to their IDs.
    
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


# ============================================================================
# 5. UPDATE OPERATIONS
# ============================================================================

def updateUserProfile(userID: int, name: str, email: str, new_password_hash: str = None) -> bool:
    """
    Update user profile information.
    
    Args:
        userID: ID of the user to update
        name: New username
        email: New email address
        new_password_hash: Optional new password hash (if provided, updates password)
    
    Returns:
        True if update successful, False otherwise
        
    Example:
        >>> success = updateUserProfile(123, 'John Smith', 'john.smith@example.com')
        >>> print("Updated!" if success else "Failed")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        
        if new_password_hash is not None:
            cursor.execute(
                """
                UPDATE Users
                SET username = %s, email = %s, password = %s
                WHERE userID = %s
                """,
                (name, email, new_password_hash, userID)
            )
        else:
            cursor.execute(
                """
                UPDATE Users
                SET username = %s, email = %s
                WHERE userID = %s
                """,
                (name, email, userID)
            )
        
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in updateUserProfile: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def updateUserRole(userID: int, new_roleID: int) -> bool:
    """
    Update a user's role (admin function).
    
    Args:
        userID: ID of the user to update
        new_roleID: New role ID for the user
    
    Returns:
        True if update successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE Users
            SET roleID = %s
            WHERE userID = %s
            """,
            (new_roleID, userID)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in updateUserRole: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def updateUserPassword(userID: int, new_password_hash: str) -> bool:
    """
    Update a user's password.
    
    Args:
        userID: ID of the user
        new_password_hash: New hashed password
    
    Returns:
        True if update successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE Users
            SET password = %s
            WHERE userID = %s
            """,
            (new_password_hash, userID)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in updateUserPassword: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 6. DELETE OPERATIONS
# ============================================================================

def deleteUser(userID: int) -> bool:
    """
    Delete a user account.
    
    Args:
        userID: ID of the user to delete
    
    Returns:
        True if deletion successful, False otherwise
        
    Note:
        May fail if user has associated coral submissions or reviews
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM Users WHERE userID = %s",
            (userID,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in deleteUser: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def deleteUsersByRole(roleID: int) -> int:
    """
    Delete all users with a specific role (admin function).
    
    Args:
        roleID: Role ID of users to delete
    
    Returns:
        Number of users deleted
        
    Warning: This operation is irreversible!
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM Users WHERE roleID = %s",
            (roleID,)
        )
        conn.commit()
        return cursor.rowcount
    except mysql.connector.Error as e:
        print(f"Database error in deleteUsersByRole: {e}")
        conn.rollback()
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 7. STATISTICS & VALIDATION
# ============================================================================

def getUserCount() -> int:
    """
    Get total number of registered users.
    
    Returns:
        Total user count
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Users")
        result = cursor.fetchone()
        return result[0] if result else 0
    except mysql.connector.Error as e:
        print(f"Database error in getUserCount: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getUserCountByRole(roleID: int) -> int:
    """
    Get number of users with a specific role.
    
    Args:
        roleID: Role ID to count
    
    Returns:
        Count of users with the specified role
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM Users WHERE roleID = %s",
            (roleID,)
        )
        result = cursor.fetchone()
        return result[0] if result else 0
    except mysql.connector.Error as e:
        print(f"Database error in getUserCountByRole: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def emailExists(email: str) -> bool:
    """
    Check if an email address is already registered.
    
    Args:
        email: Email address to check
    
    Returns:
        True if email exists, False otherwise
    """
    user = getByEmail(email)
    return user is not None


def userExists(userID: int) -> bool:
    """
    Check if a user exists.
    
    Args:
        userID: User ID to check
    
    Returns:
        True if user exists, False otherwise
    """
    user = getByID(userID)
    return user is not None


def getUsersWithoutActivity(days: int = 30) -> list[dict]:
    """
    Get users who have had no activity (submissions or logins) for specified days.
    
    Args:
        days: Number of days of inactivity to check
    
    Returns:
        List of inactive users
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT u.userID, u.username, u.email, u.roleID, r.roleName
            FROM Users u
            JOIN Role r ON u.roleID = r.roleID
            LEFT JOIN Coral c ON u.userID = c.submittedBy
            WHERE u.lastLogin IS NULL 
               OR u.lastLogin < DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY u.userID
            HAVING COUNT(c.coralID) = 0
            """,
            (days,)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getUsersWithoutActivity: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()