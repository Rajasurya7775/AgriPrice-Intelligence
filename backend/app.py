# app.py
# Flask application factory: registers all route blueprints and serves
# the frontend static files from the ../frontend directory.

import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, send_from_directory
from flask_cors import CORS

from .routes.prices          import prices_bp
from .routes.analytics_routes import analytics_bp
from .routes.seasonal        import seasonal_bp
from .routes.weather         import weather_bp
from .routes.advisory        import advisory_bp

app = Flask(__name__, static_folder="../frontend")
CORS(app)

app.register_blueprint(prices_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(seasonal_bp)
app.register_blueprint(weather_bp)
app.register_blueprint(advisory_bp)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(app.static_folder, filename)


@app.route("/run-fetch")
def run_fetch():
    """
    Cron-job.org webhook endpoint.
    Triggers the Agmarknet ETL pipeline and refreshes today's prices.
    """
    try:
        try:
            from .fetch_prices import fetch_and_store
        except ImportError:
            from fetch_prices import fetch_and_store
        fetch_and_store()
        return {"status": "ok", "message": "Prices fetched and stored."}, 200
    except Exception as exc:
        return {"status": "error", "message": str(exc)}, 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
