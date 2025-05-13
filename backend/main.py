from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from authlib.integrations.starlette_client import OAuth
from starlette.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
import random
import smtplib
from email.message import EmailMessage
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException


# Dummy email credentials (USE ENV VARS IN PRODUCTION!)
EMAIL_ADDRESS = "anjukashyap109@gmail.com"
EMAIL_PASSWORD = "ygtp ofma mvmu rtrm"  # Use App Password for Gmail

# Function to send email
def send_email(recipient: str, subject: str, body: str):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"Email sent to {recipient}")
    except Exception as e:
        print(f"Failed to send email: {e}")

app = FastAPI()

# Middleware to handle sessions
app.add_middleware(SessionMiddleware, secret_key="1234567abcdefg")
# Allow CORS for React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth = OAuth()
oauth.register(
    name='google',
    client_id='1017849676008-4vo6hdku0jp1ti99j35k2raiq401clrn.apps.googleusercontent.com',
    client_secret='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',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account'  # Always shows account chooser
    },
    
)


# Temporary in-memory stores
otp_store = {}
users_db = {"anjukashyap109@gmail.com": {"password": "123456"}}  # Example user

@app.get("/login/google")
async def login_google(request: Request):
    redirect_uri = request.url_for('auth_google')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth/google")
async def auth_google(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info =token.get('userinfo')
    # user_info = resp.json()

    email = user_info['email']
    name = user_info.get('name', '')

    # Redirect to frontend with email
    return RedirectResponse(url=f"http://localhost:3000/verify?email={email}")



@app.post("/verify-password")
async def verify_password(email: str = Form(...), password: str = Form(...)):
    user = users_db.get(email)
    if user and user['password'] == password:
        otp = str(random.randint(100000, 999999))
        otp_store[email] = otp
        print(f"OTP for {email}: {otp}")  # Replace with email logic
         # Send the OTP via email
        send_email(
            recipient=email,
            subject="Your OTP Code",
            body=f"Hello,\n\nYour OTP is: {otp}\n\nThanks,\nYour App Team"
        )
        
        return JSONResponse({"status": "otp_sent"})
    return JSONResponse({"error": "Invalid credentials"}, status_code=400)



@app.post("/verify-otp")
async def verify_otp(email: str = Form(...), otp: str = Form(...)):
    if otp_store.get(email) == otp:
       return JSONResponse({"status": "success"})
    
    return JSONResponse({"error": "Invalid OTP"}, status_code=400)


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()  # Clear local session
    # Redirect to Google's logout endpoint, then back to your login
    google_logout_url = (
        "https://accounts.google.com/Logout?"
        "continue=https://appengine.google.com/_ah/logout"
        f"&continue=http://localhost:8000/login/google"  # Back to login flow
    )
    return RedirectResponse(url=google_logout_url)