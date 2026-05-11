from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from models import UserRole

SECRET_KEY = "predictforfst-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # короткий
REFRESH_TOKEN_EXPIRE_DAYS = 7     # длинный

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Бизнес-логика аутентификации."""

    def __init__(self, user_repository):
        self.user_repo = user_repository
        # Хранилище refresh токенов: {username: set_of_tokens}
        self._refresh_tokens: dict[str, set] = {}

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    def create_access_token(self, username: str, role: str) -> str:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": username,
            "role": role,
            "exp": expire,
            "type": "access",
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def create_refresh_token(self, username: str) -> str:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": username,
            "exp": expire,
            "type": "refresh",
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        # Сохраняем refresh токен
        if username not in self._refresh_tokens:
            self._refresh_tokens[username] = set()
        self._refresh_tokens[username].add(token)
        return token

    def verify_token(self, token: str, expected_type: str) -> dict:
        """Проверить и декодировать токен."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != expected_type:
                raise JWTError("Invalid token type")
            return payload
        except JWTError:
            raise ValueError("Невалидный токен")

    def refresh_access_token(self, refresh_token: str) -> str:
        """Обновить access token по refresh token."""
        payload = self.verify_token(refresh_token, "refresh")
        username = payload.get("sub")

        # Проверить, что токен не отозван
        if username not in self._refresh_tokens or refresh_token not in self._refresh_tokens[username]:
            raise ValueError("Токен отозван или не существует")

        user = self.user_repo.get_by_username(username)
        if not user:
            raise ValueError("Пользователь не найден")

        # Ротация: удаляем старый refresh, создаём новый
        self._refresh_tokens[username].remove(refresh_token)
        new_refresh = self.create_refresh_token(username)

        return self.create_access_token(username, user["role"].value if isinstance(user["role"], UserRole) else user["role"])

    def revoke_refresh_token(self, username: str, refresh_token: str):
        """Отозвать refresh token (выход)."""
        if username in self._refresh_tokens:
            self._refresh_tokens[username].discard(refresh_token)

    def revoke_all_tokens(self, username: str):
        """Отозвать все refresh токены пользователя."""
        if username in self._refresh_tokens:
            self._refresh_tokens[username].clear()


class PredictionService:
    """Бизнес-логика прогнозов."""

    def __init__(self, prediction_repository):
        self.prediction_repo = prediction_repository

    def create(self, username: str, ticker: str, date: str, price: float) -> dict:
        return self.prediction_repo.create(
            username=username,
            ticker=ticker,
            date=date,
            predicted_price=price,
            created_at=datetime.utcnow().isoformat(),
        )

    def get_for_user(self, username: str, is_admin: bool = False) -> list[dict]:
        if is_admin:
            return self.prediction_repo.get_all()
        return self.prediction_repo.get_by_user(username)

    def get_by_id(self, prediction_id: int, username: str, is_admin: bool = False) -> dict:
        record = self.prediction_repo.get_by_id(prediction_id)
        if not record:
            raise ValueError("Прогноз не найден")
        if record["username"] != username and not is_admin:
            raise PermissionError("Доступ запрещён")
        return record

    def delete(self, prediction_id: int, username: str, is_admin: bool = False):
        record = self.prediction_repo.get_by_id(prediction_id)
        if not record:
            raise ValueError("Прогноз не найден")
        if record["username"] != username and not is_admin:
            raise PermissionError("Доступ запрещён")
        self.prediction_repo.delete(prediction_id)