import os
import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.user import User, UserCreate, UserResponse, TokenResponse, UserRole
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')


class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.secret_key = os.environ.get('JWT_SECRET_KEY', 'default-secret-key')
        self.algorithm = os.environ.get('JWT_ALGORITHM', 'HS256')
        self.access_token_expire = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', 30))
        self.refresh_token_expire = int(os.environ.get('REFRESH_TOKEN_EXPIRE_DAYS', 7))
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    
    def create_access_token(self, user_id: str, role: str) -> Tuple[str, int]:
        """Create a JWT access token"""
        expires = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire)
        payload = {
            "sub": user_id,
            "role": role,
            "type": "access",
            "exp": expires,
            "iat": datetime.now(timezone.utc)
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token, self.access_token_expire * 60
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a JWT refresh token"""
        expires = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire)
        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": expires,
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def register_user(self, user_data: UserCreate) -> Tuple[Optional[User], Optional[str]]:
        """Register a new user"""
        # Check if user already exists
        existing = await self.db.users.find_one({"email": user_data.email})
        if existing:
            return None, "User with this email already exists"
        
        # Create new user
        hashed_password = self.hash_password(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            organization_id=user_data.organization_id
        )
        
        # Save to database
        user_dict = user.model_dump()
        user_dict['created_at'] = user_dict['created_at'].isoformat()
        user_dict['updated_at'] = user_dict['updated_at'].isoformat()
        
        await self.db.users.insert_one(user_dict)
        return user, None
    
    async def authenticate_user(self, email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """Authenticate a user by email and password"""
        user_doc = await self.db.users.find_one({"email": email}, {"_id": 0})
        if not user_doc:
            return None, "Invalid email or password"
        
        # Convert timestamps
        if isinstance(user_doc.get('created_at'), str):
            user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
        if isinstance(user_doc.get('updated_at'), str):
            user_doc['updated_at'] = datetime.fromisoformat(user_doc['updated_at'])
        
        user = User(**user_doc)
        
        if not self.verify_password(password, user.hashed_password):
            return None, "Invalid email or password"
        
        if not user.is_active:
            return None, "Account is disabled"
        
        return user, None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        user_doc = await self.db.users.find_one({"id": user_id}, {"_id": 0})
        if not user_doc:
            return None
        
        # Convert timestamps
        if isinstance(user_doc.get('created_at'), str):
            user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
        if isinstance(user_doc.get('updated_at'), str):
            user_doc['updated_at'] = datetime.fromisoformat(user_doc['updated_at'])
        
        return User(**user_doc)
    
    def create_token_response(self, user: User) -> TokenResponse:
        """Create a full token response for a user"""
        access_token, expires_in = self.create_access_token(user.id, user.role.value)
        refresh_token = self.create_refresh_token(user.id)
        
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            organization_id=user.organization_id,
            kitchen_ids=user.kitchen_ids,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            user=user_response
        )
    
    async def refresh_access_token(self, refresh_token: str) -> Tuple[Optional[TokenResponse], Optional[str]]:
        """Generate new tokens using a refresh token"""
        payload = self.decode_token(refresh_token)
        if not payload:
            return None, "Invalid or expired refresh token"
        
        if payload.get("type") != "refresh":
            return None, "Invalid token type"
        
        user = await self.get_user_by_id(payload["sub"])
        if not user:
            return None, "User not found"
        
        if not user.is_active:
            return None, "Account is disabled"
        
        return self.create_token_response(user), None
