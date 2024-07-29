from datetime import datetime, timedelta
from typing import Callable
from openai import OpenAI
from __BaseManager import __BaseManager
from lib.chatGPT.chats import MenuModel, PublicationsModel
from lib.google.drive import Drive
from lib.google.sheets import Sheets

import random

from lib.other.localmetricApi import Localmetric
from lib.sql.sql import SQL



class PublicationsCreater(__BaseManager):
    def __init__(self, openAIClient: OpenAI, database: SQL, publicationsSheet: Sheets,
                 emailsSheet: Sheets, driveService: Drive, localmetricService: Localmetric, creds) -> None:

        super().__init__(
            openAIClient, database, publicationsSheet, 
            emailsSheet, driveService, localmetricService, creds
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
        ) if len(allPublications[-1]) > 4 and allPublications[-1][5] < (
            datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'
        ) else (datetime.fromisoformat(allPublications[-1][5]) + timedelta(days=6))

        postDates: list[str] = [(postReference + timedelta(days=(i*7)+1)).strftime('%Y-%m-%d 12:00:00') for i in range(len(newPublications['publications']))] 
        self.publicationsSheet.insertRows([["", publication, "", "", "", postDates[i]] for i, publication in enumerate(newPublications['publications'])], clientName)