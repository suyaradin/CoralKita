from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_PATH = "credential.json"
TOKEN_PATH = "token.json"

def main():
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=8090)
    with open(TOKEN_PATH, "w") as token:
        token.write(creds.to_json())
    print("token.json saved successfully.")

if __name__ == "__main__":
    main()