import eventlet
eventlet.monkey_patch()

import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.infrastructure.extensions import db, socketio
from app.infrastructure.config import DevelopmentConfig, ProductionConfig

config_class = ProductionConfig if os.environ.get('FLASK_ENV') == 'production' else DevelopmentConfig
app = create_app(config_class)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host='0.0.0.0', debug=app.config['DEBUG'], port=5500)
