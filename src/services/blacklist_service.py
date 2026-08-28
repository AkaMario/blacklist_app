import uuid
from typing import Dict, Any
from ..repositories.blacklist_repository import BlacklistRepository
from ..models.errors import NotFoundError


class BlacklistService:
    """
    Service for managing blacklist operations.
    """

    def __init__(self):
        self.repository = BlacklistRepository()

    def add_to_blacklist(self, email: str, app_uuid: str, blocked_reason: str, ip_address: str) -> Dict[str, Any]:
        """
        Add an email to the blacklist.
        
        Args:
            email: Email address to blacklist
            app_uuid: Application UUID
            blocked_reason: Reason for blocking (optional)
            ip_address: IP address of the requester
            
        Returns:
            Dict: Confirmation message with blacklist details
        """
        # Generate a unique ID for the blacklist entry
        blacklist_id = str(uuid.uuid4())
        
        # Create blacklist entry
        blacklist_data = {
            "id": blacklist_id,
            "email": email,
            "app_uuid": app_uuid,
            "blocked_reason": blocked_reason,
            "ip_address": ip_address
        }
        
        blacklist = self.repository.create(blacklist_data)
        
        return {
            "message": f"Email {email} added to blacklist successfully",
            "id": blacklist.id,
            "email": blacklist.email,
            "created_at": blacklist.created_at.isoformat()
        }

    def check_blacklist(self, email: str) -> Dict[str, Any]:
        """
        Check if an email is in the blacklist.
        
        Args:
            email: Email address to check
            
        Returns:
            Dict: Information about whether the email is blacklisted
        """
        blacklist = self.repository.get_by_email(email)
        
        if blacklist:
            return {
                "is_blacklisted": True,
                "email": email,
                "blocked_reason": blacklist.blocked_reason
            }
        else:
            return {
                "is_blacklisted": False,
                "email": email,
                "blocked_reason": None
            }

