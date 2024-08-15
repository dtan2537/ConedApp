from flaskwebgui import FlaskUI
from board import app

if __name__ == "__main__":
    ui = FlaskUI(app=app, server="flask") 
    ui.run()
    # app.run()