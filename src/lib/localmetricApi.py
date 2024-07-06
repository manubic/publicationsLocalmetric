import json, requests, io, random



class Localmetric:
    def __init__(self, config) -> None:
        self.credentials: str = json.loads(requests.post("https://api.localmetric.es/api/auth/token",
            headers={
                'accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            data=f'username={config.LocApiName}&password={config.LocApiKey}&grant_type=password'
        ).text)['access_token']

    def uploadDriveURLMediaFile(self, driveURL: str) -> str:
        newFileID = json.loads(requests.post(
            'https://api.localmetric.es/api/media_files',
            headers={
                'Authorization': f'Bearer {self.credentials}',
                'Content-Type': 'application/octet-stream',
            },
            data = io.BytesIO(requests.get(f"https://drive.google.com/uc?export=download&id={driveURL.split('/')[-2]}").content).getvalue(),      
        ).text)['mediaFileId']

        return {
            'sourceUrl': f'https://api.localmetric.es/api/media_files/{newFileID}',
            'mediaFormat': 'PHOTO'
        }
    
    def createScheduledPost(self, options: list[str]) -> str:
        result = requests.post(
            'https://api.localmetric.es/api/scheduled_local_posts',
            headers={
                'Authorization': f'Bearer {self.credentials}',
                'Content-Type': 'application/json',
            },
            json = {
                "active": True, "language_code": options[0],
                "summary": options[1], "call_to_action_type": options[2],
                "call_to_action_url": options[3], "event_title": "",
                "event_schedule_start": "", "event_schedule_end": "",
                "state": "SCHEDULED", "media": [options[4]],
                "topic_type": "STANDARD", "alert_type": "ALERT_TYPE_UNSPECIFIED",
                "publish_schedule": options[5], "call_to_action_url_settings": "RAW_URL"
            }
        ).text
        return json.loads(result)['id']
    
    def createLocalPost(self, options: list[str]) -> None:
        result = []
        for publicationSite in options[7]:
            body = {
                    "id": f"localPosts/{''.join([str(random.randint(0, 9)) for _ in range(24)])}", "language_code": options[0],
                    "summary": options[1], "call_to_action_type": options[2],
                    "call_to_action_url": options[3], "event_title": "",
                    "event_schedule_start": "", "event_schedule_end": "", "state": "SCHEDULED",
                    "media": [options[4]], "search_url": "", "topic_type": "STANDARD", "alert_type": "ALERT_TYPE_UNSPECIFIED",
                    "offer_coupon_code": "", "offer_redeem_online_url": "", "offer_terms_conditions": "",
                    "scheduled_local_post_id": options[5],
                    "create_time": options[6],
                    "update_time": options[6]
                }
            body.update(publicationSite)
            print(body)
            newPost = requests.post(
                'https://api.localmetric.es/api/local_posts',
                headers={
                    'Authorization': f'Bearer {self.credentials}',
                    'Content-Type': 'application/json',
                },
                json = body
            ).text
            result.append(json.loads(newPost)['id'])
        return result