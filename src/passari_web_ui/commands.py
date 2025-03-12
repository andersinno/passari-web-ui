import click
from flask.cli import with_appcontext
from sqlalchemy.sql.schema import MetaData

from passari_web_ui.db.models import Base
from passari_web_ui.db import db


@click.command(
    help="""
Initialize database for Web UI.

Creates all necessary database tables for the Web UI.
"""
)
@with_appcontext
def init_db():
    _create_database_tables()


def _create_database_tables():
    if not _has_tables_to_create(Base.metadata):
        print("Database already initialized")
        return

    print("Creating tables...")
    Base.metadata.create_all(db.engine)
    print("Done")


def _has_tables_to_create(metadata: MetaData) -> bool:
    with db.engine.begin() as conn:
        for table in metadata.sorted_tables:
            if not db.engine.dialect.has_table(conn, table):
                return True
    return False


@click.command(help="Deprecated alias for 'init_db'")
@with_appcontext
def create_db():
    _create_database_tables()
