"""
Enhanced Collaboration Service
Real-time multi-user editing, communication, and document management
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from models import Project, Activity, User
from extensions import db
from logger import log_activity, log_error

class CollaborationService:
    """Enhanced collaboration service for team management"""
    
    def __init__(self):
        self.active_sessions = {}
        self.communication_channels = {}
        self.document_versions = {}
        
    def start_collaborative_session(self, project_id: int, user_id: str) -> Dict[str, Any]:
        """Start a collaborative editing session"""
        
        session_id = f"session_{project_id}_{int(datetime.now().timestamp())}"
        
        session_data = {
            'session_id': session_id,
            'project_id': project_id,
            'user_id': user_id,
            'started_at': datetime.now().isoformat(),
            'active_users': [user_id],
            'locked_activities': [],
            'recent_changes': [],
            'status': 'active'
        }
        
        self.active_sessions[session_id] = session_data
        
        log_activity(user_id, f"Started collaborative session for project {project_id}", {
            'session_id': session_id,
            'project_id': project_id
        })
        
        return session_data
    
    def join_collaborative_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Join an existing collaborative session"""
        
        if session_id not in self.active_sessions:
            raise ValueError("Session not found")
        
        session = self.active_sessions[session_id]
        
        if user_id not in session['active_users']:
            session['active_users'].append(user_id)
        
        session['recent_changes'].append({
            'type': 'user_joined',
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        })
        
        return session
    
    def lock_activity_for_editing(self, session_id: str, activity_id: int, user_id: str) -> Dict[str, Any]:
        """Lock an activity for exclusive editing"""
        
        if session_id not in self.active_sessions:
            raise ValueError("Session not found")
        
        session = self.active_sessions[session_id]
        
        # Check if already locked
        existing_lock = next((lock for lock in session['locked_activities'] if lock['activity_id'] == activity_id), None)
        
        if existing_lock and existing_lock['user_id'] != user_id:
            return {
                'success': False,
                'message': f"Activity is currently being edited by user {existing_lock['user_id']}",
                'locked_by': existing_lock['user_id'],
                'locked_at': existing_lock['locked_at']
            }
        
        lock_data = {
            'activity_id': activity_id,
            'user_id': user_id,
            'locked_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(minutes=30)).isoformat()
        }
        
        # Remove any existing lock for this activity
        session['locked_activities'] = [lock for lock in session['locked_activities'] if lock['activity_id'] != activity_id]
        session['locked_activities'].append(lock_data)
        
        session['recent_changes'].append({
            'type': 'activity_locked',
            'activity_id': activity_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'success': True,
            'message': 'Activity locked for editing',
            'lock_data': lock_data
        }
    
    def release_activity_lock(self, session_id: str, activity_id: int, user_id: str) -> Dict[str, Any]:
        """Release an activity lock"""
        
        if session_id not in self.active_sessions:
            raise ValueError("Session not found")
        
        session = self.active_sessions[session_id]
        
        # Remove the lock
        session['locked_activities'] = [lock for lock in session['locked_activities'] 
                                      if not (lock['activity_id'] == activity_id and lock['user_id'] == user_id)]
        
        session['recent_changes'].append({
            'type': 'activity_unlocked',
            'activity_id': activity_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        })
        
        return {'success': True, 'message': 'Activity lock released'}
    
    def sync_activity_changes(self, session_id: str, activity_id: int, changes: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Sync real-time activity changes"""
        
        if session_id not in self.active_sessions:
            raise ValueError("Session not found")
        
        session = self.active_sessions[session_id]
        
        # Verify user has lock on this activity
        has_lock = any(lock['activity_id'] == activity_id and lock['user_id'] == user_id 
                      for lock in session['locked_activities'])
        
        if not has_lock:
            return {
                'success': False,
                'message': 'You must lock the activity before making changes'
            }
        
        # Apply changes to database
        activity = Activity.query.get(activity_id)
        if not activity:
            return {'success': False, 'message': 'Activity not found'}
        
        change_log = []
        
        for field, new_value in changes.items():
            if hasattr(activity, field):
                old_value = getattr(activity, field)
                if old_value != new_value:
                    setattr(activity, field, new_value)
                    change_log.append({
                        'field': field,
                        'old_value': str(old_value),
                        'new_value': str(new_value)
                    })
        
        if change_log:
            db.session.commit()
            
            session['recent_changes'].append({
                'type': 'activity_updated',
                'activity_id': activity_id,
                'user_id': user_id,
                'changes': change_log,
                'timestamp': datetime.now().isoformat()
            })
        
        return {
            'success': True,
            'message': 'Changes synced successfully',
            'changes_applied': len(change_log)
        }
    
    def create_communication_channel(self, project_id: int, channel_name: str, created_by: str) -> Dict[str, Any]:
        """Create a communication channel for project team"""
        
        channel_id = f"channel_{project_id}_{channel_name}_{int(datetime.now().timestamp())}"
        
        channel_data = {
            'channel_id': channel_id,
            'project_id': project_id,
            'name': channel_name,
            'created_by': created_by,
            'created_at': datetime.now().isoformat(),
            'members': [created_by],
            'messages': [],
            'type': 'project_discussion',
            'status': 'active'
        }
        
        self.communication_channels[channel_id] = channel_data
        
        return channel_data
    
    def send_message(self, channel_id: str, user_id: str, message: str, message_type: str = 'text') -> Dict[str, Any]:
        """Send a message to a communication channel"""
        
        if channel_id not in self.communication_channels:
            raise ValueError("Channel not found")
        
        channel = self.communication_channels[channel_id]
        
        message_data = {
            'message_id': f"msg_{int(datetime.now().timestamp())}_{user_id}",
            'user_id': user_id,
            'message': message,
            'type': message_type,
            'timestamp': datetime.now().isoformat(),
            'reactions': [],
            'thread_replies': []
        }
        
        channel['messages'].append(message_data)
        
        # Notify other channel members
        notification_data = {
            'type': 'new_message',
            'channel_id': channel_id,
            'channel_name': channel['name'],
            'sender': user_id,
            'message_preview': message[:50] + '...' if len(message) > 50 else message,
            'timestamp': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'message_id': message_data['message_id'],
            'notification': notification_data
        }
    
    def create_document_version(self, project_id: int, document_name: str, content: str, created_by: str) -> Dict[str, Any]:
        """Create a new version of a project document"""
        
        document_key = f"doc_{project_id}_{document_name}"
        
        if document_key not in self.document_versions:
            self.document_versions[document_key] = {
                'document_name': document_name,
                'project_id': project_id,
                'versions': []
            }
        
        document = self.document_versions[document_key]
        version_number = len(document['versions']) + 1
        
        version_data = {
            'version': version_number,
            'content': content,
            'created_by': created_by,
            'created_at': datetime.now().isoformat(),
            'size_bytes': len(content.encode('utf-8')),
            'checksum': hash(content),
            'changes_summary': self._generate_changes_summary(document['versions'], content) if document['versions'] else "Initial version"
        }
        
        document['versions'].append(version_data)
        
        log_activity(created_by, f"Created document version {version_number}", {
            'document': document_name,
            'project_id': project_id,
            'version': version_number
        })
        
        return version_data
    
    def get_document_history(self, project_id: int, document_name: str) -> Dict[str, Any]:
        """Get version history for a document"""
        
        document_key = f"doc_{project_id}_{document_name}"
        
        if document_key not in self.document_versions:
            return {
                'document_name': document_name,
                'project_id': project_id,
                'versions': [],
                'total_versions': 0
            }
        
        document = self.document_versions[document_key]
        
        return {
            'document_name': document['document_name'],
            'project_id': document['project_id'],
            'versions': document['versions'],
            'total_versions': len(document['versions']),
            'latest_version': document['versions'][-1] if document['versions'] else None,
            'created_at': document['versions'][0]['created_at'] if document['versions'] else None,
            'last_modified': document['versions'][-1]['created_at'] if document['versions'] else None
        }
    
    def setup_video_conference(self, project_id: int, meeting_title: str, organizer: str, participants: List[str]) -> Dict[str, Any]:
        """Setup video conference for project team"""
        
        meeting_id = f"meeting_{project_id}_{int(datetime.now().timestamp())}"
        
        # Simulate video conferencing integration (Zoom, Teams, etc.)
        meeting_data = {
            'meeting_id': meeting_id,
            'project_id': project_id,
            'title': meeting_title,
            'organizer': organizer,
            'participants': participants,
            'scheduled_at': datetime.now().isoformat(),
            'meeting_url': f"https://bbschedule-meeting.com/join/{meeting_id}",
            'meeting_password': f"PROJ{project_id}",
            'status': 'scheduled',
            'duration_minutes': 60,
            'agenda': [
                "Project status review",
                "Schedule updates discussion", 
                "Risk assessment",
                "Next steps planning"
            ],
            'recording_enabled': True,
            'screen_sharing_enabled': True
        }
        
        # Send meeting invites
        for participant in participants:
            log_activity(participant, f"Invited to video conference: {meeting_title}", {
                'meeting_id': meeting_id,
                'project_id': project_id,
                'organizer': organizer
            })
        
        return meeting_data
    
    def get_team_communication_analytics(self, project_id: int) -> Dict[str, Any]:
        """Get communication analytics for project team"""
        
        # Filter channels and sessions for this project
        project_channels = [ch for ch in self.communication_channels.values() if ch['project_id'] == project_id]
        project_sessions = [s for s in self.active_sessions.values() if s['project_id'] == project_id]
        
        total_messages = sum(len(ch['messages']) for ch in project_channels)
        active_users = set()
        
        for channel in project_channels:
            active_users.update(msg['user_id'] for msg in channel['messages'])
        
        for session in project_sessions:
            active_users.update(session['active_users'])
        
        recent_activity = []
        
        # Collect recent collaboration activity
        for session in project_sessions:
            for change in session['recent_changes'][-5:]:  # Last 5 changes
                recent_activity.append({
                    'type': 'collaboration',
                    'action': change['type'],
                    'user_id': change.get('user_id'),
                    'timestamp': change['timestamp'],
                    'details': change
                })
        
        for channel in project_channels:
            for message in channel['messages'][-5:]:  # Last 5 messages
                recent_activity.append({
                    'type': 'communication',
                    'action': 'message_sent',
                    'user_id': message['user_id'],
                    'timestamp': message['timestamp'],
                    'details': {
                        'channel': channel['name'],
                        'message_preview': message['message'][:100]
                    }
                })
        
        # Sort by timestamp
        recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'project_id': project_id,
            'analytics_generated': datetime.now().isoformat(),
            'summary': {
                'active_communication_channels': len(project_channels),
                'total_messages': total_messages,
                'active_users': len(active_users),
                'collaborative_sessions': len(project_sessions),
                'document_versions': len([doc for doc in self.document_versions.values() if doc['project_id'] == project_id])
            },
            'recent_activity': recent_activity[:20],  # Top 20 recent activities
            'collaboration_health': {
                'score': min(100, (total_messages + len(active_users) * 10 + len(project_sessions) * 5)),
                'status': 'excellent' if total_messages > 20 else 'good' if total_messages > 5 else 'needs_improvement'
            }
        }
    
    def _generate_changes_summary(self, existing_versions: List[Dict[str, Any]], new_content: str) -> str:
        """Generate a summary of changes between document versions"""
        
        if not existing_versions:
            return "Initial version"
        
        latest_version = existing_versions[-1]
        old_content = latest_version['content']
        
        # Simple change detection (in a real implementation, use proper diff algorithms)
        old_lines = old_content.split('\n')
        new_lines = new_content.split('\n')
        
        added_lines = len(new_lines) - len(old_lines)
        
        if added_lines > 0:
            return f"Added {added_lines} lines"
        elif added_lines < 0:
            return f"Removed {abs(added_lines)} lines"
        else:
            return "Content modified"

# Global service instance
collaboration_service = CollaborationService()