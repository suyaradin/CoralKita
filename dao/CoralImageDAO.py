"""
CoralImage DAO Module
=====================
Data Access Object for CoralImage table operations.
Handles CRUD operations for coral images including upload tracking and relationships with corals.
"""

import mysql.connector
from util.DBConnection import getConnection


# ============================================================================
# 1. CREATE OPERATIONS
# ============================================================================

def createCoralImage(imagePath: str, uploadBy: int, coralID: int) -> int | None:
    """
    Create a new coral image record.
    
    Args:
        imagePath: Relative path to the uploaded image file
        uploadBy: ID of the user who uploaded the image
        coralID: ID of the coral this image belongs to
    
    Returns:
        The ID of the newly created image record, or None if failed
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO CoralImage (imagePath, uploadBy, coralID)
            VALUES (%s, %s, %s)
            """,
            (imagePath, uploadBy, coralID)
        )
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error as e:
        print(f"Database error in createCoralImage: {e}")
        conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def addCoralImage(imagePath: str, uploadBy: int, coralID: int) -> int | None:
    """
    Alias for createCoralImage. Creates a new coral image record.
    
    Args:
        imagePath: Relative path to the uploaded image file
        uploadBy: ID of the user who uploaded the image
        coralID: ID of the coral this image belongs to
    
    Returns:
        The ID of the newly created image record, or None if failed
    """
    return createCoralImage(imagePath, uploadBy, coralID)


# ============================================================================
# 2. READ OPERATIONS (Single Records)
# ============================================================================

def getImageByID(imageID: int) -> dict | None:
    """
    Retrieve an image record by its ID.
    
    Args:
        imageID: ID of the image to retrieve
    
    Returns:
        Dictionary containing image data, or None if not found
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM CoralImage WHERE imageID = %s LIMIT 1",
            (imageID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getImageByID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getLatestImageByCoralID(coralID: int) -> dict | None:
    """
    Retrieve the most recent image for a specific coral.
    
    Args:
        coralID: ID of the coral
    
    Returns:
        Dictionary containing the latest image data, or None if not found
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM CoralImage
            WHERE coralID = %s
            ORDER BY uploadDate DESC
            LIMIT 1
            """,
            (coralID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getLatestImageByCoralID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 3. READ OPERATIONS (Multiple Records)
# ============================================================================

def getImagesByCoralID(coralID: int) -> list[dict]:
    """
    Retrieve all images for a specific coral, ordered newest first.
    
    Args:
        coralID: ID of the coral
    
    Returns:
        List of dictionaries containing image data (empty list if none found)
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM CoralImage
            WHERE coralID = %s
            ORDER BY uploadDate DESC
            """,
            (coralID,)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getImagesByCoralID: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getImagesByUserID(userID: int) -> list[dict]:
    """
    Retrieve all images uploaded by a specific user, ordered newest first.
    
    Args:
        userID: ID of the user who uploaded the images
    
    Returns:
        List of dictionaries containing image data (empty list if none found)
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM CoralImage
            WHERE uploadBy = %s
            ORDER BY uploadDate DESC
            """,
            (userID,)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getImagesByUserID: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getImagesByDateRange(start_date: str, end_date: str) -> list[dict]:
    """
    Retrieve images uploaded within a specific date range.
    
    Args:
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
    
    Returns:
        List of dictionaries containing image data
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM CoralImage
            WHERE DATE(uploadDate) BETWEEN %s AND %s
            ORDER BY uploadDate DESC
            """,
            (start_date, end_date)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getImagesByDateRange: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getImagesWithDetailsByCoralID(coralID: int) -> list[dict]:
    """
    Retrieve all images for a coral with classification and review details.
    
    Args:
        coralID: ID of the coral
    
    Returns:
        List of dictionaries containing image data with classification and review status
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT 
                ci.imageID,
                ci.imagePath,
                ci.uploadDate,
                ci.uploadBy,
                u.username as uploadedByName,
                cl.classID,
                cl.confidenceScore,
                h.healthName,
                r.reviewStatus,
                r.rejectionReason
            FROM CoralImage ci
            LEFT JOIN Users u ON ci.uploadBy = u.userID
            LEFT JOIN Classification cl ON ci.imageID = cl.imageID
            LEFT JOIN HealthStatus h ON cl.healthID = h.healthID
            LEFT JOIN Review r ON cl.classID = r.classID
            WHERE ci.coralID = %s
            ORDER BY ci.uploadDate DESC
            """,
            (coralID,)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getImagesWithDetailsByCoralID: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 4. UPDATE OPERATIONS
# ============================================================================

def updateImagePath(imageID: int, new_imagePath: str) -> bool:
    """
    Update the file path of an image.
    
    Args:
        imageID: ID of the image to update
        new_imagePath: New relative path to the image file
    
    Returns:
        True if update successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE CoralImage
            SET imagePath = %s
            WHERE imageID = %s
            """,
            (new_imagePath, imageID)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in updateImagePath: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def reassignImageToCoral(imageID: int, new_coralID: int) -> bool:
    """
    Reassign an image to a different coral.
    
    Args:
        imageID: ID of the image to reassign
        new_coralID: New coral ID to associate with the image
    
    Returns:
        True if reassignment successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE CoralImage
            SET coralID = %s
            WHERE imageID = %s
            """,
            (new_coralID, imageID)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in reassignImageToCoral: {e}")
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

def deleteImage(imageID: int) -> bool:
    """
    Delete an image record.
    
    Args:
        imageID: ID of the image to delete
    
    Returns:
        True if deletion successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM CoralImage WHERE imageID = %s",
            (imageID,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in deleteImage: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def deleteImagesByCoralID(coralID: int) -> int:
    """
    Delete all images associated with a specific coral.
    
    Args:
        coralID: ID of the coral whose images should be deleted
    
    Returns:
        Number of images deleted
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM CoralImage WHERE coralID = %s",
            (coralID,)
        )
        conn.commit()
        return cursor.rowcount
    except mysql.connector.Error as e:
        print(f"Database error in deleteImagesByCoralID: {e}")
        conn.rollback()
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def deleteImagesByUserID(userID: int) -> int:
    """
    Delete all images uploaded by a specific user.
    
    Args:
        userID: ID of the user whose images should be deleted
    
    Returns:
        Number of images deleted
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM CoralImage WHERE uploadBy = %s",
            (userID,)
        )
        conn.commit()
        return cursor.rowcount
    except mysql.connector.Error as e:
        print(f"Database error in deleteImagesByUserID: {e}")
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

def getImageCountByCoralID(coralID: int) -> int:
    """
    Count the number of images associated with a coral.
    
    Args:
        coralID: ID of the coral
    
    Returns:
        Number of images for the coral
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM CoralImage WHERE coralID = %s",
            (coralID,)
        )
        result = cursor.fetchone()
        return result[0] if result else 0
    except mysql.connector.Error as e:
        print(f"Database error in getImageCountByCoralID: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getImageCountByUserID(userID: int) -> int:
    """
    Count the number of images uploaded by a user.
    
    Args:
        userID: ID of the user
    
    Returns:
        Number of images uploaded by the user
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM CoralImage WHERE uploadBy = %s",
            (userID,)
        )
        result = cursor.fetchone()
        return result[0] if result else 0
    except mysql.connector.Error as e:
        print(f"Database error in getImageCountByUserID: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getTotalImageCount() -> int:
    """
    Get the total number of images in the database.
    
    Returns:
        Total image count
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM CoralImage")
        result = cursor.fetchone()
        return result[0] if result else 0
    except mysql.connector.Error as e:
        print(f"Database error in getTotalImageCount: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 7. BATCH OPERATIONS
# ============================================================================

def bulkCreateCoralImages(images: list[tuple]) -> list[int]:
    """
    Create multiple coral image records in batch.
    
    Args:
        images: List of tuples, each containing (imagePath, uploadBy, coralID)
    
    Returns:
        List of created image IDs (empty list if failed)
    """
    conn = getConnection()
    cursor = None
    created_ids = []
    
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO CoralImage (imagePath, uploadBy, coralID)
            VALUES (%s, %s, %s)
        """
        cursor.executemany(sql, images)
        conn.commit()
        
        # Get the last inserted IDs (MySQL returns first ID, then we can calculate)
        first_id = cursor.lastrowid
        for i in range(len(images)):
            created_ids.append(first_id + i)
        
        return created_ids
    except mysql.connector.Error as e:
        print(f"Database error in bulkCreateCoralImages: {e}")
        conn.rollback()
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()