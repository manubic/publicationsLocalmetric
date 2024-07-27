from lib.google.sheets import Sheets
from lib.google.drive import Drive
from lib.sql.sql import SQL
from lib.other.localmetricApi import Localmetric
from openai import OpenAI



class __BaseManager:
    def __init__(self, openAIClient: OpenAI, database: SQL, publicationsSheet: Sheets,
                 emailsSheet: Sheets, driveService: Drive, localmetricService: Localmetric, creds) -> None:

        self.client = openAIClient
        self.database = database
        self.publicationsSheet = publicationsSheet
        self.emailsSheet = emailsSheet
        self.driveService = driveService
        self.localmetric = localmetricService
        self.creds = creds
        self.accountsID = self.getAccountsID()
    
    def getSheetMenuID(self, clientName: str) -> str:
        clientFolderID: str = self.driveService.search_fileOrFolder(f'mimeType = "application/vnd.google-apps.folder" and name = "{clientName}"')
        if not clientFolderID: return False

        menuFolderID: str = self.driveService.search_fileOrFolder(f"mimeType = 'application/vnd.google-apps.folder' and name = 'Menú' and '{clientFolderID}' in parents")
        menuSheetID: str = self.driveService.search_fileOrFolder(f"mimeType = 'application/vnd.google-apps.spreadsheet' and '{menuFolderID}' in parents")
        return menuSheetID
    
    def getAccountsID(self, dict: bool = True) -> dict[str, str]:
        return ({
                self.database.query(f'SELECT name FROM accounts WHERE id = "{row[5].replace('_', '/')}"')[0][0]: row[5].replace('_', '/')
                for row in self.emailsSheet.getAllRows('Clientes')[1:]
            } if dict
            else [
                row[5].replace('_', '/')
                for row in self.emailsSheet.getAllRows('Clientes')[1:]
                if len(row) > 5
            ]
        )
    
    