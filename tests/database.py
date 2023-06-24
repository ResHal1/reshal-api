from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from reshal_api.config import DatabaseSettings

db_config = DatabaseSettings()
db_config.DRIVER = "psycopg2"

engine = create_engine(db_config.url)
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
scoped_session_local = scoped_session(session_local)
