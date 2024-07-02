import json, requests, io



class Localmetric:
    def __init__(self, config) -> None:
        self.credentials: str = json.loads(requests.post("https://api.localmetric.es/api/auth/token",
            headers={
                'accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            data=f'username={config.LocApiName}&password={config.LocApiKey}&grant_type=password'
        ).text)['access_token']
    
    def uploadMediaFile(self, driveURL: str) -> str:
        newFileID = json.loads(requests.post(
            'https://api.localmetric.es/api/media_files',
            headers={
                'Authorization': f'Bearer {self.credentials}',
                'Content-Type': 'application/octet-stream'
            },
            data = io.BytesIO(requests.get(f"https://drive.google.com/uc?export=download&id={driveURL.split('/')[-2]}").content).getvalue(),
            
        ).text)['mediaFileId']

        return '''[{
            'sourceUrl': 'https://api.localmetric.es/api/media_files/FILEID',
            'mediaFormat': 'PHOTO'
        }]'''.replace('FILEID', newFileID).replace('  ', '')