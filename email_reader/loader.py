from __future__ import annotations

from pathlib import Path

from rich.console import Console

from email_reader.services.gmail import GmailService


def load_emails(service: GmailService, since_last_commit: bool = True) -> None:

    from email_reader.database.tables.email import Email
    from email_reader.database.engine import SessionFactory

    console = Console()

    with SessionFactory() as session:

        if since_last_commit:
            emails = service.get_emails(Email.get_last_updated_email_time(session))
        else:
            emails = service.get_emails()

        for email_message in emails:
            session.merge(email_message)

        session.commit()
        console.log(f"Added {len(emails)} Emails")


def run():
    from argparse import ArgumentParser

    parser = ArgumentParser(description='Load Emails from Gmail')
    parser.add_argument(
        '--from-beginning', '-b',
        help='Sync Email From Beginning Instead of Last Sync',
        action='store_false',
    )

    parser.add_argument(
        '--credentials-file', '-c',
        help='Path for the Client Secrets File Generated During Client App Creation',
        type=Path
    )

    args = parser.parse_args()

    service = GmailService.create(args.credentials_file)

    load_emails(service, args.from_beginning)
