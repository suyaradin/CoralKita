"""
Coral Management Module
=======================
Handles coral submissions, batch uploads, classification, review workflows,
and email notifications for coral entries.
"""

import os
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for, current_app
from werkzeug.utils import secure_filename

# DAO Imports
from dao.CoralDAO import createCoral, getCoralByID
from dao.CoralImageDAO import addCoralImage, getImagesByCoralID
from dao.ClassificationDAO import createClassification
from dao.ReviewDAO import createReview, approveReviewWithDetails, rejectReviewWithDetails
from dao.HealthStatusDAO import getHealthStatusByName
from dao.UserDAO import getNotificationRecipients
from dao.RegionDAO import getRegionByID

# Utilities
from util.CoralClassifier import classifyCoral
from util.DBConnection import getConnection
from util.gmail_notify import send_email_to_recipients


# ============================================================================
# 1. BLUEPRINT & CONSTANTS
# ============================================================================

coral_bp = Blueprint("coral", __name__)

# File upload configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER_RELATIVE = 'static/uploads'

# ============================================================================
# 2. FILE VALIDATION UTILITIES
# ============================================================================

def allowed_file(filename: str) -> bool:
    """
    Check if file has an allowed extension.
    
    Args:
        filename: Name of the file to check
    
    Returns:
        True if file extension is allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def secure_image_filename(original_filename: str) -> str:
    """
    Generate a secure filename with timestamp prefix.
    
    Args:
        original_filename: Original uploaded filename
    
    Returns:
        Secure filename with timestamp
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return secure_filename(f"{timestamp}_{original_filename}")


def save_uploaded_image(file, app_root: str) -> tuple[str, str]:
    """
    Save uploaded image to disk.
    
    Args:
        file: Uploaded file object
        app_root: Application root path
    
    Returns:
        Tuple of (filename, filepath)
    """
    filename = secure_image_filename(file.filename)
    upload_folder = os.path.join(app_root, UPLOAD_FOLDER_RELATIVE)
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    return filename, filepath


# ============================================================================
# 3. GMAIL NOTIFICATION UTILITIES
# ============================================================================

def notify_reviewers(coral_id: int, genus: str, species: str, region_id: int, submitted_by_name: str, is_update: bool) -> None:
    """
    Send notifications to all users with roleID 1 (Scientific Reviewer) and 2 (Marine Biologist).
    
    Args:
        coral_id: ID of the submitted coral
        genus: Coral genus name
        species: Coral species name
        region_id: ID of the region
        submitted_by_name: Name of the submitter
        is_update: Whether this is an update to existing coral
    """
    try:
        recipients = getNotificationRecipients()
        region = getRegionByID(int(region_id))
        region_name = region.get("regionName") if region else f"Region {region_id}"

        if not recipients:
            print("[Coral] No notification recipients found for roleID 1 or 2")
            return

        subject_prefix = (
            "Coral Observation Update Submitted"
            if is_update
            else "New Coral Entry Submitted"
        )
        subject = f"[CoralKita] {subject_prefix} - CK-{coral_id:04d}"
        intro_line = (
            "A new coral observation has been submitted and is pending review."
            if is_update
            else "A new coral entry has been submitted and is pending review."
        )
        body = (
            f"Dear CoralKita User,\n\n"
            f"{intro_line}\n\n"
            f"Coral ID: CK-{coral_id:04d}\n"
            f"Species: {genus} {species}\n"
            f"Region: {region_name}\n"
            f"Submitted by: {submitted_by_name}\n"
            f"Submitted at: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n\n"
            f"Please log in to CoralKita and review this submission in the Pending Review section.\n\n"
            f"- CoralKita Team"
        )
        emails = [r["email"] for r in recipients if r.get("email")]
        send_email_to_recipients(emails, subject, body, log_prefix="[Coral]")
    except Exception as e:
        print(f"[Coral] Failed sending reviewer notifications: {e}")


# ============================================================================
# 4. FORM VALIDATION HELPERS
# ============================================================================

def validate_coral_submission_form(form_data: dict) -> tuple[bool, str | None]:
    """
    Validate coral submission form data.
    
    Args:
        form_data: Dictionary containing form fields
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['genus', 'species', 'regionID', 'waterTempMin', 'waterTempMax', 'pHMin', 'pHMax']
    
    for field in required_fields:
        if not form_data.get(field):
            return False, f"Missing required field: {field}"
    
    # Validate numeric values
    try:
        float(form_data.get('waterTempMin'))
        float(form_data.get('waterTempMax'))
        float(form_data.get('pHMin'))
        float(form_data.get('pHMax'))
    except (TypeError, ValueError):
        return False, "Invalid numeric values for temperature or pH"
    
    return True, None


def validate_image_upload(request_files) -> tuple[bool, str | None, object | None]:
    """
    Validate image upload from request.
    
    Args:
        request_files: Flask request.files object
    
    Returns:
        Tuple of (is_valid, error_message, file_object)
    """
    if 'coral_image' not in request_files:
        return False, "Please upload a coral image", None
    
    file = request_files['coral_image']
    
    if file.filename == '':
        return False, "Please select an image file", None
    
    if not allowed_file(file.filename):
        return False, "Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WEBP", None
    
    return True, None, file


# ============================================================================
# 5. CORAL SUBMISSION CORE LOGIC
# ============================================================================

def process_coral_classification(image_path: str) -> tuple[str, float]:
    """
    Process coral image classification.
    
    Args:
        image_path: Absolute path to the image file
    
    Returns:
        Tuple of (health_name, confidence_score)
    """
    classification = classifyCoral(image_path)
    health_name = classification["healthName"]
    confidence_score = classification["confidenceScore"]
    return health_name, confidence_score


def create_coral_record(form_data: dict, user_id: int, original_coral_id: int | None = None) -> int | None:
    """
    Create or update coral record.
    
    Args:
        form_data: Dictionary containing form fields
        user_id: ID of the submitting user
        original_coral_id: ID of existing coral for updates (optional)
    
    Returns:
        Coral ID if successful, None otherwise
    """
    genus = form_data.get("genus", "").strip()
    species = form_data.get("species", "").strip()
    region_id = form_data.get("regionID")
    growth_form_id = form_data.get("growthFormID", 1)
    water_temp_min = float(form_data.get("waterTempMin"))
    water_temp_max = float(form_data.get("waterTempMax"))
    ph_min = float(form_data.get("pHMin"))
    ph_max = float(form_data.get("pHMax"))
    
    if original_coral_id:
        # For updates, we use existing coral ID
        return original_coral_id
    else:
        # Create new coral record
        return createCoral(
            genus, species, int(growth_form_id),
            water_temp_min, water_temp_max,
            ph_min, ph_max,
            int(region_id), user_id
        )


def save_coral_submission(
    form_data: dict,
    user_id: int,
    image_file,
    app_root: str,
    original_coral_id: int | None = None
) -> tuple[bool, str | None, dict | None]:
    """
    Complete coral submission workflow.
    
    Args:
        form_data: Dictionary containing form fields
        user_id: ID of the submitting user
        image_file: Uploaded image file object
        app_root: Application root path
        original_coral_id: ID of existing coral for updates (optional)
    
    Returns:
        Tuple of (success, error_message, result_data)
    """
    try:
        # Save image
        filename, filepath = save_uploaded_image(image_file, app_root)
        
        # Create/update coral record
        coral_id = create_coral_record(form_data, user_id, original_coral_id)
        if not coral_id:
            return False, "Failed to create coral entry", None
        
        # Add coral image
        image_id = addCoralImage(filename, user_id, coral_id)
        if not image_id:
            return False, "Failed to save image", None
        
        # Process classification
        filepath_absolute = os.path.join(app_root, UPLOAD_FOLDER_RELATIVE, filename)
        health_name, confidence_score = process_coral_classification(filepath_absolute)
        
        # Get health status ID
        health_status = getHealthStatusByName(health_name)
        health_id = health_status['healthID'] if health_status else 1
        
        # Create classification record
        class_id = createClassification(image_id, health_id, confidence_score)
        if not class_id:
            return False, "Failed to classify coral", None
        
        # Create review record
        review_id = createReview(class_id)
        if not review_id:
            return False, "Coral saved but review creation failed", {"coral_id": coral_id, "partial": True}
        
        return True, None, {
            "coral_id": coral_id,
            "review_id": review_id,
            "health_name": health_name,
            "confidence_score": confidence_score,
            "is_update": bool(original_coral_id)
        }
        
    except Exception as e:
        print(f"Error in coral submission: {e}")
        return False, str(e), None


# ============================================================================
# 6. MAIN SUBMISSION ROUTE
# ============================================================================

@coral_bp.route("/submit_coral", methods=["POST"])
def submit_coral():
    """
    Handle coral submission from Marine Biologist.
    
    Supports both new coral entries and observation updates to existing corals.
    """
    # Authentication check
    if "user_id" not in session:
        flash("Please login to submit coral", "error")
        return redirect(url_for("login.login"))
    
    user_id = session["user_id"]
    form_data = request.form
    
    # Validate form
    is_valid, error = validate_coral_submission_form(form_data)
    if not is_valid:
        flash(error, "error")
        return redirect(url_for("dashboard.dashboard_section", section="upload_coral"))
    
    # Validate image
    is_valid, error, image_file = validate_image_upload(request.files)
    if not is_valid:
        flash(error, "error")
        return redirect(url_for("dashboard.dashboard_section", section="upload_coral"))
    
    # Check if this is an update to existing coral
    original_coral_id = form_data.get('originalCoralID')
    if original_coral_id:
        try:
            coral_candidate = getCoralByID(int(original_coral_id))
            if not coral_candidate or coral_candidate.get('submittedBy') != user_id:
                flash("Invalid coral selected for update", "error")
                return redirect(url_for("dashboard.dashboard_section", section="my_coral_library"))
        except Exception:
            flash("Invalid coral selected for update", "error")
            return redirect(url_for("dashboard.dashboard_section", section="my_coral_library"))
    
    # Process submission
    success, error_msg, result = save_coral_submission(
        form_data,
        user_id,
        image_file,
        current_app.root_path,
        int(original_coral_id) if original_coral_id else None
    )
    
    if not success:
        flash(error_msg or "An error occurred while submitting coral", "error")
        return redirect(url_for("dashboard.dashboard_section", section="upload_coral"))
    
    # Send notifications to reviewers
    if result and result.get("review_id"):
        notify_reviewers(
            result["coral_id"],
            form_data.get("genus", "").strip(),
            form_data.get("species", "").strip(),
            form_data.get("regionID"),
            session.get("username", "Marine Biologist"),
            result.get("is_update", False)
        )
    
    # Success message
    if original_coral_id:
        flash("New observation added and submitted for review.", "success")
    else:
        flash("Coral submitted successfully! Waiting for review.", "success")
    
    return redirect(url_for("dashboard.dashboard_section", section="my_coral_library"))


# ============================================================================
# 7. BATCH UPLOAD ROUTE
# ============================================================================

@coral_bp.route("/batch_upload", methods=["POST"])
def batch_upload():
    """
    Handle batch upload of multiple coral images.
    
    Returns:
        JSON response with upload status
    """
    if "user_id" not in session:
        return {"success": False, "error": "Not logged in"}, 401
    
    if 'coral_images[]' not in request.files:
        return {"success": False, "error": "No files uploaded"}, 400
    
    files = request.files.getlist('coral_images[]')
    uploaded_count = 0
    
    for file in files:
        if file and allowed_file(file.filename):
            # TODO: Process each file with coral classification
            uploaded_count += 1
    
    return {"success": True, "count": uploaded_count}


# ============================================================================
# 8. REVIEW API ENDPOINTS (Admin/Scientific Reviewer)
# ============================================================================

@coral_bp.route("/api/review/<int:reviewID>/approve", methods=["POST"])
def approve_review(reviewID: int):
    """
    API endpoint to approve a review.
    
    Args:
        reviewID: ID of the review to approve
    
    Returns:
        JSON response with approval status
    """
    # Authentication check
    if "user_id" not in session:
        return {"success": False, "error": "Not logged in"}, 401
    
    # Authorization check
    if session.get("role_id") != ROLE_SCIENTIFIC_REVIEWER:
        return {"success": False, "error": "Unauthorized"}, 403
    
    # Get IUCN ID from request
    data = request.get_json() or {}
    iucn_id = data.get("iucnID")
    
    if iucn_id is None or iucn_id == "":
        iucn_id = None
    else:
        try:
            iucn_id = int(iucn_id)
        except ValueError:
            return {"success": False, "error": "IUCN status is invalid"}, 400
    
    # Process approval
    result = approveReviewWithDetails(reviewID, session["user_id"], iucn_id)
    
    if result:
        return {"success": True}
    else:
        return {
            "success": False,
            "error": "Failed to approve. Select IUCN status if this coral has no previous approved IUCN yet."
        }


@coral_bp.route("/api/review/<int:reviewID>/reject", methods=["POST"])
def reject_review(reviewID: int):
    """
    API endpoint to reject a review.
    
    Args:
        reviewID: ID of the review to reject
    
    Returns:
        JSON response with rejection status
    """
    # Authentication check
    if "user_id" not in session:
        return {"success": False, "error": "Not logged in"}, 401
    
    # Authorization check
    if session.get("role_id") != ROLE_SCIENTIFIC_REVIEWER:
        return {"success": False, "error": "Unauthorized"}, 403
    
    # Get rejection reason
    data = request.get_json()
    reason = data.get("reason", "")
    
    # Process rejection
    result = rejectReviewWithDetails(reviewID, session["user_id"], reason)
    
    if result:
        return {"success": True}
    else:
        return {"success": False, "error": "Failed to reject"}


# ============================================================================
# 9. CORAL VIEW API ENDPOINT
# ============================================================================

@coral_bp.route("/api/coral/<int:coralID>/view", methods=["GET"])
def view_coral(coralID: int):
    """
    API endpoint to get coral details with review status and rejection reason.
    
    Args:
        coralID: ID of the coral to view
    
    Returns:
        JSON response with coral details
    """
    coral = getCoralByID(coralID)
    images = getImagesByCoralID(coralID)
    
    # Fetch review status and rejection reason
    review_info = None
    if coral:
        try:
            conn = getConnection()
            cursor = conn.cursor(dictionary=True)
            
            sql = """
                SELECT r.reviewStatus, r.rejectionReason, i.iucnName
                FROM Review r
                JOIN Classification cl ON r.classID = cl.classID
                JOIN CoralImage ci ON cl.imageID = ci.imageID
                LEFT JOIN IUCNStatus i ON r.iucnID = i.iucnID
                WHERE ci.coralID = %s
                ORDER BY r.reviewedAt DESC, r.reviewID DESC
                LIMIT 1
            """
            cursor.execute(sql, (coralID,))
            review_info = cursor.fetchone()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error fetching review info: {e}")
    
    if coral:
        if review_info:
            coral['reviewStatus'] = review_info.get('reviewStatus')
            coral['rejectionReason'] = review_info.get('rejectionReason')
            coral['iucnName'] = review_info.get('iucnName')
        else:
            coral['iucnName'] = None
        
        return {
            "success": True,
            "coral": coral,
            "images": images
        }
    else:
        return {"success": False, "error": "Coral not found"}