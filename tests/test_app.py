import os
from dotenv import load_dotenv

load_dotenv()

test_admin_password = os.getenv("TEST_ADMIN_PASSWORD")
test_consulta_password = os.getenv("TEST_CONSULTA_PASSWORD")

if not test_admin_password or not test_consulta_password:
    raise RuntimeError(
        "Faltan TEST_ADMIN_PASSWORD o TEST_CONSULTA_PASSWORD."
    )

test_host = os.getenv("TEST_DB_HOST")
test_port = os.getenv("TEST_DB_PORT", "5432")
test_name = os.getenv("TEST_DB_NAME")
test_user = os.getenv("TEST_DB_USER")
test_password = os.getenv("TEST_DB_PASSWORD")

if not all([test_host, test_name, test_user, test_password]):
    raise RuntimeError("Faltan variables de base de datos de TEST.")

os.environ["DB_HOST"] = test_host
os.environ["DB_PORT"] = test_port
os.environ["DB_NAME"] = test_name
os.environ["DB_USER"] = test_user
os.environ["DB_PASSWORD"] = test_password
os.environ["APP_ENV"] = "TEST"


import pytest

from app import app, db, Usuario, Aula
from werkzeug.security import generate_password_hash


@pytest.fixture
def cliente():
    app.config["TESTING"] = True

    with app.app_context():

        # Protección para evitar borrar accidentalmente DEV o PROD
        url_bd = str(db.engine.url)

        if db.engine.url.database != "auladata_test":
            raise RuntimeError(
                f"Las pruebas intentaron usar una BD incorrecta: {url_bd}"
            )

        # Solo se destruyen tablas de la BD de pruebas
        db.drop_all()
        db.create_all()

        admin = Usuario(
            username="admin_test",
            password=generate_password_hash(test_admin_password),
            role="admin"
        )

        consulta = Usuario(
            username="consulta_test",
            password=generate_password_hash(test_consulta_password),
            role="consulta"
        )

        db.session.add(admin)
        db.session.add(consulta)
        db.session.commit()

        yield app.test_client()

        db.session.remove()
        db.drop_all()

def login(cliente, usuario, password):
    return cliente.post(
        "/login",
        data={
            "username": usuario,
            "password": password
        },
        follow_redirects=True
    )


def test_health(cliente):
    respuesta = cliente.get("/health")

    assert respuesta.status_code == 200
    assert respuesta.json["status"] == "ok"


def test_login_correcto(cliente):
    respuesta = login(
        cliente,
        "admin_test",
        test_admin_password
    )

    assert respuesta.status_code == 200
    assert b"Gesti" in respuesta.data


def test_login_incorrecto(cliente):
    respuesta = login(
        cliente,
        "admin_test",
        "Incorrecta"
    )

    assert b"incorrectos" in respuesta.data


def test_crear_aula(cliente):
    login(cliente, "admin_test", test_admin_password)

    respuesta = cliente.post(
        "/aulas/nueva",
        data={
            "clave": "A101",
            "nombre": "Aula Sistemas",
            "edificio": "A",
            "capacidad": "30",
            "tipo": "Aula",
            "estado": "activa"
        },
        follow_redirects=True
    )

    assert respuesta.status_code == 200

    with app.app_context():
        aula = Aula.query.filter_by(clave="A101").first()
        assert aula is not None


def test_clave_duplicada(cliente):
    login(cliente, "admin_test", test_admin_password)

    datos = {
        "clave": "A101",
        "nombre": "Aula Sistemas",
        "edificio": "A",
        "capacidad": "30",
        "tipo": "Aula",
        "estado": "activa"
    }

    cliente.post("/aulas/nueva", data=datos)

    respuesta = cliente.post(
        "/aulas/nueva",
        data=datos,
        follow_redirects=True
    )

    assert b"ya existe" in respuesta.data


def test_capacidad_invalida(cliente):
    login(cliente, "admin_test", test_admin_password)

    respuesta = cliente.post(
        "/aulas/nueva",
        data={
            "clave": "B101",
            "nombre": "Aula Prueba",
            "edificio": "B",
            "capacidad": "0",
            "tipo": "Aula",
            "estado": "activa"
        },
        follow_redirects=True
    )

    assert b"mayor que cero" in respuesta.data


def test_editar_aula(cliente):
    login(cliente, "admin_test", test_admin_password)

    cliente.post(
        "/aulas/nueva",
        data={
            "clave": "A102",
            "nombre": "Aula Inicial",
            "edificio": "A",
            "capacidad": "20",
            "tipo": "Aula",
            "estado": "activa"
        }
    )

    with app.app_context():
        aula = Aula.query.filter_by(clave="A102").first()
        aula_id = aula.id

    cliente.post(
        f"/aulas/{aula_id}/editar",
        data={
            "clave": "A102",
            "nombre": "Aula Editada",
            "edificio": "A",
            "capacidad": "40",
            "tipo": "Laboratorio",
            "estado": "activa"
        },
        follow_redirects=True
    )

    with app.app_context():
        aula = db.session.get(Aula, aula_id)

        assert aula.nombre == "Aula Editada"
        assert aula.capacidad == 40


def test_baja_logica(cliente):
    login(cliente, "admin_test", test_admin_password)

    cliente.post(
        "/aulas/nueva",
        data={
            "clave": "A103",
            "nombre": "Aula Baja",
            "edificio": "A",
            "capacidad": "25",
            "tipo": "Aula",
            "estado": "activa"
        }
    )

    with app.app_context():
        aula = Aula.query.filter_by(clave="A103").first()
        aula_id = aula.id

    cliente.post(
        f"/aulas/{aula_id}/eliminar",
        follow_redirects=True
    )

    with app.app_context():
        aula = db.session.get(Aula, aula_id)

        assert aula is not None
        assert aula.activo is False


def test_usuario_consulta_no_puede_crear(cliente):
    login(
        cliente,
        "consulta_test",
        test_consulta_password
    )

    respuesta = cliente.get("/aulas/nueva")

    assert respuesta.status_code == 403

def test_usuario_consulta_no_puede_editar(cliente):
    login(
        cliente,
        "admin_test",
        test_admin_password
    )

    cliente.post(
        "/aulas/nueva",
        data={
            "clave": "A104",
            "nombre": "Aula Protegida",
            "edificio": "A",
            "capacidad": "35",
            "tipo": "Aula",
            "estado": "activa"
        }
    )

    with app.app_context():
        aula = Aula.query.filter_by(clave="A104").first()
        aula_id = aula.id

    cliente.get("/logout")

    login(
        cliente,
        "consulta_test",
        test_consulta_password
    )

    respuesta = cliente.get(
        f"/aulas/{aula_id}/editar"
    )

    assert respuesta.status_code == 403

def test_usuario_consulta_no_puede_eliminar(cliente):
    login(
        cliente,
        "admin_test",
        test_admin_password
    )

    cliente.post(
        "/aulas/nueva",
        data={
            "clave": "A105",
            "nombre": "Aula Protegida",
            "edificio": "B",
            "capacidad": "25",
            "tipo": "Aula",
            "estado": "activa"
        }
    )

    with app.app_context():
        aula = Aula.query.filter_by(clave="A105").first()
        aula_id = aula.id

    cliente.get("/logout")

    login(
        cliente,
        "consulta_test",
        test_consulta_password
    )

    respuesta = cliente.post(
        f"/aulas/{aula_id}/eliminar"
    )

    assert respuesta.status_code == 403

def test_campos_obligatorios(cliente):
    login(
        cliente,
        "admin_test",
        test_admin_password
    )

    respuesta = cliente.post(
        "/aulas/nueva",
        data={
            "clave": "",
            "nombre": "",
            "edificio": "",
            "capacidad": "20",
            "tipo": "",
            "estado": ""
        },
        follow_redirects=True
    )

    assert respuesta.status_code == 200
    assert b"obligatorios" in respuesta.data

