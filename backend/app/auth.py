from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Membership

_bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    user_id: UUID
    email: str | None


def _decode(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    payload = _decode(creds.credentials)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )
    return CurrentUser(user_id=UUID(sub), email=payload.get("email"))


@dataclass
class RequestContext:
    user_id: UUID
    email: str | None
    tenant_id: int
    role: str


async def get_current_context(
    user: CurrentUser = Depends(get_current_user),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db),
) -> RequestContext:
    if x_tenant_id is None:
        raise HTTPException(status_code=400, detail="Missing X-Tenant-ID header")
    try:
        tenant_id = int(x_tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="X-Tenant-ID must be an integer"
        ) from exc

    membership = (
        await db.execute(
            select(Membership).where(
                Membership.tenant_id == tenant_id,
                Membership.user_id == user.user_id,
            )
        )
    ).scalar_one_or_none()
    if membership is None:
        raise HTTPException(
            status_code=403, detail="Not a member of the requested business"
        )

    return RequestContext(
        user_id=user.user_id,
        email=user.email,
        tenant_id=tenant_id,
        role=membership.role,
    )
