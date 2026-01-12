from flask import Blueprint, jsonify, current_app, request, session
from api.utils.utils_func import validate_payload, is_valid_mail_format, hash_password, cleanup_codes
from api.config.model import db, User, VerificationCode as VC
from api.utils.error_class import CheckError
from datetime import datetime

reset_password_bp = Blueprint('reset_password', __name__)

@reset_password_bp.route('/reset-password', methods=['PATCH'])
def reset_password():
    try:
        fields = ['mail', 'phone_number']
        required_fields = {'password':str, 'code':int}
        payload = request.get_json()
        current_field = [field for field in fields if field in session]

        if len(current_field) == 1:
            field_value = current_field[0]
            validate_payload(payload, required_fields, True)

            user_code = payload.get('code')
            # checking session credentials existence
            if not (session_code := session.get(user_code)) or not (session_attr := session.get(field_value)):
                current_app.logger.error(f'Access denied.')
                return jsonify({'message': 'Access denied'}), 401

            # Session check for authentification
            if user := User.query.filter(getattr(User, field_value) == session_attr).first():
                # if the code has been used already
                if user.verificationCode.checked:
                    cleanup_codes(VC, db)
                    current_app.logger.error(f'Code already verified.')
                    return jsonify({'message': 'Code already verified'}), 400

                # if it has expired
                elif user.verificationCode.expiry < datetime.now():
                    cleanup_codes(VC, db)
                    current_app.logger.error(f'Verification code has already expired.')
                    return jsonify({'message': 'Verification code has already expired'}), 400

                # if they are matching with the user's
                if user_code == session_code and user_code == user.verificationCode.code:
                    user.hashed_password = hash_password(payload.get('password'))
                    user.verificationCode.checked = True
                    db.session.commit()
                    current_app.logger.info(f'Password successfully reset')
                    return jsonify({'message': 'Password successfully reset'}), 200
            else:
                current_app.logger.error(f'Invalid verification code or email address')
                return jsonify({'message': 'Invalid verification code or email address'}), 400
        else:
            current_app.logger.error(f'Invalid verification code or email address')
            return jsonify({'message': 'Invalid verification code or email address'}), 400

    except CheckError as err:
        db.session.rollback()
        current_app.logger.error(err)
        current_app.logger.error(err), err.error_code
    except Exception as err:
        db.session.rollback()
        current_app.logger.error(f'something went wrong: {err}')
        return jsonify({'error': str(err)}), 500