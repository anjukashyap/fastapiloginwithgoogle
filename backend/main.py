from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

app = FastAPI()

# Allow frontend (React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React's local dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Token(BaseModel):
    token: str

@app.post("/auth/google")
async def verify_google_token(data: Token):
    try:
        idinfo = id_token.verify_oauth2_token(
            data.token,
            requests.Request(),
            CLIENT_ID
        )
        # Extract user info
        return {
            "name": idinfo["name"],
            "email": idinfo["email"],
            "picture": idinfo["picture"]
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Invalid token")
