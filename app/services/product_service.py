from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.category import Category
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.user import User, UserRole
from app.models.user import User
from app.schemas.product import ProductCreate
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
)

def create_product(
    db: Session,
    product_data: ProductCreate,
    seller: User,
) -> Product:

    category = db.get(
        Category,
        product_data.category_id,
    )

    if category is None:
        raise ValueError("Category not found")

    product = Product(
        category_id=product_data.category_id,
        seller_id=seller.id,
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
    )

    for variant_data in product_data.variants:

        variant = ProductVariant(
            size=variant_data.size,
            color=variant_data.color,
            stock_quantity=variant_data.stock_quantity,
        )

        product.variants.append(variant)

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


def get_products(
    db: Session,
) -> list[Product]:

    statement = (
        select(Product)
        .where(Product.is_active.is_(True))
        .options(
            selectinload(Product.variants),
            selectinload(Product.images),
        )
        .order_by(Product.created_at.desc())
    )

    return list(db.scalars(statement).all())


def get_product(
    db: Session,
    product_id: int,
) -> Product | None:

    statement = (
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.variants),
            selectinload(Product.images),
        )
    )

    return db.scalar(statement)


def update_product(
    db: Session,
    product: Product,
    product_data: ProductUpdate,
) -> Product:

    update_data = product_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            product,
            field,
            value,
        )

    db.commit()
    db.refresh(product)

    return product


def can_manage_product(
    product: Product,
    current_user: User,
) -> bool:

    if current_user.role == UserRole.ADMIN:
        return True

    if (
        current_user.role == UserRole.SELLER
        and product.seller_id == current_user.id
    ):
        return True

    return False

def deactivate_product(
    db: Session,
    product: Product,
) -> Product:

    product.is_active = False

    db.commit()
    db.refresh(product)

    return product

def get_products(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
):
    offset = (page - 1) * page_size

    statement = (
        select(Product)
        .where(Product.is_active.is_(True))
    )

    if search:
        statement = statement.where(
            Product.name.ilike(
                f"%{search}%"
            )
        )

    statement = (
        statement
        .options(
            selectinload(Product.variants),
            selectinload(Product.images),
        )
        .order_by(Product.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    return list(
        db.scalars(statement).all()
    )
