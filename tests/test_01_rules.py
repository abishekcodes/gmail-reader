import datetime
import io
import re
from contextlib import redirect_stdout
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import cast

import pytest
from pydantic_core import ValidationError

from email_reader.loader import load_emails
from email_reader.logics.filters import Rules
from email_reader.manager import process_emails
from email_reader.database.tables.email import Email, MailBox
from email_reader.database.engine import SessionFactory
from email_reader.services.gmail import MockGmailService
from .utils.paths import RULES_FILE

# from .utils.generate_fake_emails_and_rules import RULES_FILE


def get_static_dir():
    return Path(__file__).parent


def test_001_invalid_rules() -> None:

    match_rules_invalid_action = re.compile("Value error, `folder` must be provided when `type` is MoveMessage")
    with pytest.raises(ValidationError, match=match_rules_invalid_action):
        Rules.from_file(
            get_static_dir() / Path('static/invalid/rules-invalid-action.json')
        )

    match_rules_invalid_predicate = re.compile("Filter Condition GreaterThan not support for String")
    with pytest.raises(ValidationError, match=match_rules_invalid_predicate):
        Rules.from_file(
            get_static_dir() / Path('static/invalid/rules-invalid-predicate.json')
        )

    match_rules_invalid_schema = re.compile("Field required")
    with pytest.raises(ValidationError, match=match_rules_invalid_schema):
        Rules.from_file(
            get_static_dir() / Path('static/invalid/rules-invalid-schema.json')
        )


def test_002_load(service: MockGmailService) -> None:
    buffer = io.StringIO()

    with redirect_stdout(buffer):
        load_emails(service)

    output = buffer.getvalue()
    assert '1000 Emails' in output


def test_003_filters_and_actions(service: MockGmailService) -> None:
    buffer = io.StringIO()

    with redirect_stdout(buffer):
        process_emails(service, RULES_FILE)

    rules = Rules.from_file(RULES_FILE)

    with SessionFactory() as session:

        # Tests Equal Condition and Move Message Action
        equals_ids = set()
        for email in service._service._data.values():
            if email['from_email'] == rules.rules[0].conditions.rules[0].value:
                equals_ids.add(email['id'])

        for equal_id in equals_ids:
            move_message_equals_check = cast(Email, session.get(Email, equal_id))
            assert move_message_equals_check.mailbox == MailBox.Spam

        # Test Mark messages with 'Consider' in subject (AND) from example.net as read (Case Insensitive)
        consider_ids = set()
        for email in service._service._data.values():
            if (rules.rules[1].conditions.rules[0].value.lower() in email['subject'].lower()
                    and rules.rules[1].conditions.rules[1].value in email['from_email']):
                consider_ids.add(email['id'])

        assert consider_ids

        for consider_id in consider_ids:
            move_message_contains_check = cast(Email, session.get(Email, consider_id))
            assert move_message_contains_check.read is True

        # Test Archive messages before 2025-02-14T04:52:12+05:30 (AND) from example.org
        archieved_ids = set()

        for email in service._service._data.values():
            stripped_dt = datetime.datetime.strptime(
                rules.rules[2].conditions.rules[0].value, '%Y-%m-%dT%H:%M:%S'
            ).replace(tzinfo=datetime.timezone.utc)
            is_date_condition_met = parsedate_to_datetime(email['date']) < stripped_dt
            is_from_email_condition_met = rules.rules[2].conditions.rules[1].value in email['from_email']
            if is_date_condition_met and is_from_email_condition_met:
                archieved_ids.add(email['id'])

        assert archieved_ids

        for archieved_id in archieved_ids:
            archieved_check = cast(Email, session.get(Email, archieved_id))
            assert archieved_check.mailbox == MailBox.Trash

        # Test from_email 'example.org' (OR) containing 'Whether'
        any_condition_check = set()
        for email in service._service._data.values():
            if rules.rules[3].conditions.rules[0].value.lower() in email['from_email'].lower():
                any_condition_check.add(email['id'])
            if rules.rules[3].conditions.rules[1].value.lower() in email['body'].lower():
                any_condition_check.add(email['id'])

        assert any_condition_check

        for any_condition in any_condition_check:
            any_check = cast(Email, session.get(Email, any_condition))
            assert any_check.read is False
