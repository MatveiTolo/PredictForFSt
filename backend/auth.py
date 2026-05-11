from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from models import UserRole
from repository import UserRepository
from services import AuthService

# Синглтоны репозиториев и сервисов
user_repo = UserRepository()
auth_service = AuthService(user_repo)

# Создаём admin при старте
if not user_repo.get_by_username("admin"):
    user_repo.create(
        username="admin",
        email="admin@admin.com",
        hashed_password=auth_service.hash_password("admin123"),
        role=UserRole.ADMIN,
    )
    print("*** Admin пользователь создан (admin / admin123) ***")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Получить текущего пользователя из access токена."""
    try:
        payload = auth_service.verify_token(token, "access")
        username = payload.get("sub")
        user = user_repo.get_by_username(username)
        if not user:
            raise HTTPException(status_code=401, detail="Пользователь не найден")
        return user
    except ValueError:
        raise HTTPException(status_code=401, detail="Невалидный токен")


def require_role(*roles: UserRole):
    """Проверить роль пользователя."""
    def checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", UserRole.USER)
        if user_role not in roles:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        return current_user
    return checker


def get_auth_service() -> AuthService:
    return auth_service


def get_user_repo() -> UserRepository:
    return user_repo