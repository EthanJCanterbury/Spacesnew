import os
import logging
import subprocess
import signal
import atexit
import json
from datetime import datetime, timedelta
from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import app, db
from models import User, Site, UserActivity, Club, ClubMembership, ClubPost, ClubChatChannel, ClubChatMessage, ClubResource, ClubAssignment, ClubPostLike, ClubFeaturedProject

# Configure logging - reduced verbosity
logging.basicConfig(
    level=logging.WARNING,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create console handler with a higher log level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
console_handler.setFormatter(formatter)

# Add the handlers to the logger
app.logger.addHandler(console_handler)
app.logger.setLevel(logging.WARNING)

# Global variable to store the Hackatime service process
hackatime_process = None

def initialize_database():
    """Initialize the database and create all tables."""
    try:
        app.logger.info("Initializing database...")
        with app.app_context():
            db.create_all()
        app.logger.info("Database initialized successfully.")
        return True
    except Exception as e:
        app.logger.warning(f"Database initialization error: {e}")
        return False

def start_hackatime_service():
    """Start the Hackatime service as a subprocess."""
    global hackatime_process
    try:
        app.logger.info("Starting Hackatime service...")
        hackatime_process = subprocess.Popen(
            ['python', 'hackatime_service.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        app.logger.info(f"Hackatime service started with PID {hackatime_process.pid}")
    except Exception as e:
        app.logger.error(f"Error starting Hackatime service: {str(e)}")

def stop_hackatime_service():
    """Stop the Hackatime service when the main app exits."""
    global hackatime_process
    if hackatime_process and hackatime_process.poll() is None:
        app.logger.info(f"Stopping Hackatime service (PID {hackatime_process.pid})...")
        try:
            hackatime_process.send_signal(signal.SIGTERM)
            hackatime_process.wait(timeout=5)
            app.logger.info("Hackatime service stopped gracefully")
        except subprocess.TimeoutExpired:
            app.logger.warning("Timeout waiting for service to stop, forcing termination")
            hackatime_process.kill()
        except Exception as e:
            app.logger.error(f"Error stopping service: {str(e)}")
            hackatime_process.kill()

@app.route('/support')
def support():
    return render_template('support.html')

# Club Dashboard Routes
@app.route('/club-dashboard')
@app.route('/club-dashboard/<int:club_id>')
@login_required
def club_dashboard(club_id=None):
    """Club dashboard for club leaders to manage their clubs."""
    # If no club ID is provided, try to find user's club
    if club_id is None:
        # Check if user is a club leader
        club = Club.query.filter_by(leader_id=current_user.id).first()
        
        # If not a leader, check if they belong to any clubs
        if not club:
            club_memberships = ClubMembership.query.filter_by(user_id=current_user.id).all()
            
            if not club_memberships:
                # User doesn't have any club associations
                return render_template('club_dashboard.html', club=None)
                
            if len(club_memberships) == 1:
                # If user is a member of only one club, show that club
                club = club_memberships[0].club
                club_id = club.id
            else:
                # If user belongs to multiple clubs, show club selection interface
                return render_template('club_dashboard.html', 
                                      club=None, 
                                      memberships=club_memberships)
    else:
        # Club ID was provided, show that specific club
        club = Club.query.get_or_404(club_id)
        
        # Verify user is a member or leader of this club
        if club.leader_id != current_user.id:
            membership = ClubMembership.query.filter_by(
                user_id=current_user.id,
                club_id=club_id
            ).first()
            
            if not membership:
                flash('You are not a member of this club.', 'error')
                return redirect(url_for('welcome'))
    
    # Get all memberships for the club
    memberships = []
    if club:
        memberships = ClubMembership.query.filter_by(club_id=club.id).all()
        
        # Get the default chat channel
        default_channel = ClubChatChannel.query.filter_by(
            club_id=club.id,
            name='general'
        ).first()
        
        # If no general channel exists, create it
        if not default_channel:
            default_channel = ClubChatChannel(
                club_id=club.id,
                name='general',
                description='General discussions',
                created_by=club.leader_id
            )
            db.session.add(default_channel)
            db.session.commit()
    
    # Check if user is a leader or co-leader
    is_leader = (club and club.leader_id == current_user.id)
    is_co_leader = False
    
    if club and not is_leader:
        membership = ClubMembership.query.filter_by(
            user_id=current_user.id,
            club_id=club.id,
            role='co-leader'
        ).first()
        
        is_co_leader = (membership is not None)
    
    return render_template('club_dashboard.html',
                           club=club,
                           memberships=memberships,
                           is_leader=is_leader,
                           is_co_leader=is_co_leader)

# Club API routes
@app.route('/api/clubs', methods=['POST'])
@login_required
def create_club():
    """Create a new club with the current user as leader."""
    try:
        data = request.get_json()

        if not data.get('name'):
            return jsonify({'error': 'Club name is required'}), 400

        if Club.query.filter_by(leader_id=current_user.id).first():
            return jsonify({'error': 'You already have a club'}), 400

        club = Club(name=data.get('name'),
                    description=data.get('description', ''),
                    location=data.get('location', ''),
                    leader_id=current_user.id)

        club.generate_join_code()
        db.session.add(club)
        db.session.commit()  # Commit to ensure the club has an ID

        membership = ClubMembership(user_id=current_user.id,
                                    club_id=club.id,
                                    role='co-leader')
        db.session.add(membership)
        
        # Create default channels for the club
        default_channels = [
            {'name': 'general', 'description': 'General discussion channel'},
            {'name': 'announcements', 'description': 'Important club announcements'},
            {'name': 'help', 'description': 'Ask for help with your projects'}
        ]
        
        for channel_data in default_channels:
            channel = ClubChatChannel(
                club_id=club.id,
                name=channel_data['name'],
                description=channel_data['description'],
                created_by=current_user.id
            )
            db.session.add(channel)
        
        db.session.commit()
        
        # Add welcome messages to the channels
        channels = ClubChatChannel.query.filter_by(club_id=club.id).all()
        for channel in channels:
            welcome_message = ClubChatMessage(
                channel_id=channel.id,
                user_id=current_user.id,
                content=f"Welcome to #{channel.name}! This channel was created automatically when the club was formed."
            )
            db.session.add(welcome_message)
        
        db.session.commit()

        activity = UserActivity(
            activity_type="club_creation",
            message=f'Club "{club.name}" created by {{username}}',
            username=current_user.username,
            user_id=current_user.id)
        db.session.add(activity)
        db.session.commit()

        return jsonify({'message': 'Club created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error creating club: {str(e)}')
        return jsonify({'error': 'Failed to create club'}), 500

@app.route('/api/clubs/join-code/generate', methods=['POST'])
@login_required
def generate_join_code():
    """Generate a new join code for the current user's club."""
    # Get the club based on request data
    data = request.get_json()
    club_id = data.get('club_id')
    
    if club_id:
        club = Club.query.get_or_404(club_id)
        # Verify user is club leader
        if club.leader_id != current_user.id:
            return jsonify({'error': 'Only club leaders can generate join codes'}), 403
    else:
        # Get the user's club (if they're a leader)
        club = Club.query.filter_by(leader_id=current_user.id).first()
        if not club:
            return jsonify({'error': 'You do not have a club'}), 404

    try:
        # Generate a new join code
        club.generate_join_code()
        db.session.commit()

        return jsonify({
            'message': 'Join code generated successfully',
            'join_code': club.join_code
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error generating join code: {str(e)}')
        return jsonify({'error': 'Failed to generate join code'}), 500

@app.route('/api/clubs/join', methods=['POST'])
@login_required
def join_club():
    """Join a club using a join code."""
    try:
        data = request.get_json()
        join_code = data.get('join_code')

        if not join_code:
            return jsonify({'error': 'Join code is required'}), 400

        club = Club.query.filter_by(join_code=join_code).first()

        if not club:
            return jsonify({'error': 'Invalid join code'}), 404

        existing_membership = ClubMembership.query.filter_by(
            user_id=current_user.id, club_id=club.id).first()

        if existing_membership:
            return jsonify({'error': 'You are already a member of this club'}), 400

        membership = ClubMembership(user_id=current_user.id,
                                    club_id=club.id,
                                    role='member')
        db.session.add(membership)

        activity = UserActivity(
            activity_type="club_join",
            message=f'{{username}} joined club "{club.name}"',
            username=current_user.username,
            user_id=current_user.id)
        db.session.add(activity)
        db.session.commit()

        return jsonify({'message': f'Successfully joined {club.name}'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error joining club: {str(e)}')
        return jsonify({'error': 'Failed to join club'}), 500

@app.route('/api/clubs/current', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_current_club():
    """Get, update, or delete the current user's club."""
    club = Club.query.filter_by(leader_id=current_user.id).first()

    if not club:
        return jsonify({'error': 'You do not have a club'}), 404

    if request.method == 'GET':
        return jsonify({
            'id': club.id,
            'name': club.name,
            'description': club.description,
            'location': club.location,
            'join_code': club.join_code,
            'created_at': club.created_at.isoformat(),
            'members_count': ClubMembership.query.filter_by(club_id=club.id).count()
        })

    elif request.method == 'PUT':
        try:
            data = request.get_json()

            if data.get('name'):
                club.name = data.get('name')
            if 'description' in data:
                club.description = data.get('description')
            if 'location' in data:
                club.location = data.get('location')

            db.session.commit()

            return jsonify({'message': 'Club updated successfully'})
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error updating club: {str(e)}')
            return jsonify({'error': 'Failed to update club'}), 500

    elif request.method == 'DELETE':
        try:
            # First delete all related ClubAssignment records
            ClubAssignment.query.filter_by(club_id=club.id).delete()
            
            # Delete all club memberships
            ClubMembership.query.filter_by(club_id=club.id).delete()
            
            # Delete club chat channels and messages
            channels = ClubChatChannel.query.filter_by(club_id=club.id).all()
            for channel in channels:
                # Delete messages in each channel
                ClubChatMessage.query.filter_by(channel_id=channel.id).delete()
            
            # Delete all channels
            ClubChatChannel.query.filter_by(club_id=club.id).delete()
            
            # Delete club resources
            ClubResource.query.filter_by(club_id=club.id).delete()
            
            # Delete club posts and likes
            posts = ClubPost.query.filter_by(club_id=club.id).all()
            for post in posts:
                ClubPostLike.query.filter_by(post_id=post.id).delete()
            ClubPost.query.filter_by(club_id=club.id).delete()

            # Finally delete the club itself
            db.session.delete(club)
            db.session.commit()

            activity = UserActivity(
                activity_type="club_deletion",
                message=f'Club "{club.name}" deleted by {{username}}',
                username=current_user.username,
                user_id=current_user.id)
            db.session.add(activity)
            db.session.commit()

            return jsonify({'message': 'Club deleted successfully'})
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error deleting club: {str(e)}')
            return jsonify({'error': f'Failed to delete club: {str(e)}'}), 500

@app.route('/api/clubs/memberships/<int:membership_id>/leave', methods=['POST'])
@login_required
def leave_club(membership_id):
    """Leave a club."""
    try:
        # Find the membership
        membership = ClubMembership.query.get_or_404(membership_id)

        # Verify it belongs to the current user
        if membership.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        # Prevent club leaders from leaving their own club
        if membership.club.leader_id == current_user.id:
            return jsonify({
                'error': 'Club leaders cannot leave. Delete the club instead.'
            }), 400

        club_name = membership.club.name

        # Delete the membership
        db.session.delete(membership)

        # Record activity
        activity = UserActivity(
            activity_type="club_leave",
            message=f'{{username}} left club "{club_name}"',
            username=current_user.username,
            user_id=current_user.id)
        db.session.add(activity)
        db.session.commit()

        return jsonify({'message': f'Successfully left {club_name}'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error leaving club: {str(e)}')
        return jsonify({'error': 'Failed to leave club'}), 500

@app.route('/api/clubs/members/<int:membership_id>/role', methods=['PUT'])
@login_required
def change_member_role(membership_id):
    """Change a member's role in a club."""
    try:
        membership = ClubMembership.query.get_or_404(membership_id)

        # Check if the current user is the club leader
        club = membership.club
        if club.leader_id != current_user.id:
            return jsonify({'error': 'Only club leaders can change member roles'}), 403

        # Prevent changing own role
        if membership.user_id == current_user.id:
            return jsonify({'error': 'You cannot change your own role'}), 400

        data = request.get_json()
        new_role = data.get('role')

        if new_role not in ['member', 'co-leader']:
            return jsonify({'error': 'Invalid role'}), 400

        membership.role = new_role
        db.session.commit()

        return jsonify({'message': f'Role updated to {new_role}'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error changing member role: {str(e)}')
        return jsonify({'error': 'Failed to change member role'}), 500

@app.route('/api/clubs/members/<int:membership_id>', methods=['DELETE'])
@login_required
def remove_member(membership_id):
    """Remove a member from a club."""
    try:
        membership = ClubMembership.query.get_or_404(membership_id)

        # Check if the current user is the club leader
        club = membership.club
        if club.leader_id != current_user.id:
            return jsonify({'error': 'Only club leaders can remove members'}), 403

        # Prevent removing self
        if membership.user_id == current_user.id:
            return jsonify({'error': 'You cannot remove yourself from the club'}), 400

        member_name = membership.user.username

        # Delete the membership
        db.session.delete(membership)

        # Record activity
        activity = UserActivity(
            activity_type="club_member_removal",
            message=f'{{username}} removed {member_name} from club "{club.name}"',
            username=current_user.username,
            user_id=current_user.id)
        db.session.add(activity)
        db.session.commit()

        return jsonify({'message': f'Successfully removed {member_name} from the club'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error removing member: {str(e)}')
        return jsonify({'error': 'Failed to remove member'}), 500

@app.route('/api/clubs/<int:club_id>/posts', methods=['GET', 'POST'])
@login_required
def club_posts(club_id):
    """Get all posts for a club or create a new post."""
    # Verify user is a member of the club
    club = Club.query.get_or_404(club_id)
    membership = ClubMembership.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    if not membership and club.leader_id != current_user.id:
        return jsonify({'error': 'You are not a member of this club'}), 403
        
    if request.method == 'GET':
        posts = db.session.query(ClubPost, User).join(User, ClubPost.user_id == User.id) \
                .filter(ClubPost.club_id == club_id) \
                .order_by(ClubPost.created_at.desc()).all()
                
        result = []
        for post, user in posts:
            # Get likes information
            post_likes = ClubPostLike.query.filter_by(post_id=post.id).all()
            liked_by = [like.user_id for like in post_likes]
            
            # Check if current user liked this post
            user_liked = current_user.id in liked_by
            
            result.append({
                'id': post.id,
                'content': post.content,
                'created_at': post.created_at.isoformat(),
                'updated_at': post.updated_at.isoformat(),
                'likes': post.likes or len(post_likes),  # Use stored count or calculate
                'liked_by': liked_by,
                'user_liked': user_liked,
                'user': {
                    'id': user.id,
                    'username': user.username
                }
            })
            
        return jsonify({'posts': result})
        
    elif request.method == 'POST':
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({'error': 'Post content cannot be empty'}), 400
            
        post = ClubPost(
            club_id=club_id,
            user_id=current_user.id,
            content=content
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'message': 'Post created successfully',
            'post': {
                'id': post.id,
                'content': post.content,
                'created_at': post.created_at.isoformat(),
                'user': {
                    'id': current_user.id,
                    'username': current_user.username
                }
            }
        })

@app.route('/api/clubs/<int:club_id>/posts/<int:post_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_club_post(club_id, post_id):
    """Update or delete a club post."""
    post = ClubPost.query.get_or_404(post_id)
    
    # Check if post belongs to the correct club
    if post.club_id != club_id:
        return jsonify({'error': 'Post not found in this club'}), 404
        
    # Check if user is authorized (post creator or club leader)
    if post.user_id != current_user.id and post.club.leader_id != current_user.id:
        membership = ClubMembership.query.filter_by(
            user_id=current_user.id, 
            club_id=club_id, 
            role='co-leader'
        ).first()
        
        if not membership:
            return jsonify({'error': 'You are not authorized to manage this post'}), 403
    
    if request.method == 'PUT':
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({'error': 'Post content cannot be empty'}), 400
            
        post.content = content
        post.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Post updated successfully',
            'post': {
                'id': post.id,
                'content': post.content,
                'updated_at': post.updated_at.isoformat()
            }
        })
        
    elif request.method == 'DELETE':
        try:
            # First delete all likes associated with this post
            ClubPostLike.query.filter_by(post_id=post_id).delete()
            
            # Then delete the post itself
            db.session.delete(post)
            db.session.commit()
            
            return jsonify({'message': 'Post deleted successfully'})
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error deleting post: {str(e)}')
            return jsonify({'error': f'Failed to delete post: {str(e)}'}), 500

@app.route('/api/clubs/<int:club_id>/posts/<int:post_id>/like', methods=['POST'])
@login_required
def toggle_post_like(club_id, post_id):
    """Toggle like on a club post."""
    post = ClubPost.query.get_or_404(post_id)
    
    # Check if post belongs to the correct club
    if post.club_id != club_id:
        return jsonify({'error': 'Post not found in this club'}), 404
        
    # Check if user is a club member
    membership = ClubMembership.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    if not membership and post.club.leader_id != current_user.id:
        return jsonify({'error': 'You are not a member of this club'}), 403
    
    # Check if user already liked this post
    existing_like = ClubPostLike.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        liked = False
    else:
        # Like
        new_like = ClubPostLike(post_id=post_id, user_id=current_user.id)
        db.session.add(new_like)
        liked = True
    
    # Update likes count
    like_count = ClubPostLike.query.filter_by(post_id=post_id).count()
    post.likes = like_count
    
    db.session.commit()
    
    return jsonify({
        'message': 'Like toggled successfully',
        'liked': liked,
        'likes': like_count
    })

@app.route('/api/clubs/<int:club_id>/assignments', methods=['GET', 'POST'])
@login_required
def club_assignments(club_id):
    """Get all assignments for a club or create a new assignment."""
    # Verify user is a member of the club
    club = Club.query.get_or_404(club_id)
    membership = ClubMembership.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    if not membership and club.leader_id != current_user.id:
        return jsonify({'error': 'You are not a member of this club'}), 403
        
    if request.method == 'GET':
        assignments = db.session.query(ClubAssignment, User) \
            .join(User, ClubAssignment.created_by == User.id) \
            .filter(ClubAssignment.club_id == club_id) \
            .order_by(ClubAssignment.created_at.desc()).all()
                
        result = []
        for assignment, user in assignments:
            result.append({
                'id': assignment.id,
                'title': assignment.title,
                'description': assignment.description,
                'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                'created_at': assignment.created_at.isoformat(),
                'is_active': assignment.is_active,
                'creator': {
                    'id': user.id,
                    'username': user.username
                }
            })
            
        return jsonify({'assignments': result})
        
    elif request.method == 'POST':
        # Only leaders and co-leaders can create assignments
        if club.leader_id != current_user.id:
            membership = ClubMembership.query.filter_by(
                user_id=current_user.id, 
                club_id=club_id, 
                role='co-leader'
            ).first()
            
            if not membership:
                return jsonify({'error': 'Only club leaders can create assignments'}), 403
                
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        due_date_str = data.get('due_date')
        
        if not title or not description:
            return jsonify({'error': 'Title and description are required'}), 400
            
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid due date format'}), 400
                
        assignment = ClubAssignment(
            club_id=club_id,
            title=title,
            description=description,
            due_date=due_date,
            created_by=current_user.id
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        return jsonify({
            'message': 'Assignment created successfully',
            'assignment': {
                'id': assignment.id,
                'title': assignment.title,
                'description': assignment.description,
                'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                'created_at': assignment.created_at.isoformat(),
                'is_active': assignment.is_active
            }
        })

@app.route('/api/clubs/<int:club_id>/assignments/<int:assignment_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_club_assignment(club_id, assignment_id):
    """Get, update, or delete a club assignment."""
    assignment = ClubAssignment.query.get_or_404(assignment_id)
    
    # Check if assignment belongs to the correct club
    if assignment.club_id != club_id:
        return jsonify({'error': 'Assignment not found in this club'}), 404
        
    # Check if user is a member of the club
    membership = ClubMembership.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    if not membership and assignment.club.leader_id != current_user.id:
        return jsonify({'error': 'You are not a member of this club'}), 403
    
    if request.method == 'GET':
        # Get user info for creator
        creator = User.query.get(assignment.created_by)
        
        return jsonify({
            'assignment': {
                'id': assignment.id,
                'title': assignment.title,
                'description': assignment.description,
                'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                'created_at': assignment.created_at.isoformat(),
                'updated_at': assignment.updated_at.isoformat(),
                'is_active': assignment.is_active,
                'creator': {
                    'id': creator.id,
                    'username': creator.username
                }
            }
        })
    
    # For PUT and DELETE methods, check for additional authorization
    is_authorized = False
    if assignment.created_by == current_user.id or assignment.club.leader_id == current_user.id:
        is_authorized = True
    else:
        co_leader_membership = ClubMembership.query.filter_by(
            user_id=current_user.id, 
            club_id=club_id, 
            role='co-leader'
        ).first()
        
        if co_leader_membership:
            is_authorized = True
    
    if not is_authorized:
        return jsonify({'error': 'You are not authorized to manage this assignment'}), 403
    
    if request.method == 'PUT':
        data = request.get_json()
        
        if 'title' in data:
            assignment.title = data['title']
        if 'description' in data:
            assignment.description = data['description']
        if 'due_date' in data and data['due_date']:
            try:
                assignment.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid due date format'}), 400
        if 'is_active' in data:
            assignment.is_active = data['is_active']
            
        assignment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Assignment updated successfully',
            'assignment': {
                'id': assignment.id,
                'title': assignment.title,
                'description': assignment.description,
                'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                'updated_at': assignment.updated_at.isoformat(),
                'is_active': assignment.is_active
            }
        })
        
    elif request.method == 'DELETE':
        db.session.delete(assignment)
        db.session.commit()
        
        return jsonify({'message': 'Assignment deleted successfully'})

@app.route('/api/clubs/<int:club_id>/resources', methods=['GET', 'POST'])
@login_required
def club_resources(club_id):
    """Get all resources for a club or create a new resource."""
    # Verify user is a member of the club
    club = Club.query.get_or_404(club_id)
    membership = ClubMembership.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    if not membership and club.leader_id != current_user.id:
        return jsonify({'error': 'You are not a member of this club'}), 403
        
    if request.method == 'GET':
        resources = db.session.query(ClubResource, User) \
            .join(User, ClubResource.created_by == User.id) \
            .filter(ClubResource.club_id == club_id) \
            .order_by(ClubResource.created_at.desc()).all()
                
        result = []
        for resource, user in resources:
            result.append({
                'id': resource.id,
                'title': resource.title,
                'url': resource.url,
                'description': resource.description,
                'icon': resource.icon,
                'created_at': resource.created_at.isoformat(),
                'creator': {
                    'id': user.id,
                    'username': user.username
                }
            })
            
        return jsonify({'resources': result})
        
    elif request.method == 'POST':
        data = request.get_json()
        title = data.get('title')
        url = data.get('url')
        description = data.get('description', '')
        icon = data.get('icon', 'link')
        
        if not title or not url:
            return jsonify({'error': 'Title and URL are required'}), 400
            
        resource = ClubResource(
            club_id=club_id,
            title=title,
            url=url,
            description=description,
            icon=icon,
            created_by=current_user.id
        )
        
        db.session.add(resource)
        db.session.commit()
        
        return jsonify({
            'message': 'Resource added successfully',
            'resource': {
                'id': resource.id,
                'title': resource.title,
                'url': resource.url,
                'description': resource.description,
                'icon': resource.icon,
                'created_at': resource.created_at.isoformat()
            }
        })

@app.route('/api/clubs/<int:club_id>/resources/<int:resource_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_club_resource(club_id, resource_id):
    """Get, update, or delete a club resource."""
    resource = ClubResource.query.get_or_404(resource_id)
    
    # Check if resource belongs to the correct club
    if resource.club_id != club_id:
        return jsonify({'error': 'Resource not found in this club'}), 404
        
    # Check if user is a member of the club
    membership = ClubMembership.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    if not membership and resource.club.leader_id != current_user.id:
        return jsonify({'error': 'You are not a member of this club'}), 403
    
    if request.method == 'GET':
        # Get user info for creator
        creator = User.query.get(resource.created_by)
        
        return jsonify({
            'resource': {
                'id': resource.id,
                'title': resource.title,
                'url': resource.url,
                'description': resource.description,
                'icon': resource.icon,
                'created_at': resource.created_at.isoformat(),
                'creator': {
                    'id': creator.id,
                    'username': creator.username
                }
            }
        })
    
    # For PUT and DELETE methods, check for additional authorization
    is_authorized = False
    if resource.created_by == current_user.id or resource.club.leader_id == current_user.id:
        is_authorized = True
    else:
        co_leader_membership = ClubMembership.query.filter_by(
            user_id=current_user.id, 
            club_id=club_id, 
            role='co-leader'
        ).first()
        
        if co_leader_membership:
            is_authorized = True
    
    if not is_authorized:
        return jsonify({'error': 'You are not authorized to manage this resource'}), 403
    
    if request.method == 'PUT':
        data = request.get_json()
        
        if 'title' in data:
            resource.title = data['title']
        if 'url' in data:
            resource.url = data['url']
        if 'description' in data:
            resource.description = data['description']
        if 'icon' in data:
            resource.icon = data['icon']
            
        db.session.commit()
        
        return jsonify({
            'message': 'Resource updated successfully',
            'resource': {
                'id': resource.id,
                'title': resource.title,
                'url': resource.url,
                'description': resource.description,
                'icon': resource.icon
            }
        })
        
    elif request.method == 'DELETE':
        db.session.delete(resource)
        db.session.commit()
        
        return jsonify({'message': 'Resource deleted successfully'})

@app.route('/api/clubs/<int:club_id>/channels', methods=['GET', 'POST'])
@login_required
def club_chat_channels(club_id):
    """Get all chat channels for a club or create a new channel."""
    # Verify user is a member of the club
    club = Club.query.get_or_404(club_id)
    membership = ClubMembership.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    if not membership and club.leader_id != current_user.id:
        return jsonify({'error': 'You are not a member of this club'}), 403
        
    if request.method == 'GET':
        channels = ClubChatChannel.query.filter_by(club_id=club_id).all()
                
        result = []
        for channel in channels:
            result.append({
                'id': channel.id,
                'name': channel.name,
                'description': channel.description,
                'created_at': channel.created_at.isoformat()
            })
            
        return jsonify({'channels': result})
        
    elif request.method == 'POST':
        # Only leaders and co-leaders can create channels
        if club.leader_id != current_user.id:
            membership = ClubMembership.query.filter_by(
                user_id=current_user.id, 
                club_id=club_id, 
                role='co-leader'
            ).first()
            
            if not membership:
                return jsonify({'error': 'Only club leaders can create channels'}), 403
                
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        
        if not name:
            return jsonify({'error': 'Channel name is required'}), 400
            
        # Check if channel with this name already exists
        existing = ClubChatChannel.query.filter_by(club_id=club_id, name=name).first()
        if existing:
            return jsonify({'error': f'Channel "{name}" already exists'}), 400
            
        channel = ClubChatChannel(
            club_id=club_id,
            name=name,
            description=description,
            created_by=current_user.id
        )
        
        db.session.add(channel)
        db.session.commit()
        
        # Add a welcome message
        welcome_message = ClubChatMessage(
            channel_id=channel.id,
            user_id=current_user.id,
            content=f"Welcome to #{name}! This channel was created by {current_user.username}."
        )
        db.session.add(welcome_message)
        db.session.commit()
        
        return jsonify({
            'message': 'Channel created successfully',
            'channel': {
                'id': channel.id,
                'name': channel.name,
                'description': channel.description,
                'created_at': channel.created_at.isoformat()
            }
        })

@app.route('/api/clubs/<int:club_id>/channels/<int:channel_id>/messages', methods=['GET', 'POST'])
@login_required
def club_chat_messages(club_id, channel_id):
    """Get all messages for a channel or send a new message."""
    # Verify channel belongs to the requested club
    channel = ClubChatChannel.query.get_or_404(channel_id)
    if channel.club_id != club_id:
        return jsonify({'error': 'Channel not found in this club'}), 404
    
    # Verify user is a member of the club
    club = Club.query.get_or_404(club_id)
    membership = ClubMembership.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    if not membership and club.leader_id != current_user.id:
        return jsonify({'error': 'You are not a member of this club'}), 403
        
    if request.method == 'GET':
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Query messages with user data
        messages = db.session.query(ClubChatMessage, User) \
            .join(User, ClubChatMessage.user_id == User.id) \
            .filter(ClubChatMessage.channel_id == channel_id) \
            .order_by(ClubChatMessage.sent_at.desc()) \
            .paginate(page=page, per_page=per_page)
                
        result = []
        for message, user in messages.items:
            result.append({
                'id': message.id,
                'content': message.content,
                'sent_at': message.sent_at.isoformat(),
                'sender': {
                    'id': user.id,
                    'username': user.username,
                    'avatar': user.avatar
                }
            })
            
        return jsonify({
            'messages': result,
            'total': messages.total,
            'pages': messages.pages,
            'current_page': messages.page
        })
        
    elif request.method == 'POST':
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({'error': 'Message content cannot be empty'}), 400
            
        message = ClubChatMessage(
            channel_id=channel_id,
            user_id=current_user.id,
            content=content
        )
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'message': 'Message sent successfully',
            'chat_message': {
                'id': message.id,
                'content': message.content,
                'sent_at': message.sent_at.isoformat(),
                'sender': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'avatar': current_user.avatar if hasattr(current_user, 'avatar') else None
                }
            }
        })

@app.route('/api/clubs/<int:club_id>/channels/<int:channel_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_chat_channel(club_id, channel_id):
    """Update or delete a chat channel."""
    # Verify channel belongs to the requested club
    channel = ClubChatChannel.query.get_or_404(channel_id)
    if channel.club_id != club_id:
        return jsonify({'error': 'Channel not found in this club'}), 404
    
    # Check if user is authorized (club leader or co-leader)
    club = Club.query.get_or_404(club_id)
    is_authorized = False
    
    if club.leader_id == current_user.id:
        is_authorized = True
    else:
        membership = ClubMembership.query.filter_by(
            user_id=current_user.id, 
            club_id=club_id, 
            role='co-leader'
        ).first()
        
        if membership:
            is_authorized = True
    
    if not is_authorized:
        return jsonify({'error': 'You are not authorized to manage this channel'}), 403
    
    # Don't allow modifying or deleting the general channel
    if channel.name == 'general':
        return jsonify({'error': 'The general channel cannot be modified or deleted'}), 400
    
    if request.method == 'PUT':
        data = request.get_json()
        
        if 'name' in data:
            # Check if new name already exists
            existing = ClubChatChannel.query.filter(
                ClubChatChannel.club_id == club_id,
                ClubChatChannel.name == data['name'],
                ClubChatChannel.id != channel_id
            ).first()
            
            if existing:
                return jsonify({'error': f'Channel "{data["name"]}" already exists'}), 400
                
            channel.name = data['name']
            
        if 'description' in data:
            channel.description = data['description']
            
        db.session.commit()
        
        return jsonify({
            'message': 'Channel updated successfully',
            'channel': {
                'id': channel.id,
                'name': channel.name,
                'description': channel.description
            }
        })
        
    elif request.method == 'DELETE':
        try:
            # Delete all messages in the channel
            ClubChatMessage.query.filter_by(channel_id=channel_id).delete()
            
            # Delete the channel
            db.session.delete(channel)
            db.session.commit()
            
            return jsonify({'message': 'Channel deleted successfully'})
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error deleting channel: {str(e)}')
            return jsonify({'error': f'Failed to delete channel: {str(e)}'}), 500

@app.route('/api/clubs/<int:club_id>/projects', methods=['GET', 'POST'])
@login_required
def club_projects(club_id):
    """Get or add featured projects for a club."""
    # Verify user is a member of the club
    club = Club.query.get_or_404(club_id)
    membership = ClubMembership.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    if not membership and club.leader_id != current_user.id:
        return jsonify({'error': 'You are not a member of this club'}), 403
        
    if request.method == 'GET':
        projects = db.session.query(ClubFeaturedProject, Site, User) \
            .join(Site, ClubFeaturedProject.site_id == Site.id) \
            .join(User, Site.user_id == User.id) \
            .filter(ClubFeaturedProject.club_id == club_id) \
            .order_by(ClubFeaturedProject.featured_at.desc()).all()
                
        result = []
        for project, site, user in projects:
            result.append({
                'id': project.id,
                'site': {
                    'id': site.id,
                    'name': site.name,
                    'slug': site.slug,
                    'site_type': site.site_type
                },
                'user': {
                    'id': user.id,
                    'username': user.username
                },
                'featured_at': project.featured_at.isoformat(),
                'notes': project.notes
            })
            
        return jsonify({'projects': result})
        
    elif request.method == 'POST':
        # Only leaders and co-leaders can feature projects
        if club.leader_id != current_user.id:
            membership = ClubMembership.query.filter_by(
                user_id=current_user.id, 
                club_id=club_id, 
                role='co-leader'
            ).first()
            
            if not membership:
                return jsonify({'error': 'Only club leaders can feature projects'}), 403
                
        data = request.get_json()
        site_id = data.get('site_id')
        notes = data.get('notes', '')
        
        if not site_id:
            return jsonify({'error': 'Site ID is required'}), 400
            
        # Verify site exists
        site = Site.query.get(site_id)
        if not site:
            return jsonify({'error': 'Site not found'}), 404
            
        # Check if project is already featured
        existing = ClubFeaturedProject.query.filter_by(club_id=club_id, site_id=site_id).first()
        if existing:
            return jsonify({'error': 'This project is already featured'}), 400
            
        project = ClubFeaturedProject(
            club_id=club_id,
            site_id=site_id,
            notes=notes,
            featured_by=current_user.id
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'message': 'Project featured successfully',
            'project': {
                'id': project.id,
                'site_id': site_id,
                'featured_at': project.featured_at.isoformat(),
                'notes': notes
            }
        })

@app.route('/api/clubs/<int:club_id>/projects/<int:project_id>', methods=['DELETE'])
@login_required
def remove_featured_project(club_id, project_id):
    """Remove a featured project."""
    # Verify project belongs to the club
    project = ClubFeaturedProject.query.get_or_404(project_id)
    if project.club_id != club_id:
        return jsonify({'error': 'Project not found in this club'}), 404
    
    # Check if user is authorized
    club = Club.query.get_or_404(club_id)
    is_authorized = False
    
    if club.leader_id == current_user.id:
        is_authorized = True
    else:
        membership = ClubMembership.query.filter_by(
            user_id=current_user.id, 
            club_id=club_id, 
            role='co-leader'
        ).first()
        
        if membership:
            is_authorized = True
    
    if not is_authorized:
        return jsonify({'error': 'You are not authorized to manage featured projects'}), 403
    
    try:
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({'message': 'Project removed from featured successfully'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error removing featured project: {str(e)}')
        return jsonify({'error': f'Failed to remove project: {str(e)}'}), 500

@app.route('/api/clubs/<int:club_id>/members', methods=['GET'])
@login_required
def get_club_members(club_id):
    """Get all members of a club."""
    # Verify user is a member of the club
    club = Club.query.get_or_404(club_id)
    membership = ClubMembership.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    if not membership and club.leader_id != current_user.id:
        return jsonify({'error': 'You are not a member of this club'}), 403
    
    # Get all memberships with user data
    memberships = db.session.query(ClubMembership, User) \
        .join(User, ClubMembership.user_id == User.id) \
        .filter(ClubMembership.club_id == club_id) \
        .all()
    
    members = []
    for membership, user in memberships:
        members.append({
            'membership_id': membership.id,
            'user': {
                'id': user.id,
                'username': user.username,
                'avatar': user.avatar if hasattr(user, 'avatar') else None
            },
            'role': membership.role,
            'joined_at': membership.joined_at.isoformat()
        })
    
    # Add club leader
    leader = User.query.get(club.leader_id)
    if leader:
        # Check if leader is already in the list
        if not any(m['user']['id'] == leader.id for m in members):
            members.append({
                'membership_id': None,
                'user': {
                    'id': leader.id,
                    'username': leader.username,
                    'avatar': leader.avatar if hasattr(leader, 'avatar') else None
                },
                'role': 'leader',
                'joined_at': club.created_at.isoformat()
            })
    
    return jsonify({'members': members})

if __name__ == '__main__':
    app.logger.info("Starting Hack Club Spaces application")

    # Initialize database
    try:
        initialize_database()
    except Exception as e:
        app.logger.warning(f"Database initialization error: {e}")

    # Start Hackatime service
    start_hackatime_service()

    # Register the cleanup function to stop Hackatime service on exit
    atexit.register(stop_hackatime_service)

    # Start the main Flask application
    port = int(os.environ.get('PORT', 3000))
    app.logger.info(f"Server running on http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)