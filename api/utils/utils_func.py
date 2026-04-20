import os
import secrets
import base64
import re
import uuid
from datetime import timedelta, datetime

import requests
from flask import current_app
from flask_jwt_extended import create_access_token
from typing import Any, Optional, Union
from werkzeug.security import generate_password_hash
from api.utils.error_class import CheckError
from flask import render_template

from flask_mail import Message
from api.extension.mail_sms import mail
from api.utils.token import generate_sign, get_imou_token

SIMPLE_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

# IDENTIFIANTS IMOU
APP_ID = os.environ.get("APP_ID")
APP_SECRET = os.environ.get("APP_SECRET")
DATA_CENTER = os.environ.get("DATACENTER")
# IDENTIFIANTS TUYA
APP_ID_POMPE = os.environ.get("APP_ID_POMPE")
CLIENT_SECRET = os.environ.get("SECRET_KEY_POMPE")
BASE_URL_TUYA = os.environ.get("BASE_URL_TUYA")
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

def cleanup_codes(VerificationCode, db):
    """
    cleaning up the expired or used code in the database
    :param db:
    :param VerificationCode:
    :return:
    """
    try:
        now = datetime.now()
        expired_codes = VerificationCode.query.filter((VerificationCode.checked == True) | (VerificationCode.expiry < now)).all()
        for record in expired_codes:
            record.checked = False
            record.code = None
            record.expiry = None
        db.session.commit()
    except CheckError as err:
        raise CheckError(str(err), err.error_code)
    except Exception as err:
        raise CheckError(str(err), 400)

def generate_new_code(id_user, VC, db):
    """
    generate a verification code
    :param id_user:
    :param db:
    :param VC:
    :return: code: int
    """
    cleanup_codes(VC, db)
    code = secrets.randbelow(90000000) + 10000000
    expiry = datetime.now() + timedelta(minutes=10)

    record = VC.query.filter_by(id_user==id_user).first()
    if record:
        record.code = code
        record.expiry = expiry
        record.checked = False
        db.session.commit()
    else:
        record = VC(id_user=id_user, code=code, expiry=expiry)
        db.session.add(record)
        db.session.commit()
    return code

def send_verification_code(code: int, field_value:str, value: Any):
    try:
        match field_value:
            case "mail":
                if isinstance(value, str) and is_valid_mail_format(value):
                    html_page = render_template('mail_reset', code=code)
                    mail_message = Message(
                        sender=current_app.config["MAIL_USERNAME"],
                        subject="Account Password Reset",
                        recipients=[value]
                    )
                    mail_message.html = html_page
                    mail.send(mail_message)

                    current_app.logger.error(f"Verification code was sent to your email address: {value}")
                    return True

            case "phone_number":
                return True

            case _:  # Default case
                raise CheckError(f"Invalid json data, field {field_value} does not exist", 400)
    except CheckError as err:
        current_app.logger.error(str(err))
        raise CheckError(str(err), 400)

# UTILITAIRE POUR APPEL IMOU
def call_imou_api(endpoint: str, params: dict, timeout: int = 10):
    """
    Fonction générique pour appeler l'API Imou.
    Ajoute automatiquement le token et les paramètres système.
    """
    token, _ = get_imou_token()
    timestamp, nonce, sign = generate_sign()

    body = {
        "system": {
            "ver": "1.0",
            "appId": APP_ID,
            "sign": sign,
            "time": timestamp,
            "nonce": nonce
        },
        "id": str(uuid.uuid4()),
        "params": {**params, "token": token}
    }

    url = f"https://openapi-{DATA_CENTER}.easy4ip.com/openapi/{endpoint}"
    response = requests.post(url, json=body, timeout=timeout)
    return response.json()
# UTILITAIRE POUR APPEL TUYA
def call_tuya_api(method: str, path: str, access_token: str = None, body: dict = None):
    import time, json, hashlib, hmac, requests

    if body is None:
        body = {}

    t = str(int(time.time() * 1000))

    body_str = json.dumps(body, separators=(",", ":")) if body else ""
    body_hash = hashlib.sha256(body_str.encode("utf-8")).hexdigest()

    string_to_sign = f"{method}\n{body_hash}\n\n{path}"

    sign_str = APP_ID_POMPE + (access_token or "") + t + string_to_sign

    sign = hmac.new(
        CLIENT_SECRET.encode("utf-8"),
        sign_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest().upper()

    headers = {
        "client_id": APP_ID_POMPE,
        "sign": sign,
        "t": t,
        "sign_method": "HMAC-SHA256"
    }

    if access_token:
        headers["access_token"] = access_token

    url = BASE_URL_TUYA + path

    if method.upper() == "GET":
        return requests.get(url, headers=headers).json()
    else:
        return requests.post(url, json=body, headers=headers).json()