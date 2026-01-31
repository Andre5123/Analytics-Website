from flask import Flask
from flask_session import Session
from routes.auth_routes import auth_bp
from routes.api_routes import api_bp
from routes.page_routes import page_bp

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)
app.register_blueprint(page_bp)

if __name__ == "__main__":
    app.run(debug=True)
