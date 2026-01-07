from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db: SQLAlchemy = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    id_user = db.Column(db.Integer, primary_key=True)
    id_culture_type = db.Column(db.Integer, nullable=True)
    farm_name = db.Column(db.String(200), nullable=False)
    mail = db.Column(db.String(100), nullable=False, unique=True)
    hashed_password = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False, unique=True)

    def __init__(self, farm_name:str, mail:str, hash_password:str, location:str, phone_number:str):
        self.farm_name = farm_name
        self.mail = mail
        self.hashed_password = hash_password
        self.location = location
        self.phone_number = f'+221{phone_number}'

    def serialize(self):
        return {
            "farm_name": self.farm_name,
            "mail": self.mail,
            "id_culture_type": self.id_culture_type,
            "location": self.location,
            "phone_number": self.phone_number
        }

class VerificationCode(db.Model):
    __tablename__ = 'verificationCode'
    id_code = db.Column(db.Integer, primary_key=True)
    mail = db.Column(db.String(100), nullable=False, unique=True)
    code = db.Column(db.Integer, nullable=True)
    checked = db.Column(db.Boolean, nullable=False, default=False)
    expiry = db.Column(db.DateTime, nullable=True)

    def __init__(self, code:int, mail:str, expiry:datetime):
        self.code = code
        self.mail = mail
        self.expiry = expiry
