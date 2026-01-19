Get All Tickers
Frequency limit: 20 times/1s (IP)

Description
Get all ticker data of the given 'productType'

HTTP Request
GET /api/v2/mix/market/tickers
Request Example
curl "https://api.bitget.com/api/v2/mix/market/tickers?productType=COIN-FUTURES"


Request Parameters
Parameter	Type	Required	Description
productType	String	Yes	Product type
USDT-FUTURES USDT-M Futures
COIN-FUTURES Coin-M Futures
USDC-FUTURES USDC-M Futures
Response Example
{
    "code": "00000",
    "msg": "success",
    "requestTime": 1695794269124,
    "data": [
        {
            "symbol": "BTCUSD",
            "lastPr": "29904.5",
            "askPr": "29904.5",
            "bidPr": "29903.5",
            "bidSz": "0.5091",
            "askSz": "2.2694",
            "high24h": "0",
            "low24h": "0",
            "ts": "1695794271400",
            "change24h": "0",
            "baseVolume": "0",
            "quoteVolume": "0",
            "usdtVolume": "0",
            "openUtc": "0",
            "changeUtc24h": "0",
            "indexPrice": "29132.353333",
            "fundingRate": "-0.0007",
            "holdingAmount": "125.6844",
            "deliveryStartTime": null,
            "deliveryTime": null,
            "deliveryStatus": "delivery_normal",
            "open24h": "0",
            "markPrice": "12345"
        },
        {
            "symbol": "ETHUSD_231229",
            "lastPr": "1829.3",
            "askPr": "1829.8",
            "bidPr": "1829.3",
            "bidSz": "0.054",
            "askSz": "0.785",
            "high24h": "0",
            "low24h": "0",
            "ts": "1695794271400",
            "change24h": "0",
            "baseVolume": "0",
            "quoteVolume": "0",
            "usdtVolume": "0",
            "openUtc": "0",
            "changeUtc24h": "0",
            "indexPrice": "1822.15",
            "fundingRate": "0",
            "holdingAmount": "9488.49",
            "deliveryStartTime": "1693538723186",
            "deliveryTime": "1703836799000",
            "deliveryStatus": "delivery_normal",
            "open24h": "0",
            "markPrice": "1234"
        }
    ]
}

Response Parameters
Parameter	Type	Description
> symbol	String	Trading pair name
> lastPr	String	Last price
> askPr	String	Ask price
> bidPr	String	Bid price
> bidSz	String	Buying amount
> askSz	String	Selling amount
> high24h	String	24h high
> low24h	String	24h low
> ts	String	Milliseconds format of current data timestamp Unix, e.g. 1597026383085
> change24h	String	Price increase or decrease (24 hours)
> baseVolume	String	Trading volume of the coin
> quoteVolume	String	Trading volume of quote currency
> usdtVolume	String	Trading volume of USDT
> openUtc	String	UTC0 opening price
> changeUtc24h	String	UTC0 24-hour price increase and decrease
> indexPrice	String	Index price
> fundingRate	String	Funding rate
> holdingAmount	String	Current positions in the unit of number of coins traded.
> open24h	String	Entry price of the last 24 hours
The opening time is compared on a 24-hour basis. i.e.: Now it is 7:00 PM of the 2nd day of the month, then the corresponding opening time is 7:00 PM of the 1st day of the month.
> deliveryStartTime	String	Delivery start time (only for delivery contracts)
> deliveryTime	String	Delivery time (only for delivery contracts）
> deliveryStatus	String	Delivery status (only for delivery contracts; delivery_config_period: Newly listed currency pairs are configured
delivery_normal: Trading normally
delivery_before: 10 minutes before delivery, opening positions are prohibited
delivery_period: Delivery, opening, closing, and canceling orders are prohibited
> markPrice	String	Mark price


Get Candlestick Data
Frequency limit: 20 times/1s (IP)

Description
By default, 100 records are returned. If there is no data, an empty array is returned. The queryable data history varies depending on the k-line granularity.


The rules are as follows:
1m, 3m, and 5m can be checked for up to one month;
15m can be checked for up to 52 days;
30m can be searched for up to 62 days;
1H can be checked for up to 83 days;
2H can be checked for up to 120 days;
4H can be checked for up to 240 days;
6H can be checked for up to 360 days
HTTP Request
GET /api/v2/mix/market/candles
Request Example
curl "https://api.bitget.com/api/v2/mix/market/candles?symbol=BTCUSDT&granularity=5m&limit=100&productType=usdt-futures"


Request Parameters
Parameter	Type	Required	Description
symbol	String	Yes	Trading pair
productType	String	Yes	Product type
USDT-FUTURES USDT-M Futures
COIN-FUTURES Coin-M Futures
USDC-FUTURES USDC-M Futures
granularity	String	Yes	K-line particle size
- 1m(1 minute)
- 3m(3 minutes)
- 5m(5 minutes)
- 15m(15 minutes)
- 30m(30 minutes)
- 1H( 1 hour)
- 4H(4 hours)
- 6H(6 hours)
- 12H(12 hours)
- 1D(1 day)
- 3D ( 3 days)
- 1W (1 week)
- 1M (monthly line)
- 6Hutc (UTC 6 hour line)
- 12Hutc (UTC 12 hour line)
- 1Dutc (UTC 1-day line)
- 3Dutc (UTC 3-day line)
- 1Wutc (UTC weekly line)
- 1Mutc (UTC monthly line)
startTime	String	No	The start time is to query the k-lines after this time
According to the different time granularity, the corresponding time unit must be rounded down to be queried.
The millisecond format of the Unix timestamp, such as 1672410780000
Request data after this start time (the maximum time query range is 90 days)
endTime	String	No	The end time is to query the k-lines before this time
According to the different time granularity, the corresponding time unit must be rounded down to be queried.
The millisecond format of the Unix timestamp, such as 1672410780000
Request data before this end time (the maximum time query range is 90 days)
kLineType	String	No	Candlestick chart types: MARKET tick; MARK mark; INDEX index;
MARKET by default
limit	String	No	Default: 100, maximum: 1000
Response Example
{
    "code": "00000",
    "msg": "success",
    "requestTime": 1695865615662,
    "data": [
        [
            "1695835800000",
            "26210.5",
            "26210.5",
            "26194.5",
            "26194.5",
            "26.26",
            "687897.63"
        ],
        [
            "1695836100000",
            "26194.5",
            "26194.5",
            "26171",
            "26171",
            "17.98",
            "470618.72"
        ]
    ]
}

Response Parameters
Parameter	Type	Description
index[0]	String	Milliseconds format of timestamp Unix, e.g. 1597026383085
index[1]	String	Entry price
index[2]	String	Highest price
index[3]	String	Lowest price
index[4]	String	Exit price. The latest exit price may be updated in the future. Subscribe to WebSocket to track the latest price.
index[5]	String	Trading volume of the base coin
index[6]	String	Trading volume of quote currency

Get Historical Candlestick
Frequency limit: 20 times/1s (IP)

Description
Query all historical K-line data and return a maximum of 200 pieces of data.

HTTP Request
GET /api/v2/mix/market/history-candles
Request Example
curl "https://api.bitget.com/api/v2/mix/market/history-candles?symbol=BTCUSDT&granularity=1W&limit=200&productType=usdt-futures"


Request Parameters
Parameter	Type	Required	Description
symbol	String	Yes	Trading pair
productType	String	Yes	Product type
USDT-FUTURES USDT-M Futures
COIN-FUTURES Coin-M Futures
USDC-FUTURES USDC-M Futures
granularity	String	Yes	K-line particle size
- 1m(1 minute)
- 3m(3 minutes)
- 5m(5 minutes)
- 15m(15 minutes)
- 30m(30 minutes)
- 1H( 1 hour)
- 4H(4 hours)
- 6H(6 hours)
- 12H(12 hours)
- 1D(1 day)
- 3D ( 3 days)
- 1W (1 week)
- 1M (monthly line)
- 6Hutc (UTC 6 hour line)
- 12Hutc (UTC 12 hour line)
- 1Dutc (UTC 1-day line)
- 3Dutc (UTC 3-day line)
- 1Wutc (UTC weekly line)
- 1Mutc (UTC monthly line)
startTime	String	No	The start time is to query the k-lines after this time
According to the different time granularity, the corresponding time unit must be rounded down to be queried.
The millisecond format of the Unix timestamp, such as 1672410780000
Request data after this start time (the maximum time query range is 90 days)
endTime	String	No	The end time is to query the k-lines before this time
According to the different time granularity, the corresponding time unit must be rounded down to be queried.
The millisecond format of the Unix timestamp, such as 1672410780000
Request data before this end time (the maximum time query range is 90 days)
limit	String	No	Default: 100, maximum: 200
Response Example
{
    "code": "00000",
    "msg": "success",
    "requestTime": 1695865864944,
    "data": [
        [
            "1687708800000",
            "27176.93",
            "27177.43",
            "27166.93",
            "27177.43",
            "2990.08",
            "81246917.3294"
        ],
        [
            "1688313600000",
            "27177.43",
            "27177.43",
            "24000",
            "24001",
            "2989.1",
            "72450031.0448"
        ]
    ]
}

Response Parameters
Parameter	Type	Description
index[0]	String	Milliseconds format of timestamp Unix, e.g. 1597026383085
index[1]	String	Entry price
index[2]	String	Highest price
index[3]	String	Lowest price
index[4]	String	Exit price(Only include the finished K line data)
index[5]	String	Trading volume of the base coin
index[6]	String	Trading volume of quote currency

Get Merge Market Depth
Frequency limit: 20 times/1s (IP)

Description
Get merge depth data

HTTP Request
GET /api/v2/mix/market/merge-depth
Request Example
curl "https://api.bitget.com/api/v2/mix/market/merge-depth?productType=usdt-futures&symbol=BTCUSDT"


Request Parameters
Parameter	Type	Required	Description
symbol	String	Yes	Trading pair
productType	String	Yes	Product type
USDT-FUTURES USDT-M Futures
COIN-FUTURES Coin-M Futures
USDC-FUTURES USDC-M Futures
precision	String	No	Price accuracy, according to the selected accuracy as the step size to return the cumulative depth, enumeration value:
scale0/scale1/scale2/scale3
'scale0' is not merged, the default value
In general, 'scale1' is the merged depth of the transaction pair’s quotation accuracy10
Generally, 'scale2' is the quotation precision 100
'scale3' is the quotation precision *1000
The precision corresponding to 0/1/2/3 is subject to the actual return parameter "scale". The quotation precision of each trading pair is different, and some trading pairs does not have 'scale2', and the request for a scale that does not exist for the currency pair will be processed according to the maximum scale. Example: A certain trading pair only has scale 0/1, and when scale2 is requested, it will be automatically reduced to 'scale1'.
limit	String	No	Fixed gear enumeration value: 1/5/15/50/max, the default gear is 100, passing max returns the maximum gear of the trading pair
When the actual depth does not meet the limit, return according to the actual gear . If max is passed in, the maximum level of the trading pair will be returned.
Response Example
{
    "code": "00000",
    "msg": "success",
    "requestTime": 1695870963008,
    "data": {
        "asks": [
            [
                26347.5,
                0.25
            ],
            [
                26348.0,
                0.16
            ]
        ],
        "bids": [
            [
                26346.5,
                0.16
            ],
            [
                26346.0,
                0.32
            ]
        ],
        "ts": "1695870968804",
        "scale": "0.1",
        "precision": "scale0",
        "isMaxPrecision": "NO"
    }
}

Response Parameters
Parameter	Type	Description
asks	List<String>	The selling price
elements are price and quantity.
> Index 0	String	Price
> Index 1	String	Quantity
bids	List<String>	Buying price
The elements are price and quantity.
> Index 0	String	Price
> Index 1	String	Quantity
precision	String	Requested precision
scale	String	Actual precision value
isMaxPrecision	String	YES indicates that the current accuracy is the maximum, NO indicates that it is not the maximum accuracy.
ts	String	Matching engine timestamp(ms), e.g. 1597026383085

Market Channel
Description
Retrieve the latest traded price, bid price, ask price and 24-hour trading volume of the instruments. When there is a change (deal, buy, sell, issue): 300ms to 400ms.

Request Example
{
    "op": "subscribe",
    "args": [
        {
            "instType": "USDT-FUTURES",
            "channel": "ticker",
            "instId": "BTCUSDT"
        }
    ]
}

Request Parameters
Parameter	Type	Required	Description
op	String	Yes	Operation, subscribe unsubscribe
args	List<Object>	Yes	List of channels to request subscription
> instType	String	Yes	Product type
> channel	String	Yes	Channel name
> instId	String	Yes	Product ID
E.g. ETHUSDT
Response Example
{
    "event": "subscribe",
    "arg": {
        "instType": "USDT-FUTURES",
        "channel": "ticker",
        "instId": "BTCUSDT"
    }
}

Response Parameters
Parameter	Type	Description
event	String	Event
arg	Object	Subscribed channels
> instType	String	Product type
> channel	String	Channel name
> instId	String	Product ID
E.g. ETHUSDT
code	String	Error code
msg	String	Error message
Push Data
{
  "data": [
    {
      "lastPr": "87673.6",
      "symbol": "BTCUSDT",
      "indexPrice": "87714.0732915359034044",
      "open24h": "87027.0",
      "nextFundingTime": "1766678400000",
      "bidPr": "87673.6",
      "change24h": "0.00743",
      "quoteVolume": "1521198076.61216",
      "deliveryPrice": "0",
      "askSz": "14.333",
      "low24h": "86542.5",
      "symbolType": "1",
      "openUtc": "87628.9",
      "instId": "BTCUSDT",
      "bidSz": "6.9129",
      "markPrice": "87673.7",
      "high24h": "88022.1",
      "askPr": "87673.7",
      "holdingAmount": "28135.5456",
      "baseVolume": "17398.1612",
      "fundingRate": "0.000055",
      "ts": "1766674540816"
    }
  ],
  "arg": {
    "instType": "USDT-FUTURES",
    "instId": "BTCUSDT",
    "channel": "ticker"
  },
  "action": "snapshot",
  "ts": 1766674540817
}

Push Parameters
Parameter	Type	Description
arg	Object	Channels with successful subscription
> instType	String	Product type
> channel	String	Channel name
> instId	String	Product ID
action	String	Push data action, snapshot or update
data	List	Subscription data
> instId	String	Product ID, BTCUSDT
>lastPr	String	Latest price
>askPr	String	Ask price
>bidPr	String	Bid price
>high24h	String	24h high
>low24h	String	24h low
>change24h	String	24h change
>fundingRate	String	Funding rate
>nextFundingTime	String	Next funding rate settlement time, Milliseconds format of timestamp Unix, e.g. 1597026383085
>ts	String	System time, Milliseconds format of current data timestamp Unix, e.g. 1597026383085
>markPrice	String	Mark price
>indexPrice	String	Index price
>holdingAmount	String	Open interest
>baseVolume	String	Trading volume of the coin
>quoteVolume	String	Trading volume of quote currency
>openUtc	String	Price at 00:00 (UTC)
>symbolType	String	SymbolType: 1->perpetual 2->delivery
>symbol	String	Trading pair
>deliveryPrice	String	Delivery price of the delivery futures, when symbolType = 1(perpetual) it is always 0
It will be pushed 1 hour before delivery
>bidSz	String	Buying amount
>askSz	String	selling amount
>open24h	String	Entry price of the last 24 hours, The opening time is compared on a 24-hour basis. i.e.: Now it is 7:00 PM of the 2nd day of the month, then the corresponding opening time is 7:00 PM of the 1st day of the month.
ts	String	Data streaming time

Depth Channel
Description
This is the channel to get the depth data
Default data push frequency for books, books5, books15 is 150ms
Default data push frequency for books1:10ms

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

After subscribe to the channel (such as books ) of Order book , user first receive the initial snapshot of market depth. Afterwards the incremental update is subsequently received, user are responsible to update the snapshot from client side.

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
            "instType": "USDT-FUTURES",
            "channel": "books5",
            "instId": "BTCUSDT"
        }
    ]
}

Request Parameters
Parameter	Type	Required	Description
op	String	Yes	Operation, subscribe unsubscribe
args	List<Object>	Yes	List of channels to request subscription
> instType	String	Yes	Product type
USDT-FUTURES USDT-M Futures
COIN-FUTURES Coin-M Futures
USDC-FUTURES USDC-M Futures
> channel	String	Yes	Channel name: books/books1/books5/books15
> instId	String	Yes	Product ID
Response Example
{
    "event": "subscribe",
    "arg": {
        "instType": "USDT-FUTURES",
        "channel": "books5",
        "instId": "BTCUSDT"
    }
}

Response Parameters
Parameter	Type	Description
event	String	Event,
arg	Object	Subscribed channels
> instType	String	Product type
USDT-FUTURES USDT-M Futures
COIN-FUTURES Coin-M Futures
USDC-FUTURES USDC-M Futures
> channel	String	Channel name, books/books1/books5/books15
> instId	String	Product ID, e.g. ETHUSDT
msg	String	Error message
code	String	Error code, returned only on error
Push Data
{
    "action": "snapshot",
    "arg": {
        "instType": "USDT-FUTURES",
        "channel": "books5",
        "instId": "BTCUSDT"
    },
    "data": [
        {
            "asks": [
                [
                    "27000.5",
                    "8.760"
                ],
                [
                    "27001.0",
                    "0.400"
                ]
            ],
            "bids": [
                [
                    "27000.0",
                    "2.710"
                ],
                [
                    "26999.5",
                    "1.460"
                ]
            ],
            "checksum": 0,
            "seq": 123,
            "ts": "1695716059516"
        }
    ],
    "ts": 1695716059516
}

Push Parameters
Parameter	Type	Description
arg	Object	Channels with successful subscription
> instType	String	Product type
USDT-FUTURES USDT-M Futures
COIN-FUTURES Coin-M Futures
USDC-FUTURES USDC-M Futures
> channel	String	Channel name, books/books1/books5/books15
> instId	String	Product ID
action	String	Push data action, Incremental push data or full volume push data
data	List<Object>	Subscription data
> asks	List<String>	Seller depth
> bids	List<String>	Buyer depth
> ts	String	Match engine timestamp(ms), e.g. 1597026383085
> checksum	Long	Testing and
> seq	Long	Serial number.
It increases when the order book is updated and can be used to determine whether there is out-of-order packets.
ts	String	Data streaming time