from datetime import datetime, timedelta
from openai import OpenAI

from managers.models.__BaseManager import __BaseManager

from lib.google.drive import Drive
from lib.google.sheets import Sheets

from lib.chatGPT.chats import Chat

from lib.other.localmetric_api import Localmetric

from lib.sql.sql import SQL


class PublicationsScheduler(__BaseManager):
    def __init__(
        self,
        openai_client: OpenAI,
        database: SQL,
        publications_sheet: Sheets,
        emails_sheet: Sheets,
        drive_service: Drive,
        localmetric_service: Localmetric,
        creds,
    ) -> None:
        super().__init__(
            openai_client,
            database,
            publications_sheet,
            emails_sheet,
            drive_service,
            localmetric_service,
            creds,
        )

    def schedule_publications(self, client_name: str) -> list[str]:
        language: str = self.database.query(
            f'SELECT language_code FROM locations WHERE account_id = "{self.accounts_id[client_name]}"'
        )[0][0]
        now_date: datetime = datetime.now()

        chat = Chat(
            self.client,
            """
            Tu trabajo es emparejar las publicaciones con los productos correctos.
            Devolver el resultado con este formato JSON: {"product": Nombre del producto}
            """,
        )

        images = self.get_images(client_name)
        images_id = {image["name"]: image["id"] for image in images}

        for i, publication in enumerate(
            self.publications_sheet.get_all_rows(client_name)[1:]
        ):
            update_date = (
                datetime.fromisoformat(publication[5].replace("/", "-"))
                if publication[5]
                else False
            )
            if not publication[4]:
                result = chat.query(
                    f"""
                        En base a esta publicación:
                        {publication[1]}
                        Empareja la publicación con el producto correcto de esta lista:
                        {"\n".join(f"- {image["name"]}" for image in images)}
                        En algunos casos, tendras varias opciones de un mismo producto, en ese caso, escoge aleatoriamente una de ellos.
                        Ejemplo de esto:
                        - Hamburguesa
                        - Hamburguesa - 1
                        - Hamburguesa - 2
                    """
                )
                link = f"https://drive.google.com/file/d/{images_id[result["product"]]}/view?usp=drive_link"
                self.publications_sheet.insert_rows(
                    [[link]], client_name, f"E{i + 2}:F{i + 2}"
                )

            if (
                len(publication) != 7
                or not update_date
                or not publication[3]
                or update_date.day != now_date.day
                or update_date.month != now_date.month
                or update_date.year != now_date.year
            ):
                continue

            locations_id: list[str] = (
                [location_id for location_id in publication[6].split(", ")]
                if publication[6] != "Account"
                else [
                    location_id[0]
                    for location_id in self.database.query(
                        f'SELECT id FROM locations WHERE account_id = "{self.accounts_id[client_name]}"'
                    )
                ]
            )
            publication_added_sites: dict[str, str] = [
                {"account_id": self.accounts_id[client_name], "location_id": location_id}
                for location_id in locations_id
            ]

            media_content: str = self.localmetric.upload_drive_url_media_file(publication[4])
            new_scheduled_post_id: str = self.localmetric.create_scheduled_post(
                [
                    language,
                    publication[1],
                    publication[2],
                    publication[3],
                    media_content,
                    (
                        datetime.fromisoformat(publication[5]) - timedelta(hours=2)
                    ).strftime("%Y-%m-%dT%H:%M:%S.00Z"),
                ]
            )
            new_ids: list[str] = self.localmetric.create_local_post(
                [
                    language,
                    publication[1],
                    publication[2],
                    publication[3],
                    media_content,
                    new_scheduled_post_id,
                    now_date.strftime("%Y-%m-%dT%H:%M:%S.00Z"),
                    publication_added_sites,
                ]
            )
            return new_ids
