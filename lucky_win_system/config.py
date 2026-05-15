# config.py
import os

# ========== TELEGRAM BOT CONFIGURATION ==========
BOT_TOKEN = "8620660638:AAEEa5j_T-6ZD7ZD_2VaZO7U71uQXSZWNOM"
ADMIN_ID = 679235327  # Replace with YOUR Telegram user ID

# ========== WEB ADMIN CONFIGURATION ==========
SECRET_KEY = "your-secret-key-change-this"
PORT = 5000
DEBUG = True

# ========== ADMIN LOGIN ==========
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# ========== GAME SETTINGS ==========
ENTRY_FEE = 300  # Birr per player
TOTAL_PLAYERS = 20  # Exactly 20 players needed
WINNER_PRIZES = {
    1: 5000,  # 1st place
    2: 500,   # 2nd place
    3: 300    # 3rd place
}
HOUSE_PERCENT = 3.33  # Approximately 3.33%
PROFIT_PER_GAME = 200  # 6000 - 5800 = 200

# ========== DEMO MODE ==========
DEMO_BALANCE_START = 300  # Starting demo balance (enough for 1 entry)

# ========== PAYMENT ACCOUNTS ==========
TELEBIRR_ACCOUNT = "09XX XXX XXX"
CBE_ACCOUNT = "1000XXXXXX"
BANK_NAME = "Commercial Bank of Ethiopia"
ACCOUNT_HOLDER = "Your Business Name"

# ========== DATABASE ==========
DATABASE_PATH = "lucky_win.db"

# ========== CALCULATIONS ==========
TOTAL_COLLECTED = TOTAL_PLAYERS * ENTRY_FEE  # 6,000 Birr
TOTAL_PAID = sum(WINNER_PRIZES.values())  # 5,800 Birr
PROFIT_PER_GAME = TOTAL_COLLECTED - TOTAL_PAID  # 200 Birr

# ========== APP INFO ==========
APP_NAME = "Lucky Win"
APP_VERSION = "1.0.0"