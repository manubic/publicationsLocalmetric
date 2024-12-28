from googleapiclient.discovery import build


class Sheets:
    def __init__(self, _id: str, creds) -> None:
        self.sample_spreadsheet_id: str = _id
        self.creds = creds
        self.service = build("sheets", "v4", credentials=self.creds)

    def get_all_rows(self, sheet_name: str) -> list[list[str]]:
        sheet = self.service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=self.sample_spreadsheet_id, range=f'{sheet_name}!A:ZZ')
            .execute()
        )
        values: list[str|int] = result.get("values", [])
        return values
    
    def get_sheets(self, res_format = list) -> set[str] | list[str]:
        service = build("sheets", "v4", credentials=self.creds)
        sheets = service.spreadsheets().get(spreadsheetId=self.sample_spreadsheet_id).execute().get('sheets', '')
        return res_format(sheet['properties']['title'] for sheet in sheets)

    def insert_rows(self, values: list[list[str]], sheet_name: str, range_ = "") -> None:
        body: dict[str, list[list[str]]] = {"values": values}
  
        if not range_:
            all_rows: list[list[str]] = self.get_all_rows(sheet_name)
            range_: str = f"A{len(all_rows)+1}:F{len(all_rows)+len(values)+1}"

        (
            self.service.spreadsheets()
            .values()
            .update(
                spreadsheetId=self.sample_spreadsheet_id,
                range=f'{sheet_name}!{range_}',
                valueInputOption='RAW',
                body=body,
            )
            .execute()
        )

    def create_sheet(self, title: str) -> str:
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
        batch_update_request: dict[str, list] = {'requests': requests}
        response = self.service.spreadsheets().batchUpdate(spreadsheetId=self.sample_spreadsheet_id, body=batch_update_request).execute()
        return response.get('replies')[0].get('addSheet').get('properties').get('sheetId')