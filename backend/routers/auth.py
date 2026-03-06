from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.user import UserCreate, UserLogin, TokenResponse, RefreshTokenRequest, UserResponse
from services.auth_service import AuthService
from dependencies import get_db, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Register a new user"""
    auth_service = AuthService(db)
    user, error = await auth_service.register_user(user_data)
    
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return auth_service.create_token_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Login with email and password"""
    auth_service = AuthService(db)
    user, error = await auth_service.authenticate_user(credentials.email, credentials.password)
    
    if error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error)
    
    return auth_service.create_token_response(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Refresh access token using refresh token"""
    auth_service = AuthService(db)
    token_response, error = await auth_service.refresh_access_token(request.refresh_token)
    
    if error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error)
    
    return token_response


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info"""
    return UserResponse(**current_user)
