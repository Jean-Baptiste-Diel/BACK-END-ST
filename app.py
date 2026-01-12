import os
from flask import Flask
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from api.config.model import db
from api.extension.cors import init_cors
from api.extension.logging import init_logging
from api.utils.register import register_routes
from api.extension.mail_sms import mail

load_dotenv()
migrate = Migrate()

def create_app(test_config=None):
    sotilma_app = Flask(__name__)

    sotilma_app.config.from_object("api.config.app_config.Config") # .env variable configuration
    init_logging(sotilma_app)
    init_cors(sotilma_app)
    mail.init_app(sotilma_app)
    jtw_manager = JWTManager(sotilma_app)
    migrate.init_app(app=sotilma_app, db=db)
    db.init_app(app=sotilma_app)
    register_routes(sotilma_app) # Registering the routes

    if test_config is not None:
        sotilma_app.config.update(test_config)
    return sotilma_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT")))
