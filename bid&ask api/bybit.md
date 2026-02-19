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
Go
Java
Node.js
from pybit.unified_trading import HTTP
session = HTTP(testnet=True)
print(session.get_tickers(
    category="inverse",
    symbol="BTCUSD",
))

Response Example
Inverse
Option
Spot
{
    "retCode": 0,
    "retMsg": "OK",
    "result": {
        "category": "inverse",
        "list": [
            {
                "symbol": "BTCUSD",
                "lastPrice": "120635.50",
                "indexPrice": "114890.92",
                "markPrice": "114898.43",
                "prevPrice24h": "105595.90",
                "price24hPcnt": "0.142425",
                "highPrice24h": "131309.30",
                "lowPrice24h": "102007.60",
                "prevPrice1h": "119806.10",
                "openInterest": "240113967",
                "openInterestValue": "2089.79",
                "turnover24h": "115.6907",
                "volume24h": "13713832.0000",
                "fundingRate": "0.0001",
                "nextFundingTime": "1760371200000",
                "predictedDeliveryPrice": "",
                "basisRate": "",
                "deliveryFeeRate": "",
                "deliveryTime": "0",
                "ask1Size": "9854",
                "bid1Price": "103401.00",
                "ask1Price": "109152.80",
                "bid1Size": "1063",
                "basis": "",
                "preOpenPrice": "",
                "preQty": "",
                "curPreListingPhase": "",
                "fundingIntervalHour": "8",
                "basisRateYear": "",
                "fundingCap": "0.005"
            }
        ]
    },
    "retExtInfo": {},
    "time": 1760352369814
}