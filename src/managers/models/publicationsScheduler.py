from datetime import datetime, timedelta
from openai import OpenAI
from __BaseManager import __BaseManager
from lib.google.drive import Drive
from lib.google.sheets import Sheets
from lib.other.localmetricApi import Localmetric
from lib.sql.sql import SQL



class PublicationsScheduler(__BaseManager):
    def __init__(self, openAIClient: OpenAI, database: SQL, publicationsSheet: Sheets,
                 emailsSheet: Sheets, driveService: Drive, localmetricService: Localmetric, creds) -> None:

        super().__init__(
            openAIClient, database, publicationsSheet, 
            emailsSheet, driveService, localmetricService, creds
        )

    def schedulePublications(self, clientName: str) -> list[str]:
        lenguage: str = self.database.query(f'SELECT language_code FROM locations WHERE account_id = "{self.accountsID[clientName]}"')[0][0]
        nowDate: datetime = datetime.now()
        
        for publication in self.publicationsSheet.getAllRows(clientName)[1:]:
            updateDate = datetime.fromisoformat(publication[5].replace('/', '-')) if publication[5] else False
            if (
                len(publication) != 7 or not updateDate
                or updateDate.day != nowDate.day
                or updateDate.month != nowDate.month
                or updateDate.year != nowDate.year
            ):
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