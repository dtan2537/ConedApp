from flask import Flask
import os
from board import pages
from flask_bootstrap import Bootstrap

def create_app():
    app = Flask(__name__)

    app.register_blueprint(pages.bp)
    SECRET_KEY = os.urandom(32)
    app.config['SECRET_KEY'] = SECRET_KEY
    # bootstrap = Bootstrap()
    # bootstrap.init_app(app)
    return app