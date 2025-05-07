from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import time
from datetime import datetime
from airtable_service import airtable_service

pizza_grants_bp = Blueprint('pizza_grants', __name__, url_prefix='/api/pizza-grants')

@pizza_grants_bp.route('/submit', methods=['POST'])
@login_required
def submit_pizza_grant():
    """Submit a new pizza grant request"""
    try:
        from models import Club, ClubMembership

        # Get request data
        data = request.get_json()

        # Extract first and last name from username or user model if available
        if 'username' in data and ('first_name' not in data or 'last_name' not in data):
            from models import User
            user = User.query.filter_by(id=data.get('user_id')).first()
            if user:
                data['first_name'] = getattr(user, 'first_name', '') or ''
                data['last_name'] = getattr(user, 'last_name', '') or ''
                data['email'] = getattr(user, 'email', '') or data.get('email', '')
            else:
                # If we can't find the user, use the username as first name
                name_parts = data['username'].split()
                if len(name_parts) > 1:
                    data['first_name'] = name_parts[0]
                    data['last_name'] = ' '.join(name_parts[1:])
                else:
                    data['first_name'] = data['username']
                    data['last_name'] = ''

        # Validate required fields
        required_fields = [
            'club_id', 'user_id', 'username', 'project_name', 
            'project_description', 'project_hours', 'grant_amount',
            'shipping_address', 'github_url', 'live_url', 'screenshot', 'email', 
            'first_name', 'last_name', 'birthday', 'what_learned', 'doing_well', 'improve'
        ]

        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400

        # Validate shipping address fields
        address_fields = ['address1', 'city', 'state', 'zip', 'country']
        shipping_address = data.get('shipping_address', {})

        for field in address_fields:
            if field not in shipping_address or not shipping_address[field]:
                return jsonify({'success': False, 'message': f'Missing required address field: {field}'}), 400

        # Validate screenshot URL
        screenshot_url = data.get('screenshot', '')
        if not screenshot_url:
            return jsonify({'success': False, 'message': 'Screenshot URL is required'}), 400
            
        # Check if the URL ends with an image extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        is_valid_image_url = any(screenshot_url.lower().endswith(ext) for ext in valid_extensions)
        if not is_valid_image_url:
            return jsonify({'success': False, 'message': 'Screenshot URL must point to an image file (with .jpg, .png, .gif, or similar extension)'}), 400
            
        # Format screenshot URL as an array of objects for Airtable if it's a valid URL
        if is_valid_image_url:
            # Airtable requires this format: [{"url": "https://..."}]
            data['screenshot'] = [{"url": screenshot_url}]
            
        # Validate submitter is authorized (either submitting for self or as club leader/co-leader)
        is_authorized = False
        target_user_id = int(data['user_id'])

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
            
        # Look up club name from database
        from models import Club
        club = Club.query.filter_by(id=data['club_id']).first()
        if club:
            data['club_name'] = club.name
        else:
            data['club_name'] = "Unknown Club"

        # Log to Airtable
        airtable_result = airtable_service.log_pizza_grant(data)

        return jsonify({
            'success': True, 
            'message': 'Pizza grant submitted successfully! Your submission is pending review and updates will be sent to your email.',
            'submission_id': data['id'],
            'airtable_logged': airtable_result is not None
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error submitting pizza grant: {str(e)}'}), 500