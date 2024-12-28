from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import os

from credentials.config import Config

from managers.app_manager import AppManager

from lib.google.sheets import Sheets
from lib.google.drive import Drive

from lib.sql.sql import SQL

from lib.other.localmetric_api import Localmetric


def get_credentials(config: Config):
    creds = None
    if os.path.exists(config.token_path):
        with open(config.token_path, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.credentials_path, config.scopes
            )
            creds = flow.run_local_server(port=0)
        with open(config.token_path, "wb") as token:
            pickle.dump(creds, token)
    return creds


settings = Config()
creds = get_credentials(settings)

publications_manager = AppManager().publications_creater(
    settings.client,
    SQL(settings.db_user, settings.db_host, settings.db_name, settings.db_password),
    Sheets(settings.gmb_redes_sheet_id, creds),
    Sheets(settings.emails_sheet_id, creds),
    Drive(creds),
    Localmetric(settings),
    creds,
)


def publications_manager_test():
    values = publications_manager.get_accounts_id(dict=False)
    sheets = Sheets(settings.gmb_redes_sheet_id, creds).get_sheets(res_format=set)
    database_result = sorted(
        SQL(settings.db_user, settings.db_host, settings.db_name, settings.db_password).query(
            f"SELECT name FROM accounts WHERE id IN ('{"', '".join(values).replace(' ', '')}') ORDER BY id"
        )
    )

    for i, client in enumerate(database_result):
        print(client, i)
        if client[0] not in sheets and client[0] in settings.exceptions:
            continue
        publications_manager.create_publications(client[0])


publications_manager_test()
