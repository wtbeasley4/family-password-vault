import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the Fernet key from the environment
SECRET_KEY = os.getenv("FERNET_KEY")

if SECRET_KEY is None:
    raise ValueError("FERNET_KEY not found in environment variables")

# Convert to bytes if needed
if isinstance(SECRET_KEY, str):
    SECRET_KEY = SECRET_KEY.encode()

cipher_suite = Fernet(SECRET_KEY)

def encrypt_password(password):
    return cipher_suite.encrypt(password.encode()).decode()

def decrypt_password(encrypted):
    return cipher_suite.decrypt(encrypted.encode()).decode()
