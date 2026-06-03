"""
Dashboard Module
================
Handles all dashboard routes, user role-based views, profile management,
and CRUD operations for coral data across different user roles.
"""

import os
from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, session, url_for, jsonify, current_app

# DAO Imports - User Management
from dao.UserDAO import (
    getByID,
    getAllUsers,
    updateUserProfile,
    deleteUser,
    createUser,
    getByEmail
)

# DAO Imports - Coral Management
from dao.CoralDAO import (
    getCoralsWithReviewStatus,
    getMarineBiologistCoralsWithStatus,
    getMarineBiologistHealthLogs,
    getApprovedCoralsForEducator,
    getDashboardCounts,
    getPendingReviewCorals,
    getCoralByID
)

# DAO Imports - Review Management
from dao.ReviewDAO import (
    getReviewsWithCoralDetails,
    getUserSubmissionsWithStatus,
    approveReviewWithDetails,
    rejectReviewWithDetails
)

# DAO Imports - Reference Data
from dao.IUCNStatusDAO import getAllIUCNStatuses
from dao.RoleDAO import getRoleNameByID

# Utilities
from util.Bcrypt import checkPassword, hashPassword


# ============================================================================
# 1. BLUEPRINT & ROLE CONSTANTS
# ============================================================================

dashboard_bp = Blueprint("dashboard", __name__)

# Role IDs
ROLE_ADMIN = 1              # Scientific Reviewer / Admin
ROLE_MARINE_BIOLOGIST = 2   # Marine Biologist
ROLE_EDUCATOR = 3           # Educator

# Valid dashboard sections
VALID_SECTIONS = {
    "overview",
    "pending_review",
    "coral_library",
    "upload_coral",
    "my_coral_library",
    "health_log",
    "my_profile",
    "user_management"
}


# ============================================================================
# 2. HELPER FUNCTIONS
# ============================================================================

def get_user_initials(username: str) -> str:
    """Extract initials from username."""
    if not username:
        return ""
    return "".join([part[0].upper() for part in username.split() if part])[:2]


def get_section_mapping(role_id: int, section: str) -> str:
    """Map generic section names to role-appropriate sections."""
    if section == "coral":
        if role_id == ROLE_ADMIN:
            return "pending_review"
        elif role_id == ROLE_MARINE_BIOLOGIST:
            return "upload_coral"
        else:
            return "overview"
    
    if section == "settings":
        return "my_profile"
    
    return section


def validate_section(section: str) -> str:
    """Ensure section is valid, defaulting to 'overview'."""
    return section if section in VALID_SECTIONS else "overview"


def get_user_context(user_id: int, username: str, role_id: int) -> dict:
    """Get common user context data for templates."""
    current_user = getByID(user_id) if user_id else None
    user_email = current_user.get("email") if current_user else ""
    user_initials = get_user_initials(username)
    user_role_name = session.get("user_role", "")
    
    return {
        "user_email": user_email,
        "user_initials": user_initials,
        "user_role_name": user_role_name,
        "user_role": user_role_name
    }


# ============================================================================
# 3. DATA FETCHING BY ROLE
# ============================================================================

def fetch_corals_for_admin(section: str) -> list:
    """Fetch coral data for Admin/Scientific Reviewer role."""
    if section == 'pending_review':
        return getPendingReviewCorals() or []
    # coral_library and overview show all corals with review status
    return getCoralsWithReviewStatus() or []


def fetch_corals_for_marine_biologist(section: str, user_id: int, prefill_coral_ref: dict) -> tuple[list, dict]:
    """Fetch coral data for Marine Biologist role."""
    prefill_coral = None
    corals = []
    
    if section == 'health_log':
        logs = getMarineBiologistHealthLogs(user_id) or []
        grouped = {}
        
        for row in logs:
            coral_id = row.get("coralID")
            if coral_id not in grouped:
                grouped[coral_id] = {
                    "coralID": coral_id,
                    "genus": row.get("genus"),
                    "species": row.get("species"),
                    "regionName": row.get("regionName"),
                    "submittedAt": row.get("submittedAt"),
                    "logs": []
                }
            grouped[coral_id]["logs"].append(row)
        
        # Process grouped logs
        for coral in grouped.values():
            coral_logs = coral.get("logs", [])
            coral_logs.sort(
                key=lambda x: x.get("uploadDate") or x.get("submittedAt") or datetime.min,
                reverse=True
            )
            
            if coral_logs:
                latest = max(
                    coral_logs,
                    key=lambda x: x.get("uploadDate") or x.get("submittedAt") or datetime.min
                )
                coral["healthName"] = latest.get("healthName")
                coral["reviewStatus"] = latest.get("reviewStatus")
                coral["uploadDate"] = latest.get("uploadDate") or latest.get("submittedAt")
                coral["submissionCount"] = len(coral_logs)
                coral["logs"] = coral_logs
            else:
                coral["healthName"] = None
                coral["reviewStatus"] = None
                coral["uploadDate"] = coral.get("submittedAt")
                coral["submissionCount"] = 0
            
            corals.append(coral)
            
    elif section in ('my_coral_library', 'overview'):
        corals = getMarineBiologistCoralsWithStatus(user_id) or []
    
    # Handle upload_coral prefill
    if section == 'upload_coral':
        prefill_id = prefill_coral_ref.get('prefill_id')
        if prefill_id:
            try:
                prefill_candidate = getCoralByID(int(prefill_id))
                if prefill_candidate and prefill_candidate.get('submittedBy') == user_id:
                    prefill_coral = prefill_candidate
            except Exception:
                pass
    
    return corals, prefill_coral


def fetch_corals_for_educator() -> list:
    """Fetch coral data for Educator role."""
    return getApprovedCoralsForEducator() or []


# ============================================================================
# 4. DEBUGGING UTILITIES
# ============================================================================

def debug_dashboard_state(section: str, role_id: int, corals: list) -> None:
    """Debug logging to help trace rendering issues."""
    try:
        print(f"[dashboard] section={section} role_id={role_id} "
              f"corals_type={type(corals)} "
              f"corals_len={len(corals) if corals is not None else 'None'}")
        
        if corals and len(corals) > 0:
            first = corals[0]
            try:
                print(f"[dashboard] first_item_keys={list(first.keys())}")
            except Exception:
                print(f"[dashboard] first_item_repr={repr(first)[:200]}")
    except Exception:
        pass


# ============================================================================
# 5. MAIN DASHBOARD ROUTE
# ============================================================================

@dashboard_bp.route("/dashboard")
def dashboard():
    """Redirect to default overview section."""
    return dashboard_section("overview")


@dashboard_bp.route("/dashboard/<section>")
def dashboard_section(section):
    """
    Main dashboard view - renders role-appropriate dashboard.
    
    Supports sections:
    - overview: Main dashboard with counts and metrics
    - pending_review: Corals awaiting review (Admin only)
    - coral_library: All approved corals (Admin/Educator)
    - my_coral_library: User's corals (Marine Biologist)
    - upload_coral: Upload new coral (Marine Biologist)
    - health_log: Coral health logs (Marine Biologist)
    - my_profile: User profile settings
    - user_management: Manage users (Admin only)
    """
    # Authentication check
    if "user_id" not in session:
        return redirect(url_for("login.login"))
    
    # Get session data
    role_id = session.get("role_id")
    user_name = session.get("username")
    user_id = session.get("user_id")
    
    # Get user context
    user_context = get_user_context(user_id, user_name, role_id)
    
    # Get users for admin
    users = getAllUsers() if role_id == ROLE_ADMIN else []
    
    # Get dashboard counts
    try:
        counts = getDashboardCounts() or {}
    except Exception:
        counts = {}
    
    # Map and validate section
    section = get_section_mapping(role_id, section)
    section = validate_section(section)
    
    # Fetch corals based on role
    corals = []
    prefill_coral = None
    
    try:
        if role_id == ROLE_ADMIN:
            corals = fetch_corals_for_admin(section)
            
        elif role_id == ROLE_MARINE_BIOLOGIST:
            corals, prefill_coral = fetch_corals_for_marine_biologist(
                section, user_id, {"prefill_id": request.args.get('prefillCoralID')}
            )
            
        elif role_id == ROLE_EDUCATOR:
            corals = fetch_corals_for_educator()
            
    except Exception as e:
        print(f"[dashboard] Error fetching corals: {e}")
        corals = []

    # Role-specific card count: total corals for currently logged-in Marine Biologist only.
    if role_id == ROLE_MARINE_BIOLOGIST:
        try:
            my_corals = getMarineBiologistCoralsWithStatus(user_id) or []
            counts["my_total"] = len(my_corals)
            counts["my_pending"] = sum(1 for c in my_corals if (c.get("reviewStatus") or "").lower() == "pending")
            counts["my_approved"] = sum(1 for c in my_corals if (c.get("reviewStatus") or "").lower() == "approved")
            counts["my_rejected"] = sum(1 for c in my_corals if (c.get("reviewStatus") or "").lower() == "rejected")
        except Exception:
            counts["my_total"] = 0
            counts["my_pending"] = 0
            counts["my_approved"] = 0
            counts["my_rejected"] = 0
    
    # Debug logging
    debug_dashboard_state(section, role_id, corals)
    
    # Get IUCN statuses for admin
    iucn_statuses = []
    if role_id == ROLE_ADMIN:
        try:
            iucn_statuses = getAllIUCNStatuses() or []
        except Exception:
            iucn_statuses = []
    
    # Get Mapbox token from environment
    mapbox_token = os.getenv('MAPBOX_TOKEN')
    
    # Prepare template kwargs
    template_kwargs = {
        "username": user_name,
        "user_name": user_name,
        "roleID": role_id,
        "counts": counts,
        "corals": corals,
        "active_section": section,
        "users": users,
        "prefillCoral": prefill_coral,
        "iucn_statuses": iucn_statuses,
        "mapbox_token": mapbox_token,      # For templates using 'mapbox_token'
        "MAPBOX_TOKEN": mapbox_token,      # For templates using 'MAPBOX_TOKEN'
        **user_context
    }
    
    # Render appropriate dashboard template
    if role_id == ROLE_ADMIN:
        return render_template("scientificR_dashboard.html", **template_kwargs)
    elif role_id == ROLE_MARINE_BIOLOGIST:
        return render_template("marineB_dashboard.html", **template_kwargs)
    elif role_id == ROLE_EDUCATOR:
        return render_template("educator_dashboard.html", **template_kwargs)
    else:
        session.clear()
        return redirect(url_for("login.login"))


# ============================================================================
# 6. PROFILE MANAGEMENT
# ============================================================================

@dashboard_bp.route("/dashboard/update_profile", methods=["POST"])
def update_profile():
    """Update user profile information."""
    if "user_id" not in session:
        return redirect(url_for("login.login"))
    
    user_id = session.get("user_id")
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    
    # Validation
    if not name or not email:
        flash("Name and email are required.", "error")
        return redirect(url_for("dashboard.dashboard_section", section="my_profile"))
    
    # Hash password if provided
    password_hash = hashPassword(password) if password else None
    
    # Update profile
    updateUserProfile(user_id, name, email, password_hash)
    session["username"] = name
    
    flash("Profile updated successfully.", "success")
    return redirect(url_for("dashboard.dashboard_section", section="my_profile"))


# ============================================================================
# 7. USER MANAGEMENT (ADMIN ONLY)
# ============================================================================

@dashboard_bp.route("/api/user/<int:userID>/delete", methods=["POST"])
def delete_user(userID):
    """
    API endpoint to delete a user.
    Admin only.
    """
    # Authentication check
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    # Authorization check
    if session.get("role_id") != ROLE_ADMIN:
        return jsonify({"success": False, "error": "Forbidden"}), 403
    
    # Delete user
    result = deleteUser(userID)
    
    if result:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Failed to delete user"})


@dashboard_bp.route("/dashboard/create_scientific_reviewer", methods=["POST"])
def create_scientific_reviewer():
    """Create a new scientific reviewer account (Admin only)."""
    # Authentication check
    if "user_id" not in session:
        return redirect(url_for("login.login"))
    
    # Authorization check
    if session.get("role_id") != ROLE_ADMIN:
        flash("Unauthorized action.", "error")
        return redirect(url_for("dashboard.dashboard_section", section="user_management"))
    
    # Get form data
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    
    # Validation
    if not name or not email or not password:
        flash("Name, email, and password are required.", "error")
        return redirect(url_for("dashboard.dashboard_section", section="user_management"))
    
    # Check if email exists
    existing = getByEmail(email)
    if existing:
        flash("Email already exists. Please use a different email.", "error")
        return redirect(url_for("dashboard.dashboard_section", section="user_management"))
    
    # Create reviewer
    try:
        password_hash = hashPassword(password)
        reviewer_id = createUser(name, email, password_hash, ROLE_ADMIN)
        
        if reviewer_id:
            flash("Scientific reviewer created successfully.", "success")
        else:
            flash("Failed to create scientific reviewer.", "error")
    except Exception:
        flash("An error occurred while creating scientific reviewer.", "error")
    
    return redirect(url_for("dashboard.dashboard_section", section="user_management"))