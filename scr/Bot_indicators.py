'''
*Connection to Binance: Use API keys to connect in testnet mode.
*Historical data collection: Obtains 5-minute candles (last 200) to analyze prices.
*Calculation of technical indicators: Uses simple moving averages (50 and 200 periods), RSI, and MACD.
*Detection of buy and sell signals: Based on the MACD crossing its signal line and RSI levels.
*Order management: Buys or sells ETH according to the signals, considering available balances.
*Continuous loop: Runs each cycle every 15 minutes, updating data and making decisions.'''


from binance.client import Client
import pandas as pd
import ta
import time

# your Api keys
api_key = 'your Api key'
api_secret = 'your secret key'

# Create client with testnet
client = Client(api_key, api_secret, testnet=True)
symbol = 'ETHUSDT'

def get_historical_data(symbol, interval='5m', limit=200):
    try:
        candles = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(candles, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_volume', 'taker_buy_buy', 'ignore'
        ])
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close'] = pd.to_numeric(df['close'])
        return df
    except Exception as e:
        print("Error getting data:", e)
        return pd.DataFrame()

def calculate_indicators(df):
    df['SMA50'] = df['close'].rolling(50).mean()
    df['SMA200'] = df['close'].rolling(200).mean()
    df['RSI'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()
    macd = ta.trend.MACD(close=df['close'])
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    return df

def get_symbol_info(symbol):
    info = client.get_symbol_info(symbol)
    lot_size_filter = next(filter(lambda f: f['filterType'] == 'LOT_SIZE', info['filters']))
    min_qty = float(lot_size_filter['minQty'])
    step_size = float(lot_size_filter['stepSize'])
    return min_qty, step_size

# Function to find out how much ETH you can buy
def get_buy_quantity():
    try:
        account_info = client.get_account()
        usdt_balance = 0
        for asset in account_info['balances']:
            if asset['asset'] == 'USDT':
                usdt_balance = float(asset['free'])
        print(f"USDT available for purchase: {usdt_balance}")

        # adjust the % you want to use from your USDT balance
        budget = usdt_balance * 0.5  

        ticker = client.get_symbol_ticker(symbol=symbol)
        price = float(ticker['price'])
        print(f"Current price: {price}")

        qty = budget / price
        min_qty, step_size = get_symbol_info(symbol)

        if qty < min_qty:
            print(f"Calculated amount {qty} below the minimum {min_qty}.")
            return 0

        qty = (qty // step_size) * step_size
        if qty < min_qty:
            print(f"After rounding, amount {qty} below the minimum.")
            return 0
        return qty
    except Exception as e:
        print("Error en get_buy_quantity:", e)
        return 0

# Function to obtain how much ETH you have to sell
def get_sell_quantity():
    try:
        account_info = client.get_account()
        eth_balance = 0
        for asset in account_info['balances']:
            if asset['asset'] == 'ETH':
                eth_balance = float(asset['free'])
        print(f"ETH available for sale: {eth_balance}")
        return eth_balance
    except Exception as e:
        print("Error en get_sell_quantity:", e)
        return 0

def execute_order(symbol, side, quantity):
    if quantity <= 0:
        print("Invalid quantity for order.")
        return
    try:
        order = client.create_order(
            symbol=symbol,
            side=side.upper(),
            type='MARKET',
            quantity=quantity
        )
        print(f"{side.capitalize()} order executed with quantity: {quantity}. ID: {order['orderId']}")
    except Exception as e:
        print("Error placing order:", e)

# Variables for controlling signals
last_signal = None
print("Starting trading cycle...")

while True:
    print("Running cycle...")
    df = get_historical_data(symbol)
    if df.empty:
        print("No data obtained, waiting 60 seconds...")
        time.sleep(60)
        continue
    else:
        print(f"Data received: {len(df)} rows")
    df = calculate_indicators(df)
    print("Calculated indicators.")
    
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    print(f"Last row:\n{last_row[['close', 'MACD', 'RSI']]}")
    print(f"Second to last row:\n{prev_row[['close', 'MACD', 'RSI']]}")

    # Conditions for purchase
    if (last_row['MACD'] > last_row['MACD_signal'] + 0.5) and (last_row['RSI'] < 80):
        print("Purchase condition fulfilled.")
        if last_signal != 'buy':
            qty_buy = get_buy_quantity()  # calculate how much to buy
            if qty_buy > 0:
                execute_order(symbol, 'buy', qty_buy)
                last_signal = 'buy'

    # Conditions for selling
    elif (last_row['MACD'] < last_row['MACD_signal'] - 0.5) and (last_row['RSI'] > 20):
        print("Condition of sale fulfilled.")
        if last_signal != 'sell':
            qty_sell = get_sell_quantity()  # calculate how much to sell
            if qty_sell > 0:
                execute_order(symbol, 'sell', qty_sell)
                last_signal = 'sell'

    print("Sleeping for 10 minutes...")
    time.sleep(600)
