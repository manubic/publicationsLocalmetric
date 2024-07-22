from lib.chats import MenuModel, PublicationsModel
from lib.sheets import Sheets
from lib.drive import Drive
from lib.sql import SQL
from lib.localmetricApi import Localmetric
from typing import Callable
from datetime import datetime, timedelta
from openai import OpenAI
import random



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
    
    def get_itemsInfo(self, clientName: str) -> list[list | bool | Sheets | Callable]:
        clientMenuSheetID: str = self.getSheetMenuID(clientName)
        if not clientMenuSheetID: return False
        menuSheet: Sheets = Sheets(clientMenuSheetID, self.creds)
        menuSheetSheets: list[str] = menuSheet.getSheets()
        urls: list[str] = [url for url in menuSheet.getAllRows(menuSheetSheets[0])]

        if "Menu" in menuSheetSheets:
            return [[[item[0], item[1]] if len(item) > 1 else [item[0]] for item in menuSheet.getAllRows('Menu')], False]

        self.menuChat: MenuModel = MenuModel(self.client)
        return [
            urls,
            self.menuChat.getMenuFromFile if urls[0][0].split('?')[0].split('.')[-1] in {'jpg', 'jpeg', 'png', 'webp', 'gif', 'pdf'} else self.menuChat.getMenuOrServicesFromHTML,
            menuSheet,
        ]

    def insertPublicationsToSheet(self, clientName: str) -> None | bool:
        itemsInfo: list[list | bool | Sheets | Callable] = self.get_itemsInfo(clientName)

        if not itemsInfo:
            return False
        elif itemsInfo[1]:
            items: dict[str, list[list[str]]] = itemsInfo[1](itemsInfo[0])
            if not items: return False
            itemsInfo[2].create_sheet('Menu')
            itemsInfo[2].insertRows([[item[0], item[1]] for item in items['Items']], 'Menu')
        else:
            items: list[list[str]] = itemsInfo[0]
        
        self.publicationsChat: PublicationsModel = PublicationsModel(self.client)
        allPublications: list[list[str]] = self.publicationsSheet.getAllRows(clientName)
        newPublications: list[str] = self.publicationsChat.createPublications(items, [random.choice(allPublications[2:])[1] for _ in range(3)], clientName)

        postReference: datetime = datetime.fromisoformat(
            f'{datetime.now().year}-{('0' * (2 - len(str(datetime.now().month)))) + str(datetime.now().month)}-30T12:00:00.00Z'
        ) if len(allPublications[-1]) <= 4 or allPublications[-1][5] < (
            datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'
        ) else (datetime.fromisoformat(allPublications[-1][5]) + timedelta(days=6))

        postDates: list[str] = [(postReference + timedelta(days=(i*7)+1)).strftime('%Y-%m-%d 12:00:00') for i in range(len(newPublications['publications']))] 
        self.publicationsSheet.insertRows([["", publication, "", "", "", postDates[i]] for i, publication in enumerate(newPublications['publications'])], clientName)
    
    def schedulePublications(self, clientName: str) -> list[str]:
        lenguage: str = self.database.query(f'SELECT language_code FROM locations WHERE account_id = "{self.accountsID[clientName]}"')[0][0]
        nowDate: datetime = datetime.now()
        
        for publication in self.publicationsSheet.getAllRows(clientName)[1:]:
            fecha = datetime.fromisoformat(publication[5]) if publication[5] else False
            if (len(publication) != 7 or not publication[5]
                or fecha.day != nowDate.day
                or fecha.month != nowDate.month):
                continue
    
            locationsID: list[str] = [
                locationID 
                for locationID in publication[6].split(', ')
            ] if publication[6] != 'Account' else [
                locationID[0]
                for locationID in self.database.query(f'SELECT id FROM locations WHERE account_id = "{self.accountsID[clientName]}"')
            ]
            publicationAddedSites: dict[str, str] = [{"account_id": self.accountsID[clientName], "location_id": locationID} for locationID in locationsID]

            mediaContent: str = self.localmetric.uploadDriveURLMediaFile(publication[4])
            newScheduledPostID: str = self.localmetric.createScheduledPost([
                lenguage, publication[1], publication[2], 
                publication[3], mediaContent, (datetime.fromisoformat(publication[5]) - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%S.00Z'),
            ])
            newIDs: list[str] = self.localmetric.createLocalPost([
                lenguage, publication[1], publication[2], 
                publication[3], mediaContent, newScheduledPostID, 
                nowDate.strftime('%Y-%m-%dT%H:%M:%S.00Z'), publicationAddedSites,
            ])
            return newIDs