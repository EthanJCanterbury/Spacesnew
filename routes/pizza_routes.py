
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import requests
import os
import json
from datetime import datetime
from models import db, User, Club, ClubMembership

pizza_bp = Blueprint('pizza', __name__, url_prefix='/api/clubs')

@pizza_bp.route('/<int:club_id>/pizza-grant', methods=['POST'])
@login_required
def submit_pizza_grant(club_id):
    """Submit a pizza grant to Airtable"""
    try:
        # Verify user is a club leader or co-leader
        club = Club.query.get_or_404(club_id)
        if club.leader_id != current_user.id:
            membership = ClubMembership.query.filter_by(
                club_id=club_id, 
                user_id=current_user.id,
                role='co-leader'
            ).first()
            if not membership:
                return jsonify({'success': False, 'message': 'Permission denied'}), 403
        
        # Get request data
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        # Validate required fields
        required_fields = ['member_name', 'project_name', 'coding_hours', 'project_description', 'club_name', 'leader_email']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        # Convert hours to float
        try:
            hours = float(data['coding_hours'])
            if hours < 1:
                return jsonify({'success': False, 'message': 'Project must have at least 1 hour of coding time'}), 400
                
            # Determine grant amount
            grant_amount = 10 if hours >= 2 else 5
            
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid coding hours'}), 400
        
        # Get Airtable API key from environment
        airtable_api_key = os.environ.get('AIRTABLE_API_KEY')
        if not airtable_api_key:
            return jsonify({'success': False, 'message': 'Airtable API key not configured'}), 500
            
        # Get Airtable base ID and table name
        airtable_base_id = os.environ.get('AIRTABLE_PIZZA_BASE_ID')
        airtable_table_name = os.environ.get('AIRTABLE_PIZZA_TABLE_NAME', 'Pizza Grants')
        
        if not airtable_base_id:
            return jsonify({'success': False, 'message': 'Airtable base ID not configured'}), 500
        
        # Prepare Airtable record
        airtable_record = {
            "fields": {
                "Member Name": data['member_name'],
                "Project Name": data['project_name'],
                "Coding Hours": hours,
                "Project Description": data['project_description'],
                "Project URL": data.get('project_url', ''),
                "Club Name": data['club_name'],
                "Leader Email": data['leader_email'],
                "Grant Amount": grant_amount,
                "Submission Date": datetime.now().isoformat(),
                "Status": "Pending"
            }
        }
        
        # Send to Airtable
        airtable_url = f"https://api.airtable.com/v0/{airtable_base_id}/{airtable_table_name}"
        headers = {
            "Authorization": f"Bearer {airtable_api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            airtable_url,
            headers=headers,
            json=airtable_record
        )
        
        if response.status_code != 200:
            return jsonify({
                'success': False, 
                'message': f'Failed to submit to Airtable: {response.text}'
            }), 500
            
        # Get the record ID from Airtable response
        airtable_response = response.json()
        record_id = airtable_response.get('id')
        
        # Return success
        return jsonify({
            'success': True, 
            'message': 'Pizza grant submitted successfully',
            'record_id': record_id,
            'grant_amount': grant_amount
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error submitting pizza grant: {str(e)}'}), 500


@pizza_bp.route('/<int:club_id>/pizza-grants', methods=['GET'])
@login_required
def get_pizza_grants(club_id):
    """Get pizza grant submissions for a club"""
    try:
        # Verify user is a club leader or co-leader
        club = Club.query.get_or_404(club_id)
        if club.leader_id != current_user.id:
            membership = ClubMembership.query.filter_by(
                club_id=club_id, 
                user_id=current_user.id,
                role='co-leader'
            ).first()
            if not membership:
                return jsonify({'error': 'Permission denied'}), 403
        
        # Get Airtable API key from environment
        airtable_api_key = os.environ.get('AIRTABLE_API_KEY')
        if not airtable_api_key:
            return jsonify({'error': 'Airtable API key not configured'}), 500
            
        # Get Airtable base ID and table name
        airtable_base_id = os.environ.get('AIRTABLE_PIZZA_BASE_ID')
        airtable_table_name = os.environ.get('AIRTABLE_PIZZA_TABLE_NAME', 'Pizza Grants')
        
        if not airtable_base_id:
            return jsonify({'error': 'Airtable base ID not configured'}), 500
        
        # Query Airtable for submissions from this club
        airtable_url = f"https://api.airtable.com/v0/{airtable_base_id}/{airtable_table_name}"
        headers = {
            "Authorization": f"Bearer {airtable_api_key}"
        }
        
        # Filter by club name - adjust if you have a better club identifier in Airtable
        params = {
            "filterByFormula": f"{{Club Name}}='{club.name}'"
        }
        
        response = requests.get(
            airtable_url,
            headers=headers,
            params=params
        )
        
        if response.status_code != 200:
            return jsonify({
                'error': f'Failed to fetch from Airtable: {response.text}'
            }), 500
            
        # Parse the response
        airtable_data = response.json()
        records = airtable_data.get('records', [])
        
        # Format the submissions
        submissions = []
        for record in records:
            fields = record.get('fields', {})
            submission = {
                'id': record.get('id'),
                'project_name': fields.get('Project Name', 'Unknown Project'),
                'member_name': fields.get('Member Name', 'Unknown Member'),
                'coding_hours': fields.get('Coding Hours', 0),
                'project_description': fields.get('Project Description', ''),
                'project_url': fields.get('Project URL', ''),
                'grant_amount': fields.get('Grant Amount', 0),
                'submitted_at': fields.get('Submission Date', ''),
                'status': fields.get('Status', 'pending').lower()
            }
            submissions.append(submission)
        
        # Sort by submission date (newest first)
        submissions.sort(key=lambda x: x['submitted_at'], reverse=True)
        
        return jsonify({'submissions': submissions})
        
    except Exception as e:
        return jsonify({'error': f'Error getting pizza grants: {str(e)}'}), 500
