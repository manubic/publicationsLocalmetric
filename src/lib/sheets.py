from googleapiclient.discovery import build



class Sheets:
    def __init__(self, _id: str, creds) -> None:
        self.sample_spreadsheet_id: str = _id
        self.creds = creds
        self.service = build("sheets", "v4", credentials=self.creds)

    def getAllRows(self, sheet_name: str) -> list[list[str]]:
        sheet = self.service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=self.sample_spreadsheet_id, range=f'{sheet_name}!A:ZZ')
            .execute()
        )
        values: list[str|int] = result.get("values", [])
        return values
    
    def getSheets(self) -> dict[str, list[str|int]]:
        service = build("sheets", "v4", credentials=self.creds)
        sheets = service.spreadsheets().get(spreadsheetId=self.sample_spreadsheet_id).execute().get('sheets', '')
        return [sheet['properties']['title'] for sheet in sheets]

    def insertRows(self, values: list, sheet_name: str) -> None:
        body: dict[str, list[list[str]]] = {"values": values}
        allRows = self.getAllRows(sheet_name) 
        range_name: list[list[str]] = f"{sheet_name}!A{len(allRows)+1}:B{len(allRows)+len(values)+1}"
        result = (
            self.service.spreadsheets()
            .values()
            .update(
                spreadsheetId=self.sample_spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body,
            )
            .execute()
        )
        return result

    def create_sheet(self, title) -> str:
        requests = [{
            'addSheet': {
                'properties': {
                    'title': title,
                    'gridProperties': {
                        'rowCount': 1000,
                        'columnCount': 26
                    }
                }
            }
        }]
        batch_update_request = {'requests': requests}
        response = self.service.spreadsheets().batchUpdate(spreadsheetId=self.sample_spreadsheet_id, body=batch_update_request).execute()
        return response.get('replies')[0].get('addSheet').get('properties').get('sheetId')