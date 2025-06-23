"""Configuration module for environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
API_TOKEN = os.getenv("API_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN")