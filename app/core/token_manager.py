from datetime import datetime
from typing import Optional, Set
from motor.motor_asyncio import AsyncIOMotorCollection
from fastapi import HTTPException, status

class TokenManager:
    """Manages JWT tokens including blacklisting and refresh token rotation."""
    
    def __init__(self, db_collection: AsyncIOMotorCollection):
        self.collection = db_collection
        self._blacklisted_tokens: Set[str] = set()
    
    async def blacklist_token(self, token_id: str, reason: str = "logout"):
        """Add a token to the blacklist."""
        await self.collection.insert_one({
            "token_id": token_id,
            "blacklisted_at": datetime.utcnow(),
            "reason": reason
        })
        self._blacklisted_tokens.add(token_id)
    
    async def is_token_blacklisted(self, token_id: str) -> bool:
        """Check if a token is blacklisted."""
        # Check memory cache first
        if token_id in self._blacklisted_tokens:
            return True
            
        # Check database
        token = await self.collection.find_one({"token_id": token_id})
        if token:
            self._blacklisted_tokens.add(token_id)
            return True
        return False
    
    async def cleanup_expired_tokens(self):
        """Remove expired tokens from the blacklist."""
        expired_before = datetime.utcnow()
        result = await self.collection.delete_many({
            "blacklisted_at": {"$lt": expired_before}
        })
        return result.deleted_count
    
    async def rotate_refresh_token(
        self,
        current_token_id: str,
        new_token_id: str,
        user_id: str
    ) -> bool:
        """
        Implement refresh token rotation for enhanced security.
        Returns True if rotation was successful.
        """
        # Check if current token is valid
        if await self.is_token_blacklisted(current_token_id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )
        
        # Blacklist the current token
        await self.blacklist_token(
            current_token_id,
            reason="rotated"
        )
        
        # Record the new token
        await self.collection.insert_one({
            "token_id": new_token_id,
            "user_id": user_id,
            "created_at": datetime.utcnow()
        })
        
        return True
    
    async def revoke_all_user_tokens(self, user_id: str):
        """Revoke all tokens for a specific user."""
        tokens = self.collection.find({"user_id": user_id})
        async for token in tokens:
            await self.blacklist_token(
                token["token_id"],
                reason="user_revoked_all"
            ) 