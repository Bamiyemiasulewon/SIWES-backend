from datetime import datetime

from app.extensions import db


class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    serial_number = db.Column(db.String(120), nullable=False, unique=True)
    status = db.Column(db.String(50), nullable=False, default="active")
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    assigned_user = db.relationship("User", back_populates="assets")
    department = db.relationship("Department", back_populates="assets")
    tickets = db.relationship("Ticket", back_populates="asset")
