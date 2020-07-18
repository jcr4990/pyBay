import gspread
from oauth2client.service_account import ServiceAccountCredentials


def ebaysheet():
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = ServiceAccountCredentials.from_json_keyfile_name(r"C:\PythonScripts\ebay\Gideon-eBay-268b7a34b93b.json", scope)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key("1cRZC3KRuNnYgOEyKwBmu0m9_W1BvsqhNvhdIxeXQYaQ")
    return sh


