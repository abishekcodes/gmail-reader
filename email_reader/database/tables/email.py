from __future__ import annotations

import datetime
from email.message import EmailMessage
from email.utils import parseaddr, parsedate_to_datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import Text, func, select
from sqlalchemy.orm import Mapped, mapped_column, Session

from email_reader.database.base import Base
from bs4 import BeautifulSoup


class MailBox(Enum):
    Inbox = 'INBOX'
    Trash = 'TRASH'
    Spam = 'SPAM'
    Sent = 'SENT'
    Draft = 'DRAFT'

    @classmethod
    def from_labels(cls, labels: List[str]):
        for label in reversed(labels):  # The Main Label is usually the last one
            try:
                mailbox = cls(label)
                return mailbox
            except ValueError:
                pass
        return cls.Inbox

    def get_movable_locations(self) -> List[MailBox]:
        if self == MailBox.Draft:
            return [MailBox.Trash]
        if self == MailBox.Sent:
            return [MailBox.Trash]
        return [MailBox.Inbox, MailBox.Spam, MailBox.Trash]


class Email(Base):
    __tablename__ = "email"

    id: Mapped[str] = mapped_column(primary_key=True)
    from_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    from_email: Mapped[str] = mapped_column(nullable=False)
    to_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    to_email: Mapped[str] = mapped_column(nullable=False, index=True)
    subject: Mapped[str] = mapped_column(nullable=False)
    date: Mapped[datetime.datetime] = mapped_column(nullable=False, index=True)
    mailbox: Mapped[MailBox] = mapped_column(nullable=False)
    read: Mapped[bool] = mapped_column(nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"Email(id={self.id!r}, from={self.from_email!r}, subject={self.subject!r})"

    @classmethod
    def from_email_message(cls, email_message: EmailMessage, msg_id: str, labels: List[str]):

        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if "attachment" in content_disposition:
                    continue

                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode()  # type: ignore
                elif content_type == "text/html":
                    body = "\n".join(
                        BeautifulSoup(
                            part.get_payload(decode=True).decode(), "html.parser"
                        ).stripped_strings
                    )

        else:
            content_type = email_message.get_content_type()
            if content_type == "text/html":
                body = "\n".join(
                    BeautifulSoup(
                        email_message.get_payload(decode=True).decode(), "html.parser"
                    ).stripped_strings
                )
            else:
                body = email_message.get_payload(decode=True).decode()

        from_name, from_email = parseaddr(email_message['From'])
        to_name, to_email = parseaddr(email_message['To'])

        return Email(
            id=msg_id,
            from_name=from_name if from_name else None,
            from_email=from_email,
            to_name=to_name if to_name else None,
            to_email=to_email,
            subject=email_message['Subject'],
            date=parsedate_to_datetime(email_message['Date']),
            mailbox=MailBox.from_labels(labels),
            read='UNREAD' in labels,
            body=body
        )

    @classmethod
    def get_last_updated_email_time(cls, session: Session) -> datetime.datetime:
        # Remove the dependency on SessionFactory
        stmt = select(func.max(Email.date))
        last_date = session.execute(stmt).scalar_one() or datetime.datetime.min
        return last_date
