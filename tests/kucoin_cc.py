'''This is a test code just to check the conection between 
bot and exchange, where we'll use the ccxt framework to work'''

import ccxt  

# Set up exchange credentials
api_key = 'your api key'  
api_secret = 'your secret key'  
password = 'your password'  # the password you set when creating the API (in case it's kucoin)

# Create the Kucoin instance  
kucoin = ccxt.kucoin({  
    'apiKey': api_key,  
    'secret': api_secret,  
    'password': password,  # in case it's kucoin  
})  

try:  
    # Get  balance  
    balance = kucoin.fetch_balance()  
    print("Balance:", balance)  

    # Obtener price of BTC/USDT  
    ticker = kucoin.fetch_ticker('BTC/USDT')  
    print("Precio de BTC/USDT:", ticker['last'])  

except ccxt.BaseError as e:  
    print("Error:", e)  