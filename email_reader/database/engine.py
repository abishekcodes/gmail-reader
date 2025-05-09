from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker
from email_reader.database.base import Base
import email_reader.database.tables  # noqa


def get_engine():

    engine_suffix = '/:memory:'

    if not os.getenv('DB_USE_INMEMORY', '') == '1':
        db_file = Path.home() / Path(".email_reader/emails.sqlite")
        if not db_file.parent.is_dir():
            os.mkdir(db_file.parent)
        engine_suffix = f'/{db_file}'

    engine = create_engine(f"sqlite://{engine_suffix}", echo=True)

    Base.metadata.create_all(bind=engine)

    return engine


SessionFactory = sessionmaker(bind=get_engine(), future=True)
