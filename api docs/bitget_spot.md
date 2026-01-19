Get Coin Info
Frequency limit: 3 times/1s (IP)

Description
Get spot coin information,supporting both individual and full queries.

HTTP Request
GET /api/v2/spot/public/coins
Request Example
curl "https://api.bitget.com/api/v2/spot/public/coins"


Request Parameters
Parameter	Type	Required	Description
coin	String	No	Coin name, If the field is left blank, all coin information will be returned by default
Response Example
{
    "code": "00000",
    "msg": "success",
    "requestTime": 1695799900330,
    "data": [
        {
            "coinId": "1",
            "coin": "BTC",
            "transfer": "true",
            "chains": [
                {
                    "chain": "BTC",
                    "needTag": "false",
                    "withdrawable": "true",
                    "rechargeable": "true",
                    "withdrawFee": "0.005",
                    "extraWithdrawFee": "0",
                    "depositConfirm": "1",
                    "withdrawConfirm": "1",
                    "minDepositAmount": "0.001",
                    "minWithdrawAmount": "0.001",
                    "browserUrl": "https://blockchair.com/bitcoin/testnet/transaction/",
                    "contractAddress": "0xdac17f958d2ee523a2206206994597c13d831ec7",
                    "withdrawStep": "0",
                    "withdrawMinScale": "8",
                    "congestion":"normal"
                }
            ]
        }
    ]
}


Response Parameters
Parameter	Type	Description
coinId	String	Currency ID
coin	String	Token name
transfer	Boolean	Transferability
chains	Array	Support chain list
> chain	String	Chain name
> needTag	Boolean	Need tag
> withdrawable	Boolean	Withdrawal supported
> rechargeable	Boolean	Deposit supported
> withdrawFee	String	Withdrawal transaction fee
> extraWithdrawFee	String	Extra charge. On chain destruction: 0.1 means 10%
> depositConfirm	String	Deposit confirmation blocks
> withdrawConfirm	String	Withdrawal confirmation blocks
> minDepositAmount	String	Minimum deposit amount
> minWithdrawAmount	String	Minimum withdrawal amount
> browserUrl	String	Blockchain explorer address
> contractAddress	String	coin contract address
> withdrawStep	String	withdrawal count step
If the value is not 0, it indicates that the withdraswl size should be multiple of the value.
if it's 0, that means there is no the limit above.
> withdrawMinScale	String	Decimal places of withdrawal amount
> congestion	String	chain network status
normal: normal
congested: congestion


Get Ticker Information
Frequency limit: 20 times/1s (IP)

Description
Get Ticker Information,Supports both single and batch queries

HTTP Request
GET /api/v2/spot/market/tickers
Request Example
curl "https://api.bitget.com/api/v2/spot/market/tickers?symbol=BTCUSDT"


Request Parameters
Parameter	Type	Required	Description
symbol	String	No	trading pair name, e.g. BTCUSDT
If the field is left blank, all trading pair information will be returned by default
Response Example
{
    "code": "00000",
    "msg": "success",
    "requestTime": 1695808949356,
    "data": [
        {
            "symbol": "BTCUSDT",
            "high24h": "37775.65",
            "open": "35134.2",
            "low24h": "34413.1",
            "lastPr": "34413.1",
            "quoteVolume": "0",
            "baseVolume": "0",
            "usdtVolume": "0",
            "bidPr": "0",
            "askPr": "0",
            "bidSz": "0.0663",
            "askSz": "0.0119",
            "openUtc": "23856.72",
            "ts": "1625125755277",
            "changeUtc24h": "0.00301",
            "change24h": "0.00069"
        }
    ]
}

Response Parameters
Parameter	Type	Description
symbol	String	Trading pair
high24h	String	24h highest price
open	String	24h open price
lastPr	String	Latest price
low24h	String	24h lowest price
quoteVolume	String	Trading volume in quote currency
baseVolume	String	Trading volume in base currency
usdtVolume	String	Trading volume in USDT
bidPr	String	Bid 1 price
askPr	String	Ask 1 price
bidSz	String	Buying 1 amount
askSz	String	selling 1 amount
openUtc	String	UTC±00:00 Entry price
ts	String	Current time Unix millisecond timestamp, e.g. 1690196141868
changeUtc24h	String	Change at UTC+0, 0.01 means 1%.
change24h	String	24-hour change, 0.01 means 1%.

Get OrderBook Depth
Frequency limit: 20 times/1s (IP)

Description
Get OrderBook Depth

HTTP Request
GET /api/v2/spot/market/orderbook
Request Example
curl "https://api.bitget.com/api/v2/spot/market/orderbook?symbol=BTCUSDT&type=step0&limit=100"


Request Parameters
Parameter	Type	Required	Description
symbol	String	Yes	Trading pair
type	String	No	Default：step0： The value enums：step0，step1，step2，step3，step4，step5
limit	String	No	Number of queries: Default: 150, maximum: 150
Response Example
{
    "code": "00000",
    "msg": "success",
    "requestTime": 1698303884579,
    "data": {
        "asks": [
            [
                "34567.15",
                "0.0131"
            ],
            [
                "34567.25",
                "0.0144"
            ]
        ],
        "bids": [
            [
                "34567",
                "0.2917"
            ],
            [
                "34566.85",
                "0.0145"
            ]
        ],
        "ts": "1698303884584"
    }
}

Response Parameters
Parameter	Type	Description
asks	Array	Ask depth
e.g. ["38084.5","0.5"] ，"38084.5" is price，"0.5" is base coin volume
bids	Array	Bid depth
ts	String	Matching engine timestamp(ms), e.g. 1597026383085

Get Candlestick Data
Frequency limit: 20 times/1s (IP)

Description
Get Candlestick Data

HTTP Request
GET /api/v2/spot/market/candles
Request Example
curl "https://api.bitget.com/api/v2/spot/market/candles?symbol=BTCUSDT&granularity=1min&startTime=1659076670000&endTime=1659080270000&limit=100"


Request Parameters
Parameter	Type	Required	Description
symbol	String	Yes	Trading pair e.g.BTCUSDT
granularity	String	Yes	Time interval of charts
For the corresponding relationship between granularity and value, refer to the list below.
minute: 1min,3min,5min,15min,30min
hour: 1h,4h,6h,12h
day: 1day,3day
week: 1week
month: 1M
hour in UTC:6Hutc,12Hutc
day in UTC:1Dutc,3Dutc
week in UTC:1Wutc
month in UTC: 1Mutc
1m, 3m, 5m can query for one month,15m can query for 52 days,30m can query for 62 days,1H can query for 83 days,2H can query for 120 days,4H can query for 240 days,6H can query for 360 days.
startTime	String	No	The time start point of the chart data, i.e., to get the chart data after this time stamp
Unix millisecond timestamp, e.g. 1690196141868
endTime	String	No	The time end point of the chart data, i.e., get the chart data before this time stamp
Unix millisecond timestamp, e.g. 1690196141868
limit	String	No	Number of queries: Default: 100, maximum: 1000.
Response Example
{
    "code": "00000",
    "msg": "success",
    "requestTime": 1695800278693,
    "data": [
        [
            "1656604800000",
            "37834.5",
            "37849.5",
            "37773.5",
            "37773.5",
            "428.3462",
            "16198849.1079",
            "16198849.1079"
        ],
        [
            "1656604800000",
            "37834.5",
            "37849.5",
            "37773.5",
            "37773.5",
            "428.3462",
            "16198849.1079",
            "16198849.1079"
        ]
    ]
}

Response Parameters
Parameter	Type	Description
index[0]	String	System timestamp, Unix millisecond timestamp, e.g. 1690196141868
index[1]	String	Opening price
index[2]	String	Highest price
index[3]	String	Lowest price
index[4]	String	Closing price
index[5]	String	Trading volume in base currency, e.g. "BTC" in the "BTCUSDT" pair.
index[6]	String	Trading volume in USDT
index[7]	String	Trading volume in quote currency, e.g. "USDT" in the "BTCUSDT" pair.

Get History Candlestick Data
Frequency limit: 20 times/1s (IP)

Description
Get History Candlestick Data

HTTP Request
GET /api/v2/spot/market/history-candles
Request Example
curl "https://api.bitget.com/api/v2/spot/market/history-candles?symbol=BTCUSDT&granularity=1min&endTime=1659080270000&limit=100"


Request Parameters
Parameter	Type	Required	Description
symbol	String	Yes	Trading pair
granularity	String	Yes	Time interval of charts
For the corresponding relationship between granularity and value, refer to the list below.
minute: 1min,3min,5min,15min,30min
hour: 1h,4h,6h,12h
day: 1day,3day
week: 1week
month: 1M
hour in UTC:6Hutc,12Hutc
day in UTC:1Dutc,3Dutc
week in UTC:1Wutc
month in UTC: 1Mutc
endTime	String	Yes	The time end point of the chart data, i.e., get the chart data before this time stamp
Unix millisecond timestamp, e.g. 1690196141868
limit	String	No	Number of queries: Default: 100, maximum: 200.
Response Example
{
    "code": "00000",
    "msg": "success",
    "requestTime": 1695799900330,
    "data": [
        [
            "1646064000000",
            "43500.8",
            "48207.2",
            "38516",
            "46451.9",
            "2581.4668",
            "118062073.82644",
            "118062073.82644"
        ],
        [
            "1648742400000",
            "46451.9",
            "55199.6",
            "15522.1",
            "38892.5",
            "42331329.5473",
            "1726993402150.991724",
            "1726993402150.991724"
        ],
        [
            "1654012800000",
            "38892.5",
            "38892.5",
            "38892.5",
            "38892.5",
            "0",
            "0",
            "0"
        ],
        [
            "1654012800000",
            "39270.4",
            "39270.4",
            "37834.5",
            "37834.5",
            "42.444",
            "1619934.779",
            "1619934.779"
        ],
        [
            "1656604800000",
            "37834.5",
            "37849.5",
            "37773.5",
            "37773.5",
            "428.3462",
            "16198849.1079",
            "16198849.1079"
        ]
    ]
}

Response Parameters
Parameter	Type	Description
index[0]	String	System timestamp, Unix millisecond timestamp, e.g. 1690196141868
index[1]	String	Opening price
index[2]	String	Highest price
index[3]	String	Lowest price
index[4]	String	Closing price
index[5]	String	Trading volume in base currency, e.g. "BTC" in the "BTCUSDT" pair.
index[6]	String	Trading volume in USDT
index[7]	String	Trading volume in quote currency, e.g. "USDT" in the "BTCUSDT" pair.

Market Channel
Description
Get the product's latest price, bid price, bid price and 24h trading volume information. Frequency of data push: 200ms ~ 300ms

Request Example
{
    "op": "subscribe",
    "args": [
        {
            "instType": "SPOT",
            "channel": "ticker",
            "instId": "ETHUSDT"
        }
    ]
}

Request Parameters
Parameter	Type	Required	Description
op	String	Yes	Operation, subscribe unsubscribe
args	Array	List<Object>	Yes
List of channels to request subscription
> instType	String	Yes	Product line type
> channel	String	Yes	Channel name
> instId	String	Yes	Product ID, e.g. ETHUSDT
Response Example
{
  "event": "subscribe",
  "arg": {
    "instType": "SPOT",
    "channel": "ticker",
    "instId": "ETHUSDT"
  }
}

Response Parameters
Parameter	Type	Description
event	String	Yes
Event
arg	Object	Subscribed channels
> instType	String	Product type
> channel	String	Channel name
> instId	String	Product ID, e.g. ETHUSDT
code	String	Error code, returned only on error
msg	String	Error message
Push Data
{
    "action": "snapshot",
    "arg": {
        "instType": "SPOT",
        "channel": "ticker",
        "instId": "ETHUSDT"
    },
    "data": [
        {
            "instId": "ETHUSDT",
            "lastPr": "2200.10",
            "open24h": "0.00",
            "high24h": "0.00",
            "low24h": "0.00",
            "change24h": "0.00",
            "bidPr": "1792",
            "askPr": "2200.1",
            "bidSz": "0.0084",
            "askSz": "19740.8811",
            "baseVolume": "0.0000",
            "quoteVolume": "0.0000",
            "openUtc": "0.00",
            "changeUtc24h": "0",
            "ts": "1695702438018"
        }
    ],
    "ts": 1695702438029
}

Push Parameters
Parameter	Type	Description
arg	Object	Channels with successful subscription
> instType	String	Product type
> channel	String	Channel name
> instId	String	Product ID, e.g. ETHUSDT
action	String	Push data action: snapshot
data	List<Object>	Subscription data
> instId	String	Product ID, e.g. ETHUSDT
> lastPr	String	Latest price
> askPr	String	Ask price
> bidPr	String	Bid price
> open24h	String	Entry price of the last 24 hours
> high24h	String	24h high
> low24h	String	24h low
> baseVolume	String	24h trading volume in left coin
> quoteVolume	String	24h trading volume in right coin
> ts	String	Milliseconds format of data generation time Unix timestamp, e.g. 1597026383085
> openUtc	String	UTC±00:00 Entry price
> changeUtc24h	String	Change at UTC+0, 0.01 means 1%.
> bidSz	String	Buying amount
> askSz	String	Selling amount
> change24h	String	24-hour change, 0.01 means 1%.

Depth Channel
Description
This is the channel to get the depth data
Default data push frequency for books, books5, books15 is 200ms
Default data push frequency for books1 is 10ms

books: All levels of depth. First update pushed is full data: snapshot, and then push the update data: update
books1: 1st level of depth. Push snapshot each time
books5: 5 depth levels. Push snapshot each time
books15: 15 depth levels. Push snapshot each time
Checksum
Calculate Checksum
1. More than 25 levels of bid and ask
A local snapshot of market depth (only 2 levels of the orderbook are shown here, while 25 levels of orderbook should actually be intercepted):
    "bids": [
      [ 43231.1, 4 ],   //bid1
      [ 43231,   6 ]    //bid2
    ]
    "asks": [
      [ 43232.8, 9 ],   //ask1
      [ 43232.9, 8 ]    //ask2
    ]
Build the string to check CRC32:
"43231.1:4:43232.8:9:43231:6:43232.9:8"
The sequence:
"bid1[price:amount]:ask1[price:amount]:bid2[price:amount]:ask2[price:amount]"

2. Less than 25 levels of bid or ask
A local snapshot of market depth:
    "bids": [
      [ 3366.1, 7 ] //bid1
    ]
    "asks": [
      [ 3366.8, 9 ],    //ask1
      [ 3368  , 8 ],    //ask2
      [ 3372  , 8 ]     //ask3
    ]

Build the string to check CRC32:
"3366.1:7:3366.8:9:3368:8:3372:8"
The sequence:
"bid1[price:amount]:ask1[price:amount]:ask2[price:amount]:ask3[price:amount]"


This mechanism can assist users in checking the accuracy of depth(order book) data.

Merging update data into snapshot

After subscribe to the channel (such as books 400 levels) of Order book , user first receive the initial snapshot of market depth. Afterwards the incremental update is subsequently received, user are responsible to update the snapshot from client side.

If there are any levels with same price from the updates, compare the amount with the snapshot order book:

If the amount is 0, delete this depth data.

If the amount changes, replace the depth data.

If there is no level in the snapshot with same price from the update, insert the update depth information into the snapshot sort by price (bid in descending order, ask in ascending order).

Calculate Checksum

Use the first 25 bids and asks in the local snapshot to build a string (where a colon connects the price and amount in an ask or a bid), and then calculate the CRC32 value (32-bit signed integer).

When the bid and ask depth data exceeds 25 levels, each of them will intercept 25 levels of data, and the string to be checked is queued in a way that the bid and ask depth data are alternately arranged. Such as: bid1[price:amount]:ask1[price:amount]:bid2[price:amount]:ask2[price:amount]...
When the bid or ask depth data is less than 25 levels, the missing depth data will be ignored. Such as: bid1[price:amount]:ask1[price:amount]:ask2[price:amount]:ask3[price:amount]...
If price is '0.5000', DO NOT calculate the checksum by '0.5', please DO use the original value
Explanation of seq

The seq of update incremental messages is incrementing except during symbol maintenance.
Request Example
{
    "op": "subscribe",
    "args": [
        {
            "instType": "SPOT",
            "channel": "books5",
            "instId": "BTCUSDT"
        }
    ]
}

Request Parameters
Parameter	Type	Required	Description
op	String	Yes	Operation, subscribe unsubscribe
args	List<Object>	Yes	List of channels to request subscription
> instType	String	Yes	Product line type
> channel	String	Yes	Channel name: books/books1/books5/books15
> instId	String	Yes	Product ID, e.g. ETHUSDT
Response Example
{
  "event": "subscribe",
  "arg": {
    "instType": "SPOT",
    "channel": "books5",
    "instId": "BTCUSDT"
  }
}

Response Parameters
Parameter	Type	Description
event	String	Yes
Event
arg	Object	Subscribed channels
> instType	String	Product type
> channel	String	Channel name: books/books1/books5/books15
> instId	String	Product ID, e.g. ETHUSDT
code	String	Error code, returned only on error
msg	String	Error message
Push Data
{
  "action": "snapshot",
  "arg": {
    "instType": "SPOT",
    "channel": "books5",
    "instId": "BTCUSDT"
  },
  "data": [
    {
      "asks": [
        [
          "26274.9",
          "0.0009"
        ],
        [
          "26275.0",
          "0.0500"
        ]
      ],
      "bids": [
        [
          "26274.8",
          "0.0009"
        ],
        [
          "26274.7",
          "0.0027"
        ]
      ],
      "checksum": 0, 
      "seq": 123,
      "ts": "1695710946294"
    }
  ],
  "ts": 1695710946294
}

Push Parameters
Parameter	Type	Description
arg	Object	Channels with successful subscription
> instType	String	Product type
> channel	String	Channel name: books/books1/books5/books15
> instId	String	Product ID, e.g. ETHUSDT
action	String	Push data action, snapshot or update
data	List<Object>	Subscription data
> instId	String	Product ID, e.g. ETHUSDT
> asks	List<String>	Seller depth
> bids	List<String>	Buyer depth
> ts	String	Matching engine timestamp(ms), e.g. 1597026383085
> checksum	Long	Checksum
> seq	Long	Serial number.
It increases when the order book is updated and can be used to determine whether there is out-of-order packets.