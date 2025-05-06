
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import json
import os
import time
from datetime import datetime

pizza_grants_bp = Blueprint('pizza_grants', __name__, url_prefix='/api/pizza-grants')

# Create data directory if it doesn't exist
data_dir = 'data/pizza_grants'
os.makedirs(data_dir, exist_ok=True)

def get_submissions_file_path():
    """Get the path to the submissions JSON file"""
    return os.path.join(data_dir, 'submissions.json')

def load_submissions():
    """Load all submissions from the JSON file"""
    file_path = get_submissions_file_path()
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Return empty list if file is empty or invalid
            return []
    return []

def save_submissions(submissions):
    """Save submissions to the JSON file"""
    file_path = get_submissions_file_path()
    with open(file_path, 'w') as f:
        json.dump(submissions, f, indent=2)

@pizza_grants_bp.route('/submit', methods=['POST'])
@login_required
def submit_pizza_grant():
    """Submit a new pizza grant request"""
    try:
        from models import Club, ClubMembership
        
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        required_fields = [
            'club_id', 'user_id', 'username', 'project_name', 
            'project_description', 'project_hours', 'grant_amount'
        ]
        
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        # Validate submitter is authorized (either submitting for self or as club leader/co-leader)
        is_authorized = False
        target_user_id = data['user_id']
        
        if target_user_id == current_user.id or current_user.is_admin:
            is_authorized = True
        else:
            # Check if current user is a club leader for this club
            club = Club.query.filter_by(
                id=data['club_id'],
                leader_id=current_user.id
            ).first()
            
            if club:
                # Verify target user is a member of this club
                membership = ClubMembership.query.filter_by(
                    club_id=club.id,
                    user_id=target_user_id
                ).first()
                
                if membership:
                    is_authorized = True
            
            # If not a leader, check if co-leader
            if not is_authorized:
                coleader_membership = ClubMembership.query.filter_by(
                    club_id=data['club_id'],
                    user_id=current_user.id,
                    role='co-leader'
                ).first()
                
                if coleader_membership:
                    # Verify target user is a member of this club
                    membership = ClubMembership.query.filter_by(
                        club_id=data['club_id'],
                        user_id=target_user_id
                    ).first()
                    
                    if membership:
                        is_authorized = True
        
        if not is_authorized:
            return jsonify({'success': False, 'message': 'Unauthorized to submit for this user'}), 403
        
        # Add additional metadata
        data['submitted_by'] = current_user.id
        data['submitted_by_username'] = current_user.username
        
        # Add submission ID and timestamp if not provided
        if 'id' not in data:
            data['id'] = int(time.time() * 1000)  # Use timestamp as ID
        
        if 'submitted_at' not in data:
            data['submitted_at'] = datetime.now().isoformat()
        
        # Default status to pending if not provided
        if 'status' not in data:
            data['status'] = 'pending'
        
        # Load existing submissions
        submissions = load_submissions()
        
        # Add new submission
        submissions.append(data)
        
        # Save updated submissions
        save_submissions(submissions)
        
        return jsonify({
            'success': True, 
            'message': 'Pizza grant submitted successfully',
            'submission_id': data['id']
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error submitting pizza grant: {str(e)}'}), 500

@pizza_grants_bp.route('/user/<int:user_id>', methods=['GET'])
@login_required
def get_user_submissions(user_id):
    """Get all submissions for a specific user"""
    try:
        from models import Club, ClubMembership
        
        # Validate that the requested user_id matches the current user
        # or current user is an admin/club leader
        is_authorized = False
        
        if user_id == current_user.id or current_user.is_admin:
            is_authorized = True
        else:
            # Check if current user is a club leader
            led_clubs = Club.query.filter_by(leader_id=current_user.id).all()
            for club in led_clubs:
                # Check if requested user is a member of this club
                membership = ClubMembership.query.filter_by(
                    club_id=club.id,
                    user_id=user_id
                ).first()
                if membership:
                    is_authorized = True
                    break
                    
            # Check if current user is a co-leader
            if not is_authorized:
                coleader_memberships = ClubMembership.query.filter_by(
                    user_id=current_user.id,
                    role='co-leader'
                ).all()
                
                for membership in coleader_memberships:
                    # Check if requested user is a member of this club
                    user_membership = ClubMembership.query.filter_by(
                        club_id=membership.club_id,
                        user_id=user_id
                    ).first()
                    if user_membership:
                        is_authorized = True
                        break
        
        if not is_authorized:
            return jsonify({'success': False, 'message': 'Unauthorized to view these submissions'}), 403
        
        # Load all submissions
        all_submissions = load_submissions()
        
        # Filter submissions for the requested user
        user_submissions = [s for s in all_submissions if s.get('user_id') == user_id]
        
        return jsonify({
            'success': True,
            'submissions': user_submissions
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error fetching submissions: {str(e)}'}), 500

@pizza_grants_bp.route('/club/<int:club_id>', methods=['GET'])
@login_required
def get_club_submissions(club_id):
    """Get all submissions for a specific club"""
    try:
        # TODO: Check if current user is club leader or admin
        
        # Load all submissions
        all_submissions = load_submissions()
        
        # Filter submissions for the requested club
        club_submissions = [s for s in all_submissions if s.get('club_id') == club_id]
        
        return jsonify({
            'success': True,
            'submissions': club_submissions
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching club submissions: {str(e)}'}), 500

@pizza_grants_bp.route('/status/<int:submission_id>', methods=['PUT'])
@login_required
def update_submission_status(submission_id):
    """Update the status of a submission (admin/leader only)"""
    try:
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify({'success': False, 'message': 'Status is required'}), 400
        
        # Valid statuses
        valid_statuses = ['pending', 'approved', 'rejected']
        if data['status'] not in valid_statuses:
            return jsonify({'success': False, 'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        # TODO: Check if current user is a club leader or admin
        
        # Load all submissions
        submissions = load_submissions()
        
        # Find and update the submission
        submission_found = False
        for submission in submissions:
            if submission.get('id') == submission_id:
                submission['status'] = data['status']
                if 'feedback' in data:
                    submission['feedback'] = data['feedback']
                submission_found = True
                break
        
        if not submission_found:
            return jsonify({'success': False, 'message': 'Submission not found'}), 404
        
        # Save updated submissions
        save_submissions(submissions)
        
        return jsonify({
            'success': True,
            'message': 'Submission status updated successfully'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating submission status: {str(e)}'}), 500
