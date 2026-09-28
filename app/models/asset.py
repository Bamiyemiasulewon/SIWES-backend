from datetime import datetime

from sqlalchemy import Enum

from app.extensions import db


class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(Enum("projector", "lab_equipment", "hvac", "generator", "furniture", "other", name="asset_type_enum", native_enum=False), nullable=False)
    serial_number = db.Column(db.String(120), nullable=False, unique=True)
    status = db.Column(db.String(50), nullable=False, default="active")
    building = db.Column(db.String(120), nullable=True)
    room = db.Column(db.String(60), nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    assigned_user = db.relationship("User", back_populates="assets")
    department = db.relationship("Department", back_populates="assets")
    requests = db.relationship("Request", back_populates="asset")
