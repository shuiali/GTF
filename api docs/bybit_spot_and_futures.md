Get Tickers
Query for the latest price snapshot, best bid/ask price, and trading volume in the last 24 hours.

Covers: Spot / USDT contract / USDC contract / Inverse contract / Option

info
If category=option, symbol or baseCoin must be passed.

HTTP Request
GET /v5/market/tickers

Request Parameters
Parameter	Required	Type	Comments
category	true	string	Product type. spot,linear,inverse,option
symbol	false	string	Symbol name, like BTCUSDT, uppercase only
baseCoin	false	string	Base coin, uppercase only. Apply to option only
expDate	false	string	Expiry date. e.g., 25DEC22. Apply to option only
Response Parameters
Linear/Inverse
Option
Spot
Parameter	Type	Comments
category	string	Product type
list	array	Object
> symbol	string	Symbol name
> bid1Price	string	Best bid price
> bid1Size	string	Best bid size
> ask1Price	string	Best ask price
> ask1Size	string	Best ask size
> lastPrice	string	Last price
> prevPrice24h	string	Market price 24 hours ago
> price24hPcnt	string	Percentage change of market price relative to 24h
> highPrice24h	string	The highest price in the last 24 hours
> lowPrice24h	string	The lowest price in the last 24 hours
> turnover24h	string	Turnover for 24h
> volume24h	string	Volume for 24h
> usdIndexPrice	string	USD index price
used to calculate USD value of the assets in Unified account
non-collateral margin coin returns ""
Only those trading pairs like "XXX/USDT" or "XXX/USDC" have the value
RUN >>
Request Example
Inverse
Option
Spot
HTTP
Python
GO
Java
Node.js
from pybit.unified_trading import HTTP
session = HTTP(testnet=True)
print(session.get_tickers(
    category="spot",
    symbol="BTCUSDT",
))

Response Example
Inverse
Option
Spot
{
    "retCode": 0,
    "retMsg": "OK",
    "result": {
        "category": "spot",
        "list": [
            {
                "symbol": "BTCUSDT",
                "bid1Price": "20517.96",
                "bid1Size": "2",
                "ask1Price": "20527.77",
                "ask1Size": "1.862172",
                "lastPrice": "20533.13",
                "prevPrice24h": "20393.48",
                "price24hPcnt": "0.0068",
                "highPrice24h": "21128.12",
                "lowPrice24h": "20318.89",
                "turnover24h": "243765620.65899866",
                "volume24h": "11801.27771",
                "usdIndexPrice": "20784.12009279"
            }
        ]
    },
    "retExtInfo": {},
    "time": 1673859087947
}

Get Orderbook
Query for orderbook depth data.

Covers: Spot / USDT contract / USDC contract / Inverse contract / Option

Contract: 1000-level of orderbook data
Spot: 1000-level of orderbook data
Option: 25-level of orderbook data
info
The response is in the snapshot format.
Retail Price Improvement (RPI) orders will not be included in the response message and will not be visible over API.
HTTP Request
GET /v5/market/orderbook

Request Parameters
Parameter	Required	Type	Comments
category	true	string	Product type. spot, linear, inverse, option
symbol	true	string	Symbol name, like BTCUSDT, uppercase only
limit	false	integer	Limit size for each bid and ask
spot: [1, 200]. Default: 1.
linear&inverse: [1, 500]. Default: 25.
option: [1, 25]. Default: 1.
Response Parameters
Parameter	Type	Comments
s	string	Symbol name
b	array	Bid, buyer. Sorted by price in descending order
> b[0]	string	Bid price
> b[1]	string	Bid size
a	array	Ask, seller. Sorted by price in ascending order
> a[0]	string	Ask price
> a[1]	string	Ask size
ts	integer	The timestamp (ms) that the system generates the data
u	integer	Update ID, is always in sequence
For contract, corresponds to u in the 1000-level WebSocket orderbook stream
For spot, corresponds to u in the 1000-level WebSocket orderbook stream
seq	integer	Cross sequence
You can use this field to compare different levels orderbook data, and for the smaller seq, then it means the data is generated earlier.
cts	integer	The timestamp from the matching engine when this orderbook data is produced. It can be correlated with T from public trade channel
RUN >>
Request Example
HTTP
Python
Go
Java
Node.js
from pybit.unified_trading import HTTP
session = HTTP(testnet=True)
print(session.get_orderbook(
    category="linear",
    symbol="BTCUSDT",
))

Response Example
{
    "retCode": 0,
    "retMsg": "OK",
    "result": {
        "s": "BTCUSDT",
        "a": [
            [
                "65557.7",
                "16.606555"
            ]
        ],
        "b": [
            [
                "65485.47",
                "47.081829"
            ]
        ],
        "ts": 1716863719031,
        "u": 230704,
        "seq": 1432604333,
        "cts": 1716863718905
    },
    "retExtInfo": {},
    "time": 1716863719382
}

Get Kline
Query for historical klines (also known as candles/candlesticks). Charts are returned in groups based on the requested interval.

Covers: Spot / USDT contract / USDC contract / Inverse contract

HTTP Request
GET /v5/market/kline

Request Parameters
Parameter	Required	Type	Comments
category	false	string	Product type. spot,linear,inverse
When category is not passed, use linear by default
symbol	true	string	Symbol name, like BTCUSDT, uppercase only
interval	true	string	Kline interval. 1,3,5,15,30,60,120,240,360,720,D,W,M
start	false	integer	The start timestamp (ms)
end	false	integer	The end timestamp (ms)
limit	false	integer	Limit for data size per page. [1, 1000]. Default: 200
Response Parameters
Parameter	Type	Comments
category	string	Product type
symbol	string	Symbol name
list	array	
An string array of individual candle
Sort in reverse by startTime
> list[0]: startTime	string	Start time of the candle (ms)
> list[1]: openPrice	string	Open price
> list[2]: highPrice	string	Highest price
> list[3]: lowPrice	string	Lowest price
> list[4]: closePrice	string	Close price. Is the last traded price when the candle is not closed
> list[5]: volume	string	Trade volume
USDT or USDC contract: unit is base coin (e.g., BTC)
Inverse contract: unit is quote coin (e.g., USD)
> list[6]: turnover	string	Turnover.
USDT or USDC contract: unit is quote coin (e.g., USDT)
Inverse contract: unit is base coin (e.g., BTC)
RUN >>
Request Example
HTTP
Python
Go
Java
Node.js
from pybit.unified_trading import HTTP
session = HTTP(testnet=True)
print(session.get_kline(
    category="inverse",
    symbol="BTCUSD",
    interval=60,
    start=1670601600000,
    end=1670608800000,
))

Response Example
{
    "retCode": 0,
    "retMsg": "OK",
    "result": {
        "symbol": "BTCUSD",
        "category": "inverse",
        "list": [
            [
                "1670608800000",
                "17071",
                "17073",
                "17027",
                "17055.5",
                "268611",
                "15.74462667"
            ],
            [
                "1670605200000",
                "17071.5",
                "17071.5",
                "17061",
                "17071",
                "4177",
                "0.24469757"
            ],
            [
                "1670601600000",
                "17086.5",
                "17088",
                "16978",
                "17071.5",
                "6356",
                "0.37288112"
            ]
        ]
    },
    "retExtInfo": {},
    "time": 1672025956592
}

Get Coin Info
Query coin information, including chain information, withdraw and deposit status.

HTTP Request
GET /v5/asset/coin/query-info

Request Parameters
Parameter	Required	Type	Comments
coin	false	string	Coin, uppercase only
Response Parameters
Parameter	Type	Comments
rows	array	Object
> name	string	Coin name
> coin	string	Coin
> remainAmount	string	Maximum withdraw amount per transaction
> chains	array	Object
>> chain	string	Chain
>> chainType	string	Chain type
>> confirmation	string	Number of confirmations for deposit: Once this number is reached, your funds will be credited to your account and available for trading
>> withdrawFee	string	withdraw fee. If withdraw fee is empty, It means that this coin does not support withdrawal
>> depositMin	string	Min. deposit
>> withdrawMin	string	Min. withdraw
>> minAccuracy	string	The precision of withdraw or deposit
>> chainDeposit	string	The chain status of deposit. 0: suspend. 1: normal
>> chainWithdraw	string	The chain status of withdraw. 0: suspend. 1: normal
>> withdrawPercentageFee	string	The withdraw fee percentage. It is a real figure, e.g., 0.022 means 2.2%
>> contractAddress	string	Contract address. "" means no contract address
>> safeConfirmNumber	string	Number of security confirmations: Once this number is reached, your USD equivalent worth funds will be fully unlocked and available for withdrawal.
RUN >>
Request Example
HTTP
Python
Node.js
from pybit.unified_trading import HTTP
session = HTTP(
    testnet=True,
    api_key="xxxxxxxxxxxxxxxxxx",
    api_secret="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
)
print(session.get_coin_info(
    coin="MNT",
))

Response Example
{
    "retCode": 0,
    "retMsg": "success",
    "result": {
        "rows": [
            {
                "name": "MNT",
                "coin": "MNT",
                "remainAmount": "10000000",
                "chains": [
                    {
                        "chainType": "Ethereum",
                        "confirmation": "6",
                        "withdrawFee": "3",
                        "depositMin": "0",
                        "withdrawMin": "3",
                        "chain": "ETH",
                        "chainDeposit": "1",
                        "chainWithdraw": "1",
                        "minAccuracy": "8",
                        "withdrawPercentageFee": "0",
                        "contractAddress": "0x3c3a81e81dc49a522a592e7622a7e711c06bf354",
                        "safeConfirmNumber": "65"
                    },
                    {
                        "chainType": "Mantle Network",
                        "confirmation": "100",
                        "withdrawFee": "0",
                        "depositMin": "0",
                        "withdrawMin": "10",
                        "chain": "MANTLE",
                        "chainDeposit": "1",
                        "chainWithdraw": "1",
                        "minAccuracy": "8",
                        "withdrawPercentageFee": "0",
                        "contractAddress": "",
                        "safeConfirmNumber": "100"
                    }
                ]
            }
        ]
    },
    "retExtInfo": {},
    "time": 1736395486989
}

Connect
WebSocket public stream:

Mainnet:
Spot: wss://stream.bybit.com/v5/public/spot
USDT, USDC perpetual & USDT Futures: wss://stream.bybit.com/v5/public/linear
Inverse contract: wss://stream.bybit.com/v5/public/inverse
Spread trading: wss://stream.bybit.com/v5/public/spread
USDT/USDC Options: wss://stream.bybit.com/v5/public/option

Testnet:
Spot: wss://stream-testnet.bybit.com/v5/public/spot
USDT,USDC perpetual & USDT Futures: wss://stream-testnet.bybit.com/v5/public/linear
Inverse contract: wss://stream-testnet.bybit.com/v5/public/inverse
Spread trading: wss://stream-testnet.bybit.com/v5/public/spread
USDT/USDC Options: wss://stream-testnet.bybit.com/v5/public/option

WebSocket private stream:

Mainnet:
wss://stream.bybit.com/v5/private

Testnet:
wss://stream-testnet.bybit.com/v5/private

WebSocket Order Entry:

Mainnet:
wss://stream.bybit.com/v5/trade (Spread trading is not supported)

Testnet:
wss://stream-testnet.bybit.com/v5/trade (Spread trading is not supported)

WebSocket GET System Status:

Mainnet:
wss://stream.bybit.com/v5/public/misc/status

Testnet:
wss://stream-testnet.bybit.com/v5/public/misc/status

info
If your account is registered from www.bybit-tr.com, please use stream.bybit-tr.com for mainnet access
If your account is registered from www.bybit.kz, please use stream.bybit.kz for mainnet access
If your account is registered from www.bybitgeorgia.ge, please use stream.bybitgeorgia.ge for mainnet access
Customise Private Connection Alive Time
For private stream and order entry, you can customise alive duration by adding a param max_active_time, the lowest value is 30s (30 seconds), the highest value is 600s (10 minutes). You can also pass 1m, 2m etc when you try to configure by minute level. e.g., wss://stream-testnet.bybit.com/v5/private?max_active_time=1m.

In general, if there is no "ping-pong" and no stream data sent from server end, the connection will be cut off after 10 minutes. When you have a particular need, you can configure connection alive time by max_active_time.

Since ticker scans every 30s, so it is not fully exact, i.e., if you configure 45s, and your last update or ping-pong is occurred on 2023-08-15 17:27:23, your disconnection time maybe happened on 2023-08-15 17:28:15

Authentication
info
Public topics do not require authentication. The following section applies to private topics only.
Apply for authentication when establishing a connection.

Note: if you're using pybit, bybit-api, or another high-level library, you can ignore this code - as authentication is handled for you.

{
    "req_id": "10001", // optional
    "op": "auth",
    "args": [
        "api_key",
        1662350400000, // expires; is greater than your current timestamp
        "signature"
    ]
}

# based on: https://github.com/bybit-exchange/pybit/blob/master/pybit/_http_manager.py

import hmac
import json
import time
import websocket

api_key = ""
api_secret = ""

# Generate expires.
expires = int((time.time() + 1) * 1000)

# Generate signature.
signature = str(hmac.new(
    bytes(api_secret, "utf-8"),
    bytes(f"GET/realtime{expires}", "utf-8"), digestmod="sha256"
).hexdigest())

ws = websocket.WebSocketApp(
    url=url,
    ...
)

# Authenticate with API.
ws.send(
    json.dumps({
        "op": "auth",
        "args": [api_key, expires, signature]
    })
)

Successful authentication sample response

{
    "success": true,
    "ret_msg": "",
    "op": "auth",
    "conn_id": "cejreaspqfh3sjdnldmg-p"
}

note
Example signature algorithms can be found here.

caution
Due to network complexity, your may get disconnected at any time. Please follow the instructions below to ensure that you receive WebSocket messages on time:

Keep connection alive by sending the heartbeat packet
Reconnect as soon as possible if disconnected
IP Limits
Do not frequently connect and disconnect the connection.
Do not build over 500 connections in 5 minutes. This is counted per WebSocket domain.
Public channel - Args limits
Regardless of Perpetual, Futures, Options or Spot, for one public connection, you cannot have length of "args" array over 21,000 characters.

Spot can input up to 10 args for each subscription request sent to one connection
Options can input up to 2000 args for a single connection
No args limit for Futures and Spread for now
How to Send the Heartbeat Packet
How to Send

// req_id is a customised ID, which is optional
ws.send(JSON.stringify({"req_id": "100001", "op": "ping"}));

Pong message example of public channels

Spot
Linear/Inverse
Option/Spread
{
    "success": true,
    "ret_msg": "pong",
    "conn_id": "0970e817-426e-429a-a679-ff7f55e0b16a",
    "op": "ping"
}

Pong message example of private channels

{
    "req_id": "test",
    "op": "pong",
    "args": [
        "1675418560633"
    ],
    "conn_id": "cfcb4ocsvfriu23r3er0-1b"
}

caution
To avoid network or program issues, we recommend that you send the ping heartbeat packet every 20 seconds to maintain the WebSocket connection.

How to Subscribe to Topics
Understanding WebSocket Filters
How to subscribe with a filter

// Subscribing level 1 orderbook
{
    "req_id": "test", // optional
    "op": "subscribe",
    "args": [
        "orderbook.1.BTCUSDT"
    ]
}

Subscribing with multiple symbols and topics is supported.

{
    "req_id": "test", // optional
    "op": "subscribe",
    "args": [
        "orderbook.1.BTCUSDT",
        "publicTrade.BTCUSDT",
        "orderbook.1.ETHUSDT"
    ]
}

Understanding WebSocket Filters: Unsubscription
You can dynamically subscribe and unsubscribe from topics without unsubscribing from the WebSocket like so:

{
    "op": "unsubscribe",
    "args": [
        "publicTrade.ETHUSD"
    ],
    "req_id": "customised_id"
}

Understanding the Subscription Response
Topic subscription response message example

Private
Public Spot
Linear/Inverse
Option/Spread
{
    "success": true,
    "ret_msg": "",
    "op": "subscribe",
    "conn_id": "cejreassvfrsfvb9v1a0-2m"
}

{
    "success": true,
    "ret_msg": "subscribe",
    "conn_id": "2324d924-aa4d-45b0-a858-7b8be29ab52b",
    "req_id": "10001",
    "op": "subscribe"
}

{
    "success": true,
    "ret_msg": "",
    "conn_id": "3cd84cb1-4d06-4a05-930a-2efe5fc70f0f",
    "req_id": "",
    "op": "subscribe"
}

Orderbook
Subscribe to the orderbook stream. Supports different depths.

info
Retail Price Improvement (RPI) orders will not be included in the messages.

Depths
Linear & inverse:
Level 1 data, push frequency: 10ms
Level 50 data, push frequency: 20ms
Level 200 data, push frequency: 100ms
Level 1000 data, push frequency: 200ms

Spot:
Level 1 data, push frequency: 10ms
Level 50 data, push frequency: 20ms
Level 200 data, push frequency: 200ms
Level 1000 data, push frequency: 200ms

Option:
Level 25 data, push frequency: 20ms
Level 100 data, push frequency: 100ms

Topic:
orderbook.{depth}.{symbol} e.g., orderbook.1.BTCUSDT

Process snapshot/delta
To process snapshot and delta messages, please follow these rules:

Once you have subscribed successfully, you will receive a snapshot. The WebSocket will keep pushing delta messages every time the orderbook changes. If you receive a new snapshot message, you will have to reset your local orderbook. If there is a problem on Bybit's end, a snapshot will be re-sent, which is guaranteed to contain the latest data.

To apply delta updates:

If you receive an amount that is 0, delete the entry
If you receive an amount that does not exist, insert it
If the entry exists, you simply update the value
See working code examples of this logic in the FAQ.

info
Linear, inverse, spot level 1 data: if 3 seconds have elapsed without a change in the orderbook, a snapshot message will be pushed again, and the field u will be the same as that in the previous message.
Linear, inverse, spot level 1 data has snapshot message only
Response Parameters
Parameter	Type	Comments
topic	string	Topic name
type	string	Data type. snapshot,delta
ts	number	The timestamp (ms) that the system generates the data
data	map	Object
> s	string	Symbol name
> b	array	Bids. For snapshot stream. Sorted by price in descending order
>> b[0]	string	Bid price
>> b[1]	string	Bid size
The delta data has size=0, which means that all quotations for this price have been filled or cancelled
> a	array	Asks. For snapshot stream. Sorted by price in ascending order
>> a[0]	string	Ask price
>> a[1]	string	Ask size
The delta data has size=0, which means that all quotations for this price have been filled or cancelled
> u	integer	Update ID
Occasionally, you'll receive "u"=1, which is a snapshot data due to the restart of the service. So please overwrite your local orderbook
For level 1 of linear, inverse Perps and Futures, the snapshot data will be pushed again when there is no change in 3 seconds, and the "u" will be the same as that in the previous message
> seq	integer	Cross sequence
You can use this field to compare different levels orderbook data, and for the smaller seq, then it means the data is generated earlier.
cts	number	The timestamp from the matching engine when this orderbook data is produced. It can be correlated with T from public trade channel
Subscribe Example
from pybit.unified_trading import WebSocket
from time import sleep
ws = WebSocket(
    testnet=True,
    channel_type="linear",
)
def handle_message(message):
    print(message)
ws.orderbook_stream(
    depth=50,
    symbol="BTCUSDT",
    callback=handle_message
)
while True:
    sleep(1)

Response Example
Snapshot
Delta
{
    "topic": "orderbook.50.BTCUSDT",
    "type": "snapshot",
    "ts": 1672304484978,
    "data": {
        "s": "BTCUSDT",
        "b": [
            ...,
            [
                "16493.50",
                "0.006"
            ],
            [
                "16493.00",
                "0.100"
            ]
        ],
        "a": [
            [
                "16611.00",
                "0.029"
            ],
            [
                "16612.00",
                "0.213"
            ],
            ...,
        ],
    "u": 18521288,
    "seq": 7961638724
    },
    "cts": 1672304484976
}

Ticker
Subscribe to the ticker stream.

note
This topic utilises the snapshot field and delta field. If a response param is not found in the message, then its value has not changed.
Spot & Option tickers message are snapshot only
Push frequency: Derivatives & Options - 100ms, Spot - 50ms

Topic:
tickers.{symbol}

Response Parameters
Linear/Inverse
Option
Spot
Parameter	Type	Comments
topic	string	Topic name
ts	number	The timestamp (ms) that the system generates the data
type	string	Data type. snapshot
cs	integer	Cross sequence
data	array	Object
> symbol	string	Symbol name
> lastPrice	string	Last price
> highPrice24h	string	The highest price in the last 24 hours
> lowPrice24h	string	The lowest price in the last 24 hours
> prevPrice24h	string	Percentage change of market price relative to 24h
> volume24h	string	Volume for 24h
> turnover24h	string	Turnover for 24h
> price24hPcnt	string	Percentage change of market price relative to 24h
> usdIndexPrice	string	USD index price
used to calculate USD value of the assets in Unified account
non-collateral margin coin returns ""
Subscribe Example
Linear
Option
Spot
from pybit.unified_trading import WebSocket
from time import sleep
ws = WebSocket(
    testnet=True,
    channel_type="spot",
)
def handle_message(message):
    print(message)
ws.ticker_stream(
    symbol="BTCUSDT",
    callback=handle_message
)
while True:
    sleep(1)

Response Example
Linear
Option
Spot
{
    "topic": "tickers.BTCUSDT",
    "ts": 1673853746003,
    "type": "snapshot",
    "cs": 2588407389,
    "data": {
        "symbol": "BTCUSDT",
        "lastPrice": "21109.77",
        "highPrice24h": "21426.99",
        "lowPrice24h": "20575",
        "prevPrice24h": "20704.93",
        "volume24h": "6780.866843",
        "turnover24h": "141946527.22907118",
        "price24hPcnt": "0.0196",
        "usdIndexPrice": "21120.2400136"
    }
}

Ticker
Subscribe to the ticker stream.

note
This topic utilises the snapshot field and delta field. If a response param is not found in the message, then its value has not changed.
Spot & Option tickers message are snapshot only
Push frequency: Derivatives & Options - 100ms, Spot - 50ms

Topic:
tickers.{symbol}

Response Parameters
Linear/Inverse
Option
Spot
Parameter	Type	Comments
topic	string	Topic name
ts	number	The timestamp (ms) that the system generates the data
type	string	Data type. snapshot
cs	integer	Cross sequence
data	array	Object
> symbol	string	Symbol name
> lastPrice	string	Last price
> highPrice24h	string	The highest price in the last 24 hours
> lowPrice24h	string	The lowest price in the last 24 hours
> prevPrice24h	string	Percentage change of market price relative to 24h
> volume24h	string	Volume for 24h
> turnover24h	string	Turnover for 24h
> price24hPcnt	string	Percentage change of market price relative to 24h
> usdIndexPrice	string	USD index price
used to calculate USD value of the assets in Unified account
non-collateral margin coin returns ""
Subscribe Example
Linear
Option
Spot
from pybit.unified_trading import WebSocket
from time import sleep
ws = WebSocket(
    testnet=True,
    channel_type="spot",
)
def handle_message(message):
    print(message)
ws.ticker_stream(
    symbol="BTCUSDT",
    callback=handle_message
)
while True:
    sleep(1)

Response Example
Linear
Option
Spot
{
    "topic": "tickers.BTCUSDT",
    "ts": 1673853746003,
    "type": "snapshot",
    "cs": 2588407389,
    "data": {
        "symbol": "BTCUSDT",
        "lastPrice": "21109.77",
        "highPrice24h": "21426.99",
        "lowPrice24h": "20575",
        "prevPrice24h": "20704.93",
        "volume24h": "6780.866843",
        "turnover24h": "141946527.22907118",
        "price24hPcnt": "0.0196",
        "usdIndexPrice": "21120.2400136"
    }
}