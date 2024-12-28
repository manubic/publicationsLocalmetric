from googleapiclient.discovery import build



class Drive:
    def __init__(self, creds) -> None:
        self.drive_service = build('drive', 'v3', credentials=creds)
    
    def search(self, query: str) -> list[dict[str, str]]:
        result = (
            self.drive_service.files()
            .list(
                q=query,
                spaces="drive",
                corpora="drive",
                driveId='0ACH9JCa0FgTzUk9PVA',
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
            )
            .execute()
        )

        return result.get("files", [])