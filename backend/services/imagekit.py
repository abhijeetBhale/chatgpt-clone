import time
import hashlib
import hmac
from settings import settings


def get_upload_auth_params() -> dict:
    """Get ImageKit authentication parameters for client-side uploads."""
    private_key = settings.IMAGEKIT_URL_PRIVATE_KEY
    expire = int(time.time()) + 2400
    token = "token_random_string"

    signature = hmac.new(
        private_key.encode("utf-8"),
        f"{token}{expire}".encode("utf-8"),
        hashlib.sha1,
    ).hexdigest()

    return {
        "token": token,
        "expire": expire,
        "signature": signature,
    }
