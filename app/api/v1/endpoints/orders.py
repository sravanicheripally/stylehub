from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.permissions import require_roles
from app.db.dependencies import get_db
from app.models.user import User, UserRole
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderSummaryResponse,
)
from app.services.order_service import (
    OrderConflictError,
    create_order,
    get_customer_orders,
    get_managed_orders,
    get_order_summary,
)
from app.services.payment_verification import (
    PaymentVerificationError,
    verify_payment,
)


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order_endpoint(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.CUSTOMER)
    ),
):
    try:
        verify_payment(order_data.payment)
        return create_order(db, order_data, current_user)
    except PaymentVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(exc),
        ) from exc
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except OrderConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/history",
    response_model=list[OrderResponse],
)
def customer_order_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.CUSTOMER)
    ),
):
    return get_customer_orders(db, current_user, page, page_size)


@router.get(
    "/summary",
    response_model=OrderSummaryResponse,
)
def order_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.SELLER)
    ),
):
    return get_order_summary(db, current_user)


@router.get(
    "",
    response_model=list[OrderResponse],
)
def managed_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.SELLER)
    ),
):
    return get_managed_orders(db, current_user, page, page_size)
