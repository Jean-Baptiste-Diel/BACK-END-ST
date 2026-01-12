from flask import Blueprint, jsonify, current_app, request, session
from api.utils.utils_func import validate_payload, is_valid_mail_format, hash_password
from api.config.model import db, User, VerificationCode as VC
from api.utils.error_class import CheckError
from datetime import datetime

reset_password_bp = Blueprint('reset_password', __name__)

@reset_password_bp.route('/reset-password', methods=['PATCH'])
def reset_password():
    try:
        required_field = {'password': str, 'code': int}
        payload = request.get_json()
        if validate_payload(payload, required_field, True) is None:
            current_app.logger.info(f'Proper payload sent')
            return jsonify({'message': str(payload['error'])}), 400


        if not (verification := VC.query.filter_by(code=payload.get('code'), mail=payload.get('email')).first()):
            current_app.logger.error(f'Invalid email: Access denied.')
            return jsonify({'message': 'Access denied'}), 401

        # Verification of code validity: been checked or expired
        if verification.cheched:
            current_app.logger.error(f'Code already verified: {payload.get("email")}')
            return jsonify({'message': 'Code already verified'}), 400
        if verification.expiry < datetime.now():
            # cleanup_codes()
            current_app.logger.error(f'Code has already expired')
            return jsonify({'message': 'Code has already expired'}), 400

        if  user := User.query.filter_by(email=payload.get('email')).first():
           user.hashed_password = hash_password(payload.get('password'))
           db.session.commit()
           current_app.logger.info(f'Password successfully reset')
           return jsonify({'message': 'Password successfully reset'}), 200
        else:
            current_app.logger.error(f'Invalid email: {payload.get("email")}')
            return jsonify({'message': 'Invalid email or password'}), 401
    except CheckError as err:
        current_app.logger.error(err)
        current_app.logger.error(err), err.error_code
    except Exception as err:
        current_app.logger.error(f'something went wrong: {err}')
        return jsonify({'error': str(err)}), 500