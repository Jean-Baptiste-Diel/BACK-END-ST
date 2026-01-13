import os
from flask import Flask
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager

from api.blueprints.camera.b import bd_c
from api.blueprints.camera.camera import bp_camera
from api.config.model import db
from api.extension.cors import init_cors
from api.extension.logging import init_logging
from api.utils.register import register_routes

load_dotenv()
migrate = Migrate()

def create_app(test_config=None):
    app = Flask(__name__)

    app.config.from_object("api.config.app_config.Config") # .env variable configuration
    init_logging(app)
    init_cors(app)
    jtw_manager = JWTManager(app)
    migrate.init_app(app=app, db=db)
    db.init_app(app=app)
    register_routes(app)
    app.register_blueprint(bp_camera)
    app.register_blueprint(bd_c)
    if test_config is not None:
        app.config.update(test_config)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT")))
