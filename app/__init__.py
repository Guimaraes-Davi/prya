from flask import Flask


def criar_app():
    app = Flask(__name__, template_folder="../templates")

    from .routes import rotas
    app.register_blueprint(rotas)

    return app
