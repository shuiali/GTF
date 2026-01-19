Order book
GET /api/v3/depth

Weight: Adjusted based on the limit:

Limit	Request Weight
1-100	5
101-500	25
501-1000	50
1001-5000	250
Parameters:

Name	Type	Mandatory	Description
symbol	STRING	YES	
limit	INT	NO	Default: 100; Maximum: 5000.
If limit > 5000, only 5000 entries will be returned.
symbolStatus	ENUM	NO	Filters for symbols that have this tradingStatus.
A status mismatch returns error -1220 SYMBOL_DOES_NOT_MATCH_STATUS.
Valid values: TRADING, HALT, BREAK
Data Source: Memory

Response:

{
    "lastUpdateId": 1027024,
    "bids": [
        [
            "4.00000000",      // PRICE
            "431.00000000"     // QTY
        ]
    ],
    "asks": [["4.00000200", "12.00000000"]]
}

Kline/Candlestick data
GET /api/v3/klines

Kline/candlestick bars for a symbol. Klines are uniquely identified by their open time.

Weight: 2

Parameters:

Name	Type	Mandatory	Description
symbol	STRING	YES	
interval	ENUM	YES	
startTime	LONG	NO	
endTime	LONG	NO	
timeZone	STRING	NO	Default: 0 (UTC)
limit	INT	NO	Default: 500; Maximum: 1000.
Supported kline intervals (case-sensitive):

Interval	interval value
seconds	1s
minutes	1m, 3m, 5m, 15m, 30m
hours	1h, 2h, 4h, 6h, 8h, 12h
days	1d, 3d
weeks	1w
months	1M
Notes:

If startTime and endTime are not sent, the most recent klines are returned.
Supported values for timeZone:
Hours and minutes (e.g. -1:00, 05:45)
Only hours (e.g. 0, 8, 4)
Accepted range is strictly [-12:00 to +14:00] inclusive
If timeZone provided, kline intervals are interpreted in that timezone instead of UTC.
Note that startTime and endTime are always interpreted in UTC, regardless of timeZone.
Data Source: Database

Response:

[
    [
        1499040000000,         // Kline open time
        "0.01634790",          // Open price
        "0.80000000",          // High price
        "0.01575800",          // Low price
        "0.01577100",          // Close price
        "148976.11427815",     // Volume
        1499644799999,         // Kline Close time
        "2434.19055334",       // Quote asset volume
        308,                   // Number of trades
        "1756.87402397",       // Taker buy base asset volume
        "28.46694368",         // Taker buy quote asset volume
        "0"                    // Unused field, ignore.
    ]
]


UIKlines
GET /api/v3/uiKlines

The request is similar to klines having the same parameters and response.

uiKlines return modified kline data, optimized for presentation of candlestick charts.

Weight: 2

Parameters:

Name	Type	Mandatory	Description
symbol	STRING	YES	
interval	ENUM	YES	See klines
startTime	LONG	NO	
endTime	LONG	NO	
timeZone	STRING	NO	Default: 0 (UTC)
limit	INT	NO	Default: 500; Maximum: 1000.
If startTime and endTime are not sent, the most recent klines are returned.
Supported values for timeZone:
Hours and minutes (e.g. -1:00, 05:45)
Only hours (e.g. 0, 8, 4)
Accepted range is strictly [-12:00 to +14:00] inclusive
If timeZone provided, kline intervals are interpreted in that timezone instead of UTC.
Note that startTime and endTime are always interpreted in UTC, regardless of timeZone.
Data Source: Database

Response:

[
    [
        1499040000000,         // Kline open time
        "0.01634790",          // Open price
        "0.80000000",          // High price
        "0.01575800",          // Low price
        "0.01577100",          // Close price
        "148976.11427815",     // Volume
        1499644799999,         // Kline close time
        "2434.19055334",       // Quote asset volume
        308,                   // Number of trades
        "1756.87402397",       // Taker buy base asset volume
        "28.46694368",         // Taker buy quote asset volume
        "0"                    // Unused field. Ignore.
    ]
]

Symbol price ticker
GET /api/v3/ticker/price

Latest price for a symbol or symbols.

Weight:

Parameter	Symbols Provided	Weight
symbol	1	2
symbol parameter is omitted	4
symbols	Any	4
Parameters:

Name	Type	Mandatory	Description
symbol	STRING	NO	Parameter symbol and symbols cannot be used in combination.
If neither parameter is sent, prices for all symbols will be returned in an array.

Examples of accepted format for the symbols parameter: ["BTCUSDT","BNBUSDT"]
or
%5B%22BTCUSDT%22,%22BNBUSDT%22%5D
symbols	STRING	NO
symbolStatus	ENUM	NO	Filters for symbols that have this tradingStatus.
For a single symbol, a status mismatch returns error -1220 SYMBOL_DOES_NOT_MATCH_STATUS.
For multiple or all symbols, non-matching ones are simply excluded from the response.
Valid values: TRADING, HALT, BREAK
Data Source: Memory

Response:

{
    "symbol": "LTCBTC",
    "price": "4.00000200"
}

OR

[
    {
        "symbol": "LTCBTC",
        "price": "4.00000200"
    },
    {
        "symbol": "ETHBTC",
        "price": "0.07946600"
    }
]

Symbol order book ticker
GET /api/v3/ticker/bookTicker

Best price/qty on the order book for a symbol or symbols.

Weight:

Parameter	Symbols Provided	Weight
symbol	1	2
symbol parameter is omitted	4
symbols	Any	4
Parameters:

Name	Type	Mandatory	Description
symbol	STRING	NO	Parameter symbol and symbols cannot be used in combination.
If neither parameter is sent, bookTickers for all symbols will be returned in an array.

Examples of accepted format for the symbols parameter: ["BTCUSDT","BNBUSDT"]
or
%5B%22BTCUSDT%22,%22BNBUSDT%22%5D
symbols	STRING	NO
symbolStatus	ENUM	NO	Filters for symbols that have this tradingStatus.
For a single symbol, a status mismatch returns error -1220 SYMBOL_DOES_NOT_MATCH_STATUS.
For multiple or all symbols, non-matching ones are simply excluded from the response.
Valid values: TRADING, HALT, BREAK
Data Source: Memory

Response:

{
    "symbol": "LTCBTC",
    "bidPrice": "4.00000000",
    "bidQty": "431.00000000",
    "askPrice": "4.00000200",
    "askQty": "9.00000000"
}

OR

[
    {
        "symbol": "LTCBTC",
        "bidPrice": "4.00000000",
        "bidQty": "431.00000000",
        "askPrice": "4.00000200",
        "askQty": "9.00000000"
    },
    {
        "symbol": "ETHBTC",
        "bidPrice": "0.07946700",
        "bidQty": "9.00000000",
        "askPrice": "100000.00000000",
        "askQty": "1000.00000000"
    }
]

24hr ticker price change statistics
GET /api/v3/ticker/24hr

24 hour rolling window price change statistics. Careful when accessing this with no symbol.

Weight:

Parameter	Symbols Provided	Weight
symbol	1	2
symbol parameter is omitted	80
symbols	1-20	2
21-100	40
101 or more	80
symbols parameter is omitted	80
Parameters:

Name	Type	Mandatory	Description
symbol	STRING	NO	Parameter symbol and symbols cannot be used in combination.
If neither parameter is sent, tickers for all symbols will be returned in an array.

Examples of accepted format for the symbols parameter: ["BTCUSDT","BNBUSDT"]
or
%5B%22BTCUSDT%22,%22BNBUSDT%22%5D
symbols	STRING	NO
type	ENUM	NO	Supported values: FULL or MINI.
If none provided, the default is FULL
symbolStatus	ENUM	NO	Filters for symbols that have this tradingStatus.
For a single symbol, a status mismatch returns error -1220 SYMBOL_DOES_NOT_MATCH_STATUS.
For multiple or all symbols, non-matching ones are simply excluded from the response.
Valid values: TRADING, HALT, BREAK
Data Source: Memory

Response - FULL:

{
    "symbol": "BNBBTC",
    "priceChange": "-94.99999800",
    "priceChangePercent": "-95.960",
    "weightedAvgPrice": "0.29628482",
    "prevClosePrice": "0.10002000",
    "lastPrice": "4.00000200",
    "lastQty": "200.00000000",
    "bidPrice": "4.00000000",
    "bidQty": "100.00000000",
    "askPrice": "4.00000200",
    "askQty": "100.00000000",
    "openPrice": "99.00000000",
    "highPrice": "100.00000000",
    "lowPrice": "0.10000000",
    "volume": "8913.30000000",
    "quoteVolume": "15.30000000",
    "openTime": 1499783499040,
    "closeTime": 1499869899040,
    "firstId": 28385,     // First tradeId
    "lastId": 28460,      // Last tradeId
    "count": 76           // Trade count
}

OR

[
    {
        "symbol": "BNBBTC",
        "priceChange": "-94.99999800",
        "priceChangePercent": "-95.960",
        "weightedAvgPrice": "0.29628482",
        "prevClosePrice": "0.10002000",
        "lastPrice": "4.00000200",
        "lastQty": "200.00000000",
        "bidPrice": "4.00000000",
        "bidQty": "100.00000000",
        "askPrice": "4.00000200",
        "askQty": "100.00000000",
        "openPrice": "99.00000000",
        "highPrice": "100.00000000",
        "lowPrice": "0.10000000",
        "volume": "8913.30000000",
        "quoteVolume": "15.30000000",
        "openTime": 1499783499040,
        "closeTime": 1499869899040,
        "firstId": 28385,     // First tradeId
        "lastId": 28460,      // Last tradeId
        "count": 76           // Trade count
    }
]

Response - MINI:

{
    "symbol": "BNBBTC",               // Symbol Name
    "openPrice": "99.00000000",       // Opening price of the Interval
    "highPrice": "100.00000000",      // Highest price in the interval
    "lowPrice": "0.10000000",         // Lowest  price in the interval
    "lastPrice": "4.00000200",        // Closing price of the interval
    "volume": "8913.30000000",        // Total trade volume (in base asset)
    "quoteVolume": "15.30000000",     // Total trade volume (in quote asset)
    "openTime": 1499783499040,        // Start of the ticker interval
    "closeTime": 1499869899040,       // End of the ticker interval
    "firstId": 28385,                 // First tradeId considered
    "lastId": 28460,                  // Last tradeId considered
    "count": 76                       // Total trade count
}

OR

[
    {
        "symbol": "BNBBTC",
        "openPrice": "99.00000000",
        "highPrice": "100.00000000",
        "lowPrice": "0.10000000",
        "lastPrice": "4.00000200",
        "volume": "8913.30000000",
        "quoteVolume": "15.30000000",
        "openTime": 1499783499040,
        "closeTime": 1499869899040,
        "firstId": 28385,
        "lastId": 28460,
        "count": 76
    },
    {
        "symbol": "LTCBTC",
        "openPrice": "0.07000000",
        "highPrice": "0.07000000",
        "lowPrice": "0.07000000",
        "lastPrice": "0.07000000",
        "volume": "11.00000000",
        "quoteVolume": "0.77000000",
        "openTime": 1656908192899,
        "closeTime": 1656994592899,
        "firstId": 0,
        "lastId": 10,
        "count": 11
    }
]

Order book
{
    "id": "51e2affb-0aba-4821-ba75-f2625006eb43",
    "method": "depth",
    "params": {
        "symbol": "BNBBTC",
        "limit": 5
    }
}

Get current order book.

Note that this request returns limited market depth.

If you need to continuously monitor order book updates, please consider using WebSocket Streams:

<symbol>@depth<levels>
<symbol>@depth
You can use depth request together with <symbol>@depth streams to maintain a local order book.

Weight: Adjusted based on the limit:

Limit	Weight
1–100	5
101–500	25
501–1000	50
1001–5000	250
Parameters:

Name	Type	Mandatory	Description
symbol	STRING	YES	
limit	INT	NO	Default: 100; Maximum: 5000
symbolStatus	ENUM	NO	Filters for symbols that have this tradingStatus.
A status mismatch returns error -1220 SYMBOL_DOES_NOT_MATCH_STATUS
Valid values: TRADING, HALT, BREAK
Data Source: Memory

Response:

{
    "id": "51e2affb-0aba-4821-ba75-f2625006eb43",
    "status": 200,
    "result": {
        "lastUpdateId": 2731179239,
        // Bid levels are sorted from highest to lowest price.
        "bids": [
            [
                "0.01379900",     // Price
                "3.43200000"      // Quantity
            ],
            ["0.01379800", "3.24300000"],
            ["0.01379700", "10.45500000"],
            ["0.01379600", "3.82100000"],
            ["0.01379500", "10.26200000"]
        ],
        // Ask levels are sorted from lowest to highest price.
        "asks": [
            ["0.01380000", "5.91700000"],
            ["0.01380100", "6.01400000"],
            ["0.01380200", "0.26800000"],
            ["0.01380300", "0.33800000"],
            ["0.01380400", "0.26800000"]
        ]
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 2
        }
    ]
}

Symbol price ticker
{
    "id": "043a7cf2-bde3-4888-9604-c8ac41fcba4d",
    "method": "ticker.price",
    "params": {
        "symbol": "BNBBTC"
    }
}

Get the latest market price for a symbol.

If you need access to real-time price updates, please consider using WebSocket Streams:

<symbol>@aggTrade
<symbol>@trade
Weight: Adjusted based on the number of requested symbols:

Parameter	Weight
symbol	2
symbols	4
none	4
Parameters:

Name	Type	Mandatory	Description
symbol	STRING	NO	Query price for a single symbol
symbols	ARRAY of STRING	Query price for multiple symbols
symbolStatus	ENUM	NO	Filters for symbols that have this tradingStatus.
For a single symbol, a status mismatch returns error -1220 SYMBOL_DOES_NOT_MATCH_STATUS.
For multiple or all symbols, non-matching ones are simply excluded from the response.
Valid values: TRADING, HALT, BREAK
Notes:

symbol and symbols cannot be used together.

If no symbol is specified, returns information about all symbols currently trading on the exchange.

Data Source: Memory

Response:

{
    "id": "043a7cf2-bde3-4888-9604-c8ac41fcba4d",
    "status": 200,
    "result": {
        "symbol": "BNBBTC",
        "price": "0.01361900"
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 2
        }
    ]
}

If more than one symbol is requested, response returns an array:

{
    "id": "e739e673-24c8-4adf-9cfa-b81f30330b09",
    "status": 200,
    "result": [
        {
            "symbol": "BNBBTC",
            "price": "0.01363700"
        },
        {
            "symbol": "BTCUSDT",
            "price": "24267.15000000"
        },
        {
            "symbol": "BNBBUSD",
            "price": "331.10000000"
        }
    ],
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 4
        }
    ]
}

Symbol order book ticker
{
    "id": "057deb3a-2990-41d1-b58b-98ea0f09e1b4",
    "method": "ticker.book",
    "params": {
        "symbols": ["BNBBTC", "BTCUSDT"]
    }
}

Get the current best price and quantity on the order book.

If you need access to real-time order book ticker updates, please consider using WebSocket Streams:

<symbol>@bookTicker
Weight: Adjusted based on the number of requested symbols:

Parameter	Weight
symbol	2
symbols	4
none	4
Parameters:

Name	Type	Mandatory	Description
symbol	STRING	NO	Query ticker for a single symbol
symbols	ARRAY of STRING	Query ticker for multiple symbols
symbolStatus	ENUM	NO	Filters for symbols that have this tradingStatus.
For a single symbol, a status mismatch returns error -1220 SYMBOL_DOES_NOT_MATCH_STATUS.
For multiple or all symbols, non-matching ones are simply excluded from the response.
Valid values: TRADING, HALT, BREAK
Notes:

symbol and symbols cannot be used together.

If no symbol is specified, returns information about all symbols currently trading on the exchange.

Data Source: Memory

Response:

{
    "id": "9d32157c-a556-4d27-9866-66760a174b57",
    "status": 200,
    "result": {
        "symbol": "BNBBTC",
        "bidPrice": "0.01358000",
        "bidQty": "12.53400000",
        "askPrice": "0.01358100",
        "askQty": "17.83700000"
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 2
        }
    ]
}

If more than one symbol is requested, response returns an array:

{
    "id": "057deb3a-2990-41d1-b58b-98ea0f09e1b4",
    "status": 200,
    "result": [
        {
            "symbol": "BNBBTC",
            "bidPrice": "0.01358000",
            "bidQty": "12.53400000",
            "askPrice": "0.01358100",
            "askQty": "17.83700000"
        },
        {
            "symbol": "BTCUSDT",
            "bidPrice": "23980.49000000",
            "bidQty": "0.01000000",
            "askPrice": "23981.31000000",
            "askQty": "0.01512000"
        }
    ],
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 4
        }
    ]
}