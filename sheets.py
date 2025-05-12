import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Подключение к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
gc = gspread.authorize(credentials)

SPREADSHEET_ID = "1rQ82zgeUBy9BQZ-wd5UkuAi2waxEgxHEBp2SscLWvg4"
SHEET_NAME = "Лист1"
sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

def append_row(data: dict):
    row = [
        data.get("faceit_nick"),
        data.get("faceit_link"),
        data.get("email"),
        str(data.get("telegram_id"))
    ]
    sheet.append_row(row, value_input_option="USER_ENTERED")
