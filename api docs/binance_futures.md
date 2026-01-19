24hr Ticker Price Change Statistics
API Description
24 hour rolling window price change statistics.
Careful when accessing this with no symbol.

HTTP Request
GET /fapi/v1/ticker/24hr

Request Weight
1 for a single symbol;
40 when the symbol parameter is omitted

Request Parameters
Name	Type	Mandatory	Description
symbol	STRING	NO	
If the symbol is not sent, tickers for all symbols will be returned in an array.
Response Example
Response:

{
  "symbol": "BTCUSDT",
  "priceChange": "-94.99999800",
  "priceChangePercent": "-95.960",
  "weightedAvgPrice": "0.29628482",
  "lastPrice": "4.00000200",
  "lastQty": "200.00000000",
  "openPrice": "99.00000000",
  "highPrice": "100.00000000",
  "lowPrice": "0.10000000",
  "volume": "8913.30000000",
  "quoteVolume": "15.30000000",
  "openTime": 1499783499040,
  "closeTime": 1499869899040,
  "firstId": 28385,   // First tradeId
  "lastId": 28460,    // Last tradeId
  "count": 76         // Trade count
}

OR

[
	{
  		"symbol": "BTCUSDT",
  		"priceChange": "-94.99999800",
  		"priceChangePercent": "-95.960",
  		"weightedAvgPrice": "0.29628482",
  		"lastPrice": "4.00000200",
  		"lastQty": "200.00000000",
  		"openPrice": "99.00000000",
  		"highPrice": "100.00000000",
  		"lowPrice": "0.10000000",
  		"volume": "8913.30000000",
  		"quoteVolume": "15.30000000",
  		"openTime": 1499783499040,
  		"closeTime": 1499869899040,
  		"firstId": 28385,   // First tradeId
  		"lastId": 28460,    // Last tradeId
  		"count": 76         // Trade count
	}
]

Kline/Candlestick Data
API Description
Kline/candlestick bars for a symbol. Klines are uniquely identified by their open time.

HTTP Request
GET /fapi/v1/klines

Request Weight
based on parameter LIMIT

LIMIT	weight
[1,100)	1
[100, 500)	2
[500, 1000]	5
> 1000	10
Request Parameters
Name	Type	Mandatory	Description
symbol	STRING	YES	
interval	ENUM	YES	
startTime	LONG	NO	
endTime	LONG	NO	
limit	INT	NO	Default 500; max 1500.
If startTime and endTime are not sent, the most recent klines are returned.
Response Example
[
  [
    1499040000000,      // Open time
    "0.01634790",       // Open
    "0.80000000",       // High
    "0.01575800",       // Low
    "0.01577100",       // Close
    "148976.11427815",  // Volume
    1499644799999,      // Close time
    "2434.19055334",    // Quote asset volume
    308,                // Number of trades
    "1756.87402397",    // Taker buy base asset volume
    "28.46694368",      // Taker buy quote asset volume
    "17928899.62484339" // Ignore.
  ]
]

Order Book
API Description
Query symbol orderbook

HTTP Request
GET /fapi/v1/depth

Note:

Retail Price Improvement(RPI) orders are not visible and excluded in the response message.

Request Weight
Adjusted based on the limit:

Limit	Weight
5, 10, 20, 50	2
100	5
500	10
1000	20
Request Parameters
Name	Type	Mandatory	Description
symbol	STRING	YES	
limit	INT	NO	Default 500; Valid limits:[5, 10, 20, 50, 100, 500, 1000]
Response Example
{
  "lastUpdateId": 1027024,
  "E": 1589436922972,   // Message output time
  "T": 1589436922959,   // Transaction time
  "bids": [
    [
      "4.00000000",     // PRICE
      "431.00000000"    // QTY
    ]
  ],
  "asks": [
    [
      "4.00000200",
      "12.00000000"
    ]
  ]
}

Order Book
API Description
Get current order book. Note that this request returns limited market depth. If you need to continuously monitor order book updates, please consider using Websocket Market Streams:

<symbol>@depth<levels>
<symbol>@depth
You can use depth request together with <symbol>@depth streams to maintain a local order book.

Method
depth

Note:

Retail Price Improvement(RPI) orders are not visible and excluded in the response message.

Request
{
    "id": "51e2affb-0aba-4821-ba75-f2625006eb43",
    "method": "depth",
    "params": {
      "symbol": "BTCUSDT"
    }
}

Request Weight
Adjusted based on the limit:

Limit	Weight
5, 10, 20, 50	2
100	5
500	10
1000	20
Request Parameters
Name	Type	Mandatory	Description
symbol	STRING	YES	
limit	INT	NO	Default 500; Valid limits:[5, 10, 20, 50, 100, 500, 1000]
Response Example
{
  "id": "51e2affb-0aba-4821-ba75-f2625006eb43",
  "status": 200,
  "result": {
    "lastUpdateId": 1027024,
    "E": 1589436922972,   // Message output time
    "T": 1589436922959,   // Transaction time
    "bids": [
      [
        "4.00000000",     // PRICE
        "431.00000000"    // QTY
      ]
    ],
    "asks": [
      [
        "4.00000200",
        "12.00000000"
      ]
    ]
  },
  "rateLimits": [
    {
      "rateLimitType": "REQUEST_WEIGHT",
      "interval": "MINUTE",
      "intervalNum": 1,
      "limit": 2400,
      "count": 5
    }
  ]
}

Symbol Price Ticker
API Description
Latest price for a symbol or symbols.

Method
ticker.price

Request
{
   	"id": "9d32157c-a556-4d27-9866-66760a174b57",
    "method": "ticker.price",
    "params": {
        "symbol": "BTCUSDT"
    }
}

Weight:

1 for a single symbol;
2 when the symbol parameter is omitted

Request Parameters
Name	Type	Mandatory	Description
symbol	STRING	NO	
If the symbol is not sent, prices for all symbols will be returned in an array.
Response Example
{
  "id": "9d32157c-a556-4d27-9866-66760a174b57",
  "status": 200,
  "result": {
	"symbol": "BTCUSDT",
	"price": "6000.01",
	"time": 1589437530011   // Transaction time
  },
  "rateLimits": [
    {
      "rateLimitType": "REQUEST_WEIGHT",
      "interval": "MINUTE",
      "intervalNum": 1,
      "limit": 2400,
      "count": 2
    }
  ]
}

OR

{
  "id": "9d32157c-a556-4d27-9866-66760a174b57",
  "status": 200,
  "result": [
	{
    	"symbol": "BTCUSDT",
      	"price": "6000.01",
      	"time": 1589437530011
  	}
  ],
  "rateLimits": [
    {
      "rateLimitType": "REQUEST_WEIGHT",
      "interval": "MINUTE",
      "intervalNum": 1,
      "limit": 2400,
      "count": 2
    }
  ]
}

Symbol Order Book Ticker
API Description
Best price/qty on the order book for a symbol or symbols.

Method
ticker.book

Note:

Retail Price Improvement(RPI) orders are not visible and excluded in the response message.

Request
{
    "id": "9d32157c-a556-4d27-9866-66760a174b57",
    "method": "ticker.book",
    "params": {
        "symbol": "BTCUSDT"
    }
}

Request Weight
2 for a single symbol;
5 when the symbol parameter is omitted

Request Parameters
Name	Type	Mandatory	Description
symbol	STRING	NO	
If the symbol is not sent, bookTickers for all symbols will be returned in an array.
The field X-MBX-USED-WEIGHT-1M in response header is not accurate from this endpoint, please ignore.
Response Example
{
  "id": "9d32157c-a556-4d27-9866-66760a174b57",
  "status": 200,
  "result": {
    "lastUpdateId": 1027024,
    "symbol": "BTCUSDT",
    "bidPrice": "4.00000000",
    "bidQty": "431.00000000",
    "askPrice": "4.00000200",
    "askQty": "9.00000000",
    "time": 1589437530011   // Transaction time
  },
  "rateLimits": [
    {
      "rateLimitType": "REQUEST_WEIGHT",
      "interval": "MINUTE",
      "intervalNum": 1,
      "limit": 2400,
      "count": 2
    }
  ]
}

OR

{
  "id": "9d32157c-a556-4d27-9866-66760a174b57",
  "status": 200,
  "result": [
    {
      "lastUpdateId": 1027024,
      "symbol": "BTCUSDT",
      "bidPrice": "4.00000000",
      "bidQty": "431.00000000",
      "askPrice": "4.00000200",
      "askQty": "9.00000000",
      "time": 1589437530011
    }
  ],
  "rateLimits": [
    {
      "rateLimitType": "REQUEST_WEIGHT",
      "interval": "MINUTE",
      "intervalNum": 1,
      "limit": 2400,
      "count": 2
    }
  ]
}