from __future__ import annotations

from pathlib import Path

from sqlalchemy import and_, or_, select

from email_reader.console import console
from email_reader.logics.filters import Rules
from email_reader.database.tables.email import Email
from email_reader.database.engine import SessionFactory
from email_reader.services.gmail import GmailService


def process_emails(service: GmailService, rules_filepath: Path) -> None:

    rules = Rules.from_file(file=rules_filepath)
    failed_actions = []
    succeded_actions = []

    with SessionFactory() as session:
        for rule in rules.rules:
            stmts = [r.get_statement() for r in rule.conditions.rules]
            query = or_(*stmts) if rule.conditions.operator == "ANY" else and_(*stmts)
            stmt = select(Email.id, Email.from_email, Email.date).where(query)
            emails = session.execute(stmt).mappings().all()

            for email in emails:
                for action in rule.actions:
                    action_processed, error = action.process_action(email['id'], service)
                    email_string = (
                        f"{email['id']}: From: {email['from_email']}, "
                        f"Date:{email['date']:%Y-%m-%d %H:%m}"
                    )
                    if action_processed:
                        succeded_actions.append((email_string, action))
                    else:
                        failed_actions.append((email_string, action, error))

    for email_string, action, error in failed_actions:
        console.print(f'[red] Failed to Process Email {email_string}[/] {action=} {error=}')
    for email_string, action in succeded_actions:
        console.print(f'[green] Succeded in Email {email_string} {action=}')


def run():
    from argparse import ArgumentParser

    from email_reader.loader import load_emails

    parser = ArgumentParser(description='Actions To Take on Emails')
    parser.add_argument(
        '--rules', '-r',
        help='Path for the Rules JSON File',
        type=Path, required=True
    )
    parser.add_argument(
        '--credentials-file', '-c',
        help='Path for the Client Secrets File Generated During Client App Creation',
        type=Path,
        required=True
    )
    parser.add_argument('--load-emails', '-load', help='Updates Emails from Gmail', action='store_false')

    args = parser.parse_args()

    gmail_service = GmailService.create(args.credentials_file)

    if args.load_emails:
        load_emails(service=gmail_service)

    process_emails(gmail_service, args.rules)
