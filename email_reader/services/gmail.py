from __future__ import annotations

import base64
import csv
import datetime
import os
from email import message, message_from_bytes
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, Optional, cast

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from email_reader.console import console
from email_reader.database.engine import SessionFactory
from email_reader.database.tables.email import Email, MailBox
from email_reader.services.gauth import GoogleAuth, MockGoogleAuth


class EmailAction(Enum):
    MarkAsRead = 'mark_as_read'
    MarkAsUnread = 'mark_as_unread'
    MoveMessage = 'move_message'


class GmailService:
    def __init__(self, auth: GoogleAuth):
        self._service = build('gmail', 'v1', credentials=auth.credentials)

    @classmethod
    def create(cls, credentials_file: Optional[Path]):
        return GmailService(GoogleAuth(credentials_file))

    def get_emails(self, after: Optional[datetime.datetime] = None) -> List[Email]:
        kwargs: dict[str, Any] = {}

        if after and after > datetime.datetime.min:
            kwargs['q'] = f"after:{int(after.timestamp() * 1000)}"

        results = self._service.users().messages().list(userId='me', **kwargs).execute()
        return [self.get_email(msg['id']) for msg in results.get('messages', [])]

    def get_email(self, msg_id: str) -> Email:

        full_message = self._service.users().messages().get(userId='me', id=msg_id, format='raw').execute()

        email_message = cast(
            message.EmailMessage, message_from_bytes(base64.urlsafe_b64decode(full_message['raw']))
        )
        return Email.from_email_message(
            email_message=email_message, msg_id=msg_id,
            labels=full_message.get('labelIds', [])
        )

    def alter_email_read_state(
            self, msg_id: str, action: EmailAction) -> tuple[bool, Optional[str]]:

        email = None

        with SessionFactory() as session:
            email = session.get(Email, msg_id)
            if not email:
                return False, "EmailNotFound"

        add_label_id, remove_label_id = [], []
        if action == EmailAction.MarkAsRead:
            remove_label_id = ['UNREAD']
        elif action == EmailAction.MarkAsUnread:
            add_label_id = ['UNREAD']

        try:
            message = self._service.users().messages().modify(
                userId='me', id=msg_id,
                body=dict(addLabelIds=add_label_id, removeLabelIds=remove_label_id)
            ).execute()

        except HttpError as e:
            console.log(f"[red] When Altering Email {msg_id=}, {action=}, {email} {e} [/red]")
            return False, str(e)

        if message:
            with SessionFactory() as session:
                is_read = (action == EmailAction.MarkAsRead)
                session.query(Email).filter(Email.id == message['id']).update({Email.read: is_read})
                session.commit()

        return message is not None, None

    def move_email(self, msg_id: str, to_location: MailBox) -> tuple[bool, Optional[str]]:

        with SessionFactory() as session:

            current_email = session.get(Email, msg_id)
            if not current_email:
                return False, "EmailNotFound"

            movable_locations = current_email.mailbox.get_movable_locations()

            if current_email.mailbox == to_location:
                console.log("From and To Locations are same, Skipping")
                return True, None

            if to_location not in movable_locations:
                console.log(f"Cannot Move Email {msg_id} To Location {to_location}, {current_email}")
                return False, "CannotMoveEmail"

            try:
                if to_location == MailBox.Trash:
                    message = self._service.users().messages().trash(userId='me', id=msg_id).execute()
                else:
                    message = self._service.users().messages().modify(
                        userId='me', id=msg_id,
                        body=dict(addLabelIds=[to_location.value], removeLabelIds=[current_email.mailbox.value])
                    ).execute()

            except HttpError as e:
                console.log(f"[red] When Moving Message {msg_id=}, {to_location=}, {current_email} {e} [/red]")
                return False, str(e)

            if message:
                session.query(Email).filter(Email.id == message['id']).update({Email.mailbox: to_location})
                session.commit()

        return message is not None, None


class MockGmailService(GmailService):

    class Service:
        def __init__(self, data):
            self._data = data

        def users(self):
            return self

        def messages(self, *args, **kwargs):
            return self

        def list(self, *args, **kwargs):
            return SimpleNamespace(execute=lambda: {
                'messages': [{'id': msg_id} for msg_id in self._data]
            })

        def trash(self, id: str, *args, **kwargs):
            return SimpleNamespace(execute=lambda: {'id': id})

        def modify(self, id: str, *args, **kwargs):
            return SimpleNamespace(execute=lambda: {'id': id})

        def get(self, id: str, *args, **kwargs):
            return SimpleNamespace(execute=lambda: self._data[id])

    def __init__(self, auth: MockGoogleAuth) -> None:

        email_file_path = os.getenv('PY_EMAIL_FILE_PATH')
        if not email_file_path:
            raise ValueError('Need Email File Path to Run Tests')

        emails_for_test = {}
        with open(email_file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                emails_for_test[row['id']] = row

        self._service = MockGmailService.Service(emails_for_test)  # type: ignore

    @classmethod
    def create(cls, credentials_file: Optional[Path]):
        return MockGmailService(MockGoogleAuth(None))
