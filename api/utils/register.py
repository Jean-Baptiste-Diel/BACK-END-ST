from api.blueprints.auth.forgot_password import forgot_password_bp
from api.blueprints.camera.camera import camera_bp
from api.blueprints.camera.alarme import alarme_bp
from api.blueprints.camera.operation import operate_bp
from api.blueprints.camera.detection_mouvement import detection_bp
from api.blueprints.camera.storage import storage_bp
from api.blueprints.camera.video import video_bp
from api.blueprints.meteo.bp_meteo import bp_meteo
from api.blueprints.user.create_user import create_user_bp
from api.blueprints.auth.login import login_bp
from api.utils.utils_func import CheckError

BLUEPRINTS = [
    create_user_bp,
    login_bp,
    camera_bp,
    video_bp,
    operate_bp,
    bp_meteo,
    alarme_bp,
    detection_bp,
    storage_bp,
    forgot_password_bp
]

def register_routes(app):
    try:
        for bp in BLUEPRINTS:
            app.register_blueprint(bp)
    except Exception as err:
        raise CheckError(f'Failed to register blueprint: {err}', 500)