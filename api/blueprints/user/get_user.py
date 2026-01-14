from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError

from api.config.model import db, User

def get_user(id):
    try:
        user = db.session.get(User, id)
        if not user:
            return jsonify({"message": "utilisateur introuvable"}), 404
        return jsonify(user.serialize()), 200
    except SQLAlchemyError as e:
        return jsonify({"message": str(e)}), 500