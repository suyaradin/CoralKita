import os
from dotenv import load_dotenv
from flask import Flask, redirect, url_for
from controller.login import login_bp
from controller.register import register_bp
from controller.dashboard import dashboard_bp
from controller.coral import coral_bp
from controller.sst import sst_bp

# Load environment variables from .env file
load_dotenv()

# Create Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")

# Use environment variable for secret key
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Get Mapbox token for templates
MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN')
app.config['MAPBOX_TOKEN'] = MAPBOX_TOKEN  # Make available to all templates

# Register all blueprints
app.register_blueprint(login_bp)
app.register_blueprint(register_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(coral_bp)
app.register_blueprint(sst_bp)

@app.route("/")
def index():
    return redirect(url_for("login.login"))

if __name__ == "__main__":
    print("=" * 50)
    print("CoralKita Server Starting...")
    print("=" * 50)
    print("URL: http://localhost:5000")
    print("Press CTRL+C to stop")
    print("=" * 50)
    app.run(port=5000, debug=True)