from lib.chats import MenuModel, PublicationsModel
from lib.sheets import Sheets
from lib.drive import Drive
from lib.sql import SQL
from lib.localmetricApi import Localmetric
from typing import Callable
from datetime import datetime
from openai import OpenAI



class PublicationsManager:
    def __init__(self, client: OpenAI, database: SQL, publicationsSheet: Sheets,
                 emailsSheet: Sheets, driveService: Drive, localmetric: Localmetric, creds) -> None:

        self.client = client
        self.database = database
        self.publicationsSheet = publicationsSheet
        self.emailsSheet = emailsSheet
        self.driveService = driveService
        self.localmetric = localmetric
        self.creds = creds
    
    def getSheetMenuID(self, clientName: str) -> str:
        clientFolderID: str = self.driveService.search_fileOrFolder(f"mimeType = 'application/vnd.google-apps.folder' and name = '{clientName}'")
        menuFolderID: str = self.driveService.search_fileOrFolder(f"mimeType = 'application/vnd.google-apps.folder' and name = 'Menú' and '{clientFolderID}' in parents")
        menuSheetID: str = self.driveService.search_fileOrFolder(f"mimeType = 'application/vnd.google-apps.spreadsheet' and '{menuFolderID}' in parents")
        return menuSheetID
    
    def getAccountsID(self) -> dict[str, str]:
        return {row[2].split(' - ')[1]: row[2].split(' - ')[0].replace('_', '/') for row in self.emailsSheet.getAllRows('Clientes')[1:]}
    
    def get_itemsInfo(self, clientName: str) -> list[list | bool | Sheets | Callable]:
        menuSheet: Sheets = Sheets(self.getSheetMenuID(clientName), self.creds)
        menuSheetSheets: list[str] = menuSheet.getSheets()
        urls: list[str] = [url for url in menuSheet.getAllRows(menuSheetSheets[0])]

        if "Menu" in menuSheetSheets:
            return [[[item[0], item[1]] if len(item) > 1 else [item[0]] for item in menuSheet.getAllRows('Menu')], False]

        self.menuChat = MenuModel(self.client)
        return [
            urls,
            self.menuChat.getMenuFromIMG if urls[0][0].split('?')[0].split('.')[-1] in {'jpg', 'jpeg', 'png', 'webp', 'gif'} else self.menuChat.getMenuOrServicesFromHTML,
            menuSheet,
        ]

    def insertPublicationsToSheet(self, clientName: str) -> None:
        itemsInfo: list[list | bool | Sheets | Callable] = self.get_itemsInfo(clientName)
        if itemsInfo[1]:
            items: dict[str, list[list[str]]] = itemsInfo[1](itemsInfo[0])
            itemsInfo[2].create_sheet('Menu')
            itemsInfo[2].insertRows([[item[0], item[1]] for item in items['Items']], 'Menu')
        else:
            items: list[list[str]] = itemsInfo[0]
        
        self.publicationsChat = PublicationsModel(self.client)
        publicationsExample: list[str] = [row[1] for row in self.publicationsSheet.getAllRows(clientName)[-3::]]
        newPublications: list[str] = self.publicationsChat.createPublications(items, publicationsExample, clientName)
        
        self.publicationsSheet.insertRows([["", publication] for publication in newPublications['publications']], clientName)
    
    def insertPublicationsToDB(self, clientName: str) -> None:
        lenguage = self.database.query(f'SELECT language_code FROM locations WHERE account_id = "{self.getAccountsID()[clientName]}"')[0][0]
        formattedDate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for publication in self.publicationsSheet.getAllRows(clientName)[1:]:
            if len(publication) != 7 or publication[5] < formattedDate: continue

            mediaContent: str = self.localmetric.uploadMediaFile(publication[4]).replace('\n', '')
            query: str = """
                INSERT INTO scheduled_local_posts(
                    active, language_code, summary, call_to_action_type, 
                    call_to_action_url, state, media, topic_type, alert_type, 
                    publish_schedule, call_to_action_url_settings,
                    create_time_internal, update_time_internal
                ) 
                VALUES (
                    "1", "{}", "{}", "{}", "{}",
                    "SCHEDULED", "{}", "STANDARD", "ALERT_TYPE_UNSPECIFIED",
                    "{}", "RAW_URL", "{}", "{}"
                );
            """.replace('\n', '').replace('  ', '').format(
                lenguage, publication[1], publication[2], 
                publication[3], mediaContent, publication[5],
                formattedDate, formattedDate,
            )
            self.database.query(query)