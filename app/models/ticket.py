from datetime import datetime

from sqlalchemy import Enum

from app.extensions import db


class Request(db.Model):
    __tablename__ = "requests"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(Enum("maintenance", "complaint", name="request_type_enum", native_enum=False), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(Enum("low", "medium", "high", "critical", name="request_priority_enum", native_enum=False), nullable=False, default="medium")
    status = db.Column(db.String(50), nullable=False, default="submitted")
    is_anonymous = db.Column(db.Boolean, nullable=False, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    building = db.Column(db.String(120), nullable=True)
    room = db.Column(db.String(60), nullable=True)
    course_code = db.Column(db.String(50), nullable=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"), nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    reopen_count = db.Column(db.Integer, nullable=False, default=0)
    is_flagged = db.Column(db.Boolean, nullable=False, default=False)
    flag_type = db.Column(Enum("abuse", "threat", "false_report", name="flag_type_enum", native_enum=False), nullable=True)
    flag_reason = db.Column(db.Text, nullable=True)
    flagged_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    flagged_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    identity_revealed = db.Column(db.Boolean, nullable=False, default=False)

    creator = db.relationship("User", foreign_keys=[created_by], back_populates="created_requests")
    assignee = db.relationship("User", foreign_keys=[assigned_to], back_populates="assigned_requests")
    asset = db.relationship("Asset", back_populates="requests")
    department = db.relationship("Department", back_populates="requests")
    history = db.relationship("RequestHistory", back_populates="request", cascade="all, delete-orphan")


Ticket = Request

