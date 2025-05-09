from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


class GoogleAuth:
    scopes: ClassVar[list[str]] = ['https://www.googleapis.com/auth/gmail.modify']
    token_filename: ClassVar[Path] = Path('token.json')
    credentials: Optional[Credentials] = None

    def __init__(self, credentials_file: Optional[Path]) -> None:
        self.credentials = self.get_credentials(credentials_file)

    @classmethod
    def get_credentials(cls, credentials_file: Optional[Path] = None) -> Credentials:
        if not credentials_file:
            raise FileNotFoundError('Credentials File Not Found')

        credentials = None
        credentials_folder = Path(credentials_file).parent

        token_file = Path(credentials_folder) / cls.token_filename

        if token_file.exists():
            credentials = Credentials.from_authorized_user_file(
                token_file.absolute().as_posix(), cls.scopes
            )

        if credentials:
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            return credentials

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file.absolute().as_posix(),
                cls.scopes
            )
            credentials = flow.run_local_server(port=0)
            token_file.write_text(credentials.to_json())
            return credentials


class MockGoogleAuth(GoogleAuth):

    def __init__(self, credentials_file: Optional[Path] = None) -> None:
        pass
