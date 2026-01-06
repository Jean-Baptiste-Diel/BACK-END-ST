import secrets
import base64
import re
from datetime import timedelta
from flask import current_app, jsonify
from flask_jwt_extended import create_access_token
from typing import Any, Optional, Union
from werkzeug.security import generate_password_hash
from api.utils.error_class import CheckError

SIMPLE_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

def is_valid_mail_format(mail: str) -> bool:
    """Check if the email is in valid format."""
    if not mail or mail == "":
        raise CheckError("Email is required", 400)
    return bool(SIMPLE_RE.match(mail))

def hash_password(password: str) -> str:
    password = password.strip()
    return generate_password_hash(password)


def generate_key(length: int = 32) -> str:
    """
    Generate a secure random key and return it as a base64 string.
    """
    random_bytes = secrets.token_bytes(length)
    # Encode as base64 (URL-safe)
    return base64.urlsafe_b64encode(random_bytes).decode('utf-8')

def tokenize(identity: Any, claims: dict, expire = None) -> str:
    """
    create the token
    :param identity:
    :param claims:
    :param expire:
    :return: token
    """
    exp = expire or int(current_app.config.get("JWT_EXP_DELTA_SECONDS"))
    # setting the expiration time
    token = create_access_token(identity=identity, additional_claims=claims, expires_delta=timedelta(seconds=exp))
    return token

def validate_payload(payload: Any, required_fields: Optional[Union[list, dict]] = None, type_check: bool = False) -> None:
    """
    Validate the payload from request.get_json()

    :param payload: dict expected
    :param required_fields: list of field names OR dict of {field: type}
    :param type_check: if True, required_fields must be a dict with type mapping
    :return: None (raises Error if invalid)
    """
    if not payload:
        raise CheckError("Payload required", 400)

    if not isinstance(payload, dict):
        raise CheckError("Invalid payload format", 400)

    if not required_fields:
        raise CheckError("Fields are required", 400)

    # Case 1: required_fields is a list (basic validation)
    if not type_check and isinstance(required_fields, list):
        for field in required_fields:
            if field not in payload:
                raise CheckError(f"Field '{field}' is required", 400)

            value = payload.get(field)
            if value is None or value == "":
                raise CheckError(f"Field '{field}' cannot be empty", 400)

            if not isinstance(value, str):
                raise CheckError(f"Field '{field}' must be a string", 400)

    # Case 2: required_fields is a dict (type validation)
    elif type_check and isinstance(required_fields, dict):
        for field, expected_type in required_fields.items():
            if field not in payload:
                raise CheckError(f"Field '{field}' is required", 400)

            value = payload.get(field)
            if value is None or value == "":
                raise CheckError(f"Field '{field}' cannot be empty", 400)

            if not isinstance(value, expected_type):
                raise CheckError(f"Field '{field}' must be of type {expected_type.__name__}", 400)

    else:
        raise CheckError("Invalid required_fields format", 400)



