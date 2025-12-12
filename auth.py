from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from config import settings
from models import TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthUtils:
    """JWT and password hashing utilities"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token with expiration"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[TokenData]:
        """Decode JWT token and return TokenData or None"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            admin_id: Optional[str] = payload.get("admin_id")
            organization_id: Optional[str] = payload.get("organization_id")
            email: Optional[str] = payload.get("email")
            
            if admin_id is None or organization_id is None or email is None:
                return None
            
            return TokenData(
                admin_id=admin_id,
                organization_id=organization_id,
                email=email or ""
            )
        except JWTError:
            return None


# Global auth utilities instance
auth_utils = AuthUtils()
