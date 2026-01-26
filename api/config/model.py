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

    verificationCode = db.relationship('VerificationCode', back_populates='user', uselist=False)

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
    id_user = db.Column(db.Integer, db.ForeignKey('user.id_user'), nullable=False)
    code = db.Column(db.Integer, nullable=True)
    checked = db.Column(db.Boolean, nullable=False, default=False)
    expiry = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', back_populates='verificationCode')

    def __init__(self, code:int, id_user:int, expiry:datetime):
        self.code = code
        self.id_user = id_user
        self.expiry = expiry

# Affaire a suivre
class Alarm(db.Model):
    __tablename__ = "alarms"

    id = db.Column(db.Integer, primary_key=True)

    device_id = db.Column(db.String(64), nullable=False, index=True)
    channel_id = db.Column(db.String(8), default="0")

    imou_alarm_id = db.Column(db.String(64), unique=True, nullable=False)

    type = db.Column(db.String(32), nullable=False)
    label_type = db.Column(db.String(32))

    alarm_time = db.Column(db.DateTime, nullable=False, index=True)

    image_url = db.Column(db.Text)
    video_url = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<Alarm {self.device_id} {self.type} {self.alarm_time}>"