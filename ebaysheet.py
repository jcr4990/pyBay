import gspread
from oauth2client.service_account import ServiceAccountCredentials


def ebaysheet():
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "gideon-ebay-fe269e8abfa1.json", scope)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key("1cRZC3KRuNnYgOEyKwBmu0m9_W1BvsqhNvhdIxeXQYaQ")
    return sh
