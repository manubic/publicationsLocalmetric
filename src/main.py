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

values = publicationsManager.getAccountsID(dict=False)
sheets = Sheets(config.GMBRedesSheetID, creds).getSheets(resFormat=set)
database_result = sorted(SQL(config.DBUser, config.DBHost, config.DBName, config.DBPassword).query(f"SELECT name FROM accounts WHERE id IN ('{"', '".join(values).replace(' ', '')}') ORDER BY id"))
# for i, client in enumerate(database_result): 
#     print(client, i)
#     if client[0] not in sheets or client[0] != "Bingo Plaza":
#         continue
#     print(client[0])
#     result = publicationsManager.insertPublicationsToSheet(client[0])
#     if result == False: print(client[0])
print(publicationsManager.schedulePublications('Urogallo'))