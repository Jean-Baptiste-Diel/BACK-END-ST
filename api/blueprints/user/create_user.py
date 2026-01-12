from api.utils.utils_func import validate_payload, is_valid_mail_format, tokenize, hash_password
from api.utils.error_class import CheckError
from flask import Blueprint, request, jsonify, current_app
from api.config.model import db, User

create_user_bp = Blueprint('create_user', __name__)

@create_user_bp.route('/create-user', methods=['POST'])
def create_user():
    try:
        payload = request.get_json()
        current_app.logger.info(f"Requête reçue: {payload}")

        required_fields = ['farm_name', 'mail', 'password', 'location', 'phone_number']
        validate_payload(payload, required_fields)
        current_app.logger.info("Payload validé avec succès.")

        if not is_valid_mail_format(payload.get('mail')):
            current_app.logger.warning(f"Format de mail invalide: {payload.get('mail')}")
            return jsonify({'message': 'Invalid Mail format'}), 400

        if not (curr_user := User.query.filter_by(mail=payload.get('mail').strip().lower()).first()):
            user = User(
                farm_name=payload.get('farm_name').strip(),
                mail=payload.get('mail').strip().lower(),
                hash_password=hash_password(payload.get('password').strip()),
                phone_number=payload.get('phone_number').strip(),
                location=payload.get('location').strip()
            )

            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f"Compte créé pour: {user.mail}")

            # création du token
            claims = {'id_culture_type': user.id_culture_type}
            token = tokenize(user.id_user, claims)
            current_app.logger.info(f"Token généré pour {user.mail}: {token}")

            return jsonify({'message': 'Account created successfully.', 'token': token}), 201
        else:
            current_app.logger.warning(f"Compte déjà existant: {curr_user.mail}")
            return jsonify({'message': 'Account already exists.'}), 409

    except CheckError as err:
        db.session.rollback()
        current_app.logger.error(f"CheckError: {str(err)}")
        return jsonify({'message': str(err)}), err.error_code

    except Exception as err:
        db.session.rollback()
        current_app.logger.exception(f"Erreur inattendue: {str(err)}")
        return jsonify({'message': str(err)}), 500
