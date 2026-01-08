from flask import Blueprint, request, jsonify, current_app

from api.utils.error_class import CheckError
from api.utils.utils_func import tokenize, validate_payload, is_valid_mail_format
from api.config.model import db, User
from werkzeug.security import check_password_hash

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['POST'])
def login():
    try:
        payload = request.get_json()
        required_fields = ['identifier', 'password']
        validate_payload(payload, required_fields)

        identifier = payload['identifier'].strip()

        password = payload['password'].strip()
        if is_valid_mail_format(identifier):
            user = User.query.filter_by(mail=identifier.lower()).first()
            current_app.logger.info(f"Tentative login par mail: {identifier}")
        else:
            user = User.query.filter_by(phone_number=identifier).first()
            current_app.logger.info(f"Tentative login par téléphone: {identifier}")

        if not user:
            current_app.logger.info(f"Identifiants invalides: {identifier}")
            return jsonify({
                "message": "Identifiants invalides"
            }), 401

        if not check_password_hash(user.hashed_password, password):\
            return jsonify({
                "message": "Identifiants invalides"
            }), 401
        # creating token after successful connection
        claims ={"id_culture_type": user.id_culture_type}
        token =tokenize(user.id_user, claims)
        current_app.logger.info(f"Login successful: {payload.get('mail')}")
        return jsonify({'message': 'Login successful',
                        'token': token}), 200
    except CheckError as err:
        current_app.logger.error(f"CheckError: {str(err)}")
        return jsonify({"message": str(err)}), err.error_code
    except Exception as err:
        current_app.logger.exception(f"Erreur inattendue: {str(err)}")
        return jsonify({'message': str(err)}), 500