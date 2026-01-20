GET / Candlesticks
Retrieve the candlestick charts. This endpoint can retrieve the latest 1,440 data entries. Charts are returned in groups based on the requested bar.

Rate Limit: 40 requests per 2 seconds
Rate limit rule: IP
HTTP Request
GET /api/v5/market/candles

Request Example

GET /api/v5/market/candles?instId=BTC-USDT
Request Parameters
Parameter	Type	Required	Description
instId	String	Yes	Instrument ID, e.g. BTC-USDT
bar	String	No	Bar size, the default is 1m
e.g. [1m/3m/5m/15m/30m/1H/2H/4H]
UTC+8 opening price k-line: [6H/12H/1D/2D/3D/1W/1M/3M]
UTC+0 opening price k-line: [6Hutc/12Hutc/1Dutc/2Dutc/3Dutc/1Wutc/1Mutc/3Mutc]
after	String	No	Pagination of data to return records earlier than the requested ts
before	String	No	Pagination of data to return records newer than the requested ts. The latest data will be returned when using before individually
limit	String	No	Number of results per request. The maximum is 300. The default is 100.
Response Example

{
    "code":"0",
    "msg":"",
    "data":[
     [
        "1597026383085",
        "3.721",
        "3.743",
        "3.677",
        "3.708",
        "8422410",
        "22698348.04828491",
        "12698348.04828491",
        "0"
    ],
    [
        "1597026383085",
        "3.731",
        "3.799",
        "3.494",
        "3.72",
        "24912403",
        "67632347.24399722",
        "37632347.24399722",
        "1"
    ]
    ]
}
Response Parameters
Parameter	Type	Description
ts	String	Opening time of the candlestick, Unix timestamp format in milliseconds, e.g. 1597026383085
o	String	Open price
h	String	highest price
l	String	Lowest price
c	String	Close price
vol	String	Trading volume, with a unit of contract.
If it is a derivatives contract, the value is the number of contracts.
If it is SPOT/MARGIN, the value is the quantity in base currency.
volCcy	String	Trading volume, with a unit of currency.
If it is a derivatives contract, the value is the number of base currency.
If it is SPOT/MARGIN, the value is the quantity in quote currency.
volCcyQuote	String	Trading volume, the value is the quantity in quote currency
e.g. The unit is USDT for BTC-USDT and BTC-USDT-SWAP;
The unit is USD for BTC-USD-SWAP
confirm	String	The state of candlesticks.
0: K line is uncompleted
1: K line is completed
The first candlestick data may be incomplete, and should not be polled repeatedly.

The data returned will be arranged in an array like this: [ts,o,h,l,c,vol,volCcy,volCcyQuote,confirm].
For the current cycle of k-line data, when there is no transaction, the opening high and closing low default take the closing price of the previous cycle.


GET / Candlesticks history
Retrieve history candlestick charts from recent years(It is last 3 months supported for 1s candlestick).

Rate Limit: 20 requests per 2 seconds
Rate limit rule: IP
HTTP Request
GET /api/v5/market/history-candles

Request Example

GET /api/v5/market/history-candles?instId=BTC-USDT
Request Parameters
Parameter	Type	Required	Description
instId	String	Yes	Instrument ID, e.g. BTC-USDT
after	String	No	Pagination of data to return records earlier than the requested ts
before	String	No	Pagination of data to return records newer than the requested ts. The latest data will be returned when using before individually
bar	String	No	Bar size, the default is 1m
e.g. [1s/1m/3m/5m/15m/30m/1H/2H/4H]
UTC+8 opening price k-line: [6H/12H/1D/2D/3D/1W/1M/3M]
UTC+0 opening price k-line: [6Hutc/12Hutc/1Dutc/2Dutc/3Dutc/1Wutc/1Mutc/3Mutc]
limit	String	No	Number of results per request. The maximum is 300. The default is 100.
Response Example

{
    "code":"0",
    "msg":"",
    "data":[
     [
        "1597026383085",
        "3.721",
        "3.743",
        "3.677",
        "3.708",
        "8422410",
        "22698348.04828491",
        "12698348.04828491",
        "1"
    ],
    [
        "1597026383085",
        "3.731",
        "3.799",
        "3.494",
        "3.72",
        "24912403",
        "67632347.24399722",
        "37632347.24399722",
        "1"
    ]
    ]
}
Response Parameters
Parameter	Type	Description
ts	String	Opening time of the candlestick, Unix timestamp format in milliseconds, e.g. 1597026383085
o	String	Open price
h	String	Highest price
l	String	Lowest price
c	String	Close price
vol	String	Trading volume, with a unit of contract.
If it is a derivatives contract, the value is the number of contracts.
If it is SPOT/MARGIN, the value is the quantity in base currency.
volCcy	String	Trading volume, with a unit of currency.
If it is a derivatives contract, the value is the number of base currency.
If it is SPOT/MARGIN, the value is the quantity in quote currency.
volCcyQuote	String	Trading volume, the value is the quantity in quote currency
e.g. The unit is USDT for BTC-USDT and BTC-USDT-SWAP;
The unit is USD for BTC-USD-SWAP
confirm	String	The state of candlesticks
0: K line is uncompleted
1: K line is completed
The data returned will be arranged in an array like this: [ts,o,h,l,c,vol,volCcy,volCcyQuote,confirm]

 1s candle is not supported by OPTION, but it is supported by other business lines (SPOT, MARGIN, FUTURES and SWAP)


WS / Candlesticks channel
Retrieve the candlesticks data of an instrument. the push frequency is the fastest interval 1 second push the data.

URL Path
/ws/v5/business

Request Example

{
  "id": "1512",
  "op": "subscribe",
  "args": [
    {
      "channel": "candle1D",
      "instId": "BTC-USDT"
    }
  ]
}
Request Parameters
Parameter	Type	Required	Description
id	String	No	Unique identifier of the message
Provided by client. It will be returned in response message for identifying the corresponding request.
A combination of case-sensitive alphanumerics, all numbers, or all letters of up to 32 characters.
op	String	Yes	Operation
subscribe
unsubscribe
args	Array of objects	Yes	List of subscribed channels
> channel	String	Yes	Channel name
candle3M
candle1M
candle1W
candle1D
candle2D
candle3D
candle5D
candle12H
candle6H
candle4H
candle2H
candle1H
candle30m
candle15m
candle5m
candle3m
candle1m
candle1s
candle3Mutc
candle1Mutc
candle1Wutc
candle1Dutc
candle2Dutc
candle3Dutc
candle5Dutc
candle12Hutc
candle6Hutc
> instId	String	Yes	Instrument ID
Successful Response Example

{
  "id": "1512",
  "event": "subscribe",
  "arg": {
    "channel": "candle1D",
    "instId": "BTC-USDT"
  },
  "connId": "a4d3ae55"
}
Failure Response Example

{
  "id": "1512",
  "event": "error",
  "code": "60012",
  "msg": "Invalid request: {\"op\": \"subscribe\", \"argss\":[{ \"channel\" : \"candle1D\", \"instId\" : \"BTC-USD-191227\"}]}",
  "connId": "a4d3ae55"
}
Response parameters
Parameter	Type	Required	Description
id	String	No	Unique identifier of the message
event	String	Yes	Event
subscribe
unsubscribe
error
arg	Object	No	Subscribed channel
> channel	String	yes	channel name
> instId	String	Yes	Instrument ID
code	String	No	Error code
msg	String	No	Error message
connId	String	Yes	WebSocket connection ID
Push Data Example

{
  "arg": {
    "channel": "candle1D",
    "instId": "BTC-USDT"
  },
  "data": [
    [
      "1597026383085",
      "8533.02",
      "8553.74",
      "8527.17",
      "8548.26",
      "45247",
      "529.5858061",
      "5529.5858061",
      "0"
    ]
  ]
}
Push data parameters
Parameter	Type	Description
arg	Object	Successfully subscribed channel
> channel	String	Channel name
> instId	String	Instrument ID
data	Array of Arrays	Subscribed data
> ts	String	Opening time of the candlestick, Unix timestamp format in milliseconds, e.g. 1597026383085
> o	String	Open price
> h	String	highest price
> l	String	Lowest price
> c	String	Close price
> vol	String	Trading volume, with a unit of contract.
If it is a derivatives contract, the value is the number of contracts.
If it is SPOT/MARGIN, the value is the quantity in base currency.
> volCcy	String	Trading volume, with a unit of currency.
If it is a derivatives contract, the value is the number of base currency.
If it is SPOT/MARGIN, the value is the quantity in quote currency.
> volCcyQuote	String	Trading volume, the value is the quantity in quote currency
e.g. The unit is USDT for BTC-USDT and BTC-USDT-SWAP
The unit is USD for BTC-USD-SWAP
> confirm	String	The state of candlesticks
0: K line is uncompleted
1: K line is completed

WS / Order book channel
Retrieve order book data. Best ask price may be lower than the best bid price during the pre-open period.

Use books for 400 depth levels, books5 for 5 depth levels, bbo-tbt tick-by-tick 1 depth level, books50-l2-tbt tick-by-tick 50 depth levels, and books-l2-tbt for tick-by-tick 400 depth levels.

books: 400 depth levels will be pushed in the initial full snapshot. Incremental data will be pushed every 100 ms for the changes in the order book during that period of time.
books-elp: only push ELP orders. 400 depth levels will be pushed in the initial full snapshot. Incremental data will be pushed every 100 ms for the changes in the order book during that period of time.
books5: 5 depth levels snapshot will be pushed in the initial push. Snapshot data will be pushed every 100 ms when there are changes in the 5 depth levels snapshot.
bbo-tbt: 1 depth level snapshot will be pushed in the initial push. Snapshot data will be pushed every 10 ms when there are changes in the 1 depth level snapshot.
books-l2-tbt: 400 depth levels will be pushed in the initial full snapshot. Incremental data will be pushed every 10 ms for the changes in the order book during that period of time.
books50-l2-tbt: 50 depth levels will be pushed in the initial full snapshot. Incremental data will be pushed every 10 ms for the changes in the order book during that period of time.
The push sequence for order book channels within the same connection and trading symbols is fixed as: bbo-tbt -> books-l2-tbt -> books50-l2-tbt -> books -> books-elp -> books5.
Users can not simultaneously subscribe to books-l2-tbt and books50-l2-tbt/books channels for the same trading symbol.
For more details, please refer to the changelog 2024-07-17
 Only API users who are VIP6 and above in trading fee tier are allowed to subscribe to "books-l2-tbt" 400 depth channels
Only API users who are VIP5 and above in trading fee tier are allowed to subscribe to "books50-l2-tbt" 50 depth channels
Identity verification refers to Login

URL Path
/ws/v5/public

Request Example

{
  "id": "1512",
  "op": "subscribe",
  "args": [
    {
      "channel": "books",
      "instId": "BTC-USDT"
    }
  ]
}
Request Parameters
Parameter	Type	Required	Description
id	String	No	Unique identifier of the message
Provided by client. It will be returned in response message for identifying the corresponding request.
A combination of case-sensitive alphanumerics, all numbers, or all letters of up to 32 characters.
op	String	Yes	Operation
subscribe
unsubscribe
args	Array of objects	Yes	List of subscribed channels
> channel	String	Yes	Channel name
books
books5
bbo-tbt
books50-l2-tbt
books-l2-tbt
> instId	String	Yes	Instrument ID
Response Example

{
  "id": "1512",
  "event": "subscribe",
  "arg": {
    "channel": "books",
    "instId": "BTC-USDT"
  },
  "connId": "a4d3ae55"
}
Failure example

{
  "id": "1512",
  "event": "error",
  "code": "60012",
  "msg": "Invalid request: {\"op\": \"subscribe\", \"argss\":[{ \"channel\" : \"books\", \"instId\" : \"BTC-USD-191227\"}]}",
  "connId": "a4d3ae55"
}
Response parameters
Parameter	Type	Required	Description
id	String	No	Unique identifier of the message
event	String	Yes	Event
subscribe
unsubscribe
error
arg	Object	No	Subscribed channel
> channel	String	Yes	Channel name
> instId	String	Yes	Instrument ID
msg	String	No	Error message
code	String	No	Error code
connId	String	Yes	WebSocket connection ID
Push Data Example: Full Snapshot

{
  "arg": {
    "channel": "books",
    "instId": "BTC-USDT"
  },
  "action": "snapshot",
  "data": [
    {
      "asks": [
        ["8476.98", "415", "0", "13"],
        ["8477", "7", "0", "2"],
        ["8477.34", "85", "0", "1"],
        ["8477.56", "1", "0", "1"],
        ["8505.84", "8", "0", "1"],
        ["8506.37", "85", "0", "1"],
        ["8506.49", "2", "0", "1"],
        ["8506.96", "100", "0", "2"]
      ],
      "bids": [
        ["8476.97", "256", "0", "12"],
        ["8475.55", "101", "0", "1"],
        ["8475.54", "100", "0", "1"],
        ["8475.3", "1", "0", "1"],
        ["8447.32", "6", "0", "1"],
        ["8447.02", "246", "0", "1"],
        ["8446.83", "24", "0", "1"],
        ["8446", "95", "0", "3"]
      ],
      "ts": "1597026383085",
      "checksum": -855196043,
      "prevSeqId": -1,
      "seqId": 123456
    }
  ]
}
Push Data Example: Incremental Data

{
  "arg": {
    "channel": "books",
    "instId": "BTC-USDT"
  },
  "action": "update",
  "data": [
    {
      "asks": [
        ["8476.98", "415", "0", "13"],
        ["8477", "7", "0", "2"],
        ["8477.34", "85", "0", "1"],
        ["8477.56", "1", "0", "1"],
        ["8505.84", "8", "0", "1"],
        ["8506.37", "85", "0", "1"],
        ["8506.49", "2", "0", "1"],
        ["8506.96", "100", "0", "2"]
      ],
      "bids": [
        ["8476.97", "256", "0", "12"],
        ["8475.55", "101", "0", "1"],
        ["8475.54", "100", "0", "1"],
        ["8475.3", "1", "0", "1"],
        ["8447.32", "6", "0", "1"],
        ["8447.02", "246", "0", "1"],
        ["8446.83", "24", "0", "1"],
        ["8446", "95", "0", "3"]
      ],
      "ts": "1597026383085",
      "checksum": -855196043,
      "prevSeqId": 123456,
      "seqId": 123457
    }
  ]
}
Push data parameters
Parameter	Type	Description
arg	Object	Successfully subscribed channel
> channel	String	Channel name
> instId	String	Instrument ID
action	String	Push data action, incremental data or full snapshot.
snapshot: full
update: incremental
data	Array of objects	Subscribed data
> asks	Array of Arrays	Order book on sell side
> bids	Array of Arrays	Order book on buy side
> ts	String	Order book generation time, Unix timestamp format in milliseconds, e.g. 1597026383085
Exception: For the bbo-tbt channel, ts is the timestamp when the push is triggered
> checksum	Integer	Checksum, implementation details below
> prevSeqId	Integer	Sequence ID of the last sent message. Only applicable to books, books-l2-tbt, books50-l2-tbt
> seqId	Integer	Sequence ID of the current message, implementation details below
 An example of the array of asks and bids values: ["411.8", "10", "0", "4"]
- "411.8" is the depth price
- "10" is the quantity at the price (number of contracts for derivatives, quantity in base currency for Spot and Spot Margin)
- "0" is part of a deprecated feature and it is always "0"
- "4" is the number of orders at the price.
 If you need to subscribe to many 50 or 400 depth level channels, it is recommended to subscribe through multiple websocket connections, with each of less than 30 channels.
 The order book data will be updated around once a second during the call auction.
 `books/books5/bbo-tbt/books-l2-tbt/books50-l2-tbt` don't return ELP orders
`books-elp` only return ELP orders, including both valid and invalid parts (invalid parts means ELP buy orders with a price higher than best bid of non-ELP orders; or ELP sell orders with a price lower than best ask of non-ELP orders). Users should distinguish valid and invalid parts using the best bid/ask price of non-ELP orders.
Sequence ID
seqId is the sequence ID of the market data published. The set of sequence ID received by users is the same if users are connecting to the same channel through multiple websocket connections. Each instId has an unique set of sequence ID. Users can use prevSeqId and seqId to build the message sequencing for incremental order book updates. Generally the value of seqId is larger than prevSeqId. The prevSeqId in the new message matches with seqId of the previous message. The smallest possible sequence ID value is 0, except in snapshot messages where the prevSeqId is always -1.

Exceptions:
1. If there are no updates to the depth for an extended period(Around 60 seconds), for the channel that always updates snapshot data, OKX will send the latest snapshot, for the channel that has incremental data, OKX will send a message with 'asks': [], 'bids': [] to inform users that the connection is still active. seqId is the same as the last sent message and prevSeqId equals to seqId. 2. The sequence number may be reset due to maintenance, and in this case, users will receive an incremental message with seqId smaller than prevSeqId. However, subsequent messages will follow the regular sequencing rule.

Example
Snapshot message: prevSeqId = -1, seqId = 10
Incremental message 1 (normal update): prevSeqId = 10, seqId = 15
Incremental message 2 (no update): prevSeqId = 15, seqId = 15
Incremental message 3 (sequence reset): prevSeqId = 15, seqId = 3
Incremental message 4 (normal update): prevSeqId = 3, seqId = 5