import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
DATABASE_URL= os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")