from flask import Blueprint, jsonify, request, current_app, session
from api.config.model import db, VerificationCode as VC, User, VerificationCode
from datetime import datetime

from api.utils.error_class import CheckError
from api.utils.utils_func import validate_payload, is_valid_mail_format, generate_new_code, send_verification_code

forgot_password_bp = Blueprint('forgot_password', __name__)

@forgot_password_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        fields = ['mail', 'phone_number']
        payload = request.get_json()
        current_field = [field for field in fields if field in payload]
        if len(current_field) == 1:
            current_app.logger.info(f'{current_field[0]} provided')
            validate_payload(payload, current_field)
            field_value = current_field[0]


            if field_value == fields[1]:
                if not is_valid_mail_format(payload.get('field_value')):
                    current_app.logger.info(f'{payload.get('field_value')} is not a valid mail format')
                    return jsonify({'message': f'{payload.get('field_value')} is not a valid mail format'}), 400
            # Should implement phone verification

            if not (user := User.query.filter(getattr(User, field_value)) == payload.get(field_value).first()):
                  current_app.logger.info(f'Please enter valid mail or phone number')
                  return jsonify({"message": "Please enter a valid mail mail or phone number"}), 401

            # Storing user data (phone or mail) in session temporarily
            session[field_value] = payload.get(field_value)
            code = generate_new_code(user.id_user, VC, db)

            session['reset_code'] = code # storing the code in the session
            send_verification_code(code, field_value, getattr(user, field_value))

            current_app.logger.info(f'Verification code has been sent successfully to you {field_value}')
            return jsonify({'message': f'Verification code has been sent successfully to you {field_value}'}), 200

    except CheckError as e:
        current_app.logger.error(e), e.error_code
    except Exception as e:
        return jsonify({'message': str(e)}), 500