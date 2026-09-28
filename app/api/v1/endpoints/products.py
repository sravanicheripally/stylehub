from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.permissions import require_roles
from app.db.dependencies import get_db
from app.models.user import User, UserRole
from app.models.product_image import ProductImage
from app.schemas.product import (
    ProductCreate,
    ProductImageResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services.product_service import (
    can_manage_product,
    create_product,
    deactivate_product,
    get_product,
    get_products,
    update_product,
)


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)

IMAGE_DIR = Path(__file__).resolve().parents[3] / "static" / "product-images"
MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_IMAGES_PER_UPLOAD = 5
IMAGE_SIGNATURES = {
    "image/jpeg": (b"\xff\xd8\xff", ".jpg"),
    "image/png": (b"\x89PNG\r\n\x1a\n", ".png"),
    "image/gif": (b"GIF87a", ".gif"),
    "image/webp": (b"RIFF", ".webp"),
}


def _image_extension(content_type: str | None, content: bytes) -> str | None:
    image_type = IMAGE_SIGNATURES.get(content_type or "")
    if image_type is None:
        return None

    signature, extension = image_type
    if not content.startswith(signature):
        return None
    if content_type == "image/webp" and content[8:12] != b"WEBP":
        return None
    return extension


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product_endpoint(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.SELLER,
        )
    ),
):

    try:
        return create_product(
            db,
            product_data,
            current_user,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.post(
    "/{product_id}/images",
    response_model=list[ProductImageResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_product_images(
    product_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.SELLER,
        )
    ),
):
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    if not can_manage_product(product, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot manage this product",
        )
    if not files or len(files) > MAX_IMAGES_PER_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload between 1 and {MAX_IMAGES_PER_UPLOAD} images",
        )

    validated_files = []
    for image_file in files:
        content = await image_file.read(MAX_IMAGE_SIZE + 1)
        if len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Each image must be 5 MiB or smaller",
            )

        extension = _image_extension(image_file.content_type, content)
        if extension is None:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Images must be valid JPEG, PNG, GIF, or WebP files",
            )
        validated_files.append((content, extension))

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    saved_paths = []
    created_images = []
    try:
        for content, extension in validated_files:
            filename = f"{uuid4().hex}{extension}"
            image_path = IMAGE_DIR / filename
            image_path.write_bytes(content)
            saved_paths.append(image_path)

            product_image = ProductImage(
                image_url=f"/media/product-images/{filename}",
            )
            product.images.append(product_image)
            created_images.append(product_image)

        db.commit()
    except Exception:
        db.rollback()
        for image_path in saved_paths:
            image_path.unlink(missing_ok=True)
        raise

    return created_images


@router.get(
    "",
    response_model=list[ProductResponse],
)
def list_products(
    db: Session = Depends(get_db),
):
    return get_products(db)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product_by_id(
    product_id: int,
    db: Session = Depends(get_db),
):

    product = get_product(
        db,
        product_id,
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_product_endpoint(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.SELLER,
        )
    ),
):
    product = get_product(
        db,
        product_id,
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if not can_manage_product(
        product,
        current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot manage this product",
        )

    return update_product(
        db,
        product,
        product_data,
    )

@router.delete(
    "/{product_id}",
    response_model=ProductResponse,
)
def delete_product_endpoint(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.SELLER,
        )
    ),
):
    product = get_product(
        db,
        product_id,
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if not can_manage_product(
        product,
        current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot manage this product",
        )

    return deactivate_product(
        db,
        product,
    )

@router.get(
    "",
    response_model=list[ProductResponse],
)
def list_products(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    search: str | None = None,
    db: Session = Depends(get_db),
):
    return get_products(
        db,
        page,
        page_size,
        search,
    )
