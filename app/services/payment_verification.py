import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.schemas.order import RazorpayPaymentProof


class PaymentVerificationError(Exception):
    pass


def verify_payment(payment: RazorpayPaymentProof) -> None:
    request = Request(
        f"{settings.payment_service_url.rstrip('/')}/payments/verify",
        data=json.dumps(payment.model_dump()).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            if not 200 <= response.status < 300:
                raise PaymentVerificationError(
                    "Payment verification service rejected the payment"
                )
    except HTTPError as exc:
        if exc.code in {400, 401, 403, 422}:
            raise PaymentVerificationError(
                "Payment verification failed"
            ) from exc
        raise PaymentVerificationError(
            "Payment verification service is unavailable"
        ) from exc
    except URLError as exc:
        raise PaymentVerificationError(
            "Payment verification service is unavailable"
        ) from exc
