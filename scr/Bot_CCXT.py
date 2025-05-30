import ccxt
import time

api_key = 'YOUR_API_KEY'
api_secret = 'YOUR_API_SECRET'

symbol= 'ETH/USDT'

# Create instance and activate sandbox mode
binance_testnet = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True, #es un parámetro booleano que, cuando se establece en True, indica a ccxt que 
})                           #debe gestionar automáticamente el control de la tasa de llamadas a la API.

binance_testnet.set_sandbox_mode(True)
exchange = ccxt.binance({ 'timeout': 30000 })

############################################-2-#############################################################


markets = binance_testnet.fetch_markets()  #Get market list 

market_info = next((m for m in markets if m['symbol'] == symbol), None) #Search the markets for information on the 'ETH/USDT' pair.

filters = market_info['info'].get('filters', []) #From that information, you get the list of filters, which contain market-specific limits and rules.

notional_filter = next((f for f in filters if f['filterType'] == 'NOTIONAL'), None) #Look for a filter of the 'NOTIONAL' type, which indicates the minimum order amount in USDT.

if notional_filter:
    min_notional = float(notional_filter['minNotional']) #If there is a 'NOTIONAL' filter, the minimum allowed value is obtained,
else:                                                    # converted to a number. If there is no 'NOTIONAL' filter, a default value is assigned.
    min_notional = 10  # Default 10 USDT

#print("Notional minimum:", min_notional, "USDT")

###########################################-3-######################################################################

# Configuring bot parameters and variables
MIN_USDT = max(10, min_notional)
last_order_id = None
POSITION = None  # 'long' o None
consecutive_errors = 0
max_errors = 5

##############################################-4-###################################################################
def create_order(symbol, order_type, side, amount): # order_type if we want to add other type
    order= None

    try:
      
        if order_type == 'market':
             if side == 'buy':
                order = binance_testnet.create_market_buy_order(symbol, amount)

             elif side == 'sell':
                order = binance_testnet.create_market_sell_order(symbol, amount)
                
        if order:
            print("Order created:", order)
        return order
   
    except ccxt.BaseError as e:
        print("Error creating order:", e)
        return None
##############################################-5-###################################################################

def get_current_price():
    ticker = binance_testnet.fetch_ticker(symbol)
    return ticker['last']

###############################################-6-##################################################################

try:
    while True:
        current_price = get_current_price()
        print("Current price:", current_price)

        
        amount = max(MIN_USDT / current_price, 0.0001) # Calculate quantity

        if POSITION != 'long': # Check if there is an active order or if the operation has already been completed
            print("No position, trying to buy...")

            order = create_order(symbol, 'market', 'buy', amount) # funtion call

            if order:
                last_buy_price = current_price
                POSITION = 'long'
                consecutive_errors = 0


            else:
                consecutive_errors += 1

        else: #Evaluation to sell or buy more

            price_change = (current_price - last_buy_price) / last_buy_price

            if price_change >= 0.005: # If there is an increase >= 0.5%
                print("Up 0.5%, selling...")
                order = create_order(symbol, 'market', 'sell', amount)

                if order: # If the sale is successful, reset POSITION to None and last_buy_price
                    POSITION = None
                    last_buy_price = None
                    consecutive_errors = 0
                else:
                    consecutive_errors += 1

            elif price_change <= -0.005: # If there is a drop >= 0.5%:
                print("0.5%, drop, buying more...")
                order = create_order(symbol, 'market', 'buy', amount)
                if order:
                    last_buy_price = current_price
                    consecutive_errors = 0

                else:
                    consecutive_errors += 1

        
        if consecutive_errors >= max_errors: # If consecutive errors reach max_errors (5), print message and break the loop
            print("Too many consecutive errors, stopping.")
            break

        time.sleep(20) # If not, wait 20 seconds before the next iteration

except KeyboardInterrupt: # When you press Ctrl+C, it catches KeyboardInterrupt and displays a message to stop it manually.
    print("Stopped manually.")