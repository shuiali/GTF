Get Symbols - Cross Margin
GET
https://api.kucoin.com/api/v3/margin/symbols
api-channel:
Public
api-permission:
NULL
api-rate-limit-pool:
Public
sdk-service:
Margin
sdk-sub-service:
Market
sdk-method-name:
getCrossMarginSymbols
api-rate-limit-weight:
3
Description
This endpoint allows querying the configuration of cross margin symbol.
Request
Query Params
symbol
string 
optional
If not provided, all cross margin symbol will be queried. If provided, only the specified symbol will be queried.
Examples:
BTC-USDT
ETH-USDT
KCS-USDT
Request Code Samples
http.client
Requests
import http.client

conn = http.client.HTTPSConnection("api.kucoin.com")
payload = ''
headers = {}
conn.request("GET", "/api/v3/margin/symbols?symbol=null", payload, headers)
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
data
object 
required
timestamp
integer <int64>
required
items
array [object {16}] 
required
Example
{
    "code": "200000",
    "data": {
        "timestamp": 1729665839353,
        "items": [
            {
                "symbol": "BTC-USDT",
                "name": "BTC-USDT",
                "enableTrading": true,
                "market": "USDS",
                "baseCurrency": "BTC",
                "quoteCurrency": "USDT",
                "baseIncrement": "0.00000001",
                "baseMinSize": "0.00001",
                "baseMaxSize": "10000000000",
                "quoteIncrement": "0.000001",
                "quoteMinSize": "0.1",
                "quoteMaxSize": "99999999",
                "priceIncrement": "0.1",
                "feeCurrency": "USDT",
                "priceLimitRate": "0.1",
                "minFunds": "0.1"
            }
        ]
    }
}

Get Symbols - Isolated Margin
GET
https://api.kucoin.com/api/v1/isolated/symbols
api-channel:
Public
api-permission:
NULL
api-rate-limit-pool:
Public
sdk-service:
Margin
sdk-sub-service:
Market
sdk-method-name:
getIsolatedMarginSymbols
api-rate-limit-weight:
3
Description
This endpoint allows querying the configuration of isolated margin symbol.
Request
None
Request Code Samples
http.client
Requests
import http.client

conn = http.client.HTTPSConnection("api.kucoin.com")
payload = ''
headers = {}
conn.request("GET", "/api/v1/isolated/symbols", payload, headers)
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
data
array [object {14}] 
required
symbol
string 
required
symbol
symbolName
string 
required
Symbol name
baseCurrency
string 
required
Base currency, e.g. BTC.
quoteCurrency
string 
required
Quote currency, e.g. USDT.
maxLeverage
integer 
required
Max. leverage of this symbol
flDebtRatio
string 
required
tradeEnable
boolean 
required
autoRenewMaxDebtRatio
string 
required
baseBorrowEnable
boolean 
required
quoteBorrowEnable
boolean 
required
baseTransferInEnable
boolean 
required
quoteTransferInEnable
boolean 
required
baseBorrowCoefficient
string 
required
quoteBorrowCoefficient
string 
required
Example
{
    "code": "200000",
    "data": [
        {
            "symbol": "BTC-USDT",
            "symbolName": "BTC-USDT",
            "baseCurrency": "BTC",
            "quoteCurrency": "USDT",
            "maxLeverage": 10,
            "flDebtRatio": "0.97",
            "tradeEnable": true,
            "autoRenewMaxDebtRatio": "0.96",
            "baseBorrowEnable": true,
            "quoteBorrowEnable": true,
            "baseTransferInEnable": true,
            "quoteTransferInEnable": true,
            "baseBorrowCoefficient": "1",
            "quoteBorrowCoefficient": "1"
        }
    ]
}

Get All Tickers
GET
https://api.kucoin.com/api/v1/market/allTickers
api-channel:
Public
api-permission:
NULL
api-rate-limit-pool:
Public
sdk-service:
Spot
sdk-sub-service:
Market
sdk-method-name:
getAllTickers
api-rate-limit-weight:
15
Description
Request market tickers for all the trading pairs in the market (including 24h volume); takes a snapshot every 2 seconds.
On the rare occasion that we change the currency name, if you still want the changed symbol name, you can use the symbolName field instead of the symbol field via “Get Symbols List” endpoint.
Request
None
Request Code Samples
http.client
Requests
import http.client

conn = http.client.HTTPSConnection("api.kucoin.com")
payload = ''
headers = {}
conn.request("GET", "/api/v1/market/allTickers", payload, headers)
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
data
object 
required
time
integer <int64>
required
timestamp
ticker
array [object {18}] 
required
symbol
string 
required
Symbol
symbolName
string 
required
Name of trading pairs, it will change after renaming
buy
string 
required
Best bid price
bestBidSize
string 
required
Best bid size
sell
string 
required
Best ask price
bestAskSize
string 
required
Best ask size
changeRate
string 
required
24h change rate
changePrice
string 
required
24h change price
high
string 
required
Highest price in 24h
low
string 
required
Lowest price in 24h
vol
string 
required
24h volume, executed based on base currency
volValue
string 
required
24h traded amount
last
string 
required
Last traded price
averagePrice
string 
required
Average trading price in the last 24 hours
takerFeeRate
string 
required
Basic Taker Fee
makerFeeRate
string 
required
Basic Maker Fee
takerCoefficient
string 
required
The taker fee coefficient. The actual fee needs to be multiplied by this coefficient to get the final fee. Most currencies have a coefficient of 1. If set to 0, it means no fee
makerCoefficient
string 
required
The maker fee coefficient. The actual fee needs to be multiplied by this coefficient to get the final fee. Most currencies have a coefficient of 1. If set to 0, it means no fee
Example
{
    "code": "200000",
    "data": {
        "time": 1729173207043,
        "ticker": [
            {
                "symbol": "BTC-USDT",
                "symbolName": "BTC-USDT",
                "buy": "67192.5",
                "bestBidSize": "0.000025",
                "sell": "67192.6",
                "bestAskSize": "1.24949204",
                "changeRate": "-0.0014",
                "changePrice": "-98.5",
                "high": "68321.4",
                "low": "66683.3",
                "vol": "1836.03034612",
                "volValue": "124068431.06726933",
                "last": "67193",
                "averagePrice": "67281.21437289",
                "takerFeeRate": "0.001",
                "makerFeeRate": "0.001",
                "takerCoefficient": "1",
                "makerCoefficient": "1"
            }
        ]
    }
}

Get Klines
GET
https://api.kucoin.com/api/v1/market/candles
api-channel:
Public
api-permission:
NULL
api-rate-limit-pool:
Public
sdk-service:
Spot
sdk-sub-service:
Market
sdk-method-name:
getKlines
api-rate-limit-weight:
3
Description
Get the Kline of the symbol. Data are returned in grouped buckets based on requested type.
For each query, the system would return at most 1500 pieces of data. To obtain more data, please page the data by time.
Tips
Klines data may be incomplete. No data is published for intervals where there are no ticks.
Request
Query Params
symbol
string 
required
symbol
Example:
BTC-USDT
type
enum<string> 
required
Type of candlestick patterns: 1min, 3min, 5min, 15min, 30min, 1hour, 2hour, 4hour, 6hour, 8hour, 12hour, 1day, 1week, 1month
Allowed values:
1min
3min
5min
15min
30min
1hour
2hour
4hour
6hour
8hour
12hour
1day
1week
1month
Example:
1hour
startAt
integer <int64>
optional
Start time (second), default is 0
Default:
0
Example:
1750389927
endAt
integer <int64>
optional
End time (second), default is 0
Default:
0
Example:
1750393527
Request Code Samples
http.client
Requests
import http.client

conn = http.client.HTTPSConnection("api.kucoin.com")
payload = ''
headers = {}
conn.request("GET", "/api/v1/market/candles?symbol=BTC-USDT&type=1hour&startAt=1750389927&endAt=1750393527", payload, headers)
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
data
array [array] 
required
string 
optional
Start time of the candle cycle (unix time), opening price, closing price, highest price, Lowest price, Transaction volume (in base asset), Transaction amount (in quote asset)
Example
{
    "code": "200000",
    "data": [
        [
            "1566789720",
            "10411.5",
            "10401.9",
            "10411.5",
            "10396.3",
            "29.11357276",
            "302889.301529914"
        ],
        [
            "1566789660",
            "10416",
            "10411.5",
            "10422.3",
            "10411.5",
            "15.61781842",
            "162703.708997029"
        ],
        [
            "1566789600",
            "10408.6",
            "10416",
            "10416",
            "10405.4",
            "12.45584973",
            "129666.51508559"
        ]
    ]
}

Get Part OrderBook
GET
https://api.kucoin.com/api/v1/market/orderbook/level2_{size}
api-channel:
Public
api-permission:
NULL
api-rate-limit-pool:
Public
sdk-service:
Spot
sdk-sub-service:
Market
sdk-method-name:
getPartOrderBook
api-rate-limit-weight:
2
Description
Query for part orderbook depth data. (aggregated by price)
You are recommended to request via this endpoint as the system reponse would be faster and cosume less traffic.
Request
Path Params
size
enum<integer> <int32>
required
Get the depth layer, optional value: 20, 100
Allowed values:
20
100
Example:
20
Query Params
symbol
string 
required
symbol
Example:
BTC-USDT
Request Code Samples
http.client
Requests
import http.client

conn = http.client.HTTPSConnection("api.kucoin.com")
payload = ''
headers = {}
conn.request("GET", "/api/v1/market/orderbook/level2_20?symbol=BTC-USDT", payload, headers)
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
data
object 
required
time
integer <int64>
required
Timestamp(millisecond)
sequence
string 
required
Sequence number
bids
array [array] 
required
bids, from high to low
string 
optional
Price, Size
asks
array [array] 
required
asks, from low to high
string 
optional
Price, Size
Example
{
    "code": "200000",
    "data": {
        "time": 1729176273859,
        "sequence": "14610502970",
        "bids": [
            [
                "66976.4",
                "0.69109872"
            ],
            [
                "66976.3",
                "0.14377"
            ]
        ],
        "asks": [
            [
                "66976.5",
                "0.05408199"
            ],
            [
                "66976.8",
                "0.0005"
            ]
        ]
    }
}

Ticker
wss://ws-api-spot.kucoin.com
Topic: /market/ticker:{symbol},{symbol}
Description
Subscribe to this topic to get the specified symbol push of BBO changes.
A topic supports up to 100 symbols.
Push frequency: once every 100ms
Subscribe Message
{
  "id": 1545910660739,
  "type": "subscribe",
  "topic": "/market/ticker:BTC-USDT",
  "response": true
}
Response
Data Schema
ticker
type
string 
required
topic
string 
required
subject
string 
required
data
object 
required
sequence
string 
required
Sequence number
price
string 
required
Last traded price
size
string 
required
Last traded amount
bestAsk
string 
required
Best ask price
bestAskSize
string 
required
Best ask size
bestBid
string 
required
Best bid price
bestBidSize
string 
required
Best bid size
time
integer <int64>
required
Timestamp of matching-engine last execution(only for matched, not include bbo change)
Example
{
  "type": "message",
  "topic": "/market/ticker:BTC-USDT",
  "subject": "trade.ticker",
  "data": {
    "sequence": "1545896668986", // Sequence number
    "price": "0.08", // Last traded price
    "size": "0.011", //  Last traded amount
    "bestAsk": "0.08", // Best ask price
    "bestAskSize": "0.18", // Best ask size
    "bestBid": "0.049", // Best bid price
    "bestBidSize": "0.036", // Best bid size
    "Time": 1704873323416 //The matching time of the latest transaction
  }
}      
Request
Query Params
token
string 
required
The token required to establish a websocket connection
Example:
2neAiuYvAU61ZDXANAGAsiL4-iAExhsBXZxftpOeh_55i3Ysy2q2LEsEWU64mdzUOPusi34M_wGoSf7iNyEWJ2gZJLp3fgqGGvpzdfennGL3R06_0gIS-diYB9J6i9GjsxUuhPw3Blq6rhZlGykT3Vp1phUafnulOOpts-MEmEF-3bpfetLOAjzQ04YZ_8fRJBvJHl5Vs9Y=.28mIdGU0xg5pJ6TpPYIhjg==
connectId
string 
optional
Connection Id, a unique value taken from the client side. Both the id of the welcome message and the id of the error message are connectId.
Example:
121345

Orderbook - Level 50
wss://ws-api-spot.kucoin.com
Topic:/spotMarket/level2Depth50:{symbol},{symbol}
Description
The system will return the 50 best ask/bid orders data
A topic supports up to 100 symbols.
If there is no change in the market, data will not be pushed
Push frequency: once every 100ms
Subscribe Message
{
  "id": 1545910660739,
  "type": "subscribe",
  "topic": "/spotMarket/level2Depth50:BTC-USDT",
  "response": true
}
Response
Data Schema
orderbookLevel50
type
string 
required
topic
string 
required
subject
string 
required
data
object 
required
asks
array [array] 
required
Ask order data, each entry containing price and size.
string 
optional
bids
array [array] 
required
Bid order data, each entry containing price and size.
string 
optional
timestamp
integer <int64>
required
Timestamp of matching-engine last execution
Example
{
    "topic": "/spotMarket/level2Depth50:BTC-USDT",
    "type": "message",
    "subject": "level2",
    "data": {
        "asks": [
            [
                "95964.3",
                "0.08168874"
            ],
        ],
        "bids": [
            [
                "95964.2",
                "1.35483359"
            ],
        ],
        "timestamp": 1733124805073
    }
}

Request
Query Params
token
string 
required
The token required to establish a websocket connection
Example:
2neAiuYvAU61ZDXANAGAsiL4-iAExhsBXZxftpOeh_55i3Ysy2q2LEsEWU64mdzUOPusi34M_wGoSf7iNyEWJ_dm3WIc2VYfQG_14cxWCE7mHih-uOn90tiYB9J6i9GjsxUuhPw3Blq6rhZlGykT3Vp1phUafnulOOpts-MEmEEospqlVGyc9kAqzTuhanTCJBvJHl5Vs9Y=.CHw5RcLXqmXUv-MVK2otxw==
connectId
string 
optional
Connection Id, a unique value taken from the client side. Both the id of the welcome message and the id of the error message are connectId.
Example:
121345