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
    
    def getSheets(self, resFormat = list) -> set[str]:
        service = build("sheets", "v4", credentials=self.creds)
        sheets = service.spreadsheets().get(spreadsheetId=self.sample_spreadsheet_id).execute().get('sheets', '')
        return resFormat(sheet['properties']['title'] for sheet in sheets)

    def insertRows(self, values: list, sheetName: str, range_="") -> None:
        body: dict[str, list[list[str]]] = {"values": values}
  
        if not range_:
            allRows = self.getAllRows(sheetName)
            range_: list[list[str]] = f"A{len(allRows)+1}:B{len(allRows)+len(values)+1}"
        result = (
            self.service.spreadsheets()
            .values()
            .update(
                spreadsheetId=self.sample_spreadsheet_id,
                range=f'{sheetName}!{range_}',
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