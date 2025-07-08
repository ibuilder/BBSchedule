"""
Enterprise compliance and governance features for BBSchedule
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from functools import wraps
from flask import request, session, current_app
import csv
from io import StringIO

# Compliance logging
compliance_logger = logging.getLogger('compliance')

class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    SOX = "Sarbanes-Oxley Act"
    GDPR = "General Data Protection Regulation" 
    HIPAA = "Health Insurance Portability and Accountability Act"
    ISO27001 = "ISO 27001 Information Security"
    SOC2 = "SOC 2 Type II"
    NIST = "NIST Cybersecurity Framework"

@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_id: str
    timestamp: datetime
    user_id: str
    user_role: str
    action: str
    resource_type: str
    resource_id: str
    old_values: Dict
    new_values: Dict
    ip_address: str
    user_agent: str
    session_id: str
    risk_level: str
    compliance_tags: List[str]

class ComplianceAuditTrail:
    """Comprehensive audit trail for compliance"""
    
    def __init__(self):
        self.audit_events = []
        self.retention_days = {
            ComplianceFramework.SOX: 2555,  # 7 years
            ComplianceFramework.GDPR: 2190,  # 6 years  
            ComplianceFramework.SOC2: 2555,  # 7 years
            ComplianceFramework.ISO27001: 2190,  # 6 years
        }
    
    def log_event(self, action: str, resource_type: str, resource_id: str,
                  old_values: Dict = None, new_values: Dict = None,
                  risk_level: str = 'low', compliance_tags: List[str] = None):
        """Log compliance audit event"""
        
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.utcnow(),
            user_id=session.get('user_id', 'system'),
            user_role=session.get('user_role', 'unknown'),
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            old_values=old_values or {},
            new_values=new_values or {},
            ip_address=request.remote_addr if request else 'system',
            user_agent=request.user_agent.string if request else 'system',
            session_id=session.get('session_id', 'none'),
            risk_level=risk_level,
            compliance_tags=compliance_tags or []
        )
        
        self.audit_events.append(event)
        
        # Log to compliance logger
        compliance_logger.info(
            f"AUDIT: {event.action} on {event.resource_type}:{event.resource_id} "
            f"by {event.user_id} (risk: {event.risk_level})"
        )
        
        # Store in database for long-term retention
        self._store_audit_event(event)
    
    def _generate_event_id(self) -> str:
        """Generate unique audit event ID"""
        data = f"{datetime.utcnow().isoformat()}{os.urandom(16).hex()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _store_audit_event(self, event: AuditEvent):
        """Store audit event in database"""
        # This would integrate with your database
        # For now, we'll just ensure it's logged
        pass
    
    def get_audit_report(self, start_date: datetime, end_date: datetime,
                        user_id: str = None, risk_level: str = None) -> List[Dict]:
        """Generate audit report for compliance"""
        filtered_events = []
        
        for event in self.audit_events:
            if start_date <= event.timestamp <= end_date:
                if user_id and event.user_id != user_id:
                    continue
                if risk_level and event.risk_level != risk_level:
                    continue
                
                filtered_events.append(asdict(event))
        
        return filtered_events
    
    def export_audit_csv(self, events: List[Dict]) -> str:
        """Export audit events to CSV format"""
        output = StringIO()
        
        if events:
            fieldnames = events[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(events)
        
        return output.getvalue()

class DataGovernance:
    """Data governance and privacy controls"""
    
    def __init__(self):
        self.data_classifications = {
            'public': {'retention_days': 365, 'encryption': False},
            'internal': {'retention_days': 1095, 'encryption': True},
            'confidential': {'retention_days': 2555, 'encryption': True},
            'restricted': {'retention_days': 2555, 'encryption': True, 'access_control': True}
        }
        
        self.pii_fields = [
            'email', 'phone', 'address', 'ssn', 'tax_id',
            'first_name', 'last_name', 'birth_date'
        ]
    
    def classify_data(self, data_type: str, content: Dict) -> str:
        """Automatically classify data based on content"""
        # Check for PII
        if any(field in content for field in self.pii_fields):
            return 'confidential'
        
        # Check for financial data
        if any(field in content for field in ['budget', 'cost', 'revenue', 'salary']):
            return 'internal'
        
        # Default classification
        return 'internal'
    
    def apply_retention_policy(self, data_classification: str, created_date: datetime) -> bool:
        """Check if data should be retained based on policy"""
        if data_classification not in self.data_classifications:
            return True
        
        retention_days = self.data_classifications[data_classification]['retention_days']
        retention_cutoff = datetime.utcnow() - timedelta(days=retention_days)
        
        return created_date > retention_cutoff
    
    def anonymize_data(self, data: Dict, fields_to_anonymize: List[str]) -> Dict:
        """Anonymize sensitive data fields"""
        anonymized = data.copy()
        
        for field in fields_to_anonymize:
            if field in anonymized:
                if field in ['email']:
                    # Keep domain for analytics
                    email_parts = anonymized[field].split('@')
                    if len(email_parts) == 2:
                        anonymized[field] = f"***@{email_parts[1]}"
                elif field in ['phone']:
                    # Keep area code
                    phone = str(anonymized[field])
                    if len(phone) >= 10:
                        anonymized[field] = f"{phone[:3]}***{phone[-4:]}"
                else:
                    # Generic anonymization
                    anonymized[field] = "***ANONYMIZED***"
        
        return anonymized

class SOXCompliance:
    """Sarbanes-Oxley compliance controls"""
    
    def __init__(self, audit_trail: ComplianceAuditTrail):
        self.audit_trail = audit_trail
        
        # Critical financial processes that require SOX controls
        self.controlled_processes = [
            'budget_approval',
            'cost_allocation',
            'revenue_recognition',
            'financial_reporting',
            'project_closure'
        ]
    
    def require_segregation_of_duties(self, process: str):
        """Decorator to enforce segregation of duties"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user_id = session.get('user_id')
                user_role = session.get('user_role')
                
                # Check if user can perform this process
                if not self._check_authorization(user_id, user_role, process):
                    self.audit_trail.log_event(
                        action=f'sox_violation_attempted',
                        resource_type='process',
                        resource_id=process,
                        risk_level='high',
                        compliance_tags=['SOX', 'segregation_of_duties']
                    )
                    raise PermissionError("SOX: Segregation of duties violation")
                
                # Log the authorized action
                self.audit_trail.log_event(
                    action=f'sox_controlled_process',
                    resource_type='process',
                    resource_id=process,
                    risk_level='medium',
                    compliance_tags=['SOX', 'authorized_action']
                )
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def _check_authorization(self, user_id: str, user_role: str, process: str) -> bool:
        """Check if user is authorized for SOX-controlled process"""
        # Define role-based access for SOX processes
        sox_authorizations = {
            'budget_approval': ['cfo', 'finance_director'],
            'cost_allocation': ['project_manager', 'cost_controller'],
            'revenue_recognition': ['finance_director', 'controller'],
            'financial_reporting': ['cfo', 'controller'],
            'project_closure': ['project_manager', 'finance_director']
        }
        
        if process in sox_authorizations:
            return user_role in sox_authorizations[process]
        
        return True
    
    def generate_sox_report(self, period_start: datetime, period_end: datetime) -> Dict:
        """Generate SOX compliance report"""
        sox_events = []
        
        for event in self.audit_trail.audit_events:
            if (period_start <= event.timestamp <= period_end and
                'SOX' in event.compliance_tags):
                sox_events.append(event)
        
        # Analyze for compliance violations
        violations = [e for e in sox_events if 'violation' in e.action]
        
        return {
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'total_sox_events': len(sox_events),
            'violations': len(violations),
            'compliance_score': (1 - len(violations) / max(len(sox_events), 1)) * 100,
            'controlled_processes_accessed': len(set(e.resource_id for e in sox_events)),
            'recommendations': self._generate_sox_recommendations(sox_events)
        }
    
    def _generate_sox_recommendations(self, events: List[AuditEvent]) -> List[str]:
        """Generate SOX compliance recommendations"""
        recommendations = []
        
        # Check for unusual access patterns
        user_access = {}
        for event in events:
            if event.user_id not in user_access:
                user_access[event.user_id] = 0
            user_access[event.user_id] += 1
        
        # Users with excessive access
        avg_access = sum(user_access.values()) / len(user_access) if user_access else 0
        for user_id, count in user_access.items():
            if count > avg_access * 2:
                recommendations.append(f"Review access patterns for user {user_id}")
        
        return recommendations

class GDPRCompliance:
    """GDPR compliance controls"""
    
    def __init__(self, audit_trail: ComplianceAuditTrail):
        self.audit_trail = audit_trail
        self.consent_records = {}
        self.data_processing_purposes = [
            'project_management',
            'communication',
            'reporting',
            'analytics',
            'legal_compliance'
        ]
    
    def record_consent(self, user_id: str, purpose: str, consent_given: bool):
        """Record user consent for data processing"""
        consent_id = self._generate_consent_id()
        
        consent_record = {
            'consent_id': consent_id,
            'user_id': user_id,
            'purpose': purpose,
            'consent_given': consent_given,
            'timestamp': datetime.utcnow(),
            'ip_address': request.remote_addr if request else None,
            'user_agent': request.user_agent.string if request else None
        }
        
        self.consent_records[consent_id] = consent_record
        
        self.audit_trail.log_event(
            action='gdpr_consent_recorded',
            resource_type='consent',
            resource_id=consent_id,
            new_values=consent_record,
            compliance_tags=['GDPR', 'consent']
        )
    
    def _generate_consent_id(self) -> str:
        """Generate unique consent ID"""
        data = f"{datetime.utcnow().isoformat()}{os.urandom(8).hex()}"
        return hashlib.sha256(data.encode()).hexdigest()[:12]
    
    def process_data_subject_request(self, request_type: str, user_id: str) -> Dict:
        """Process GDPR data subject requests"""
        
        if request_type == 'access':
            return self._handle_data_access_request(user_id)
        elif request_type == 'portability':
            return self._handle_data_portability_request(user_id)
        elif request_type == 'erasure':
            return self._handle_right_to_be_forgotten(user_id)
        elif request_type == 'rectification':
            return self._handle_data_rectification_request(user_id)
        
        return {'success': False, 'error': 'Unknown request type'}
    
    def _handle_data_access_request(self, user_id: str) -> Dict:
        """Handle right of access request"""
        # Collect all user data from various sources
        user_data = {
            'personal_data': {},  # From user profile
            'project_data': {},   # From projects user is involved in
            'activity_logs': [],  # From audit trail
            'consent_records': []  # From consent management
        }
        
        # Find user's consent records
        user_consents = [
            record for record in self.consent_records.values()
            if record['user_id'] == user_id
        ]
        user_data['consent_records'] = user_consents
        
        self.audit_trail.log_event(
            action='gdpr_data_access_request',
            resource_type='user_data',
            resource_id=user_id,
            compliance_tags=['GDPR', 'data_access']
        )
        
        return {'success': True, 'data': user_data}
    
    def _handle_right_to_be_forgotten(self, user_id: str) -> Dict:
        """Handle right to erasure request"""
        # This is a complex process that requires:
        # 1. Checking legal basis for retention
        # 2. Anonymizing data where erasure isn't possible
        # 3. Notifying third parties
        
        self.audit_trail.log_event(
            action='gdpr_erasure_request',
            resource_type='user_data',
            resource_id=user_id,
            risk_level='high',
            compliance_tags=['GDPR', 'right_to_be_forgotten']
        )
        
        return {'success': True, 'message': 'Erasure request processed'}

class ComplianceReporting:
    """Generate compliance reports"""
    
    def __init__(self, audit_trail: ComplianceAuditTrail):
        self.audit_trail = audit_trail
    
    def generate_compliance_dashboard(self) -> Dict:
        """Generate compliance dashboard data"""
        now = datetime.utcnow()
        last_30_days = now - timedelta(days=30)
        
        recent_events = [
            e for e in self.audit_trail.audit_events
            if e.timestamp >= last_30_days
        ]
        
        # Compliance metrics
        high_risk_events = [e for e in recent_events if e.risk_level == 'high']
        sox_events = [e for e in recent_events if 'SOX' in e.compliance_tags]
        gdpr_events = [e for e in recent_events if 'GDPR' in e.compliance_tags]
        
        return {
            'total_events': len(recent_events),
            'high_risk_events': len(high_risk_events),
            'sox_events': len(sox_events),
            'gdpr_events': len(gdpr_events),
            'compliance_score': self._calculate_compliance_score(recent_events),
            'top_risks': self._identify_top_risks(recent_events),
            'recommendations': self._generate_compliance_recommendations(recent_events)
        }
    
    def _calculate_compliance_score(self, events: List[AuditEvent]) -> float:
        """Calculate overall compliance score"""
        if not events:
            return 100.0
        
        risk_weights = {'low': 1, 'medium': 3, 'high': 10}
        total_risk = sum(risk_weights.get(e.risk_level, 1) for e in events)
        max_possible_risk = len(events) * risk_weights['high']
        
        # Inverse score (lower risk = higher score)
        score = (1 - total_risk / max_possible_risk) * 100
        return max(0, score)
    
    def _identify_top_risks(self, events: List[AuditEvent]) -> List[Dict]:
        """Identify top compliance risks"""
        risk_patterns = {}
        
        for event in events:
            if event.risk_level in ['medium', 'high']:
                pattern = f"{event.action}_{event.resource_type}"
                if pattern not in risk_patterns:
                    risk_patterns[pattern] = {'count': 0, 'risk_level': event.risk_level}
                risk_patterns[pattern]['count'] += 1
        
        # Sort by risk level and frequency
        sorted_risks = sorted(
            risk_patterns.items(),
            key=lambda x: (x[1]['risk_level'] == 'high', x[1]['count']),
            reverse=True
        )
        
        return [
            {'pattern': pattern, 'count': data['count'], 'risk_level': data['risk_level']}
            for pattern, data in sorted_risks[:5]
        ]
    
    def _generate_compliance_recommendations(self, events: List[AuditEvent]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        # Check for common issues
        high_risk_count = len([e for e in events if e.risk_level == 'high'])
        if high_risk_count > 5:
            recommendations.append("Review and strengthen access controls")
        
        failed_logins = len([e for e in events if 'failed_login' in e.action])
        if failed_logins > 10:
            recommendations.append("Implement stronger password policies")
        
        return recommendations

# Global compliance components
audit_trail = ComplianceAuditTrail()
data_governance = DataGovernance()
sox_compliance = SOXCompliance(audit_trail)
gdpr_compliance = GDPRCompliance(audit_trail)
compliance_reporting = ComplianceReporting(audit_trail)

def init_enterprise_compliance(app):
    """Initialize enterprise compliance features"""
    
    # Add audit logging to Flask app
    @app.before_request
    def log_request_start():
        if request.endpoint and not request.endpoint.startswith('static'):
            audit_trail.log_event(
                action='request_started',
                resource_type='endpoint',
                resource_id=request.endpoint,
                new_values={
                    'method': request.method,
                    'path': request.path,
                    'args': dict(request.args)
                },
                compliance_tags=['access_control']
            )
    
    compliance_logger.info("Enterprise compliance features initialized")
    
    return {
        'audit_trail': audit_trail,
        'data_governance': data_governance,
        'sox_compliance': sox_compliance,
        'gdpr_compliance': gdpr_compliance,
        'compliance_reporting': compliance_reporting
    }