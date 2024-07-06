from googleapiclient.discovery import build



class Drive:
    def __init__(self, creds) -> None:
        self.drive_service = build('drive', 'v3', credentials=creds)
    
    def search_fileOrFolder(self, query: str) -> str:
        raw_results: dict = self.drive_service.files().list(
            q=query,
            spaces='drive',
            corpora='drive',
            driveId='0ACH9JCa0FgTzUk9PVA',
            includeItemsFromAllDrives=True,
            supportsAllDrives=True
        ).execute()
 
        return raw_results['files'][0]['id'] if len(raw_results['files']) > 0 else False 

"mimeType = 'application/vnd.google-apps.folder' and name = 'Menú' and 'False' in parents"