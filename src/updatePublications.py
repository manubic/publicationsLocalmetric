from lib.publications import PublicationsManager
from lib.sheets import Sheets
from lib.drive import Drive
from lib.sql import SQL
from lib.localmetricApi import Localmetric
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle, os, credentials.config as config



def getCredentials(config):
    creds = None
    if os.path.exists(config.TokenPath):
        with open(config.TokenPath, 'rb') as token:
            creds = pickle.load(token)    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(config.CredentialsPath, config.Scopes)
            creds = flow.run_local_server(port=0)
        with open(config.TokenPath, 'wb') as token:
            pickle.dump(creds, token)
    return creds

config = config.Config()
creds = getCredentials(config)

publicationsManager = PublicationsManager(
    config.Client,
    SQL(config.DBUser, config.DBHost, config.DBName, config.DBPassword),
    Sheets(config.GMBRedesSheetID, creds),
    Sheets(config.EmailsSheetID, creds),
    Drive(creds),
    Localmetric(config),
    creds,
)
publicationsManager.schedulePublications('Urogallo')