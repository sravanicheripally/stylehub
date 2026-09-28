from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.permissions import require_roles
from app.db.dependencies import get_db
from app.models.category import Category
from app.models.user import User, UserRole
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
)
from app.services.category_service import (
    create_category,
    get_categories,
)


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category_endpoint(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    return create_category(
        db,
        category_data,
    )


@router.get(
    "",
    response_model=list[CategoryResponse],
)
def list_categories(
    db: Session = Depends(get_db),
):
    return get_categories(db)