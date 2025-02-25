import os.path

from sqlmodel import create_engine


# sqlite_filename = "cowpoke.db"
sqlite_filename = "cowpoke.sqlite"
database_directory = "databases"
sqlite_filepath = os.path.join(os.path.pardir, database_directory, sqlite_filename)

sqlite_url = f"sqlite:///{sqlite_filepath}"

connect_args = {"check_same_thread": False}
engine = create_engine(url=sqlite_url, connect_args=connect_args)

sqlite_filepath_for_alembic = os.path.join(database_directory, sqlite_filename)
sqlite_url_for_alembic = f"sqlite:///{sqlite_filepath_for_alembic}"
