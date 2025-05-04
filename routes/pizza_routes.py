from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import requests
from models import db, User, Club, ClubMembership

pizza_bp = Blueprint('pizza', __name__, url_prefix='/api/clubs')

@pizza_bp.route('/<int:club_id>/pizza-grant', methods=['POST'])
@login_required
def submit_pizza_grant(club_id):
    """Submit a pizza grant request to Airtable."""
    try:
        club = Club.query.get_or_404(club_id)

        # Check if user is authorized (club leader or co-leader)
        if club.leader_id != current_user.id:
            is_coleader = ClubMembership.query.filter_by(
                club_id=club_id, 
                user_id=current_user.id,
                role='co-leader'
            ).first()

            if not is_coleader:
                return jsonify({'error': 'Not authorized to submit pizza grants for this club'}), 403

        # Get request data
        data = request.json

        # Validate required fields
        required_fields = ['member_id', 'member_name', 'project_name', 'coding_hours', 'project_description']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # TODO: Actually submit to Airtable
        # For now, just return success
        return jsonify({'success': True, 'message': 'Pizza grant submitted successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pizza_bp.route('/<int:club_id>/pizza-grants', methods=['GET'])
@login_required
def get_pizza_grants(club_id):
    """Get pizza grant submissions for a club."""
    try:
        club = Club.query.get_or_404(club_id)

        # Check if user is authorized (club leader or co-leader)
        if club.leader_id != current_user.id:
            is_coleader = ClubMembership.query.filter_by(
                club_id=club_id, 
                user_id=current_user.id,
                role='co-leader'
            ).first()

            if not is_coleader:
                return jsonify({'error': 'Not authorized to view pizza grants for this club'}), 403

        # TODO: Fetch submissions from a database or Airtable
        # For now, return mock data
        submissions = [
            {
                'id': 1,
                'project_name': 'Personal Portfolio',
                'member_name': 'Alice Smith',
                'coding_hours': '2.5',
                'submitted_at': '2025-04-10T14:30:00Z',
                'status': 'approved'
            },
            {
                'id': 2,
                'project_name': 'Weather App',
                'member_name': 'Bob Johnson',
                'coding_hours': '1.8',
                'submitted_at': '2025-04-09T11:15:00Z',
                'status': 'pending'
            }
        ]

        return jsonify({'submissions': submissions})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pizza_bp.route('/<int:club_id>/hackatime-members', methods=['GET'])
@login_required
def get_hackatime_members(club_id):
    """Get members with Hackatime API keys for the pizza grants page."""
    try:
        club = Club.query.get_or_404(club_id)

        # Check if user is authorized (club leader or co-leader)
        if club.leader_id != current_user.id:
            is_coleader = ClubMembership.query.filter_by(
                club_id=club_id, 
                user_id=current_user.id,
                role='co-leader'
            ).first()

            if not is_coleader:
                return jsonify({'error': 'Not authorized to view this club\'s data'}), 403

        # Get all users in the club with Hackatime API keys
        members = []

        # Track processed user IDs to avoid duplicates
        processed_user_ids = set()

        # Get leader
        leader = User.query.get(club.leader_id)
        if leader and leader.wakatime_api_key:
            members.append({
                'id': leader.id,
                'username': leader.username,
                'role': 'Club Leader',
                'has_hackatime': True
            })
            processed_user_ids.add(leader.id)

        # Get members
        memberships = ClubMembership.query.filter_by(club_id=club_id).all()
        for membership in memberships:
            # Skip if we already processed this user
            if membership.user_id in processed_user_ids:
                continue

            member = User.query.get(membership.user_id)
            if member and member.wakatime_api_key:
                members.append({
                    'id': member.id,
                    'username': member.username,
                    'role': membership.role.capitalize(),
                    'has_hackatime': True
                })
                processed_user_ids.add(member.id)

        return jsonify({'members': members})
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in get_hackatime_members: {str(e)}\n{error_details}")
        return jsonify({
            'error': f'Failed to get members: {str(e)}',
            'members': [],
            'debug_info': f"Club ID: {club_id}, User ID: {current_user.id}"
        }), 500