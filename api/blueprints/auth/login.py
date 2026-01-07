from flask import Blueprint, request, jsonify

from api.utils.error_class import CheckError
from api.utils.utils_func import tokenize, validate_payload, is_valid_mail_format
from api.config.model import db, User
from werkzeug.security import check_password_hash

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['POST'])
def login():
    try:
        payload = request.get_json()
        required_fields = ['mail', 'password']
        validate_payload(payload, required_fields)

        mail = payload['mail'].strip()
        password = payload['password'].strip()
        if not is_valid_mail_format(mail):
            return jsonify({'message': 'Incorrect mail format.'}), 400
        if not (user := User.query.filter_by(mail=mail).first()):
            return jsonify({'message': 'Invalid credentials, mail or password incorrect.'}), 401
        if not check_password_hash(user.hashed_password, password):
            return jsonify({'message': 'Invalid credentials, mail or password incorrect.'}), 401

        # creating token after successful connection
        claims ={"id_culture_type": user.id_culture_type}
        token =tokenize(user.id_user, claims)
        return jsonify({'message': 'Login successful',
                        'token': token}), 200
    except CheckError as err:
        return jsonify({"message": str(err)}), err.error_code
    except Exception as err:
        return jsonify({'message': str(err)}), 500