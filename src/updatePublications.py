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

exceptions: set[str] = {
    'Concesionario Oficial Jaguar España', 'Bonaire', 'Bonaval', 'Buena morena', 'By the way', 'Chok', 'Club allard', 'Colmado Parranda', 'Tripti CoWorking', 'Uncovercity',
    'Taberna Madrí Madre', 'Seb', 'Reketepizza', 'Primo Tavolino', 'Peritajes Médicos', 'New Machin', 'Nestseekers', 'Mitoa Pizzeria', 'Mi piace', "L'Ampadini", 'HUM2N', 'Geisha Gitana',
    'Ford con respuesta', 'Ford Sin respuesta', 'Ford Portugal Con Reseñas', 'Ford Portugal Sin Respuesta', 'Enlagloria Salads', 'El Magraner Boig', 'EL KIOSKO Franquiciadpos', 'EL Kiosko',
    'Edu Ramos', 'Desfase', 'Dermaline', 'Concesionario Oficial Jaguar Portugal', 'Concesionario Oficial Land Rover España', 'Concesionario Oficial Land Rover Portugal'
}
values = publicationsManager.getAccountsID(dict=False)
sheets = Sheets(config.GMBRedesSheetID, creds).getSheets(resFormat=set)
database_result = sorted(SQL(config.DBUser, config.DBHost, config.DBName, config.DBPassword).query(f"SELECT name FROM accounts WHERE id IN ('{"', '".join(values).replace(' ', '')}') ORDER BY id"))
for i, client in enumerate(database_result):
    if client[0] not in sheets or client[0] in exceptions or client[0] != 'Urogallo': continue
    print(client, i)
    result = publicationsManager.schedulePublications(client[0])