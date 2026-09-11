import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from urllib.parse import quote_plus
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv(override=False)

app = Flask(__name__)

# Crear carpeta para los registros de errores
if not os.path.exists("logs"):
    os.mkdir("logs")

# Configurar archivo de logs
file_handler = RotatingFileHandler(
    "logs/auladata.log",
    maxBytes=10240,
    backupCount=3
)

file_handler.setLevel(logging.INFO)

file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s"
    )
)

app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

app.logger.info("AulaData iniciado")

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "clave-temporal")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

if not all([db_host, db_name, db_user, db_password]):
    raise RuntimeError(
        "Faltan variables de configuración de la base de datos."
    )

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://{quote_plus(db_user)}:"
    f"{quote_plus(db_password)}@"
    f"{db_host}:{db_port}/{db_name}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["APP_ENV"] = os.getenv("APP_ENV", "DEV")
app.config["APP_VERSION"] = os.getenv("APP_VERSION", "0.1.0")
app.config["APP_COMMIT"] = os.getenv("APP_COMMIT", "local")

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = "login"


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="consulta")


class Aula(db.Model):
    __tablename__ = "aulas"

    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    edificio = db.Column(db.String(100), nullable=False)
    capacidad = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.String(30), nullable=False, default="activa")
    activo = db.Column(db.Boolean, nullable=False, default=True)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


def solo_admin():
    if current_user.role != "admin":
        abort(403)


@app.route("/")
def inicio():
    if current_user.is_authenticated:
        return redirect(url_for("listar_aulas"))

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        usuario = Usuario.query.filter_by(username=username).first()

        if usuario and check_password_hash(usuario.password, password):
            login_user(usuario)
            return redirect(url_for("listar_aulas"))

        flash("Usuario o contraseña incorrectos.")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/aulas")
@login_required
def listar_aulas():
    aulas = Aula.query.filter_by(activo=True).order_by(Aula.clave).all()

    return render_template("aulas.html", aulas=aulas)


@app.route("/aulas/nueva", methods=["GET", "POST"])
@login_required
def nueva_aula():
    solo_admin()

    if request.method == "POST":
        clave = request.form["clave"].strip()
        nombre = request.form["nombre"].strip()
        edificio = request.form["edificio"].strip()
        tipo = request.form["tipo"].strip()
        estado = request.form["estado"]

        if not clave or not nombre or not edificio or not tipo or not estado:
            flash("Todos los campos son obligatorios.")
            return render_template("formulario.html", aula=None)

        try:
            capacidad = int(request.form["capacidad"])
        except ValueError:
            flash("La capacidad debe ser un número.")
            return render_template("formulario.html", aula=None)

        if capacidad <= 0:
            flash("La capacidad debe ser mayor que cero.")
            return render_template("formulario.html", aula=None)

        existente = Aula.query.filter_by(clave=clave).first()

        if existente:
            flash("La clave del aula ya existe.")
            return render_template("formulario.html", aula=None)

        aula = Aula(
            clave=clave,
            nombre=nombre,
            edificio=edificio,
            capacidad=capacidad,
            tipo=tipo,
            estado=estado
        )

        db.session.add(aula)
        db.session.commit()

        flash("Aula registrada correctamente.")
        return redirect(url_for("listar_aulas"))

    return render_template("formulario.html", aula=None)


@app.route("/aulas/<int:id>/editar", methods=["GET", "POST"])
@login_required
def editar_aula(id):
    solo_admin()

    aula = db.get_or_404(Aula, id)

    if request.method == "POST":
        clave = request.form["clave"].strip()
        nombre = request.form["nombre"].strip()
        edificio = request.form["edificio"].strip()
        tipo = request.form["tipo"].strip()
        estado = request.form["estado"].strip()

        if not clave or not nombre or not edificio or not tipo or not estado:
            flash("Todos los campos son obligatorios.")
            return render_template("formulario.html", aula=aula)


        existente = Aula.query.filter(
            Aula.clave == clave,
            Aula.id != aula.id
        ).first()

        if existente:
            flash("La clave ya pertenece a otra aula.")
            return render_template("formulario.html", aula=aula)

        try:
            capacidad = int(request.form["capacidad"])
        except ValueError:
            flash("La capacidad debe ser numérica.")
            return render_template("formulario.html", aula=aula)

        if capacidad <= 0:
            flash("La capacidad debe ser mayor que cero.")
            return render_template("formulario.html", aula=aula)

        aula.clave = clave
        aula.nombre = nombre
        aula.edificio = edificio
        aula.capacidad = capacidad
        aula.tipo = tipo
        aula.estado = estado

        db.session.commit()

        flash("Aula actualizada correctamente.")
        return redirect(url_for("listar_aulas"))

    return render_template("formulario.html", aula=aula)


@app.route("/aulas/<int:id>/eliminar", methods=["POST"])
@login_required
def eliminar_aula(id):
    solo_admin()

    aula = db.get_or_404(Aula, id)

    aula.activo = False
    db.session.commit()

    flash("Aula dada de baja correctamente.")
    return redirect(url_for("listar_aulas"))


@app.route("/health")
def health():
    return {
        "status": "ok",
        "application": "AulaData",
        "environment": os.getenv("APP_ENV", "DEV"),
        "version": os.getenv("APP_VERSION", "0.1.0"),
        "commit": os.getenv("APP_COMMIT", "local")
    }


@app.cli.command("crear-usuarios")
def crear_usuarios():

    admin_password = os.getenv("ADMIN_INITIAL_PASSWORD")
    consulta_password = os.getenv("CONSULTA_INITIAL_PASSWORD")

    if not admin_password or not consulta_password:
        raise RuntimeError(
            "Faltan ADMIN_INITIAL_PASSWORD o CONSULTA_INITIAL_PASSWORD."
        )

    if not Usuario.query.filter_by(username="admin").first():
        admin = Usuario(
            username="admin",
            password=generate_password_hash(admin_password),
            role="admin"
        )

        db.session.add(admin)

    if not Usuario.query.filter_by(username="consulta").first():
        consulta = Usuario(
            username="consulta",
            password=generate_password_hash(consulta_password),
            role="consulta"
        )

        db.session.add(consulta)

    db.session.commit()

    print("Usuarios iniciales verificados/creados correctamente.")

    if __name__ == "__main__":
        app.run(
            debug=True,
            host="0.0.0.0",
            port=5000
        )