from lib.google.sheets import Sheets
from lib.google.drive import Drive
from lib.sql.sql import SQL
from lib.other.localmetric_api import Localmetric
from openai import OpenAI


class __BaseManager:
    def __init__(
        self,
        open_ai_client: OpenAI,
        database: SQL,
        publications_sheet: Sheets,
        emails_sheet: Sheets,
        drive_service: Drive,
        localmetric_service: Localmetric,
        creds,
    ) -> None:
        self.client = open_ai_client
        self.database = database
        self.publications_sheet = publications_sheet
        self.emails_sheet = emails_sheet
        self.drive_service = drive_service
        self.localmetric = localmetric_service
        self.creds = creds
        self.accounts_id = self.get_accounts_id()

    def get_sheet_menu_id(self, client_name: str) -> str:
        client_folder = self.drive_service.search(
            f'mimeType = "application/vnd.google-apps.folder" and name = "{client_name}"'
        )
        if not len(client_folder):
            return False

        menu_folder = self.drive_service.search(
            f"mimeType = 'application/vnd.google-apps.folder' and name = 'Menú' and '{client_folder[0]["id"]}' in parents"
        )[0]
        menu_sheet = self.drive_service.search(
            f"mimeType = 'application/vnd.google-apps.spreadsheet' and '{menu_folder["id"]}' in parents"
        )[0]
        return menu_sheet["id"]

    def get_images(self, client_name: str) -> list[dict[str, str]]:
        client_folder = self.drive_service.search(
            f'mimeType = "application/vnd.google-apps.folder" and name = "{client_name}"'
        )
        if not len(client_folder):
            return False

        images_folder = self.drive_service.search(
            f"mimeType = 'application/vnd.google-apps.folder' and name = 'Imagenes' and '{client_folder[0]["id"]}' in parents"
        )[0]
        images = self.drive_service.search(f"'{images_folder["id"]}' in parents")
        return images

    def get_accounts_id(self, dict: bool = True) -> dict[str, str]:
        return (
            {
                self.database.query(
                    f'SELECT name FROM accounts WHERE id = "{row[5].replace('_', '/')}"'
                )[0][0]: row[5].replace("_", "/")
                for row in self.emails_sheet.getAllRows("Clientes")[1:]
            }
            if dict
            else [
                row[5].replace("_", "/")
                for row in self.emails_sheet.getAllRows("Clientes")[1:]
                if len(row) > 5
            ]
        )
