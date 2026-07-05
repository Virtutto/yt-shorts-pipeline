import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = "client_secrets.json"  # Download from Google Cloud Console

def run_local_auth():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    print("Add this JSON to your GitHub secret YOUTUBE_TOKEN_JSON:")
    print(json.dumps(json.loads(creds.to_json()), indent=2))

if __name__ == "__main__":
    run_local_auth()
