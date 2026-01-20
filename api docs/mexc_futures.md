Get Candlestick Data
Request Example

curl "https://contract.mexc.com/api/v1/contract/kline/BTC_USDT?interval=Min15&start=1609992674&end=1610113500"

Response Example

{
    "success": true,
    "code": 0,
    "data": {
        "time": [
            1761876000,
            1761876900,
            1761877800,
            1761878700,
            1761879600
        ],
        "open": [
            109573.9,
            109006.4,
            109301.5,
            108725.9,
            108794.7
        ],
        "close": [
            109006.4,
            109301.5,
            108725.9,
            108794.7,
            108669.9
        ],
        "high": [
            109628.1,
            109426.2,
            109350.2,
            108913.8,
            108815.1
        ],
        "low": [
            108953.3,
            109006.4,
            108666.2,
            108498.5,
            108649.0
        ],
        "vol": [
            5587051.0,
            5739575.0,
            5945477.0,
            5863529.0,
            1668892.0
        ],
        "amount": [
            6.106243567181E7,
            6.270099147368E7,
            6.47966331717E7,
            6.374986900458E7,
            1.814907510911E7
        ],
        "realOpen": [
            109574.0,
            109010.0,
            109301.4,
            108726.0,
            108794.8
        ],
        "realClose": [
            109006.4,
            109301.5,
            108725.9,
            108794.7,
            108669.9
        ],
        "realHigh": [
            109628.1,
            109426.2,
            109350.2,
            108913.8,
            108815.1
        ],
        "realLow": [
            108953.3,
            109010.0,
            108666.2,
            108498.5,
            108649.0
        ]
    }
}

GET api/v1/contract/kline/{symbol}
Rate limit: 20 times / 2 seconds

Request Parameters:

Parameter	Type	Required	Description
symbol	string	true	Contract symbol
interval	string	false	Interval: Min1, Min5, Min15, Min30, Min60, Hour4, Hour8, Day1, Week1, Month1. Default is Min1 if omitted
start	long	false	Start timestamp (seconds)
end	long	false	End timestamp (seconds)
Response Parameters:

Parameter	Type	Description
open	double	Open
close	double	Close
high	double	High
low	double	Low
vol	double	Volume
time	long	Time window
Notes:

The maximum number of data points per request is 2000. If your chosen start/end time and granularity exceed this limit, only 2000 data points will be returned. To obtain fine-grained data over a larger time span, make multiple requests with segmented time ranges.

If only the start time is provided, data from the start time to the current system time is returned. If only the end time is provided, the 2000 data points closest to the end time are returned. If neither is provided, the 2000 most recent data points relative to the current system time are returned.

Order book depth
Subscribe

{
  "method": "sub.depth",
  "param": {
    "symbol": "BTC_USDT"
  }
}

Unsubscribe

{
  "method": "unsub.depth",
  "param": {
    "symbol": "BTC_USDT"
  }
}

Sample data

{
  "channel": "push.depth",
  "data": {
    "asks": [[6859.5, 3251, 1]],
    "bids": [],
    "version": 96801927
  },
  "symbol": "BTC_USDT",
  "ts": 1587442022003
}

Receive depth data for a specific contract; after subscribing, updates are pushed every 200 ms.

Response fields:

Field	Type	Description
asks	List<Numeric[]>	Ask depth
bids	List<Numeric[]>	Bid depth
version	long	Version
Note: [411.8, 10, 1] → 411.8 is price，10 is the order numbers of the contract ,1 is the order quantity

Depth — specify minimum notional step
Subscribe

{ "method": "sub.depth.step", "param": { "symbol": "BTC_USDT", "step": "10" } }

Note: 10 means notional bucket size of 10; e.g., levels like 100010, 100020, 100030.

Unsubscribe

{
  "method": "unsub.depth.step",
  "param": { "symbol": "BTC_USDT", "step": "10" }
}

Sample data

{
  "channel": "push.depth.step",
  "data": {
    "askMarketLevelPrice": 111089.4,
    "asks": [
      [111090, 398676, 26],
      [111100, 410175, 8]
    ],
    "bidMarketLevelPrice": 111085.5,
    "bids": [
      [111080, 461204, 35],
      [111070, 386809, 3]
    ],
    "ct": 1760950364388,
    "version": 27883254360
  },
  "symbol": "BTC_USDT"
}

Receive depth data for contracts with a specified minimum notional step; after subscribing, updates are pushed every 200 ms.

Response fields:

Field	Type	Description
asks	List<Numeric[]>	Ask depth
bids	List<Numeric[]>	Bid depth
askMarketLevelPrice	decimal	Highest willing ask
bidMarketLevelPrice	decimal	Highest willing bid
version	long	Version
Note: [111090,398676,26] → 111090 is price，398676 is the order numbers of the contract ,26 is the order quantity

K-line data
Subscribe

{
  "method": "sub.kline",
  "param": {
    "symbol": "BTC_USDT",
    "interval": "Min60"
  },
  "gzip": false
}

Unsubscribe

{
  "method": "unsub.kline",
  "param": {
    "symbol": "BTC_USDT"
  }
}

Sample data

{
  "channel": "push.kline",
  "data": {
    "a": 233.740269343644737245,
    "c": 6885,
    "h": 6910.5,
    "interval": "Min60",
    "l": 6885,
    "o": 6894.5,
    "q": 1611754,
    "symbol": "BTC_USDT",
    "t": 1587448800
  },
  "symbol": "BTC_USDT"
}

Receive K-line updates as they occur.

interval options: Min1, Min5, Min15, Min30, Min60, Hour4, Hour8, Day1, Week1, Month1

Response fields:

Field	Type	Description
symbol	string	Contract
interval	string	Interval: Min1, Min5, Min15, Min30, Min60, Hour4, Hour8, Day1, Week1, Month1
a	decimal	Total traded amount
q	decimal	Total traded volume
o	decimal	Open
c	decimal	Close
h	decimal	High
l	decimal	Low
v	decimal	Total volume
ro	decimal	Real open
rc	decimal	Real close
rh	decimal	Real high
rl	decimal	Real low
t	long	Trade time in seconds (window start)