# AulaData

AulaData es un módulo web para la gestión de aulas desarrollado como parte de la Práctica Integradora de la materia Infraestructura de Servicios Web.

## Tecnologías

- Python 3.11
- Flask
- PostgreSQL
- SQLAlchemy
- Flask-Login
- Flask-Migrate
- Pytest

## Funcionalidades

El módulo permite:

- Inicio y cierre de sesión.
- Gestión de aulas mediante operaciones CRUD.
- Registro de clave, nombre, edificio, capacidad, tipo y estado.
- Validación de claves únicas.
- Validación de capacidad mayor a cero.
- Edición de aulas.
- Baja lógica de aulas.
- Persistencia en PostgreSQL.
- Control de acceso mediante roles.
- Endpoint de salud `/health`.

## Roles

### Administrador

Puede:

- Consultar aulas.
- Registrar aulas.
- Editar aulas.
- Dar de baja aulas.

### Consulta

Puede:

- Consultar las aulas registradas.

No puede crear, editar ni dar de baja aulas.

## Base de datos

El proyecto utiliza PostgreSQL.

El esquema de la base de datos se administra mediante Flask-Migrate y las migraciones se encuentran en:

`migrations/`

Las credenciales y variables sensibles se almacenan mediante variables de entorno y no se incluyen en el repositorio.

Para configurar el proyecto se debe crear un archivo `.env` tomando como referencia `.env.example`.

## Instalación

Crear el entorno virtual:

```powershell
python -m venv venv

Activarlo en Windows:

```powershell
.\venv\Scripts\Activate.ps1

Instalar dependencias:

```powershell
pip install -r requirements.txt

Aplicar las migraciones:

```powershell
flask --app app db upgrade

Crear los usuarios iniciales:

```powershell
flask --app app crear-usuarios

Ejecutar la aplicación:

```powershell
python app.py

## Pruebas

Para ejecutar las pruebas automatizadas:

```powershell
pytest -v

Actualmente el proyecto cuenta con 9 pruebas automatizadas para autenticación, autorización, CRUD, validaciones, baja lógica y healthcheck.

##Healthcheck

La aplicación proporciona

/health

Este endpoint muestra el estado de la aplicación, ambiente, versión y commit desplegado.

##Ambientes

El proyecto está diseñado para desplegarse en tres ambientes:

    -DEV
    -QA
    -PROD

Cada ambiente contará con su propia configuración y base de datos.

