import datetime
import re

import fakeredis
import pytest
from flask_security import SQLAlchemySessionUserDatastore, hash_password
from sqlalchemy import create_engine
from sqlalchemy_utils import create_database, database_exists, drop_database

from passari_web_ui.app import create_app
from passari_web_ui.db import db
from passari_web_ui.db.models import Base as AuthBase
from passari_web_ui.db.models import Role, User
from passari_workflow.config import CONFIG as WORKFLOW_CONFIG
from passari_workflow.db import DBSession
from passari_workflow.db.connection import connect_db, get_connection_uri
from passari_workflow.db.models import Base, MuseumObject, MuseumPackage


@pytest.fixture(scope="function", autouse=True)
def redis(monkeypatch):
    """
    Fixture for a fake Redis server
    """
    server = fakeredis.FakeServer()
    conn = fakeredis.FakeStrictRedis(server=server)

    monkeypatch.setattr(
        "passari_workflow.queue.queues.get_redis_connection",
        lambda: conn
    )
    monkeypatch.setattr(
        "passari_web_ui.api.views.get_redis_connection",
        lambda: conn
    )
    monkeypatch.setattr(
        "passari_workflow.heartbeat.get_redis_connection",
        lambda: conn
    )

    yield conn


@pytest.fixture(scope="session")
def database(request):
    """
    Fixture for starting an ephemeral database instance for the duration
    of the test suite
    """
    db_url = get_connection_uri(default="postgresql:///passari")
    test_db_url = re.sub(r"^([^?]*[^/?])(/?[?]?.*)$", r"\1_test\2", db_url)
    assert "_test" in test_db_url
    if database_exists(test_db_url):
        drop_database(test_db_url)
    create_database(test_db_url)
    yield create_engine(test_db_url)


@pytest.fixture(scope="function")
def engine(database, monkeypatch):
    """
    Fixture for creating an empty database on each test run
    """
    monkeypatch.setitem(WORKFLOW_CONFIG["db"], "url", database.url)
    for item in ("user", "password", "host", "port", "name"):
        monkeypatch.setitem(WORKFLOW_CONFIG["db"], item, "")

    engine = connect_db()

    # pg_trgm extension must exist
    engine.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    Base.metadata.create_all(engine)
    AuthBase.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    AuthBase.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def session(engine, database):
    """
    Fixture for a database session object for running database queries
    in test functions
    """
    conn = engine.connect()
    session = DBSession(bind=conn)

    yield session

    session.close()
    conn.close()


@pytest.fixture(scope="function")
def app(session, database, engine):
    """
    Test web application fixture
    """
    app = create_app()
    app.config["DEBUG"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = engine.url
    app.config["WTF_CSRF_ENABLED"] = False

    yield app


@pytest.fixture(scope="function")
def client(app):
    """
    Test web application client fixture for making requests
    """
    with app.test_client() as client:
        yield client


@pytest.fixture(scope="function")
def user(app, client):
    """
    Fixture for an active logged-in user
    """
    with app.app_context():
        user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
        user = user_datastore.create_user(
            email="test@test.com", password=hash_password("testpassword")
        )
        user_datastore.activate_user(user)

        client.post(
            "/web-ui/login",
            data={"email": "test@test.com", "password": "testpassword"},
            follow_redirects=True
        )

    yield user


PLACEHOLDER_DATE = datetime.datetime(
    2019, 1, 2, 10, 0, 0, 0, tzinfo=datetime.timezone.utc
)


@pytest.fixture(scope="function")
def museum_object_factory(session):
    """
    Factory fixture for creating MuseumObject entries
    """
    def func(**kwargs):
        if "created_date" not in kwargs:
            kwargs["created_date"] = PLACEHOLDER_DATE
        if "modified_date" not in kwargs:
            kwargs["modified_date"] = PLACEHOLDER_DATE

        museum_object = MuseumObject(**kwargs)
        session.add(museum_object)
        session.commit()

        return museum_object

    return func


@pytest.fixture(scope="function")
def museum_package_factory(session):
    """
    Factory fixture for creating MuseumPackage entries
    """
    def func(**kwargs):
        museum_package = MuseumPackage(**kwargs)
        session.add(museum_package)
        session.commit()

        return museum_package

    return func
