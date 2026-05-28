from django.core import signing

from auth_service.settings import EMAIL_VERIFICATION_SALT


def generate_verification_token(user_id: int) -> str:
    """Return URL-safe, hmac signed base64 compressed JSON string

    Args:
        user_id (int): the user associated to token

    Returns:
        str: token
    """
    return signing.dumps({"user_id": user_id}, salt=EMAIL_VERIFICATION_SALT)


def verify_token(token: str, max_age: int = 86400) -> int:
    """the user id associated to the token

    Args:
        token (str): token associated to user

    Returns:
        int: _description_
    """
    user_obj = signing.loads(token, salt=EMAIL_VERIFICATION_SALT, max_age=max_age)  # 1 day ttl
    return user_obj["user_id"]
