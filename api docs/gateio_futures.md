Futures market K-line chart

GET /futures/{settle}/candlesticks

Futures market K-line chart

Return specified contract candlesticks. If prefix contract with mark_, the contract's mark price candlesticks are returned; if prefix with index_, index price candlesticks will be returned.

Maximum of 2000 points are returned in one query. Be sure not to exceed the limit when specifying from, to and interval

Parameters
Name	In	Type	Required	Description
settle	path	string	true	Settle currency
contract	query	string	true	Futures contract
from	query	integer(int64)	false	Start time of candlesticks, formatted in Unix timestamp in seconds. Default toto - 100 * interval if not specified
to	query	integer(int64)	false	Specify the end time of the K-line chart, defaults to current time if not specified, note that the time format is Unix timestamp with second precision
limit	query	integer	false	Maximum number of recent data points to return. limit conflicts with from and to. If either from or to is specified, request will be rejected.
interval	query	string	false	Interval time between data points. Note that 1w means natural week(Mon-Sun), while 7d means every 7d since unix 0. 30d represents a natural month, not 30 days
timezone	query	string	false	Time zone: all/utc0/utc8, default utc0
#Enumerated Values
Parameter	Value
settle	btc
settle	usdt
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
Responses
Status	Meaning	Description	Schema
200	OK(opens new window)	Query successful	[Inline]
Response Schema
Status Code 200

Name	Type	Description
» None	object	data point in every timestamp
»» t	number(double)	Unix timestamp in seconds
»» v	string	size volume (contract size). Only returned if contract is not prefixed
»» c	string	Close price (quote currency)
»» h	string	Highest price (quote currency)
»» l	string	Lowest price (quote currency)
»» o	string	Open price (quote currency)
»» sum	string	Trading volume (unit: Quote currency)
This operation does not require authentication
Code samples

# coding: utf-8
import requests

host = "https://api.gateio.ws"
prefix = "/api/v4"
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

url = '/futures/usdt/candlesticks'
query_param = 'contract=BTC_USDT'
r = requests.request('GET', host + prefix + url + "?" + query_param, headers=headers)
print(r.json())

Example responses

200 Response

[
  {
    "t": 1539852480,
    "v": "97151",
    "c": "1.032",
    "h": "1.032",
    "l": "1.032",
    "o": "1.032",
    "sum": "3580"
  }
]

Query futures market depth information

GET /futures/{settle}/order_book

Query futures market depth information

Bids will be sorted by price from high to low, while asks sorted reversely

Parameters
Name	In	Type	Required	Description
settle	path	string	true	Settle currency
contract	query	string	true	Futures contract
interval	query	string	false	Price precision for depth aggregation, 0 means no aggregation, defaults to 0 if not specified
limit	query	integer	false	Number of depth levels
with_id	query	boolean	false	Whether to return depth update ID. This ID increments by 1 each time the depth changes
#Enumerated Values
Parameter	Value
settle	btc
settle	usdt
Responses
Status	Meaning	Description	Schema
200	OK(opens new window)	Depth query successful	Inline
Response Schema
Status Code 200

Name	Type	Description
» id	integer(int64)	Order Book ID. Increases by 1 on every order book change. Set with_id=true to include this field in response
» current	number(double)	Response data generation timestamp
» update	number(double)	Order book changed timestamp
» asks	array	Ask Depth
»» futures_order_book_item	object	none
»»» p	string	Price (quote currency)
»»» s	string	Size
»» bids	array	Bid Depth
»»» futures_order_book_item	object	none
»»»» p	string	Price (quote currency)
»»»» s	string	Size
This operation does not require authentication
Code samples

# coding: utf-8
import requests

host = "https://api.gateio.ws"
prefix = "/api/v4"
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

url = '/futures/usdt/order_book'
query_param = 'contract=BTC_USDT'
r = requests.request('GET', host + prefix + url + "?" + query_param, headers=headers)
print(r.json())

Example responses

200 Response

{
  "id": 123456,
  "current": 1623898993.123,
  "update": 1623898993.121,
  "asks": [
    {
      "p": "1.52",
      "s": "100"
    },
    {
      "p": "1.53",
      "s": "40"
    }
  ],
  "bids": [
    {
      "p": "1.17",
      "s": "150"
    },
    {
      "p": "1.16",
      "s": "203"
    }
  ]

Tickers API
The ticker is a high level overview of the state of the contract. It shows you the highest, lowest, last trade price. It also includes information such as daily volume and how much the price has moved over the last day.

#Tickers subscription
Subscribe futures contract ticker.

#Request
channel

futures.tickers

event

subscribe

params

parameter	type	required	description
payload	Array	Yes	Contract list
Code example

from websocket import create_connection

ws = create_connection("wss://fx-ws-testnet.gateio.ws/v4/ws/btc")
ws.send('{"time" : 123456, "channel" : "futures.tickers","event": "subscribe", "payload" : ["BTC_USDT"]}')
print(ws.recv())
The above command returns JSON structured like this:

{
  "time": 1545404023,
  "time_ms": 1545404023123,
  "channel": "futures.tickers",
  "event": "subscribe",
  "result": {
    "status": "success"
  }
}
#Tickers notification
Notify subscribed contract ticker.

#Notify
channel

futures.tickers

event

update

params

field	type	description
result	Array	Array of objects
field	type	description
contract	String	Futures contract name
last	String	Last price
change_percentage	String	Change percentage
funding_rate	String	Funding rate
funding_rate_indicative	String	Indicative Funding rate in next period. (deprecated. use funding_rate)
mark_price	String	Recent mark price
index_price	String	Index price
total_size	String	Total size
volume_24h	String	Volume 24h
quanto_base_rate	String	Exchange rate of base currency and settlement currency in Quanto contract. Does not exists in contracts of other types
volume_24h_btc	String	Trade volumes in recent 24h in BTC(deprecated, usevolume_24h_base, volume_24h_quote, volume_24h_settle instead)
volume_24h_usd	String	Trade volumes in recent 24h in USD(deprecated, usevolume_24h_base, volume_24h_quote, volume_24h_settle instead)
volume_24h_quote	String	Trade volume in recent 24h, in quote currency
volume_24h_settle	String	Trade volume in recent 24h, in settle currency
volume_24h_base	String	Trade volume in recent 24h, in base currency
low_24h	String	Lowest trading price in recent 24h
high_24h	String	Highest trading price in recent 24h
{
  "time": 1541659086,
  "time_ms": 1541659086123,
  "channel": "futures.tickers",
  "event": "update",
  "result": [
    {
      "contract": "BTC_USDT",
      "last": "118.4",
      "change_percentage": "0.77",
      "funding_rate": "-0.000114",
      "funding_rate_indicative": "0.01875",
      "mark_price": "118.35",
      "index_price": "118.36",
      "total_size": "73648",
      "volume_24h": "745487577",
      "volume_24h_btc": "117",
      "volume_24h_usd": "419950",
      "quanto_base_rate": "",
      "volume_24h_quote": "1665006",
      "volume_24h_settle": "178",
      "volume_24h_base": "5526",
      "low_24h": "99.2",
      "high_24h": "132.5"
    }
  ]
}
#Cancel subscription
Unsubscribe contract ticker.

#Request
channel

futures.tickers

event

unsubscribe

Code example

import json
from websocket import create_connection

ws = create_connection("wss://fx-ws-testnet.gateio.ws/v4/ws/btc")
req = {
  "time": 123456,
  "channel": "futures.tickers",
  "event": "unsubscribe",
  "payload": ["BTC_USDT"]
}
ws.send(json.dumps(req))
print(ws.recv())
The above command returns JSON structured like this:

{
  "time": 1545404900,
  "time_ms": 1545404900123,
  "channel": "futures.tickers",
  "event": "unsubscribe",
  "result": {
    "status": "success"
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
Subscription Limitations:For the same contract’s depth stream, a single connection is allowed to subscribe only once. Duplicate subscription attempts will result in an error. Example of a failed attempt:
{
  "time": 1747391482,
  "time_ms": 1747391482960,
  "id": 1,
  "conn_id": "d9db9373dc5e081e",
  "trace_id": "ee001938590e183db957bd5ba71651c0",
  "channel": "futures.obu",
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

futures.obu

event

subscribe

params

payloadIt is a list containing stream names. The format is: ob.{symbol}.{level}; for example, ob.BTC_USDT.400, ob.BTC_USDT.50

The level enum values are: 400, 50; Update frequency: 400-level updates every 100 ms; 50-level updates every 20 ms.

Code example

from websocket import create_connection

ws = create_connection("wss://fx-ws-testnet.gateio.ws/v4/ws/usdt")
ws.send('{"time" : 123456, "channel" : "futures.obu",
        "event": "subscribe", "payload" : ["ob.BTC_USDT.400"]}')
print(ws.recv())
The above command returns JSON structured like this:

{
  "time": 1747391482,
  "time_ms": 1747391482384,
  "id": 1,
  "conn_id": "d9db9373dc5e081e",
  "trace_id": "ee001938590e183db957bd5ba71651c0",
  "channel": "futures.obu",
  "event": "subscribe",
  "payload": [
    "ob.BTC_USDT.400"
  ],
  "result": {
    "status": "success"
  }
}
#Order book V2 update notification
Notify contract order book v2 update

#Notify
channel

futures.obu

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
	"channel": "futures.obu",
	"result": {
		"t": 1743673026995,
		"full": true,
		"s": "ob.BTC_USDT.400",
		"u": 79072179673,
		"b": [
			["83705.9", "30166"]
		],
		"a": [
			["83706", "4208"]
		]
	},
	"time_ms": 1743673026999
}
Example of incremental push:

{
	"channel": "futures.obu",
	"result": {
		"t": 1743673027017,
		"s": "ob.BTC_USDT.400",
		"U": 79072179674,
		"u": 79072179694,
		"b": [
			["83702.2", "62"],
			["83702.1", "0"],
			["83702", "0"],
			["83685.6", "120"],
			["83685", "239"]
		]
	},
	"time_ms": 1743673027020
}
#Order book V2 update unsubscription
Unsubscribe specified contract order book v2

#Request
channel

futures.obu

event

unsubscribe

Code example

from websocket import create_connection

ws = create_connection("wss://fx-ws-testnet.gateio.ws/v4/ws/btc")
ws.send(
  '{"time" : 123456, "channel" : "futures.obu", "event": "unsubscribe", "payload" : ["ob.BTC_USDT.400"]}')
print(ws.recv())
The above command returns JSON structured like this:

{
  "time": 1743673617,
  "time_ms": 1743673617242,
  "id": 1,
  "conn_id": "7b06ff199a98ab0e",
  "trace_id": "8f86e4021a84440e502f73fde5b94918",
  "channel": "futures.obu",
  "event": "unsubscribe",
  "payload": ["ob.BTC_USDT.400"],
  "result": {
    "status": "success"
  }
}