from datetime import datetime

from sqlalchemy import Enum
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="student")
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    matric_number = db.Column(db.String(50), nullable=True, unique=True, index=True)
    level = db.Column(db.Integer, nullable=True)
    officer_scope = db.Column(Enum("department", "bursary", "general", name="officer_scope_enum", native_enum=False), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    department = db.relationship("Department", back_populates="users")
    created_requests = db.relationship("Request", foreign_keys="Request.created_by", back_populates="creator")
    assigned_requests = db.relationship("Request", foreign_keys="Request.assigned_to", back_populates="assignee")
    assets = db.relationship("Asset", back_populates="assigned_user")
    reveal_logs = db.relationship("IdentityRevealLog", back_populates="admin")

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute")

    @password.setter
    def password(self, value):
        self.password_hash = generate_password_hash(value)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_public_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "department_id": self.department_id,
            "matric_number": self.matric_number,
            "level": self.level,
            "officer_scope": self.officer_scope,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
