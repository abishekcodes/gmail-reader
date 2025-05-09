import os
from pathlib import Path
from typing import Any

import pytest

from email_reader.services.gmail import MockGmailService


def pytest_configure(config: Any) -> None:
    current_dir = Path(__file__).parent
    os.environ['DB_USE_INMEMORY'] = '1'
    os.environ['PY_EMAIL_FILE_PATH'] = (current_dir / Path("static/test_emails.csv")).as_posix()
    os.environ['PY_RULES_FILE_PATH'] = (current_dir / Path("static/rules.json")).as_posix()


@pytest.fixture(scope='session')
def service() -> MockGmailService:
    return MockGmailService.create(None)
