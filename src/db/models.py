from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from .database import db


class Blacklist(db.Model):
    """
    Blacklist model representing an email in the global blacklist.
    """
    __tablename__ = "blacklists"

    id = Column(String, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    app_uuid = Column(String, nullable=False, index=True)
    blocked_reason = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=False)  # IPv6 can be up to 45 chars
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Blacklist {self.email}>"

