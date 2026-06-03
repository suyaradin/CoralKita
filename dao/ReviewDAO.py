"""
Review DAO Module
=================
Data Access Object for Review table operations.
Handles review workflow for coral submissions including approval, rejection,
and tracking of IUCN conservation status assignments.
"""

import mysql.connector
from util.DBConnection import getConnection


# ============================================================================
# 1. CREATE OPERATIONS
# ============================================================================

def createReview(classID: int) -> int | None:
    """
    Create a new review entry (pending by default).
    
    Args:
        classID: ID of the classification being reviewed
    
    Returns:
        The ID of the newly created review, or None if failed
        
    Example:
        >>> review_id = createReview(123)
        >>> print(f"Review {review_id} created with pending status")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Review (classID) VALUES (%s)",
            (classID,)
        )
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error as e:
        print(f"Database error in createReview: {e}")
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

def getReviewByID(reviewID: int) -> dict | None:
    """
    Get review by ID with classification and health status details.
    
    Args:
        reviewID: ID of the review to retrieve
    
    Returns:
        Dictionary containing review data with joined fields, or None if not found
        
    Example:
        >>> review = getReviewByID(456)
        >>> print(review['reviewStatus'])
        'pending'
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT 
                r.*, 
                cl.imageID, 
                cl.healthID, 
                cl.confidenceScore, 
                h.healthName
            FROM Review r
            JOIN Classification cl ON r.classID = cl.classID
            LEFT JOIN HealthStatus h ON cl.healthID = h.healthID
            WHERE r.reviewID = %s
        """
        cursor.execute(sql, (reviewID,))
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getReviewByID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getReviewByClassID(classID: int) -> dict | None:
    """
    Get review by classification ID.
    
    Args:
        classID: ID of the classification
    
    Returns:
        Dictionary containing review data, or None if not found
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM Review WHERE classID = %s ORDER BY reviewID DESC LIMIT 1",
            (classID,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getReviewByClassID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 3. READ OPERATIONS (Multiple Records)
# ============================================================================

def getReviewsByStatus(reviewStatus: str) -> list[dict]:
    """
    Get all reviews by status, ordered by most recent update.
    
    Args:
        reviewStatus: Status to filter by ('pending', 'approved', 'rejected')
    
    Returns:
        List of dictionaries containing review data (empty list if none found)
        
    Example:
        >>> pending = getReviewsByStatus('pending')
        >>> print(f"{len(pending)} reviews waiting for approval")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM Review WHERE reviewStatus = %s ORDER BY updatedAt DESC",
            (reviewStatus,)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getReviewsByStatus: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getPendingReviews() -> list[dict]:
    """
    Get all pending reviews.
    
    Returns:
        List of dictionaries containing pending review data
        
    Example:
        >>> pending = getPendingReviews()
        >>> for p in pending:
        ...     print(f"Review {p['reviewID']} - {p['reviewStatus']}")
    """
    return getReviewsByStatus('pending')


def getApprovedReviews() -> list[dict]:
    """
    Get all approved reviews.
    
    Returns:
        List of dictionaries containing approved review data
    """
    return getReviewsByStatus('approved')


def getRejectedReviews() -> list[dict]:
    """
    Get all rejected reviews.
    
    Returns:
        List of dictionaries containing rejected review data
    """
    return getReviewsByStatus('rejected')


def getReviewsByReviewer(reviewerID: int) -> list[dict]:
    """
    Get all reviews handled by a specific reviewer.
    
    Args:
        reviewerID: ID of the reviewer user
    
    Returns:
        List of dictionaries containing review data
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT r.*, u.username as reviewedByName
            FROM Review r
            LEFT JOIN Users u ON r.reviewedBy = u.userID
            WHERE r.reviewedBy = %s
            ORDER BY r.reviewedAt DESC
            """,
            (reviewerID,)
        )
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getReviewsByReviewer: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 4. DASHBOARD & COMPLEX QUERIES
# ============================================================================

def getReviewsWithCoralDetails() -> list[dict]:
    """
    Get all reviews with coral, image, and classification details.
    Used for the pending review section and dashboard.
    
    Returns:
        List of dictionaries containing comprehensive review data
        
    Example:
        >>> reviews = getReviewsWithCoralDetails()
        >>> for r in reviews:
        ...     print(f"{r['genus']} {r['species']} - {r['reviewStatus']}")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT 
                r.reviewID,
                r.reviewStatus,
                r.rejectionReason,
                r.reviewedAt,
                r.iucnID,
                cl.classID,
                cl.confidenceScore,
                h.healthName,
                ci.imageID,
                ci.imagePath,
                ci.uploadDate,
                c.coralID,
                c.genus,
                c.species,
                reg.regionName,
                u.username as submittedBy,
                u.userID as submittedByID,
                reviewer.username as reviewedByName
            FROM Review r
            JOIN Classification cl ON r.classID = cl.classID
            JOIN HealthStatus h ON cl.healthID = h.healthID
            JOIN CoralImage ci ON cl.imageID = ci.imageID
            JOIN Coral c ON ci.coralID = c.coralID
            JOIN Region reg ON c.regionID = reg.regionID
            JOIN Users u ON ci.uploadBy = u.userID
            LEFT JOIN Users reviewer ON r.reviewedBy = reviewer.userID
            ORDER BY r.reviewStatus ASC, ci.uploadDate DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getReviewsWithCoralDetails: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getUserSubmissionsWithStatus(userID: int) -> list[dict]:
    """
    Get all submissions for a specific user with their review status.
    Used by Marine Biologist to see their submission status.
    
    Args:
        userID: ID of the user who submitted the corals
    
    Returns:
        List of dictionaries containing submission data with review status
        
    Example:
        >>> my_submissions = getUserSubmissionsWithStatus(789)
        >>> for s in my_submissions:
        ...     print(f"{s['genus']}: {s['reviewStatus']}")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT 
                c.coralID,
                c.genus,
                c.species,
                c.submittedAt,
                reg.regionName,
                h.healthName,
                cl.confidenceScore,
                r.reviewStatus,
                r.rejectionReason,
                r.reviewedAt,
                ci.imagePath,
                reviewer.username as reviewedBy
            FROM Coral c
            JOIN Region reg ON c.regionID = reg.regionID
            JOIN CoralImage ci ON c.coralID = ci.coralID
            JOIN Classification cl ON ci.imageID = cl.imageID
            LEFT JOIN Review r ON cl.classID = r.classID
            LEFT JOIN HealthStatus h ON cl.healthID = h.healthID
            LEFT JOIN Users reviewer ON r.reviewedBy = reviewer.userID
            WHERE c.submittedBy = %s
            GROUP BY c.coralID
            ORDER BY c.submittedAt DESC
        """
        cursor.execute(sql, (userID,))
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getUserSubmissionsWithStatus: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getPendingReviewsWithDetails() -> list[dict]:
    """
    Get pending reviews with full coral and submission details.
    Optimized for the pending review dashboard view.
    
    Returns:
        List of dictionaries containing pending review data with details
    """
    all_reviews = getReviewsWithCoralDetails()
    return [r for r in all_reviews if r.get('reviewStatus') == 'pending']


def getReviewStatistics() -> dict:
    """
    Get statistics about reviews.
    
    Returns:
        Dictionary containing review statistics:
        - total: Total number of reviews
        - pending: Number of pending reviews
        - approved: Number of approved reviews
        - rejected: Number of rejected reviews
        - approval_rate: Percentage of approved reviews
        
    Example:
        >>> stats = getReviewStatistics()
        >>> print(f"Approval rate: {stats['approval_rate']}%")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN reviewStatus = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN reviewStatus = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN reviewStatus = 'rejected' THEN 1 ELSE 0 END) as rejected
            FROM Review
            """
        )
        result = cursor.fetchone()
        
        if result and result['total'] > 0:
            total_reviewed = result['approved'] + result['rejected']
            if total_reviewed > 0:
                result['approval_rate'] = round(
                    (result['approved'] / total_reviewed) * 100, 2
                )
            else:
                result['approval_rate'] = 0
        else:
            result['approval_rate'] = 0
            
        return result or {}
    except mysql.connector.Error as e:
        print(f"Database error in getReviewStatistics: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 5. UPDATE OPERATIONS (Review Workflow)
# ============================================================================

def updateReview(
    reviewID: int,
    reviewStatus: str,
    reviewedBy: int,
    iucnID: int = None,
    rejectionReason: str = None
) -> bool:
    """
    Update review status with reviewer information.
    
    Args:
        reviewID: ID of the review to update
        reviewStatus: New status ('approved' or 'rejected')
        reviewedBy: ID of the reviewer user
        iucnID: IUCN status ID (required for approval)
        rejectionReason: Reason for rejection (required for rejection)
    
    Returns:
        True if update successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        sql = """
            UPDATE Review
            SET reviewStatus = %s,
                reviewedBy = %s,
                reviewedAt = NOW(),
                iucnID = %s,
                rejectionReason = %s
            WHERE reviewID = %s
        """
        cursor.execute(
            sql,
            (reviewStatus, reviewedBy, iucnID, rejectionReason, reviewID)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in updateReview: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def approveReviewWithDetails(reviewID: int, reviewerID: int, iucnID: int = None) -> bool:
    """
    Approve a review with IUCN status.
    If iucnID is not provided, tries to reuse the coral's latest approved IUCN status.
    
    Args:
        reviewID: ID of the review to approve
        reviewerID: ID of the reviewer user
        iucnID: IUCN status ID (optional, will try to inherit if not provided)
    
    Returns:
        True if approval successful, False otherwise
        
    Example:
        >>> success = approveReviewWithDetails(123, 456, 5)
        >>> print("Approved!" if success else "Failed to approve")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # If iucnID is not provided, try to inherit from previous approved version
        if iucnID is None:
            # Get the coral ID for this review
            cursor.execute(
                """
                SELECT ci.coralID
                FROM Review r
                JOIN Classification cl ON r.classID = cl.classID
                JOIN CoralImage ci ON cl.imageID = ci.imageID
                WHERE r.reviewID = %s
                LIMIT 1
                """,
                (reviewID,)
            )
            target = cursor.fetchone()
            
            if not target or target.get("coralID") is None:
                return False
            
            target_coral_id = int(target["coralID"])
            
            # Find the most recent approved IUCN status for this coral
            cursor.execute(
                """
                SELECT prev.iucnID
                FROM Review prev
                JOIN Classification pcl ON prev.classID = pcl.classID
                JOIN CoralImage pci ON pcl.imageID = pci.imageID
                WHERE prev.reviewStatus = 'approved'
                  AND prev.iucnID IS NOT NULL
                  AND pci.coralID = %s
                ORDER BY prev.reviewedAt DESC, prev.reviewID DESC
                LIMIT 1
                """,
                (target_coral_id,)
            )
            existing = cursor.fetchone()
            
            if existing and existing.get("iucnID") is not None:
                iucnID = int(existing["iucnID"])
            else:
                # No previous approved IUCN exists; caller must provide one
                return False
        
        # Proceed with approval
        sql = """
            UPDATE Review
            SET reviewStatus = 'approved',
                reviewedBy = %s,
                reviewedAt = NOW(),
                iucnID = %s
            WHERE reviewID = %s AND reviewStatus = 'pending'
        """
        cursor.execute(sql, (reviewerID, iucnID, reviewID))
        conn.commit()
        return cursor.rowcount > 0
        
    except mysql.connector.Error as e:
        print(f"Database error in approveReviewWithDetails: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def rejectReviewWithDetails(reviewID: int, reviewerID: int, rejectionReason: str) -> bool:
    """
    Reject a review with a reason.
    
    Args:
        reviewID: ID of the review to reject
        reviewerID: ID of the reviewer user
        rejectionReason: Reason for rejection
    
    Returns:
        True if rejection successful, False otherwise
        
    Example:
        >>> success = rejectReviewWithDetails(123, 456, "Image quality too low")
        >>> print("Rejected!" if success else "Failed to reject")
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        sql = """
            UPDATE Review
            SET reviewStatus = 'rejected',
                reviewedBy = %s,
                reviewedAt = NOW(),
                rejectionReason = %s
            WHERE reviewID = %s AND reviewStatus = 'pending'
        """
        cursor.execute(sql, (reviewerID, rejectionReason, reviewID))
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in rejectReviewWithDetails: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def bulkApproveReviews(reviewIDs: list[int], reviewerID: int, iucnID: int = None) -> int:
    """
    Bulk approve multiple reviews.
    
    Args:
        reviewIDs: List of review IDs to approve
        reviewerID: ID of the reviewer user
        iucnID: IUCN status ID to apply to all (optional)
    
    Returns:
        Number of reviews successfully approved
    """
    if not reviewIDs:
        return 0
    
    conn = getConnection()
    cursor = None
    approved_count = 0
    
    try:
        cursor = conn.cursor()
        
        for reviewID in reviewIDs:
            sql = """
                UPDATE Review
                SET reviewStatus = 'approved',
                    reviewedBy = %s,
                    reviewedAt = NOW(),
                    iucnID = %s
                WHERE reviewID = %s AND reviewStatus = 'pending'
            """
            cursor.execute(sql, (reviewerID, iucnID, reviewID))
            if cursor.rowcount > 0:
                approved_count += 1
        
        conn.commit()
        return approved_count
    except mysql.connector.Error as e:
        print(f"Database error in bulkApproveReviews: {e}")
        conn.rollback()
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 6. DELETE OPERATIONS (Admin)
# ============================================================================

def deleteReview(reviewID: int) -> bool:
    """
    Delete a review record (admin function).
    
    Args:
        reviewID: ID of the review to delete
    
    Returns:
        True if deletion successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM Review WHERE reviewID = %s",
            (reviewID,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in deleteReview: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def deleteReviewsByClassID(classID: int) -> int:
    """
    Delete all reviews associated with a classification.
    
    Args:
        classID: ID of the classification
    
    Returns:
        Number of reviews deleted
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM Review WHERE classID = %s",
            (classID,)
        )
        conn.commit()
        return cursor.rowcount
    except mysql.connector.Error as e:
        print(f"Database error in deleteReviewsByClassID: {e}")
        conn.rollback()
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()