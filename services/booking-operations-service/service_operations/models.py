"""
Service Operations module models
Contains the ServiceOperation model and related database definitions
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Date, Time, JSON, Numeric, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from models_base import Base
from common.enums import ServiceOperationStatus, OperationalAlert

# ============================================
# SERVICE OPERATIONS TABLE
# ============================================

class ServiceOperation(Base):
    """Service operations tracking and management"""
    __tablename__ = "service_operations"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core Relationships
    booking_line_id = Column(Integer, ForeignKey('booking_lines.id', ondelete='RESTRICT'), unique=True, nullable=False)
    booking_id = Column(Integer, ForeignKey('bookings.id', ondelete='RESTRICT'), nullable=False)
    order_id = Column(Integer, nullable=False)  # References orders.id

    # Operation Schedule
    operation_date = Column(Date, nullable=False, index=True)
    scheduled_start_time = Column(Time, nullable=True)
    scheduled_end_time = Column(Time, nullable=True)
    actual_start_datetime = Column(DateTime(timezone=True), nullable=True)
    actual_end_datetime = Column(DateTime(timezone=True), nullable=True)

    # Operation Status
    operation_status = Column(SQLEnum(ServiceOperationStatus), default=ServiceOperationStatus.PLANNED, index=True)

    # Service Information (denormalized for quick access)
    service_type = Column(String(50), nullable=False)  # tour/transfer/flight/hotel/activity
    service_name = Column(String(255), nullable=False)
    route_or_location = Column(String(255), nullable=True)

    # Passenger Management
    passengers_expected = Column(Integer, default=0)
    passengers_checked_in = Column(Integer, default=0)
    passengers_no_show = Column(Integer, default=0)
    passengers_cancelled = Column(Integer, default=0)
    check_in_details = Column(JSON, nullable=True)  # [{"passenger_id": 123, "checked_in_at": "2025-01-20 08:15:00", "checked_by": "guide"}]

    # Pick-up/Drop-off Management
    pickup_points = Column(JSON, nullable=True)  # [{"location": "Hotel Marriott", "scheduled_time": "08:00", "actual_time": "08:05", "passengers_count": 4, "notes": "Traffic delay"}]
    actual_pickup_location = Column(String(255), nullable=True)
    actual_dropoff_location = Column(String(255), nullable=True)

    # Operation Tracking
    route_tracking = Column(JSON, nullable=True)  # {"planned_route": ["Point A", "Point B", "Point C"], "actual_route": ["Point A", "Point B", "Point D"], "deviations": "Avoided Point C due to road closure"}
    timing_checkpoints = Column(JSON, nullable=True)  # [{"checkpoint": "Hotel pickup", "planned": "08:00", "actual": "08:05"}]

    # Incidents and Issues
    has_incidents = Column(Boolean, default=False)
    incidents = Column(JSON, nullable=True)  # [{"time": "2025-01-20 10:30:00", "type": "medical", "severity": "minor", "description": "Passenger felt dizzy", "action_taken": "Provided water and rest", "resolved": true, "reported_by": "lead_guide"}]

    # Service Quality
    service_quality = Column(String(20), nullable=True)  # excellent, good, fair, poor
    quality_issues = Column(JSON, nullable=True)  # ["late_start", "equipment_failure", "guide_issue"]
    guide_notes = Column(Text, nullable=True)
    coordinator_notes = Column(Text, nullable=True)

    # Weather and Conditions
    operating_conditions = Column(JSON, nullable=True)  # {"weather": "sunny", "temperature": "25C", "visibility": "good", "sea_conditions": "calm", "warnings": ["high_altitude"]}

    # Financial Reconciliation
    cash_collected = Column(Numeric(12, 2), default=0)
    tips_collected = Column(Numeric(12, 2), default=0)
    additional_sales = Column(Numeric(12, 2), default=0)  # Photos, souvenirs, etc
    financial_notes = Column(JSON, nullable=True)

    # Post-Operation
    requires_follow_up = Column(Boolean, default=False)
    follow_up_notes = Column(Text, nullable=True)
    passenger_feedback = Column(JSON, nullable=True)  # [{"passenger_id": 123, "rating": 5, "comment": "Excellent guide"}]

    # Manifest and Documents
    manifest_number = Column(String(50), nullable=True)
    manifest_url = Column(String(500), nullable=True)
    operation_documents = Column(JSON, nullable=True)  # ["manifest", "waiver_forms", "receipts"]

    # Communication Log
    communication_log = Column(JSON, nullable=True)  # [{"time": "2025-01-20 07:45:00", "type": "whatsapp", "from": "coordinator", "to": "guide", "message": "Confirmed 12 passengers for today"}]

    # Completion and Verification
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(Integer, nullable=True)  # References users.id
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(Integer, nullable=True)  # References users.id

    # Integration flags
    synced_to_accounting = Column(Boolean, default=False)
    feedback_requested = Column(Boolean, default=False)
    feedback_requested_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    service_operation_metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)  # ["vip_group", "special_event", "repeat_customers"]

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    booking_line = relationship("BookingLine", back_populates="service_operations")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_service_operation_date_status', 'operation_date', 'operation_status'),
        Index('idx_service_operation_type_date', 'service_type', 'operation_date'),
        Index('idx_service_operation_incidents', 'has_incidents'),
        Index('idx_service_operation_status_follow_up', 'operation_status', 'requires_follow_up'),
        Index('idx_service_operation_completed_verified', 'completed_at', 'is_verified'),
        Index('idx_service_operation_booking', 'booking_id'),
        Index('idx_service_operation_order', 'order_id'),
    )

    def __repr__(self):
        return f"<ServiceOperation(id={self.id}, booking_line_id={self.booking_line_id}, status='{self.operation_status}', date='{self.operation_date}')>"

    def is_in_progress(self):
        """Check if operation is currently in progress"""
        return self.operation_status == ServiceOperationStatus.IN_PROGRESS

    def is_completed(self):
        """Check if operation is completed"""
        return self.operation_status == ServiceOperationStatus.COMPLETED

    def has_quality_issues(self):
        """Check if operation has quality issues"""
        return bool(self.quality_issues and len(self.quality_issues) > 0)

    def calculate_attendance_rate(self):
        """Calculate passenger attendance rate"""
        if self.passengers_expected == 0:
            return 0
        return (self.passengers_checked_in / self.passengers_expected) * 100

    def get_total_financial_collection(self):
        """Get total financial collection"""
        return (self.cash_collected or 0) + (self.tips_collected or 0) + (self.additional_sales or 0)

    def add_incident(self, incident_type: str, severity: str, description: str, action_taken: str = None, reported_by: str = None):
        """Add an incident to the operation"""
        incident = {
            "time": datetime.utcnow().isoformat(),
            "type": incident_type,
            "severity": severity,
            "description": description,
            "action_taken": action_taken,
            "resolved": False,
            "reported_by": reported_by
        }

        if self.incidents is None:
            self.incidents = []

        self.incidents.append(incident)
        self.has_incidents = True

    def resolve_incident(self, incident_index: int, resolution_notes: str = None):
        """Mark an incident as resolved"""
        if self.incidents and 0 <= incident_index < len(self.incidents):
            self.incidents[incident_index]["resolved"] = True
            self.incidents[incident_index]["resolved_at"] = datetime.utcnow().isoformat()
            if resolution_notes:
                self.incidents[incident_index]["resolution_notes"] = resolution_notes

    def add_communication_log(self, comm_type: str, from_user: str, to_user: str, message: str):
        """Add communication log entry"""
        log_entry = {
            "time": datetime.utcnow().isoformat(),
            "type": comm_type,
            "from": from_user,
            "to": to_user,
            "message": message
        }

        if self.communication_log is None:
            self.communication_log = []

        self.communication_log.append(log_entry)

    def check_in_passenger(self, passenger_id: int, checked_by: str = None):
        """Check in a passenger"""
        check_in_entry = {
            "passenger_id": passenger_id,
            "checked_in_at": datetime.utcnow().isoformat(),
            "checked_by": checked_by or "system"
        }

        if self.check_in_details is None:
            self.check_in_details = []

        # Check if passenger is already checked in
        for entry in self.check_in_details:
            if entry.get("passenger_id") == passenger_id:
                return False  # Already checked in

        self.check_in_details.append(check_in_entry)
        self.passengers_checked_in += 1
        return True

    def add_passenger_feedback(self, passenger_id: int, rating: int, comment: str = None):
        """Add passenger feedback"""
        feedback_entry = {
            "passenger_id": passenger_id,
            "rating": rating,
            "comment": comment,
            "submitted_at": datetime.utcnow().isoformat()
        }

        if self.passenger_feedback is None:
            self.passenger_feedback = []

        self.passenger_feedback.append(feedback_entry)

    def calculate_average_rating(self):
        """Calculate average passenger rating"""
        if not self.passenger_feedback:
            return None

        ratings = [feedback.get("rating", 0) for feedback in self.passenger_feedback if feedback.get("rating")]
        if not ratings:
            return None

        return sum(ratings) / len(ratings)

    def get_unresolved_incidents(self):
        """Get list of unresolved incidents"""
        if not self.incidents:
            return []

        return [incident for incident in self.incidents if not incident.get("resolved", False)]

    def is_on_time(self):
        """Check if operation started on time"""
        if not self.scheduled_start_time or not self.actual_start_datetime:
            return None

        from datetime import datetime, time
        scheduled_datetime = datetime.combine(self.operation_date, self.scheduled_start_time)
        return self.actual_start_datetime <= scheduled_datetime

    def get_duration_minutes(self):
        """Get operation duration in minutes"""
        if not self.actual_start_datetime or not self.actual_end_datetime:
            return None

        duration = self.actual_end_datetime - self.actual_start_datetime
        return int(duration.total_seconds() / 60)
