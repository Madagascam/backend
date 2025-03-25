from datetime import timedelta

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings
from app.core.DTO import *

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now() + (
        expires_delta if expires_delta else timedelta(minutes=settings.security.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.security.secret_key, algorithm=settings.security.algorithm)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenDataSchema]:
    try:
        payload = jwt.decode(token, settings.security.secret_key, algorithms=[settings.security.algorithm])
        username = payload.get("sub")
        user_id = payload.get("user_id")
        role = payload.get("role")

        if username is None:
            return None

        return TokenDataSchema(username=username, user_id=user_id, role=role)
    except JWTError:
        return None


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)
