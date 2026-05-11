from typing import Optional
from models import UserInDB, UserRole


class UserRepository:
    """Слой доступа к данным пользователей (in-memory)."""

    def __init__(self):
        self._users: dict[str, dict] = {}

    def get_by_username(self, username: str) -> Optional[dict]:
        return self._users.get(username)

    def create(self, username: str, email: str, hashed_password: str, role: UserRole = UserRole.USER) -> dict:
        user = {
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "role": role,
        }
        self._users[username] = user
        return user

    def get_all(self) -> list[dict]:
        return list(self._users.values())

    def update_role(self, username: str, role: UserRole) -> bool:
        if username not in self._users:
            return False
        self._users[username]["role"] = role
        return True


class PredictionRepository:
    """Слой доступа к прогнозам (in-memory)."""

    def __init__(self):
        self._predictions: list[dict] = []
        self._next_id: int = 1

    def create(self, username: str, ticker: str, date: str, predicted_price: float, created_at: str) -> dict:
        record = {
            "id": self._next_id,
            "username": username,
            "ticker": ticker,
            "date": date,
            "predicted_price": predicted_price,
            "created_at": created_at,
        }
        self._predictions.append(record)
        self._next_id += 1
        return record

    def get_by_user(self, username: str) -> list[dict]:
        return [p for p in self._predictions if p["username"] == username]

    def get_all(self) -> list[dict]:
        return self._predictions

    def get_by_id(self, prediction_id: int) -> Optional[dict]:
        for p in self._predictions:
            if p["id"] == prediction_id:
                return p
        return None

    def delete(self, prediction_id: int) -> bool:
        for i, p in enumerate(self._predictions):
            if p["id"] == prediction_id:
                del self._predictions[i]
                return True
        return False