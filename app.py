from flask import Flask
from flask_migrate import Migrate

from config import Config
from database.db import db
from models import (
    Customer,
    Transaction,
    PaymentAttempt,
    RecoveryAction,
    RecoveryOutcome,
    AuditLog,
)
from routes.routes import register_routes


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

register_routes(app)


if __name__ == "__main__":
    app.run(debug=True)