from managers.app_manager import AppManager
from lib.google.sheets import Sheets
from lib.google.drive import Drive
from lib.sql.sql import SQL
from lib.other.localmetric_api import Localmetric
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import os
import credentials.config as config


def get_credentials(config):
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


config = config.Config()
creds = get_credentials(config)

publications_manager = AppManager().publications_scheduler(
    config.client,
    SQL(config.db_user, config.db_host, config.db_name, config.db_password),
    Sheets(config.gmb_redes_sheet_id, creds),
    Sheets(config.emails_sheet_id, creds),
    Drive(creds),
    Localmetric(config),
    creds,
)

def publications_scheduler_test():
    values = publications_manager.get_accounts_id(dict=False)
    sheets = Sheets(config.gmb_redes_sheet_id, creds).get_sheets(res_format=set)
    database_result = sorted(
        SQL(config.db_user, config.db_host, config.db_name, config.db_password).query(
            f"SELECT name FROM accounts WHERE id IN ('{"', '".join(values).replace(' ', '')}') ORDER BY id"
        )
    )

    for i, client in enumerate(database_result):
        if client[0] not in sheets or client[0] in config.exceptions:
            continue
        print(client, i)
        publications_manager.schedule_publications(client[0])

publications_scheduler_test()
