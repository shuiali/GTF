Get Ticker
GET
https://api.kucoin.com/api/ua/v1/market/ticker
api-channel:
Public
api-permission:
NULL
api-rate-limit-pool:
Public
sdk-service:
UTA
sdk-sub-service:
Market
sdk-method-name:
getTicker
api-rate-limit-weight:
15
Description
Request market tickers for the trading pairs in the market (including 24h volume);
takes a snapshot every 2 seconds.
In rare cases, we may change the currency name. If you still need the changed symbol name, you can use the “name“ instead of the ”symbol“ (but still need to use the symbol for normal transactions).
Request
Query Params
tradeType
enum<string> 
required
Product type
Allowed values:
SPOT
FUTURES
Example:
SPOT
symbol
string 
optional
When the parameter is not provided, all symbols will be returned
Example:
BTC-USDT
Request Code Samples
http.client
Requests
import http.client

conn = http.client.HTTPSConnection("api.kucoin.com")
payload = ''
headers = {}
conn.request("GET", "/api/ua/v1/market/ticker?tradeType=SPOT&symbol=BTC-USDT", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
Responses
🟢200
OK
application/json
code
string 
required
Response code
data
object 
required
tradeType
string 
required
Product type
ts
integer <int64>
required
Timestamp (nanoseconds)
list
array [object {13}] 
required
List of trading pair data
Example
{
    "code": "200000",
    "data": {
        "tradeType": "SPOT",
        "ts": 1768212175595000000,
        "list": [
            {
                "symbol": "BTC-USDT",
                "name": "BTC-USDT",
                "bestBidSize": "0.54365161",
                "bestBidPrice": "90592.1",
                "bestAskSize": "0.08703283",
                "bestAskPrice": "90592.2",
                "lastPrice": "90592.2",
                "size": "0.00001208",
                "open": "90738.1",
                "high": "92519.4",
                "low": "90236.3",
                "baseVolume": "6827.573519",
                "quoteVolume": "624153159.421449556"
            }
        ]
    }
}