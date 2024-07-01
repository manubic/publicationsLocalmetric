from lib.chats import MenuModel, PublicationsModel
from lib.sheets import Sheets
from lib.drive import Drive



class PublicationsManager:
    def __init__(self, menuChat: MenuModel, publicationsChat: PublicationsModel, 
                 publicationsSheet: Sheets, driveService: Drive, creds) -> None:

        self.menuChat = menuChat
        self.publicationsChat = publicationsChat
        self.publicationsSheet = publicationsSheet
        self.driveService = driveService
        self.creds = creds
    
    def getSheetMenuID(self, clientName: str) -> str:
        clientFolderID: str = self.driveService.search_fileOrFolder(f"mimeType = 'application/vnd.google-apps.folder' and name = '{clientName}'")
        menuFolderID: str = self.driveService.search_fileOrFolder(f"mimeType = 'application/vnd.google-apps.folder' and name = 'Menú' and '{clientFolderID}' in parents")
        menuSheetID: str = self.driveService.search_fileOrFolder(f"mimeType = 'application/vnd.google-apps.spreadsheet' and '{menuFolderID}' in parents")
        return menuSheetID
    
    def get_itemsInfo(self, clientName: str) -> list[str]:
        menuSheet: Sheets = Sheets(self.getSheetMenuID(clientName), self.creds)
        menuSheetSheets: list[str] = menuSheet.getSheets()
        urls: list[str] = [url for url in menuSheet.getAllRows(menuSheetSheets[0])]

        if "Menu" in menuSheetSheets:
            return [[[item[0], item[1]] if len(item) > 1 else [item[0]] for item in menuSheet.getAllRows('Menu')], False]
        return [
            urls,
            self.menuChat.getMenuFromIMG if urls[0][0].split('.')[-1] in {'jpg', 'jpeg', 'png', 'webp', 'gif'} else self.menuChat.getMenuOrServicesFromHTML,
            menuSheet,
        ]

    def insertPublications(self, clientName: str) -> None:
        itemsInfo: list[list | bool | Sheets] = self.get_itemsInfo(clientName)
        if itemsInfo[1]:
            items = itemsInfo[1](itemsInfo[0])
            itemsInfo[2].create_sheet('Menu')
            itemsInfo[2].insertRows([[item[0], item[1]] for item in items['Items']], 'Menu')
        else:
            items = itemsInfo[0]
        
        publicationsExample: list[str] = [row[1] for row in self.publicationsSheet.getAllRows(clientName)[-3::]]
        newPublications: list[str] = self.publicationsChat.createPublications(items, publicationsExample, clientName)
        
        self.publicationsSheet.insertRows([["", publication] for publication in newPublications['publications']], clientName)