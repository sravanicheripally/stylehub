import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.schemas.order import RazorpayPaymentProof


class PaymentVerificationError(Exception):
    pass


class PaymentVerificationUnavailable(PaymentVerificationError):
    pass


def verify_payment(payment: RazorpayPaymentProof) -> None:
    request = Request(
        f"{settings.payment_service_url.rstrip('/')}/payments/verify",
        data=json.dumps(payment.model_dump()).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=25) as response:
            if not 200 <= response.status < 300:
                raise PaymentVerificationError(
                    "Payment verification service rejected the payment"
                )
    except HTTPError as exc:
        if exc.code in {400, 422}:
            raise PaymentVerificationError(
                "Payment verification failed"
            ) from exc
        if exc.code == 404:
            raise PaymentVerificationUnavailable(
                "Payment verification route was not found; check "
                "PAYMENT_SERVICE_URL and the /payments/verify route"
            ) from exc
        if exc.code in {401, 403}:
            raise PaymentVerificationUnavailable(
                "Payment service rejected the backend request; check its "
                "authorization settings"
            ) from exc
        if exc.code == 429 or exc.code >= 500:
            raise PaymentVerificationUnavailable(
                f"Payment verification service returned HTTP {exc.code}"
            ) from exc
        raise PaymentVerificationUnavailable(
            f"Payment verification service returned unexpected HTTP {exc.code}"
        ) from exc
    except URLError as exc:
        raise PaymentVerificationUnavailable(
            "Payment verification service is unavailable"
        ) from exc
    except TimeoutError as exc:
        raise PaymentVerificationUnavailable(
            "Payment verification service timed out"
        ) from exc
