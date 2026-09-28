from fastapi import APIRouter, Depends

from app.api.permissions import require_roles
from app.models.user import User, UserRole


router = APIRouter(
    prefix="/test",
    tags=["Authorization"],
)


@router.get("/customer")
def customer_endpoint(
    current_user: User = Depends(
        require_roles(UserRole.CUSTOMER)
    ),
):
    return {
        "message": "Customer access granted",
        "user": current_user.email,
    }


@router.get("/seller")
def seller_endpoint(
    current_user: User = Depends(
        require_roles(UserRole.SELLER)
    ),
):
    return {
        "message": "Seller access granted",
        "user": current_user.email,
    }


@router.get("/admin")
def admin_endpoint(
    current_user: User = Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    return {
        "message": "Admin access granted",
        "user": current_user.email,
    }