from flask import Flask
import os
import sys

class Config:
    SECRET_KEY = os.urandom(32)
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

app = Flask(__name__, template_folder = resource_path("templates"))  
app.config.from_object(Config)

from board import pages