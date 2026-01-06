from api.utils.utils_func import validate_payload, is_valid_mail_format, tokenize
from api.utils.error_class import CheckError
from flask import Blueprint, request, jsonify
from api.config.model import db, User



create_user_bp = Blueprint('create_user', __name__)

@create_user_bp.route('/create-user', methods=['POST'])
def create_user():
    try:
        payload = request.get_json()
        required_fields = ['farm_name', 'mail', 'password']
        validate_payload(payload, required_fields)

        if not is_valid_mail_format(payload.get('mail')):
            return jsonify({'message': 'Invalid Mail format'}), 400

        if not User.query.filter_by(mail=payload.get('mail').strip().lower()).first():
            user = User(farm_name = payload.get('farm_name'),
                        mail = payload.get('mail').strip().lower(),
                        password=payload.get('password'))

            db.session.add(user)
            db.session.commit()

            # creating a token with the necessary claims(informations)
            claims = {'id_culture_type': user.id_culture_type}
            token = tokenize(user.id_user, claims)
            return jsonify({'message': 'Account created successfully.',
                            'token': token}), 201

        else:
            return jsonify({'message': 'Account already exists.'}), 409
    except CheckError as err:
        db.session.rollback()
        return jsonify({'message': str(err)}), err.error_code
    except Exception as err:
        db.session.rollback()
        return jsonify({'message': str(err)}), 500