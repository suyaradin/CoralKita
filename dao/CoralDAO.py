"""
Coral DAO Module
================
Data Access Object for Coral table operations.
Handles CRUD operations for coral entries, including relationships with regions,
growth forms, images, classifications, and reviews.
"""

import mysql.connector
from util.DBConnection import getConnection


# ============================================================================
# 1. BASIC CRUD OPERATIONS
# ============================================================================

def createCoral(
    genus: str,
    species: str,
    growthFormID: int,
    waterTempMin: float,
    waterTempMax: float,
    pHMin: float,
    pHMax: float,
    regionID: int,
    submittedBy: int
) -> int | None:
    """
    Create a new coral entry.
    
    Args:
        genus: Coral genus name
        species: Coral species name
        growthFormID: ID of the growth form
        waterTempMin: Minimum water temperature (°C)
        waterTempMax: Maximum water temperature (°C)
        pHMin: Minimum pH level
        pHMax: Maximum pH level
        regionID: ID of the region
        submittedBy: ID of the user who submitted the coral
    
    Returns:
        The ID of the newly created coral, or None if failed
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO coral (
                genus, species, growthFormID,
                waterTempMin, waterTempMax,
                pHMin, pHMax, regionID, submittedBy
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (genus, species, growthFormID, waterTempMin, 
             waterTempMax, pHMin, pHMax, regionID, submittedBy)
        )
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error as e:
        print(f"Database error in createCoral: {e}")
        conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getCoralByID(coralID: int) -> dict | None:
    """
    Get coral by ID with region, growth form, and submitter information.
    
    Args:
        coralID: ID of the coral to retrieve
    
    Returns:
        Dictionary containing coral data with joined fields, or None if not found
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT 
                c.*, 
                r.regionName, 
                g.growthFormName, 
                u.username as submittedByName
            FROM coral c
            LEFT JOIN region r ON c.regionID = r.regionID
            LEFT JOIN growthform g ON c.growthFormID = g.growthFormID
            LEFT JOIN users u ON c.submittedBy = u.userID
            WHERE c.coralID = %s
        """
        cursor.execute(sql, (coralID,))
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getCoralByID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getAllCorals() -> list[dict]:
    """
    Get all corals with basic info including region and submitter.
    
    Returns:
        List of dictionaries containing coral data, ordered newest first
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT 
                c.*, 
                r.regionName, 
                u.username as submittedByName
            FROM coral c
            LEFT JOIN region r ON c.regionID = r.regionID
            LEFT JOIN users u ON c.submittedBy = u.userID
            ORDER BY c.submittedAt DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getAllCorals: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getCoralsBySubmittedBy(userID: int) -> list[dict]:
    """
    Get corals submitted by a specific user.
    
    Args:
        userID: ID of the user who submitted the corals
    
    Returns:
        List of dictionaries containing coral data for the user
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT 
                c.*, 
                r.regionName
            FROM coral c
            LEFT JOIN region r ON c.regionID = r.regionID
            WHERE c.submittedBy = %s
            ORDER BY c.submittedAt DESC
        """
        cursor.execute(sql, (userID,))
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getCoralsBySubmittedBy: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def updateCoral(
    coralID: int,
    genus: str,
    species: str,
    growthFormID: int,
    waterTempMin: float,
    waterTempMax: float,
    pHMin: float,
    pHMax: float,
    regionID: int
) -> bool:
    """
    UPDATE coral information.
    
    Args:
        coralID: ID of the coral to update
        genus: Coral genus name
        species: Coral species name
        growthFormID: ID of the growth form
        waterTempMin: Minimum water temperature (°C)
        waterTempMax: Maximum water temperature (°C)
        pHMin: Minimum pH level
        pHMax: Maximum pH level
        regionID: ID of the region
    
    Returns:
        True if update successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        sql = """
            UPDATE coral
            SET genus = %s,
                species = %s,
                growthFormID = %s,
                waterTempMin = %s,
                waterTempMax = %s,
                pHMin = %s,
                pHMax = %s,
                regionID = %s
            WHERE coralID = %s
        """
        cursor.execute(
            sql,
            (genus, species, growthFormID, waterTempMin, 
             waterTempMax, pHMin, pHMax, regionID, coralID)
        )
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in updateCoral: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def deleteCoral(coralID: int) -> bool:
    """
    Delete a coral entry.
    
    Args:
        coralID: ID of the coral to delete
    
    Returns:
        True if deletion successful, False otherwise
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM coral WHERE coralID = %s", (coralID,))
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Database error in deleteCoral: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 2. DASHBOARD QUERIES - SCIENTIFIC REVIEWER
# ============================================================================

def getCoralsWithReviewStatus() -> list[dict]:
    """
    Get all corals with their latest classification, health status, and review status.
    Used by Scientific Reviewer dashboard overview.
    
    Returns:
        List of dictionaries containing coral data with review information
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
                r.regionName,
                h.healthName,
                cl.confidenceScore,
                rev.reviewStatus,
                rev.rejectionReason,
                u.username as submittedBy,
                ci.imagePath
            FROM coral c
            JOIN region r ON c.regionID = r.regionID
            JOIN users u ON c.submittedBy = u.userID
            LEFT JOIN coralimage ci ON c.coralID = ci.coralID
            LEFT JOIN classification cl ON ci.imageID = cl.imageID
            LEFT JOIN healthstatus h ON cl.healthID = h.healthID
            LEFT JOIN review rev ON cl.classID = rev.classID
            GROUP BY c.coralID
            ORDER BY c.submittedAt DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getCoralsWithReviewStatus: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getPendingReviewCorals() -> list[dict]:
    """
    Get all corals that are pending review with full details.
    Used by Scientific Reviewer's pending review section.
    
    Returns:
        List of dictionaries containing pending review coral data
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT 
                r.reviewID,
                r.reviewStatus,
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
                (
                    SELECT r2.iucnID
                    FROM review r2
                    JOIN classification cl2 ON r2.classID = cl2.classID
                    JOIN coralimage ci2 ON cl2.imageID = ci2.imageID
                    WHERE ci2.coralID = c.coralID
                      AND r2.reviewStatus = 'approved'
                      AND r2.iucnID IS NOT NULL
                    ORDER BY r2.reviewedAt DESC, r2.reviewID DESC
                    LIMIT 1
                ) as existingIucnID
            FROM review r
            JOIN classification cl ON r.classID = cl.classID
            JOIN healthstatus h ON cl.healthID = h.healthID
            JOIN coralimage ci ON cl.imageID = ci.imageID
            JOIN coral c ON ci.coralID = c.coralID
            JOIN region reg ON c.regionID = reg.regionID
            JOIN users u ON ci.uploadBy = u.userID
            WHERE r.reviewStatus = 'pending'
            ORDER BY ci.uploadDate ASC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getPendingReviewCorals: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 3. DASHBOARD QUERIES - MARINE BIOLOGIST
# ============================================================================

def getMarineBiologistCoralsWithStatus(userID: int) -> list[dict]:
    """
    Get corals submitted by a specific Marine Biologist with their review status.
    Used by Marine Biologist dashboard overview and library.
    
    Args:
        userID: ID of the marine biologist user
    
    Returns:
        List of dictionaries containing coral data with review status
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT 
                c.coralID,
                c.submittedBy,
                c.genus,
                c.species,
                c.submittedAt,
                ANY_VALUE(r.regionName) AS regionName,
                ANY_VALUE(h.healthName) AS healthName,
                ANY_VALUE(cl.confidenceScore) AS confidenceScore,
                ANY_VALUE(rev.reviewStatus) AS reviewStatus,
                ANY_VALUE(rev.rejectionReason) AS rejectionReason,
                ANY_VALUE(ci.imagePath) AS imagePath
            FROM coral c
            JOIN region r ON c.regionID = r.regionID
            LEFT JOIN coralimage ci ON c.coralID = ci.coralID
            LEFT JOIN classification cl ON ci.imageID = cl.imageID
            LEFT JOIN healthstatus h ON cl.healthID = h.healthID
            LEFT JOIN review rev ON cl.classID = rev.classID
            WHERE c.submittedBy = %s
            GROUP BY c.coralID, c.submittedBy, c.genus, c.species, c.submittedAt
            ORDER BY c.submittedAt DESC
        """
        cursor.execute(sql, (userID,))
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getMarineBiologistCoralsWithStatus: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getMarineBiologistHealthLogs(userID: int) -> list[dict]:
    """
    Get all submission logs (one row per image/classification) for a Marine Biologist.
    Used by the health_log section to show logs only for corals submitted by the current user.
    
    Args:
        userID: ID of the marine biologist user
    
    Returns:
        List of dictionaries containing health log entries
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT
                c.coralID,
                c.submittedBy,
                c.genus,
                c.species,
                c.submittedAt,
                r.regionName,
                h.healthName,
                cl.confidenceScore,
                rev.reviewStatus,
                rev.rejectionReason,
                ci.imagePath,
                ci.uploadDate
            FROM coral c
            JOIN region r ON c.regionID = r.regionID
            LEFT JOIN coralimage ci ON c.coralID = ci.coralID
            LEFT JOIN classification cl ON ci.imageID = cl.imageID
            LEFT JOIN healthstatus h ON cl.healthID = h.healthID
            LEFT JOIN review rev ON cl.classID = rev.classID
            WHERE c.submittedBy = %s
              AND rev.reviewStatus = 'approved'
            ORDER BY ci.uploadDate DESC, c.submittedAt DESC
        """
        cursor.execute(sql, (userID,))
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getMarineBiologistHealthLogs: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================================
# 4. DASHBOARD QUERIES - EDUCATOR
# ============================================================================

def getApprovedCoralsForEducator() -> list[dict]:
    """
    Get approved corals for educator-facing public gallery/table.
    Includes latest review-linked classification fields needed by template.
    
    Returns:
        List of dictionaries containing approved coral data for display
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
                c.waterTempMin,
                c.waterTempMax,
                c.pHMin,
                c.pHMax,
                reg.regionName,
                gf.growthFormName,
                ci.imagePath,
                h.healthName,
                cl.confidenceScore,
                i.iucnName,
                u.username as uploadedByName
            FROM coral c
            JOIN region reg ON c.regionID = reg.regionID
            LEFT JOIN growthform gf ON c.growthFormID = gf.growthFormID
            JOIN coralimage ci ON c.coralID = ci.coralID
            LEFT JOIN users u ON ci.uploadBy = u.userID
            JOIN classification cl ON ci.imageID = cl.imageID
            JOIN healthstatus h ON cl.healthID = h.healthID
            JOIN review rev ON cl.classID = rev.classID
            LEFT JOIN iucnstatus i ON rev.iucnID = i.iucnID
            WHERE rev.reviewStatus = 'approved'
            GROUP BY c.coralID
            ORDER BY c.submittedAt DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getApprovedCoralsForEducator: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 5. DASHBOARD STATISTICS & AGGREGATION
# ============================================================================

def getDashboardCounts() -> dict | None:
    """
    Get counts for dashboard status cards.
    
    Returns:
        Dictionary containing counts for:
        - total: Total number of corals
        - pending_review: Number of pending reviews
        - bleaching_risk: Number of corals with bleaching risk
        - pending_submissions: Number of pending submissions
        - approved_submissions: Number of approved submissions
        - rejected_submissions: Number of rejected submissions
        - critically_endangered: Number of critically endangered corals
        - bleaching_risk_count: Number of corals with bleaching risk
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT 
                (SELECT COUNT(DISTINCT c.coralID) FROM coral c) as total,
                (SELECT COUNT(DISTINCT r.reviewID) FROM review r 
                 WHERE r.reviewStatus = 'pending') as pending_review,
                (SELECT COUNT(DISTINCT c.coralID) FROM coral c 
                 JOIN coralimage ci ON c.coralID = ci.coralID 
                 JOIN classification cl ON ci.imageID = cl.imageID 
                 JOIN healthstatus h ON cl.healthID = h.healthID 
                 JOIN review r ON cl.classID = r.classID 
                 WHERE h.healthName = 'Bleaching' AND r.reviewStatus = 'approved') as bleaching_risk,
                (SELECT COUNT(DISTINCT c.coralID) FROM coral c 
                 JOIN coralimage ci ON c.coralID = ci.coralID 
                 JOIN classification cl ON ci.imageID = cl.imageID 
                 JOIN review r ON cl.classID = r.classID 
                 WHERE r.reviewStatus = 'pending') as pending_submissions,
                (SELECT COUNT(DISTINCT c.coralID) FROM coral c 
                 JOIN coralimage ci ON c.coralID = ci.coralID 
                 JOIN classification cl ON ci.imageID = cl.imageID 
                 JOIN review r ON cl.classID = r.classID 
                 WHERE r.reviewStatus = 'approved') as approved_submissions,
                (SELECT COUNT(DISTINCT c.coralID) FROM coral c 
                 JOIN coralimage ci ON c.coralID = ci.coralID 
                 JOIN classification cl ON ci.imageID = cl.imageID 
                 JOIN review r ON cl.classID = r.classID 
                 WHERE r.reviewStatus = 'rejected') as rejected_submissions,
                (SELECT COUNT(DISTINCT c.coralID) FROM coral c
                 JOIN coralimage ci ON c.coralID = ci.coralID
                 JOIN classification cl ON ci.imageID = cl.imageID
                 JOIN review r ON cl.classID = r.classID
                 JOIN iucnstatus i ON r.iucnID = i.iucnID
                 WHERE r.reviewStatus = 'approved'
                   AND LOWER(i.iucnName) IN ('critically endangered', 'cr')) as critically_endangered,
                (SELECT COUNT(DISTINCT c.coralID) FROM coral c 
                 JOIN coralimage ci ON c.coralID = ci.coralID 
                 JOIN classification cl ON ci.imageID = cl.imageID 
                 JOIN healthstatus h ON cl.healthID = h.healthID 
                 JOIN review r ON cl.classID = r.classID 
                 WHERE h.healthName = 'Bleaching' AND r.reviewStatus = 'approved') as bleaching_risk_count
        """
        cursor.execute(sql)
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database error in getDashboardCounts: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getCoralCountByRegion() -> dict:
    """
    Get coral count per region for Mapbox popup display.
    
    Returns:
        Dictionary mapping regionID to coral count
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT regionID, COUNT(*) as coralCount
            FROM coral
            GROUP BY regionID
        """)
        rows = cursor.fetchall()
        return {row['regionID']: row['coralCount'] for row in rows}
    except mysql.connector.Error as e:
        print(f"Database error in getCoralCountByRegion: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# 6. ADVANCED SEARCH & FILTERING
# ============================================================================

def searchCoralsByGenus(genus: str) -> list[dict]:
    """
    Search corals by genus name (partial match).
    
    Args:
        genus: Genus name to search for
    
    Returns:
        List of dictionaries containing matching coral data
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT 
                c.*, 
                r.regionName,
                u.username as submittedByName
            FROM coral c
            LEFT JOIN region r ON c.regionID = r.regionID
            LEFT JOIN users u ON c.submittedBy = u.userID
            WHERE c.genus LIKE %s
            ORDER BY c.submittedAt DESC
        """
        pattern = f"%{genus}%"
        cursor.execute(sql, (pattern,))
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in searchCoralsByGenus: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def getCoralsByRegion(regionID: int) -> list[dict]:
    """
    Get all corals from a specific region.
    
    Args:
        regionID: ID of the region
    
    Returns:
        List of dictionaries containing coral data for the region
    """
    conn = getConnection()
    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT 
                c.*, 
                r.regionName,
                u.username as submittedByName
            FROM coral c
            LEFT JOIN region r ON c.regionID = r.regionID
            LEFT JOIN users u ON c.submittedBy = u.userID
            WHERE c.regionID = %s
            ORDER BY c.submittedAt DESC
        """
        cursor.execute(sql, (regionID,))
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error in getCoralsByRegion: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()