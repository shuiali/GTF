Get All Tickers
GET
https://api-futures.kucoin.com/api/v1/allTickers
api-channel:
Public
api-permission:
NULL
api-rate-limit-pool:
Public
sdk-service:
Futures
sdk-sub-service:
Market
sdk-method-name:
getAllTickers
api-rate-limit-weight:
5
Description
This endpoint returns "last traded price/size", "best bid/ask price/size" etc. of all symbol.
These messages can also be obtained through Websocket.
Request
None
Request Code Samples
http.client
Requests
import http.client

conn = http.client.HTTPSConnection("api-futures.kucoin.com")
payload = ''
headers = {}
conn.request("GET", "/api/v1/allTickers", payload, headers)
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
200000 is for success, other is error
data
array [object {11}] 
required
sequence
integer <int64>
required
Sequence number, used to judge whether the messages pushed by Websocket are continuous.
symbol
string 
required
Symbol
side
enum<string> 
required
Trade direction
Allowed values:
buy
sell
size
integer 
required
Filled side; the trade side indicates the taker order side. A taker order is the order that was matched with orders opened on the order book.
tradeId
string 
required
Transaction ID
price
string 
required
Filled price
bestBidPrice
string 
required
Best bid price
bestBidSize
integer 
required
Best bid size
bestAskPrice
string 
required
Best ask price
bestAskSize
integer 
required
Best ask size
ts
integer <int64>
required
Filled time (nanoseconds)
Example
{
    "code": "200000",
    "data": [
        {
            "sequence": 1707992727046,
            "symbol": "XBTUSDTM",
            "side": "sell",
            "size": 21,
            "tradeId": "1784299761369",
            "price": "67153",
            "bestBidPrice": "67153",
            "bestBidSize": 2767,
            "bestAskPrice": "67153.1",
            "bestAskSize": 5368,
            "ts": 1729163466659000000
        },
        {
            "sequence": 1697895166299,
            "symbol": "XBTUSDM",
            "side": "sell",
            "size": 1956,
            "tradeId": "1697901245065",
            "price": "67145.2",
            "bestBidPrice": "67135.3",
            "bestBidSize": 1,
            "bestAskPrice": "67135.8",
            "bestAskSize": 3,
            "ts": 1729163445340000000
        }
    ]
}

Get Part OrderBook
GET
https://api-futures.kucoin.com/api/v1/level2/depth{size}
api-channel:
Public
api-permission:
NULL
api-rate-limit-pool:
Public
sdk-service:
Futures
sdk-sub-service:
Market
sdk-method-name:
getPartOrderBook
api-rate-limit-weight:
5
Discription
Query for part orderbook depth data (aggregated by price).
It is recommended that you submit requests via this endpoint as the system response will be faster and consume less traffic.
Request
Path Params
size
enum<string> 
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
Symbol of the contract. Please refer to Get Symbol endpoint: symbol
Example:
XBTUSDM
Request Code Samples
http.client
Requests
import http.client

conn = http.client.HTTPSConnection("api-futures.kucoin.com")
payload = ''
headers = {}
conn.request("GET", "/api/v1/level2/depth20?symbol=XBTUSDM", payload, headers)
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
sequence
integer <int64>
required
Sequence number
symbol
string 
required
Symbol of the contract. Please refer to Get Symbol endpoint: symbol
bids
array [array] 
required
bids, from high to low
asks
array [array] 
required
asks, from low to high
ts
integer <int64>
required
Timestamp (nanoseconds)
Example
{
    "code": "200000",
    "data": {
        "sequence": 1697895963339,
        "symbol": "XBTUSDM",
        "bids": [
            [
                66968,
                2
            ],
            [
                66964.8,
                25596
            ]
        ],
        "asks": [
            [
                66968.1,
                13501
            ],
            [
                66968.7,
                2032
            ]
        ],
        "ts": 1729168101216000000
    }
}

Get Klines
GET
https://api-futures.kucoin.com/api/v1/kline/query
api-channel:
Public
api-permission:
NULL
api-rate-limit-pool:
Public
sdk-service:
Futures
sdk-sub-service:
Market
sdk-method-name:
getKlines
api-rate-limit-weight:
3
Description
Get the symbol’s candlestick chart. Data are returned in grouped buckets based on requested type.
For each query, the system will return at most 500 pieces of data. To obtain more data, please page the data by time.
Tips
Candlestick chart data may be incomplete. No data is published for intervals where there are no ticks.
If the specified start/end time and the time granularity exceed the maximum size allowed for a single request, the system will only return 500 pieces of data for your request. If you want to get fine-grained data in a larger time range, you will need to specify the time ranges and make multiple requests for multiple times.
If you’ve specified only the start time in your request, the system will return 500 pieces of data from the specified start time to the current time of the system; if only the end time is specified, the system will return 500 pieces of data closest to the end time; if neither the start time nor the end time is specified, the system will return the 500 pieces of data closest to the current time of the system.
Request
Query Params
symbol
string 
required
Symbol of the contract. Please refer to Get Symbol endpoint: symbol, indexSymbol, premiumsSymbol1M, premiumsSymbol8H
Example:
XBTUSDTM
granularity
enum<integer> <int64>
required
Type of candlestick patterns (minutes)
Allowed values:
1
5
15
30
60
120
240
480
720
1440
10080
Example:
60
from
integer <int64>
optional
Start time (milliseconds)
Example:
1750389927000
to
integer <int64>
optional
End time (milliseconds)
Example:
1750393527000
Request Code Samples
http.client
Requests
import http.client

conn = http.client.HTTPSConnection("api-futures.kucoin.com")
payload = ''
headers = {}
conn.request("GET", "/api/v1/kline/query?symbol=XBTUSDTM&granularity=60&from=1750389927000&to=1750393527000", payload, headers)
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
number 
optional
Start time of the candle cycle, opening price, highest price, lowest price, closing price, transaction volume(lots),transaction volume
Example
{
    "code": "200000",
    "data": [
        [
            1757659080000,
            115328.4,
            115328.4,
            115284.2,
            115284.2,
            602,
            69424.9528
        ],
        [
            1757659140000,
            115273.0,
            115273.1,
            115273.0,
            115273.0,
            114,
            13141.1236
        ]
    ]
}

Ticker V2
wss://ws-api-futures.kucoin.com
Topic: /contractMarket/tickerV2:{symbol}
Description
Subscribe this topic to get the realtime push of BBO changes.
After subscription, when there are changes in the order book（Not necessarily ask1/bid1 changes）, the system will push the real-time ticker symbol information to you.
Push frequency: real-time
Tips
This topic shares the sn and sequence fields with the Order Book – Incremental Updates topic (/contractMarket/level2), and the values of both fields are identical.
Since this topic only pushes updates of the best bid / best ask prices and their corresponding quantities, the fields behave as follows:
sn and sequence increase in chronological order;
however, the values are not guaranteed to be continuous, because updates are triggered only when the top-of-book price or quantity changes.
Subscribe Message
{
  "id": 1545910660739,
  "type": "subscribe",
  "topic": "/contractMarket/tickerV2:XBTUSDTM",
  "response": true
}
Response
Data Schema
tickerv2
topic
string 
required
type
string 
required
subject
string 
required
sn
integer 
required
data
object 
required
symbol
string 
required
sequence
integer <int64>
required
bestBidSize
integer 
required
bestBidPrice
string 
required
bestAskPrice
string 
required
bestAskSize
integer 
required
ts
integer <int64>
required
The exchange's market service pushing time
Example
{
    "topic": "/contractMarket/tickerV2:XBTUSDTM",
    "type": "message",
    "subject": "tickerV2",
    "sn": 1713516609293,
    "data": {
        "symbol": "XBTUSDTM",
        "sequence": 1713516609293,
        "bestBidSize": 5044,
        "bestBidPrice": "86454.5",
        "bestAskPrice": "86454.6",
        "bestAskSize": 73,
        "ts": 1740641976241000000
    }
}
Request
Query Params
token
string 
required
The token required to establish a websocket connection
Example:
2neAiuYvAU61ZDXANAGAsiL4-iAExhsBXZxftpOeh_55i3Ysy2q2LEsEWU64mdzUOPusi34M_wGoSf7iNyEWJ_pJ4WOMrwXMkyIhbECvhdq1zW8Pg6yrotiYB9J6i9GjsxUuhPw3Blq6rhZlGykT3Vp1phUafnulOOpts-MEmEHyp3o1vulUJC6hiN9fkz7dJBvJHl5Vs9Y=.4wBgWQDXBCMJy3lMEoRLGw==
connectId
string 
optional
Connection Id, a unique value taken from the client side. Both the id of the welcome message and the id of the error message are connectId.
Example:
121345

Orderbook - Level 50
wss://ws-api-futures.kucoin.com
Topic: /contractMarket/level2Depth50:{symbol}
Description
The system will return the 50 best ask/bid orders data
If there is no change in the market, data will not be pushed
Push frequency: 100ms
Subscribe Message
{
  "id": 1545910660739,
  "type": "subscribe",
  "topic": "/contractMarket/level2Depth50:XBTUSDTM",
  "response": true
}
Response
Data Schema
orderbookLevel50
topic
string 
required
type
string 
required
subject
string 
required
sn
integer 
required
data
object 
required
bids
array [array] 
required
sequence
integer <int64>
required
timestamp
integer <int64>
required
Timestamp of pushing task. After Match engine timestamp in milliseconds
ts
integer <int64>
required
Timestamp of pushing task. After Match engine timestamp in milliseconds
asks
array [array] 
required
Example
{
    "topic": "/contractMarket/level2Depth50:XBTUSDTM",
    "type": "message",
    "subject": "level2",
    "sn": 1731680249700,
    "data": {
        "bids": [
            [
                "89778.6",
                1534
            ],
            [
                "89778.2",
                54
            ]
        ],
        "sequence": 1709294490099,
        "timestamp": 1731680249700,
        "ts": 1731680249700,
        "asks": [
            [
                "89778.7",
                854
            ],
            [
                "89779.2",
                4
            ]
        ]
    }
}
Request
Query Params
token
string 
required
The token required to establish a websocket connection
Example:
2neAiuYvAU61ZDXANAGAsiL4-iAExhsBXZxftpOeh_55i3Ysy2q2LEsEWU64mdzUOPusi34M_wGoSf7iNyEWJ_cpz4VOPFmQFib6P8hYnrVkopegzA-XTtiYB9J6i9GjsxUuhPw3Blq6rhZlGykT3Vp1phUafnulOOpts-MEmEE_W_XygA1q6ypUyk3f_-aZJBvJHl5Vs9Y=.rIAVDSL657g7mnAiHkH5aA==
connectId
string 
optional
Connection Id, a unique value taken from the client side. Both the id of the welcome message and the id of the error message are connectId.
Example:
121345