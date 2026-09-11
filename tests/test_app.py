import os

# IMPORTANTE:
# Las pruebas siempre deben usar una base separada de DEV.
os.environ["DATABASE_URL"] = (
    "postgresql://auladata_user:AulaData123@localhost:5432/auladata_test"
)
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

        if "auladata_test" not in url_bd:
            raise RuntimeError(
                f"Las pruebas intentaron usar una BD incorrecta: {url_bd}"
            )

        # Solo se destruyen tablas de la BD de pruebas
        db.drop_all()
        db.create_all()

        admin = Usuario(
            username="admin_test",
            password=generate_password_hash("Admin123"),
            role="admin"
        )

        consulta = Usuario(
            username="consulta_test",
            password=generate_password_hash("Consulta123"),
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
        "Admin123"
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
    login(cliente, "admin_test", "Admin123")

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
    login(cliente, "admin_test", "Admin123")

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
    login(cliente, "admin_test", "Admin123")

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
    login(cliente, "admin_test", "Admin123")

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
    login(cliente, "admin_test", "Admin123")

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
        "Consulta123"
    )

    respuesta = cliente.get("/aulas/nueva")

    assert respuesta.status_code == 403
