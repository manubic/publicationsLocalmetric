import json
import requests
import io
import random


class Localmetric:
    def __init__(self, config) -> None:
        self.localmetric_api_url = config.LocalmetricApiUrl

        self.credentials: str = json.loads(
            requests.post(
                f"{self.localmetric_api_url}/auth/token",
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data=f"username={config.LocApiName}&password={config.LocApiKey}&grant_type=password",
            ).text
        )["access_token"]

    def upload_drive_url_media_file(self, drive_url: str) -> dict[str, str]:
        new_file_id: str = json.loads(
            requests.post(
                f"{self.localmetric_api_url}/media_files",
                headers={
                    "Authorization": f"Bearer {self.credentials}",
                    "Content-Type": "application/octet-stream",
                },
                data=io.BytesIO(
                    requests.get(
                        f"https://drive.google.com/uc?export=download&id={drive_url.split('/')[-2]}"
                    ).content
                ).getvalue(),
            ).text
        )["mediaFileId"]

        return {
            "source_url": f"{self.localmetric_api_url}/media_files/{new_file_id}",
            "media_format": "PHOTO",
        }

    def create_scheduled_post(self, options: list[str]) -> str:
        result: str = requests.post(
            f"{self.localmetric_api_url}/scheduled_local_posts",
            headers={
                "Authorization": f"Bearer {self.credentials}",
                "Content-Type": "application/json",
            },
            json={
                "active": True,
                "language_code": options[0],
                "summary": options[1],
                "call_to_action_type": options[2],
                "call_to_action_url": options[3] if options[2] != "CALL" else "",
                "event_title": "",
                "event_schedule_start": "",
                "event_schedule_end": "",
                "state": "SCHEDULED",
                "media": [options[4]],
                "topic_type": "STANDARD",
                "alert_type": "ALERT_TYPE_UNSPECIFIED",
                "publish_schedule": options[5],
                "call_to_action_url_settings": "RAW_URL",
            },
        ).text
        return json.loads(result)["id"]

    def create_local_post(self, options: list[str]) -> list[str]:
        result = []
        for publication_site in options[7]:
            body = {
                "id": f"localPosts/{''.join([str(random.randint(0, 9)) for _ in range(24)])}",
                "language_code": options[0],
                "summary": options[1],
                "call_to_action_type": options[2],
                "call_to_action_url": options[3] if options[2] != "CALL" else "",
                "event_title": "",
                "event_schedule_start": "",
                "event_schedule_end": "",
                "state": "SCHEDULED",
                "media": [options[4]],
                "search_url": "",
                "topic_type": "STANDARD",
                "alert_type": "ALERT_TYPE_UNSPECIFIED",
                "offer_coupon_code": "",
                "offer_redeem_online_url": "",
                "offer_terms_conditions": "",
                "scheduled_local_post_id": options[5],
                "create_time": options[6],
                "update_time": options[6],
            }
            body.update(publication_site)
            new_post: str = requests.post(
                f"{self.localmetric_api_url}/api/local_posts",
                headers={
                    "Authorization": f"Bearer {self.credentials}",
                    "Content-Type": "application/json",
                },
                json=body,
            ).text
            result.append(json.loads(new_post)["id"])
        return result
