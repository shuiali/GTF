Query all currency information

GET /spot/currencies

Query all currency information

When a currency corresponds to multiple chains, you can query the information of multiple chains through the chains field, such as the charging and recharge status, identification, etc. of the chain

Responses
Status	Meaning	Description	Schema
200	OK(opens new window)	List retrieved successfully	[Inline]
Response Schema
Status Code 200

Name	Type	Description
None	array	none
» currency	string	Currency symbol
» name	string	Currency name
» delisted	boolean	Whether currency is de-listed
» withdraw_disabled	boolean	Whether currency's withdrawal is disabled (deprecated)
» withdraw_delayed	boolean	Whether currency's withdrawal is delayed (deprecated)
» deposit_disabled	boolean	Whether currency's deposit is disabled (deprecated)
» trade_disabled	boolean	Whether currency's trading is disabled
» fixed_rate	string	Fixed fee rate. Only for fixed rate currencies, not valid for normal currencies
» chain	string	The main chain corresponding to the coin
» chains	array	All links corresponding to coins
»» SpotCurrencyChain	object	none
»»» name	string	Blockchain name
»»» addr	string	token address
»»» withdraw_disabled	boolean	Whether currency's withdrawal is disabled
»»» withdraw_delayed	boolean	Whether currency's withdrawal is delayed
»»» deposit_disabled	boolean	Whether currency's deposit is disabled
This operation does not require authentication
Code samples

# coding: utf-8
import requests

host = "https://api.gateio.ws"
prefix = "/api/v4"
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

url = '/spot/currencies'
query_param = ''
r = requests.request('GET', host + prefix + url, headers=headers)
print(r.json())

Example responses

200 Response

[
  {
    "currency": "GT",
    "name": "GateToken",
    "delisted": false,
    "withdraw_disabled": false,
    "withdraw_delayed": false,
    "deposit_disabled": false,
    "trade_disabled": false,
    "chain": "GT",
    "chains": [
      {
        "name": "GT",
        "addr": "",
        "withdraw_disabled": false,
        "withdraw_delayed": false,
        "deposit_disabled": false
      },
      {
        "name": "ETH",
        "withdraw_disabled": false,
        "withdraw_delayed": false,
        "deposit_disabled": false,
        "addr": "0xE66747a101bFF2dBA3697199DCcE5b743b454759"
      },
      {
        "name": "GTEVM",
        "withdraw_disabled": false,
        "withdraw_delayed": false,
        "deposit_disabled": false,
        "addr": ""
      }
    ]
  }
]

Query all supported currency pairs

GET /spot/currency_pairs

Query all supported currency pairs

Responses
Status	Meaning	Description	Schema
200	OK(opens new window)	All currency pairs retrieved	[Inline]
Response Schema
Status Code 200

Name	Type	Description
None	array	[Spot currency pair]
» None	object	Spot currency pair
»» id	string	Currency pair
»» base	string	Base currency
»» base_name	string	Base currency name
»» quote	string	Quote currency
»» quote_name	string	Quote currency name
»» fee	string	Trading fee rate(deprecated)
»» min_base_amount	string	Minimum amount of base currency to trade, null means no limit
»» min_quote_amount	string	Minimum amount of quote currency to trade, null means no limit
»» max_base_amount	string	Maximum amount of base currency to trade, null means no limit
»» max_quote_amount	string	Maximum amount of quote currency to trade, null means no limit
»» amount_precision	integer	Amount scale
»» precision	integer	Price scale
»» trade_status	string	Trading status

- untradable: cannot be traded
- buyable: can be bought
- sellable: can be sold
- tradable: can be bought and sold
»» sell_start	integer(int64)	Sell start unix timestamp in seconds
»» buy_start	integer(int64)	Buy start unix timestamp in seconds
»» delisting_time	integer(int64)	Expected time to remove the shelves, Unix timestamp in seconds
»» type	string	Trading pair type, normal: normal, premarket: pre-market
»» trade_url	string	Transaction link
»» st_tag	boolean	Whether the trading pair is in ST risk assessment, false - No, true - Yes
»» up_rate	string	Maximum Quote Rise Percentage
»» down_rate	string	Maximum Quote Decline Percentage
»» slippage	string	Maximum supported slippage ratio for Spot Market Order Placement, calculated based on the latest market price at the time of order placement as the benchmark (Example: 0.03 means 3%)
»» market_order_max_stock	string	Maximum Market Order Quantity
»» market_order_max_money	string	Maximum Market Order Amount
#Enumerated Values
Property	Value
trade_status	untradable
trade_status	buyable
trade_status	sellable
trade_status	tradable
This operation does not require authentication
Code samples

# coding: utf-8
import requests

host = "https://api.gateio.ws"
prefix = "/api/v4"
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

url = '/spot/currency_pairs'
query_param = ''
r = requests.request('GET', host + prefix + url, headers=headers)
print(r.json())

Example responses

200 Response

[
  {
    "id": "ETH_USDT",
    "base": "ETH",
    "base_name": "Ethereum",
    "quote": "USDT",
    "quote_name": "Tether",
    "fee": "0.2",
    "min_base_amount": "0.001",
    "min_quote_amount": "1.0",
    "max_base_amount": "10000",
    "max_quote_amount": "10000000",
    "amount_precision": 3,
    "precision": 6,
    "trade_status": "tradable",
    "sell_start": 1516378650,
    "buy_start": 1516378650,
    "delisting_time": 0,
    "trade_url": "https://www.gate.io/trade/ETH_USDT",
    "st_tag": false,
    "up_rate": "0.05",
    "down_rate": "0.02",
    "slippage": "0.05",
    "max_market_order_stock": "100000",
    "max_market_order_money": "1000000"
  }
]

Get currency pair ticker information

GET /spot/tickers

Get currency pair ticker information

If currency_pair is specified, only query that currency pair; otherwise return all information

Parameters
Name	In	Type	Required	Description
currency_pair	query	string	false	Currency pair
timezone	query	string	false	Timezone
#Enumerated Values
Parameter	Value
timezone	utc0
timezone	utc8
timezone	all
Responses
Status	Meaning	Description	Schema
200	OK(opens new window)	Query successful	[Inline]
Response Schema
Status Code 200

Name	Type	Description
» currency_pair	string	Currency pair
» last	string	Last trading price
» lowest_ask	string	Recent lowest ask
» lowest_size	string	Latest seller's lowest price quantity; not available for batch queries; available for single queries, empty if no data
» highest_bid	string	Recent highest bid
» highest_size	string	Latest buyer's highest price quantity; not available for batch queries; available for single queries, empty if no data
» change_percentage	string	24h price change percentage (negative for decrease, e.g., -7.45)
» change_utc0	string	UTC+0 timezone, 24h price change percentage, negative for decline (e.g., -7.45)
» change_utc8	string	UTC+8 timezone, 24h price change percentage, negative for decline (e.g., -7.45)
» base_volume	string	Base currency trading volume in the last 24h
» quote_volume	string	Quote currency trading volume in the last 24h
» high_24h	string	24h High
» low_24h	string	24h Low
» etf_net_value	string	ETF net value
» etf_pre_net_value	string|null	ETF net value at previous rebalancing point
» etf_pre_timestamp	integer(int64)|null	ETF previous rebalancing time
» etf_leverage	string|null	ETF current leverage
This operation does not require authentication
Code samples

# coding: utf-8
import requests

host = "https://api.gateio.ws"
prefix = "/api/v4"
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

url = '/spot/tickers'
query_param = ''
r = requests.request('GET', host + prefix + url, headers=headers)
print(r.json())

Example responses

200 Response

[
  {
    "currency_pair": "BTC3L_USDT",
    "last": "2.46140352",
    "lowest_ask": "2.477",
    "highest_bid": "2.4606821",
    "change_percentage": "-8.91",
    "change_utc0": "-8.91",
    "change_utc8": "-8.91",
    "base_volume": "656614.0845820589",
    "quote_volume": "1602221.66468375534639404191",
    "high_24h": "2.7431",
    "low_24h": "1.9863",
    "etf_net_value": "2.46316141",
    "etf_pre_net_value": "2.43201848",
    "etf_pre_timestamp": 1611244800,
    "etf_leverage": "2.2803019447281203"
  }
]

Get market depth information

GET /spot/order_book

Get market depth information

Market depth buy orders are sorted by price from high to low, sell orders are reversed

Parameters
Name	In	Type	Required	Description
currency_pair	query	string	true	Currency pair
interval	query	string	false	Price precision for depth aggregation, 0 means no aggregation, defaults to 0 if not specified
limit	query	integer	false	Number of depth levels
with_id	query	boolean	false	Return order book update ID
Responses
Status	Meaning	Description	Schema
200	OK(opens new window)	Query successful	Inline
Response Schema
Status Code 200

Name	Type	Description
» id	integer(int64)	Order book ID, which is updated whenever the order book is changed. Valid only when with_id is set to true
» current	integer(int64)	The timestamp of the response data being generated (in milliseconds)
» update	integer(int64)	The timestamp of when the orderbook last changed (in milliseconds)
» asks	array	Ask Depth
»» None	array	Price and Quantity Pair
» bids	array	Bid Depth
»» None	array	Price and Quantity Pair
This operation does not require authentication
Code samples

# coding: utf-8
import requests

host = "https://api.gateio.ws"
prefix = "/api/v4"
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

url = '/spot/order_book'
query_param = 'currency_pair=BTC_USDT'
r = requests.request('GET', host + prefix + url + "?" + query_param, headers=headers)
print(r.json())

Example responses

200 Response

{
  "id": 123456,
  "current": 1623898993123,
  "update": 1623898993121,
  "asks": [
    [
      "1.52",
      "1.151"
    ],
    [
      "1.53",
      "1.218"
    ]
  ],
  "bids": [
    [
      "1.17",
      "201.863"
    ],
    [
      "1.16",
      "725.464"
    ]
  ]
}

Market K-line chart

GET /spot/candlesticks

Market K-line chart

Maximum of 1000 points can be returned in a query. Be sure not to exceed the limit when specifying from, to and interval

Parameters
Name	In	Type	Required	Description
currency_pair	query	string	true	Currency pair
limit	query	integer	false	Maximum number of recent data points to return. limit conflicts with from and to. If either from or to is specified, request will be rejected.
from	query	integer(int64)	false	Start time of candlesticks, formatted in Unix timestamp in seconds. Default toto - 100 * interval if not specified
to	query	integer(int64)	false	Specify the end time of the K-line chart, defaults to current time if not specified, note that the time format is Unix timestamp with second precision
interval	query	string	false	Time interval between data points. Note that 30d represents a calendar month, not aligned to 30 days
#Enumerated Values
Parameter	Value
interval	1s
interval	10s
interval	1m
interval	5m
interval	15m
interval	30m
interval	1h
interval	4h
interval	8h
interval	1d
interval	7d
interval	30d
Responses
Status	Meaning	Description	Schema
200	OK(opens new window)	Query successful	[[string]]
Response Schema
Status Code 200

Name	Type	Description
» None	array	Candlestick data for each time granularity, from left to right:

- Unix timestamp with second precision
- Trading volume in quote currency
- Closing price
- Highest price
- Lowest price
- Opening price
- Trading volume in base currency
- Whether window is closed; true means this candlestick data segment is complete, false means not yet complete
This operation does not require authentication
Code samples

# coding: utf-8
import requests

host = "https://api.gateio.ws"
prefix = "/api/v4"
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

url = '/spot/candlesticks'
query_param = 'currency_pair=BTC_USDT'
r = requests.request('GET', host + prefix + url + "?" + query_param, headers=headers)
print(r.json())

Example responses

200 Response

[
  [
    "1539852480",
    "971519.677",
    "0.0021724",
    "0.0021922",
    "0.0021724",
    "0.0021737",
    "true"
  ]
]

Tickers Channel
spot.tickers

update speed: 1000ms

The ticker is a high level overview of the state of the spot trading. It shows you the highest, lowest, last trade price. It also includes information such as daily volume and how much the price has changed over the last day.

#Client Subscription
Payload format:

Field	Type	Required	Description
payload	Array[String]	Yes	List of currency pairs
You can subscribe/unsubscribe multiple times. Currency pair subscribed earlier will not be overridden unless explicitly unsubscribed to.

Code samples

import time
import json

# pip install websocket_client
from websocket import create_connection

ws = create_connection("wss://api.gateio.ws/ws/v4/")
ws.send(json.dumps({
    "time": int(time.time()),
    "channel": "spot.tickers",
    "event": "subscribe",  # "unsubscribe" for unsubscription
    "payload": ["BTC_USDT"]
}))
print(ws.recv())
#Server Notification
Result format:

Field	Type	Description
result	Object	Ticker object
»currency_pair	String	Currency pair
»last	String	Last price
»lowest_ask	String	Recent best ask price
»highest_bid	String	Recent best bid price
»change_percentage	String	Change percentage
»base_volume	String	Base volume
»quote_volume	String	Quote volume
»high_24h	String	Highest price in 24h
»low_24h	String	Lowest price in 24h
Notification example

{
  "time": 1669107766,
  "time_ms": 1669107766406,
  "channel": "spot.tickers",
  "event": "update",
  "result": {
    "currency_pair": "BTC_USDT",
    "last": "15743.4",
    "lowest_ask": "15744.4",
    "highest_bid": "15743.5",
    "change_percentage": "-1.8254",
    "base_volume": "9110.473081735",
    "quote_volume": "145082083.2535",
    "high_24h": "16280.9",
    "low_24h": "15468.5"
  }
}

Order Book V2 API
Provide a faster method for retrieving depth information

#Maintain local depth
Note:

Full Depth Snapshot Push (full=true):When the channel pushes full depth data, the local depth should be completely replaced with the received data. Additionally, the depth ID should be updated to the value of the u field in the message. Note that the server may send full depth snapshots multiple times.
The first message pushed after subscribing to this channel is a full depth snapshot.
Incremental Depth Push (full=false):Incremental messages do not include the full field. Instead, each message contains the fields U (starting depth ID) and u (ending depth ID).
If U equals the local depth ID + 1, it indicates a continuous depth update:
Replace the local depth ID with the value of u from the message.
If a (asks) and b (bids) in the update are not empty, update the corresponding bid and ask depth levels based on price.(Each level[0] represents the price, and level[1] represents the quantity.)If level[1] is "0", the corresponding price level should be removed from the order book.
If U ≠ local depth ID + 1, the depth data is not continuous. In this case, you must unsubscribe from the market and resubscribe to retrieve the initial depth snapshot.
Subscription Limitations:For the same spot trading pair and the same depth stream, a single connection is allowed to subscribe only once. Duplicate subscription attempts will result in an error. Example of a failed attempt:
{
  "time": 1747391482,
  "time_ms": 1747391482960,
  "id": 1,
  "conn_id": "d9db9373dc5e081e",
  "trace_id": "ee001938590e183db957bd5ba71651c0",
  "channel": "spot.obu",
  "event": "subscribe",
  "payload": [
    "ob.BTC_USDT.400"
  ],
  "error": {
    "code": 2,
    "message": "Alert sub ob.BTC_USDT.400"
  },
  "result": {
    "status": "fail"
  }
}
#Order book V2 subscription
#Request
channel

spot.obu

event

subscribe

params

payloadIt is a list containing stream names. The format is: ob.{symbol}.{level}; for example, ob.BTC_USDT.400, ob.BTC_USDT.50

The level enum values are: 400, 50; Update frequency: 400-level updates every 100 ms; 50-level updates every 20 ms.

Code example

from websocket import create_connection

ws = create_connection("wss://api.gateio.ws/ws/v4/")
ws.send('{"time" : 123456, "channel" : "spot.obu",
        "event": "subscribe", "payload" : ["ob.BTC_USDT.50"]}')
print(ws.recv())
The above command returns JSON structured like this:

{
    "time": 1747054611,
    "time_ms": 1747054611614,
    "conn_id": "d7de96c024f2a5b2",
    "trace_id": "e6fd9bdd617fcdb80d0762ffa33e71f6",
    "channel": "spot.obu",
    "event": "subscribe",
    "payload": [
        "ob.BTC_USDT.50"
    ],
    "result": {
        "status": "success"
    }
}
#Order book V2 update notification
Notify contract order book v2 update

#Notify
channel

spot.obu

event

update

params

field	type	description
result	Object	Ask and bid price changes since the previous update
»t	Integer	Order book generation timestamp (in milliseconds)
»full	Boolean	true indicates a full depth snapshot; false indicates incremental depth updates. When the value is false, this field is omitted from the message
»s	String	Name of the depth stream
»U	Integer	Starting order book update ID of this update
»u	Integer	Ending order book update ID of this update
»b	Array[OrderBookArray]	Bids updates since the last update
»» OrderBookArray	Array[String]	An array pair [Price, Amount]; if Amount = 0, the corresponding entry should be removed from the local depth.
»a	Array[OrderBookArray]	Asks updates since the last update
»» OrderBookArray	Array[String]	An array pair [Price, Amount]; if Amount = 0, the corresponding entry should be removed from the local depth.
Example of full depth push:

{
    "channel": "spot.obu",
    "result": {
        "t": 1747054612673,
        "full": true,
        "s": "ob.BTC_USDT.50",
        "u": 73777715168,
        "b": [
            ["104027.1","509392"],
            ["104027", "477932"]
        ],
        "a": [
            ["104027.2", "44617"],
            ["104027.4", "39322"]
        ]
    },
    "time_ms": 1747054612848
}
Example of incremental push:

{
    "channel": "spot.obu",
    "result": {
        "t": 1747054612695,
        "s": "ob.BTC_USDT.50",
        "U": 73777715169,
        "u": 73777715212,
        "b": [
            ["104024.5", "10343"],
            ["104014.5", "509392"]
        ],
        "a": [
            ["104027.2", "0"],
            ["104027.4", "0"]
        ]
    },
    "time_ms": 1747054612925
}
#Order book V2 update unsubscription
Unsubscribe specified contract order book v2

#Request
channel

spot.obu

event

unsubscribe

Code example

from websocket import create_connection

ws = create_connection("wss://api.gateio.ws/ws/v4/")
ws.send(
  '{"time" : 123456, "channel" : "spot.obu", "event": "unsubscribe", "payload" : ["ob.BTC_USDT.50"]}')
print(ws.recv())
The above command returns JSON structured like this:

{
    "time": 1743673617,
    "time_ms": 1743673617242,
    "id": 1,
    "conn_id": "7b06ff199a98ab0e",
    "trace_id": "8f86e4021a84440e502f73fde5b94918",
    "channel": "spot.obu",
    "event": "unsubscribe",
    "payload": [
        "ob.BTC_USDT.50"
    ],
    "result": {
        "status": "success"
    }
}