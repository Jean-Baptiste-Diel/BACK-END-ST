from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError

from api.config.model import User, db


def update(id: int):
    try:
        user = User.query.get(id)
        if not user:
            return jsonify({"error": "Utilisateur introuvable"}), 404
        donnees = request.get_json()
        # Mise à jour des champs
        if 'farm_name' in donnees:
            user.nom = donnees['farm_name']
        if 'phone_number' in donnees:
            user.phone_number = donnees['phone_number'][1:10]
        if 'mail' in donnees:
            # Vérification nouvel email
            if donnees['mail'] != user.mail:
                if user.query.filter_by(mail=donnees['mail']).first():
                    return jsonify({"error": "Email déjà utilisé"}), 409
                user.email = donnees['email']
        db.session.commit()
        return jsonify({"message": "Utilisateur mis à jour avec succès"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "message": "Erreur de base de données",
            "error": e}), 500