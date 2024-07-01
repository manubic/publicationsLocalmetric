from lib.publications import PublicationsManager
from lib.chats import MenuModel, PublicationsModel
from lib.sheets import Sheets
from lib.drive import Drive
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle, os, credentials.config as config



def get_credentials(config):
    creds = None
    if os.path.exists(config.token_path):
        with open(config.token_path, 'rb') as token:
            creds = pickle.load(token)    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(config.credentials_path, config.scopes)
            creds = flow.run_local_server(port=0)
        with open(config.token_path, 'wb') as token:
            pickle.dump(creds, token)
    return creds

config = config.Config()
creds = get_credentials(config)

publicationsManager = PublicationsManager(
    MenuModel(config.client),
    PublicationsModel(config.client),
    Sheets('1uWaEPxQNS0SIMCCEVrB3Soa4NriDOh0oIADN6SeQ6rM', creds),
    Drive(creds),
    creds,
)

publicationsManager.insertPublications("Urogallo")

