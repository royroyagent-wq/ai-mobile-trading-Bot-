import time
import json
import math
import logging
import requests
from datetime import datetime

# ----------------------------------------------------
# Load Config
# ----------------------------------------------------
with open('config.json', 'r') as f:
    cfg = json.load(f)

API_KEY = cfg.get('API_KEY')
API_SECRET = cfg.get('API_SECRET')
ACCESS_TOKEN = cfg.get('ACCESS_TOKEN')

TELEGRAM_TOKEN = cfg.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = cfg.get('TELEGRAM_CHAT_ID')

STARTING_CAPITAL = float(cfg.get('STARTING_CAPITAL', 200))
RISK_PER_TRADE_PCT = float(cfg.get('RISK_PER_TRADE_PCT', 1.0))
MAX_DAILY_LOSS_PCT = float(cfg.get('MAX_DAILY_LOSS_PCT', 5.0))

SYMBOL = cfg.get('SYMBOL', 'RELIANCE')
INTERVAL = cfg.get('INTERVAL', '1m')

# ----------------------------------------------------
# Helper Functions
# ----------------------------------------------------
def telegram_send(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
        requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': text})
    except:
        pass

def now():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

# ----------------------------------------------------
# Broker API PLACEHOLDER
# ----------------------------------------------------

def get_latest_price(symbol, interval='1m'):
    import random
    return 1000 + random.uniform(-5, 5)

def place_order(side, symbol, qty, order_type='MARKET', price=None):
    order = {
        "order_id": f"sim{int(time.time())}",
        "symbol": symbol,
        "side": side,
        "qty": qty,
        "status": "FILLED",
        "filled_price": price if price else get_latest_price(symbol)
    }
    return order

def get_account_balance():
    try:
        with open("balance.json", "r") as f:
            b = json.load(f)
            return float(b.get("cash", STARTING_CAPITAL))
    except:
        return STARTING_CAPITAL

def update_balance(new_cash):
    with open("balance.json", "w") as f:
        json.dump({"cash": float(new_cash)}, f)

# ----------------------------------------------------
# Strategy Logic
# ----------------------------------------------------
def calculate_position_size(cash, entry_price, stop_loss_amount):
    max_risk = cash * (RISK_PER_TRADE_PCT / 100)
    if stop_loss_amount <= 0:
        return 0
    qty = math.floor(max_risk / stop_loss_amount)
    return max(0, int(qty))

# ----------------------------------------------------
# Main Loop
# ----------------------------------------------------
def main_loop():
    telegram_send("🤖 Bot started successfully!")
    logging.info("Bot started")

    daily_loss_limit = STARTING_CAPITAL * (MAX_DAILY_LOSS_PCT / 100)
    starting_balance = get_account_balance()

    while True:
        cash = get_account_balance()
        loss = max(0, starting_balance - cash)

        if loss >= daily_loss_limit:
            telegram_send("⚠️ Daily loss limit reached. Bot stopped.")
            break

        price = get_latest_price(SYMBOL, INTERVAL)
        price_change = (price - 1000) / 1000 * 100

        if price_change < -0.2:
            stop_loss_amt = 2
            qty = calculate_position_size(cash, price, stop_loss_amt)
            if qty > 0:
                order = place_order("BUY", SYMBOL, qty)
                telegram_send(f"BUY {SYMBOL} qty={qty} price={order['filled_price']}")

                time.sleep(2)

                sell_price = order["filled_price"] + 3
                sell_order = place_order("SELL", SYMBOL, qty)
                telegram_send(f"SELL {SYMBOL} qty={qty} price={sell_order['filled_price']}")

                new_cash = cash - (qty * order["filled_price"]) + (qty * sell_order["filled_price"])
                update_balance(new_cash)

        time.sleep(20)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main_loop()
