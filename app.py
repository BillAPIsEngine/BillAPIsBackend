from flask import Flask
from config import Config
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.logs import logs_bp
from routes.consumer import consumer_bp
from routes.api_usage import api_usage_bp
from routes.billing import billing_bp
from logger import setup_logger
from routes.auth import auth
from routes.admin import admin
from routes.consumer import consumer

app = Flask(__name__)
app.config.from_object(Config)

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(logs_bp)
app.register_blueprint(consumer_bp)
app.register_blueprint(api_usage_bp)
app.register_blueprint(billing_bp)
setup_logger()
app.register_blueprint(auth, url_prefix="/auth")
app.register_blueprint(admin, url_prefix="/admin")
app.register_blueprint(consumer, url_prefix="/user")

if __name__ == '__main__':
    app.run(debug=True)
