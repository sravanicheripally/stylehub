from decimal import Decimal

from sqlalchemy import case, distinct, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.user import User, UserRole
from app.schemas.order import OrderCreate


class OrderConflictError(Exception):
    pass


def create_order(
    db: Session,
    order_data: OrderCreate,
    customer: User,
) -> Order:
    existing_order = db.scalar(
        select(Order).where(
            Order.payment_reference == order_data.payment.razorpay_payment_id
        )
    )
    if existing_order is not None:
        if existing_order.customer_id != customer.id:
            raise OrderConflictError("Payment reference is already in use")
        return existing_order

    order_items = []
    stock_changes: list[tuple[int, int]] = []
    subtotal = Decimal("0.00")

    for item_data in order_data.items:
        product = db.get(Product, item_data.product_id)
        if product is None or not product.is_active:
            raise LookupError(f"Product {item_data.product_id} is unavailable")

        variants = list(
            db.scalars(
                select(ProductVariant).where(
                    ProductVariant.product_id == product.id
                )
            ).all()
        )
        variant = None
        if item_data.variant_id is not None:
            variant = next(
                (
                    candidate
                    for candidate in variants
                    if candidate.id == item_data.variant_id
                ),
                None,
            )
            if variant is None:
                raise ValueError("Selected variant does not belong to the product")
            if variant.stock_quantity < item_data.quantity:
                raise OrderConflictError(
                    f"Insufficient stock for {product.name}"
                )
            stock_changes.append((variant.id, item_data.quantity))
        elif variants:
            raise ValueError(f"Choose a variant for {product.name}")

        unit_price = Decimal(product.price)
        line_total = unit_price * item_data.quantity
        subtotal += line_total
        variant_label = (
            f"{variant.size} / {variant.color}"
            if variant is not None
            else None
        )
        order_items.append(
            OrderItem(
                product_id=product.id,
                seller_id=product.seller_id,
                product_name=product.name,
                variant_label=variant_label,
                quantity=item_data.quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
        )

    shipping_amount = (
        Decimal("99.00")
        if subtotal > 0 and subtotal < Decimal("1499.00")
        else Decimal("0.00")
    )
    total_amount = subtotal + shipping_amount
    if total_amount != order_data.expected_total:
        raise ValueError(
            "The cart total changed. Refresh your cart and try again."
        )

    order = Order(
        customer_id=customer.id,
        status="processing",
        subtotal=subtotal,
        shipping_amount=shipping_amount,
        total_amount=total_amount,
        payment_reference=order_data.payment.razorpay_payment_id,
        items=order_items,
    )
    db.add(order)

    for variant_id, quantity in stock_changes:
        update_result = db.execute(
            update(ProductVariant)
            .where(
                ProductVariant.id == variant_id,
                ProductVariant.stock_quantity >= quantity,
            )
            .values(
                stock_quantity=ProductVariant.stock_quantity - quantity
            )
        )
        if update_result.rowcount != 1:
            db.rollback()
            raise OrderConflictError("Product stock changed; refresh and retry")

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing_order = db.scalar(
            select(Order).where(
                Order.payment_reference == order_data.payment.razorpay_payment_id
            )
        )
        if existing_order is not None:
            if existing_order.customer_id != customer.id:
                raise OrderConflictError("Payment reference is already in use")
            return existing_order
        raise

    db.refresh(order)
    return order


def _order_response(
    order: Order,
    seller_id: int | None = None,
) -> dict:
    items = [
        item
        for item in order.items
        if seller_id is None or item.seller_id == seller_id
    ]
    subtotal = sum(
        (item.line_total for item in items),
        start=Decimal("0.00"),
    )
    return {
        "id": order.id,
        "customer_id": order.customer_id,
        "status": order.status,
        "subtotal": order.subtotal if seller_id is None else subtotal,
        "shipping_amount": (
            order.shipping_amount if seller_id is None else Decimal("0.00")
        ),
        "total_amount": (
            order.total_amount
            if seller_id is None
            else subtotal
        ),
        "created_at": order.created_at,
        "items": items,
    }


def get_customer_orders(
    db: Session,
    customer: User,
    page: int,
    page_size: int,
) -> list[dict]:
    statement = (
        select(Order)
        .where(Order.customer_id == customer.id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc(), Order.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return [_order_response(order) for order in db.scalars(statement).all()]


def get_managed_orders(
    db: Session,
    user: User,
    page: int,
    page_size: int,
) -> list[dict]:
    statement = select(Order).options(selectinload(Order.items))
    if user.role == UserRole.SELLER:
        statement = statement.where(
            Order.items.any(OrderItem.seller_id == user.id)
        )
    statement = (
        statement.order_by(Order.created_at.desc(), Order.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    seller_id = user.id if user.role == UserRole.SELLER else None
    return [
        _order_response(order, seller_id)
        for order in db.scalars(statement).all()
    ]


def get_order_summary(db: Session, user: User) -> dict:
    if user.role == UserRole.SELLER:
        order_count = func.count(distinct(Order.id))
        processing_count = func.count(
            distinct(case((Order.status == "processing", Order.id)))
        )
        shipped_count = func.count(
            distinct(case((Order.status == "shipped", Order.id)))
        )
        delivered_count = func.count(
            distinct(case((Order.status == "delivered", Order.id)))
        )
        cancelled_count = func.count(
            distinct(case((Order.status == "cancelled", Order.id)))
        )
        amount_total = func.coalesce(
            func.sum(
                case(
                    (
                        Order.status != "cancelled",
                        OrderItem.line_total,
                    ),
                    else_=0,
                )
            ),
            0,
        )
        statement = (
            select(
                order_count,
                processing_count,
                shipped_count,
                delivered_count,
                cancelled_count,
                amount_total,
            )
            .select_from(Order)
            .join(OrderItem)
            .where(OrderItem.seller_id == user.id)
        )
    else:
        amount_total = func.coalesce(
            func.sum(
                case(
                    (
                        Order.status != "cancelled",
                        Order.total_amount,
                    ),
                    else_=0,
                )
            ),
            0,
        )
        statement = select(
            func.count(Order.id),
            func.sum(case((Order.status == "processing", 1), else_=0)),
            func.sum(case((Order.status == "shipped", 1), else_=0)),
            func.sum(case((Order.status == "delivered", 1), else_=0)),
            func.sum(case((Order.status == "cancelled", 1), else_=0)),
            amount_total,
        )

    (
        total_orders,
        processing_orders,
        shipped_orders,
        delivered_orders,
        cancelled_orders,
        total_amount,
    ) = db.execute(statement).one()

    return {
        "total_orders": total_orders or 0,
        "processing_orders": processing_orders or 0,
        "shipped_orders": shipped_orders or 0,
        "delivered_orders": delivered_orders or 0,
        "cancelled_orders": cancelled_orders or 0,
        "total_amount": total_amount or Decimal("0.00"),
    }
