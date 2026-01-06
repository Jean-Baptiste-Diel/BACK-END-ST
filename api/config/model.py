from flask_sqlalchemy import SQLAlchemy
from api.utils.utils_func import hash_password

db: SQLAlchemy = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    id_user = db.Column(db.Integer, primary_key=True)
    id_culture_type = db.Column(db.Integer, nullable=True)
    farm_name = db.Column(db.String(200), nullable=False)
    mail = db.Column(db.String(100), nullable=False, unique=True)
    hashed_password = db.Column(db.String(200), nullable=False)

    def __init__(self, farm_name:str, mail:str, password:str):
        self.farm_name = farm_name
        self.mail = mail
        self.hashed_password = hash_password(password)

    def serialize(self):
        return {
            "farm_name": self.farm_name,
            "mail": self.mail,
            "id_culture_type": self.culture_type.name
        }