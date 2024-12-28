from datetime import datetime, timedelta
from typing import Callable
from openai import OpenAI
import random

from managers.models.__BaseManager import __BaseManager

from lib.chatGPT.chats import MenuModel, PublicationsModel

from lib.google.drive import Drive
from lib.google.sheets import Sheets

from lib.other.localmetric_api import Localmetric

from lib.sql.sql import SQL


class PublicationsCreater(__BaseManager):
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
        super().__init__(
            open_ai_client,
            database,
            publications_sheet,
            emails_sheet,
            drive_service,
            localmetric_service,
            creds,
        )

    def get_items_info(self, client_name: str) -> list[list | bool | Sheets | Callable]:
        client_menu_sheet_id: str = self.get_sheet_menu_id(client_name)
        if not client_menu_sheet_id:
            return False
        menu_sheet: Sheets = Sheets(client_menu_sheet_id, self.creds)
        menu_sheet_sheets: list[str] = menu_sheet.get_sheets()
        urls: list[str] = [url for url in menu_sheet.get_all_rows(menu_sheet_sheets[0])]

        if "Menu" in menu_sheet_sheets:
            return [
                [
                    [item[0], item[1]] if len(item) > 1 else [item[0]]
                    for item in menu_sheet.get_all_rows("Menu")
                ],
                False,
            ]

        self.menu_chat: MenuModel = MenuModel(self.client)
        return [
            urls,
            self.menu_chat.get_menu_from_file
            if urls[0][0].split("?")[0].split(".")[-1]
            in {"jpg", "jpeg", "png", "webp", "gif", "pdf"}
            else self.menu_chat.get_menu_or_services_from_html,
            menu_sheet,
        ]

    def create_publications(self, client_name: str) -> None | bool:
        items_info: list[list | bool | Sheets | Callable] = self.get_items_info(
            client_name
        )

        if not items_info:
            return False
        elif items_info[1]:
            items: dict[str, list[list[str]]] = items_info[1](items_info[0])
            if not items:
                return False

            items_info[2].create_sheet("Menu")
            items_info[2].insert_rows(
                [[item[0], item[1]] for item in items["Items"]], "Menu"
            )
        else:
            items: list[list[str]] = items_info[0]

        self.publications_chat: PublicationsModel = PublicationsModel(self.client)
        
        all_publications: list[list[str]] = self.publications_sheet.get_all_rows(client_name)
        images = self.get_images(client_name)

        new_publications: list[str] = self.publications_chat.create_publications(
            items, [random.choice(all_publications[2:])[1] for _ in range(3)], client_name, images
        )

        post_reference: datetime = (
            (datetime.fromisoformat(all_publications[-1][5]) + timedelta(days=6))
            if len(all_publications[-1]) > 4
            and all_publications[-1][5]
            > (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            else datetime.fromisoformat(
                f'{datetime.now().year}-{("0" * (2 - len(str(datetime.now().month)))) + str(datetime.now().month)}-30T12:00:00.00Z'
            )
        )

        post_dates: list[str] = [
            (post_reference + timedelta(days=(i * 7) + 1)).strftime("%Y-%m-%d 12:00:00")
            for i in range(len(new_publications["publications"]))
        ]
        images_id = {
            image["name"]: image["id"] for image in images
        }
        self.publications_sheet.insert_rows(
            [
                [
                    "",
                    publication["text"],
                    "",
                    "",
                    f"https://drive.google.com/file/d/{images_id[publication["product"]]}/view?usp=drive_link",
                    post_dates[i],
                ]
                for i, publication in enumerate(new_publications["publications"])
            ],
            client_name,
        )
