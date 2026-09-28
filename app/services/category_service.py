from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.schemas.category import CategoryCreate


def create_category(
    db: Session,
    category_data: CategoryCreate,
) -> Category:

    category = Category(
        name=category_data.name,
        description=category_data.description,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


def get_categories(
    db: Session,
) -> list[Category]:

    statement = (
        select(Category)
        .where(Category.is_active.is_(True))
        .order_by(Category.name)
    )

    return list(db.scalars(statement).all())