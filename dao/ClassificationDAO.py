"""
Classification DAO Module
=========================
Data Access Object for Classification table operations.
Handles CRUD operations for coral image classifications including health status and confidence scores.
"""

import mysql.connector
from util.DBConnection import getConnection


# ============================================================================
# 1. CREATE OPERATIONS
# ============================================================================

def createClassification(imageID: int, healthID: int, confidenceScore: float) -> int | None:
    """
    Create a new classification record.
    
    Args:
        imageID: ID of the coral image being classified
        healthID: ID of the health status (from HealthStatus table)
        confidenceScore: Confidence score of the classification (0-100)
    
    Returns:
        The ID of the newly created classification record, or None if failed
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Classification (imageID, healthID, confidenceScore)
            VALUES (%s, %s, %s)
            """,
            (imageID, healthID, confidenceScore)
        )
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error as e:
        print(f"Database error in createClassification: {e}")
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

def getClassificationByID(classID: int) -> dict | None:
    """
    Retrieve a classification record by its ID.
    
    Args:
        classID: ID of the classification to retrieve
    
    Returns:
        Dictionary containing classification data, or None if not found
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM Classification WHERE classID = %s LIMIT 1",
            (classID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getClassificationByID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getLatestClassificationByImageID(imageID: int) -> dict | None:
    """
    Retrieve the most recent classification for a specific image.
    
    Args:
        imageID: ID of the coral image
    
    Returns:
        Dictionary containing the latest classification data, or None if not found
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM Classification
            WHERE imageID = %s
            ORDER BY classID DESC
            LIMIT 1
            """,
            (imageID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getLatestClassificationByImageID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 3. READ OPERATIONS (Multiple Records)
# ============================================================================

def getClassificationsByImageID(imageID: int) -> list[dict]:
    """
    Retrieve all classifications for a specific image, ordered newest first.
    
    Args:
        imageID: ID of the coral image
    
    Returns:
        List of dictionaries containing classification data (empty list if none found)
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM Classification
            WHERE imageID = %s
            ORDER BY classID DESC
            """,
            (imageID,)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getClassificationsByImageID: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getClassificationsByHealthID(healthID: int, limit: int = 100) -> list[dict]:
    """
    Retrieve classifications by health status ID.
    
    Args:
        healthID: ID of the health status
        limit: Maximum number of records to return (default 100)
    
    Returns:
        List of dictionaries containing classification data
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM Classification
            WHERE healthID = %s
            ORDER BY classID DESC
            LIMIT %s
            """,
            (healthID, limit)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getClassificationsByHealthID: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getClassificationsByConfidenceRange(min_confidence: float, max_confidence: float = 100) -> list[dict]:
    """
    Retrieve classifications within a confidence score range.
    
    Args:
        min_confidence: Minimum confidence score (0-100)
        max_confidence: Maximum confidence score (0-100, default 100)
    
    Returns:
        List of dictionaries containing classification data
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM Classification
            WHERE confidenceScore BETWEEN %s AND %s
            ORDER BY confidenceScore DESC
            """,
            (min_confidence, max_confidence)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getClassificationsByConfidenceRange: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 4. UPDATE OPERATIONS
# ============================================================================

def updateClassificationConfidence(classID: int, new_confidence: float) -> bool:
    """
    Update the confidence score of a classification.
    
    Args:
        classID: ID of the classification to update
        new_confidence: New confidence score (0-100)
    
    Returns:
        True if update successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE Classification
            SET confidenceScore = %s
            WHERE classID = %s
            """,
            (new_confidence, classID)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in updateClassificationConfidence: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def updateClassificationHealth(classID: int, new_healthID: int) -> bool:
    """
    Update the health status of a classification.
    
    Args:
        classID: ID of the classification to update
        new_healthID: New health status ID
    
    Returns:
        True if update successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE Classification
            SET healthID = %s
            WHERE classID = %s
            """,
            (new_healthID, classID)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in updateClassificationHealth: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 5. DELETE OPERATIONS
# ============================================================================

def deleteClassification(classID: int) -> bool:
    """
    Delete a classification record.
    
    Args:
        classID: ID of the classification to delete
    
    Returns:
        True if deletion successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM Classification WHERE classID = %s",
            (classID,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in deleteClassification: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def deleteClassificationsByImageID(imageID: int) -> int:
    """
    Delete all classifications for a specific image.
    
    Args:
        imageID: ID of the coral image
    
    Returns:
        Number of classifications deleted
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM Classification WHERE imageID = %s",
            (imageID,)
        )
        conn.commit()
        return cursor.rowcount
    except mysql.connector.Error as e:
        print(f"Database error in deleteClassificationsByImageID: {e}")
        conn.rollback()
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 6. STATISTICS & AGGREGATION OPERATIONS
# ============================================================================

def getAverageConfidenceByHealthID(healthID: int) -> float | None:
    """
    Calculate average confidence score for a specific health status.
    
    Args:
        healthID: ID of the health status
    
    Returns:
        Average confidence score, or None if no records found
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT AVG(confidenceScore) as avg_confidence
            FROM Classification
            WHERE healthID = %s
            """,
            (healthID,)
        )
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else None
    except mysql.connector.Error as e:
        print(f"Database error in getAverageConfidenceByHealthID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getClassificationCountByHealthID(healthID: int) -> int:
    """
    Count number of classifications for a specific health status.
    
    Args:
        healthID: ID of the health status
    
    Returns:
        Count of classifications
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM Classification WHERE healthID = %s",
            (healthID,)
        )
        result = cursor.fetchone()
        return result[0] if result else 0
    except mysql.connector.Error as e:
        print(f"Database error in getClassificationCountByHealthID: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 7. LEGACY FUNCTION ALIASES (For backward compatibility)
# ============================================================================

# Alias for backward compatibility with existing code
def getByImageID(imageID: int) -> list[dict]:
    """
    Legacy alias for getClassificationsByImageID.
    
    Args:
        imageID: ID of the coral image
    
    Returns:
        List of dictionaries containing classification data
    """
    return getClassificationsByImageID(imageID)