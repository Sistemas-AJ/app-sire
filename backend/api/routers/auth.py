from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from core.database import get_db, User, UserSession
from core.security import hash_password, verify_password, create_token, hash_token
from api import schemas


router = APIRouter(prefix="/auth", tags=["auth"])

TOKEN_TTL_HOURS = 2


def _get_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1].strip()


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
) -> User:
    token = _get_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Token requerido")
    token_hash = hash_token(token)
    now = datetime.now(timezone.utc)
    session = (
        db.query(UserSession)
        .filter(
            UserSession.token_hash == token_hash,
            UserSession.revoked == False,
            UserSession.expires_at > now,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    user = db.query(User).filter(User.id == session.user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario inactivo")
    return user


@router.post("/bootstrap", response_model=schemas.UserMeResponse)
def bootstrap_user(req: schemas.UserCreateRequest, db: Session = Depends(get_db)):
    """
    Crea el primer usuario si la tabla está vacía.
    """
    existing = db.query(User).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un usuario. Use /auth/login.")
    user = User(username=req.username, password_hash=hash_password(req.password), is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return schemas.UserMeResponse(id=user.id, username=user.username, is_active=user.is_active)


@router.post("/login", response_model=schemas.UserLoginResponse)
def login(req: schemas.UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not user.is_active:
        return schemas.UserLoginResponse(ok=False, message="Usuario inválido")
    if not verify_password(req.password, user.password_hash):
        return schemas.UserLoginResponse(ok=False, message="Contraseña inválida")

    token = create_token()
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS)

    session = UserSession(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(session)
    db.commit()
    return schemas.UserLoginResponse(ok=True, token=token, expires_at=expires_at)


@router.post("/logout")
def logout(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
):
    token = _get_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Token requerido")
    token_hash = hash_token(token)
    updated = (
        db.query(UserSession)
        .filter(UserSession.token_hash == token_hash, UserSession.revoked == False)
        .update({"revoked": True}, synchronize_session=False)
    )
    db.commit()
    return {"ok": updated > 0}


@router.get("/me", response_model=schemas.UserMeResponse)
def me(user: User = Depends(get_current_user)):
    return schemas.UserMeResponse(id=user.id, username=user.username, is_active=user.is_active)
