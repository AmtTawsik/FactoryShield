from fastapi import APIRouter, status

from app.modules.auth.dependencies import AuthServiceDep, CurrentUser
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, service: AuthServiceDep):
    return await service.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, service: AuthServiceDep):
    return await service.login(data)


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser):
    return user
