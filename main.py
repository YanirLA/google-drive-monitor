import os.path
from datetime import datetime
from typing import Tuple

from dateutil.parser import parse
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import file_utils

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly",
          "https://www.googleapis.com/auth/drive",
          "https://www.googleapis.com/auth/drive.readonly",
          "https://www.googleapis.com/auth/drive.file"]

LAST_CHECK_TIME_FILE_PATH = "last_check_time.txt"
FILE_CHANGE_HISTORY_PATH = "files_changed_by_program.json"
FILES_CHANGED_KEY = "files_changed"

PUBLIC_PERMISSION_TYPE = "anyone"
PUBLIC_PERMISSION_ID = "anyoneWithLink"
PAGE_SIZE_TO_LOAD = 1000


def main():
    # Runs the Monitor for new public files.
    creds = get_auth_credentials()

    try:
        new_check_time = datetime.now().astimezone()
        items = get_drive_files(creds)
        if not items:
            print("No files found.")
            return
        print("Files:")
        print_default_file_permissions(creds)
        handle_files(items, creds)
        update_last_check_time(new_check_time)

    except HttpError as error:
        print(f"An error occurred: {error}")
        return


def get_auth_credentials() -> Credentials:
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def get_drive_files(creds: Credentials) -> list:
    files = []
    service = build("drive", "v3", credentials=creds)
    results = (
        service.files()
            .list(pageSize=PAGE_SIZE_TO_LOAD,
                  fields="nextPageToken, files(id, name, permissions, shared, createdTime, "
                         "modifiedTime)")
            .execute()
    )
    files += results.get("files", [])
    next_page_token = results.get("nextPageToken")
    if next_page_token:
        while next_page_token is not None:
            print("More pages exists, fetching them too")
            # get more files
            more_files, next_page_token = get_next_page_of_files(creds, next_page_token)
            files += more_files

    return files


def get_next_page_of_files(creds: Credentials, page_token: str) -> Tuple[list, str]:
    files = []
    service = build("drive", "v3", credentials=creds)
    results = (
        service.files()
            .list(pageToken=page_token, pageSize=PAGE_SIZE_TO_LOAD,
                  fields="nextPageToken, files(id, name, permissions, shared, createdTime, "
                         "modifiedTime)")
            .execute()
    )
    next_page_token = results.get("nextPageToken")
    files += results.get("files", [])
    return files, next_page_token


def get_files_changed_by_program() -> list:
    try:
        content = file_utils.get_file(FILE_CHANGE_HISTORY_PATH)
        return json.loads(content).get(FILES_CHANGED_KEY)
    except FileNotFoundError as e:
        print(f"No history file found, returns empty list")
        return []
    except ValueError as e:
        # not supposed to happen, should exit program
        print(f"The history file is corrupted: {e}")
        exit(1)


def add_file_to_changed_files(file_id: str):
    changed_files = get_files_changed_by_program()
    if file_id not in changed_files:
        changed_files.append(file_id)
    output = json.dumps({
        FILES_CHANGED_KEY: changed_files
    })
    file_utils.write_file(FILE_CHANGE_HISTORY_PATH, str(output), True)
    print(output)


def handle_files(files: dict, creds: Credentials):
    for item in files:
        file_id = item.get('id')
        print(f"\nfile: {item.get('name')}:{file_id}")
        # get sharing_status
        sharing_types = get_file_sharing_types(item)
        print(f"Sharing status is: {str(sharing_types)}")
        # check if changed by the program
        is_changed = is_file_changed_by_program(file_id)
        print(f"The file was changed by program: {is_changed}")
        if is_new_file(item):
            # is public
            if PUBLIC_PERMISSION_TYPE in sharing_types:
                print("This item is public, making it private.")
                change_permission_to_private(creds, file_id)
                # add to files changed
                add_file_to_changed_files(file_id)
            else:
                print("This item is already private, no further actions")


def get_file_sharing_types(item: dict) -> list:
    sharing_types = []
    permissions = item['permissions']
    for permission in permissions:
        sharing_types.append(permission.get("type"))
    return sharing_types


def is_file_changed_by_program(file_id: str) -> bool:
    if file_id in get_files_changed_by_program():
        return True
    else:
        return False


def change_permission_to_private(creds: Credentials, file_id: str):
    service = build("drive", "v3", credentials=creds)
    service.permissions().delete(fileId=file_id, permissionId=PUBLIC_PERMISSION_ID).execute()

    print(f"Deleted public permissions for file id: {file_id}")
    results = (
        service.permissions().list(fileId=file_id).execute()
    )
    print(f"New permissions for the file are: \n{results}")


def get_last_monitor_time() -> datetime:
    try:
        last_check_ts = file_utils.get_file(LAST_CHECK_TIME_FILE_PATH)
        return parse(last_check_ts)
    except FileNotFoundError as e:
        print("No last check file found")
        return None


def is_new_file(file: dict) -> bool:
    creation_time = file.get("createdTime")
    modification_time = file.get("modifiedTime")
    file_newer_date = get_newer_date(parse(modification_time), parse(creation_time))
    last_monitor = get_last_monitor_time()
    if last_monitor:
        if get_newer_date(file_newer_date, last_monitor) == last_monitor:
            print("This file is not new for the monitor")
            return False
        print("This file is new for the monitor!")
        return True
    else:
        print("There was no last monitor time, considering file is new")
        return True


def get_newer_date(first_date: datetime, second_date: datetime) -> datetime:
    if first_date > second_date:
        return first_date
    return second_date


def update_last_check_time(time_of_check: datetime):
    print(f"updating last check time: {time_of_check}")
    file_utils.write_file(LAST_CHECK_TIME_FILE_PATH, str(time_of_check), True)


def print_default_file_permissions(creds: Credentials):
    file_id = create_dummy_file(creds)
    default_permissions = get_file_permissions(creds, file_id)
    print(f"Default permissions for this user are: {default_permissions}")
    delete_file(creds, file_id)


def create_dummy_file(creds: Credentials) -> str:
    service = build("drive", "v3", credentials=creds)
    try:
        res = service.files().create(uploadType="media", body="").execute()
        return res.get('id')
    except Exception as e:
        print(e)


def get_file_permissions(creds: Credentials, file_id: str) -> list:
    service = build("drive", "v3", credentials=creds)
    try:
        res = service.permissions().list(fileId=file_id).execute()
        return res.get("permissions", [])
    except Exception as e:
        print(e)


def delete_file(creds: Credentials, file_id: str):
    service = build("drive", "v3", credentials=creds)
    try:
        res = service.files().delete(fileId=file_id).execute()
        print(res)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
