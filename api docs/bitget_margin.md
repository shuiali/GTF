Get Support Currencies
Frequency limit:10 times/1s (IP)

Description
HTTP Request
GET /api/v2/margin/currencies
Request Example
curl "https://api.bitget.com/api/v2/margin/currencies"
   -H "ACCESS-KEY:*******" \
   -H "ACCESS-SIGN:*******" \
   -H "ACCESS-PASSPHRASE:*****" \
   -H "ACCESS-TIMESTAMP:1659076670000" \
   -H "locale:en-US" \
   -H "Content-Type: application/json"


Request Parameters
Response Example
{
    "code": "00000",
    "msg": "success",
    "requestTime": 1679383565084,
    "data": [
        {
            "symbol": "ETHUSDT",
            "baseCoin": "ETH",
            "quoteCoin": "USDT",
            "maxCrossedLeverage": "3",
            "maxIsolatedLeverage": "10",
            "warningRiskRatio": "0.80000000",
            "liquidationRiskRatio": "1.00000000",
            "minTradeAmount": "0.00010000",
            "maxTradeAmount": "10000.00000000",
            "takerFeeRate": "0.00100000",
            "makerFeeRate": "0.00100000",
            "pricePrecision": "4",
            "quantityPrecision": "4",
            "minTradeUSDT": "5.00000000",
            "isBorrowable": true,
            "userMinBorrow": "0.00000001",
            "status": "1",
            "isIsolatedBaseBorrowable": true,
            "isIsolatedQuoteBorrowable": true,
            "isCrossBorrowable": true
        }
    ]
}

Response Parameters
Parameter	Type	Description
symbol	String	Trading pair
baseCoin	String	Base currency
quoteCoin	String	Quote currency
maxCrossedLeverage	String	Cross margin maximum leverage multiples
maxIsolatedLeverage	String	Cross margin maximum leverage multiples
warningRiskRatio	String	Warning risk ratio
liquidationRiskRatio	String	Liquidation risk ratio
minTradeAmount	String	Minimum trading volume
maxTradeAmount	String	Maximum trading volume
takerFeeRate	String	Taker rates
makerFeeRate	String	Maker rates
pricePrecision	String	Pricing precision
quantityPrecision	String	Amount precision
minTradeUSDT	String	Minimum trading volume (USDT)
isBorrowable	String	Borrowable or not(ignore)
userMinBorrow	String	Minimum borrowing
status	String	1: tradable 2: under temporary maintenance
isIsolatedBaseBorrowable	String	isolate base coin borrowable or not?
isIsolatedQuoteBorrowable	String	isolate quote coin borrowable or not?
isCrossBorrowable	String	corss borrowable or not?