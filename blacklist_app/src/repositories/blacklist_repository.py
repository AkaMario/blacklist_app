from typing import Optional
from sqlalchemy.exc import IntegrityError
from ..db.database import db
from ..db.models import Blacklist
from ..models.errors import ConflictError


class BlacklistRepository:
    """
    Repository for managing blacklist entries in the database.
    """

    def create(self, blacklist_data: dict) -> Blacklist:
        """
        Create a new blacklist entry.
        
        Args:
            blacklist_data: Dictionary containing blacklist information
            
        Returns:
            Blacklist: The created blacklist entry
            
        Raises:
            ConflictError: If email already exists in blacklist
        """
        try:
            blacklist = Blacklist(**blacklist_data)
            db.session.add(blacklist)
            db.session.commit()
            db.session.refresh(blacklist)
            return blacklist
        except IntegrityError as e:
            db.session.rollback()
            if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
                raise ConflictError(f"Email {blacklist_data.get('email')} is already in the blacklist")
            raise

    def get_by_email(self, email: str) -> Optional[Blacklist]:
        """
        Get a blacklist entry by email.
        
        Args:
            email: Email address to search for
            
        Returns:
            Optional[Blacklist]: The blacklist entry if found, None otherwise
        """
        return db.session.query(Blacklist).filter(Blacklist.email == email).first()

    def exists_by_email(self, email: str) -> bool:
        """
        Check if an email exists in the blacklist.
        
        Args:
            email: Email address to check
            
        Returns:
            bool: True if email is blacklisted, False otherwise
        """
        return db.session.query(Blacklist).filter(Blacklist.email == email).first() is not None

