from __future__ import print_function
import pyodbc
import sys
import os.path
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']
file_metadata = {
            'name': 'date_today.bak'
            
        }
path = sys.argv[1]

def make_backup():
    engine = pyodbc.connect(r'Driver=SQL Server;Server=localhost;Trusted_Connection=yes;')
    engine.autocommit = True
    cursor = engine.cursor()
    rows= cursor.execute("select name FROM sys.databases").fetchall()

    for row in rows:
        if row[0]in ['master', 'tempdb', 'model', 'msdb']:
            continue
        cursor.execute("BACKUP DATABASE "+ row[0] +" TO DISK = \'"+path+"\\"+ row[0] +".bak'")
        while cursor.nextset():
            pass
    engine.close()
def read_all_files():
    
    files = os.listdir(path)
    for i in files:
    # List files with .bak
        if i.endswith(".bak"):
            print(F"Files with extension .pak are:{i}")
    return files
     
def upload_to_drive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('drive', 'v3', credentials=creds)
        # pylint: disable=maybe-no-member
        file_metadata = {
            'name': ''
        }
        for file in read_all_files():
            file_path =path +"\\" + file
            file_metadata['name']= file
            media = MediaFileUpload(file_path,
                                resumable=True)
            file_to_upload = service.files().create( media_body=media,body = file_metadata,
                                        fields='id').execute()
            print(F'File with ID: "{file_to_upload.get("id")}" has been uploaded.')

        results = service.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
            return
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))


    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')
    



def main():
    make_backup()
    upload_to_drive()
    
    


if __name__ == '__main__':
    main()





  