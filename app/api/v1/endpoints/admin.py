from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.permissions import require_roles
from app.db.dependencies import get_db
from app.models.user import User, UserRole
from app.schemas.auth import AdminUserCreate, UserResponse
from app.services.auth_service import create_user, get_user_by_email


router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
)


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def create_admin_managed_user(
    user_data: AdminUserCreate,
    db: Session = Depends(get_db),
):
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    return create_user(
        db,
        user_data,
        role=user_data.role,
    )