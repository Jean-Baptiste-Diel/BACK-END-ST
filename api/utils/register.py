from api.blueprints.camera.camera import bp_camera
from api.blueprints.user.create_user import create_user_bp
from api.blueprints.auth.login import login_bp
from api.utils.utils_func import CheckError

BLUEPRINTS = [
    create_user_bp,
    login_bp,
]

def register_routes(app):
    try:
        for bp in BLUEPRINTS:
            app.register_blueprint(bp)
    except Exception as err:
        raise CheckError(f'Failed to register blueprint: {err}', 500)