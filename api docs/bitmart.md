Signature

The authentication type of each API endpoint will be indicated. If it is marked as SIGNED,it means that the endpoint requires a signature to access. If it is marked as KEYED, it means that the endpoint only requires an API Access KEY to be set in the request header.
Authentication Type

    NONE: Public endpoint, accessible to anyone
    KEYED: Endpoint requires a valid X-BM-KEY to be set in the request header
    SIGNED: Endpoint requires a valid X-BM-KEY and X-BM-SIGN signature to be set in the request header

1. Setting Request Parameters
1.1 Set Request Header Key

    Create X-BM-TIMESTAMP

Copy Success
// Java
System.currentTimeMillis();

// Python
int(time.time() * 1000) 

// Golang
time.Now().UnixNano() / int64(time.Millisecond)

// Nodejs & TypeScript
Date.now();

// Javascript
Date.now();

// PHP
round(microtime(true) * 1000)

// C#
DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()

    X-BM-KEY (Your created API Access KEY)
    X-BM-SIGN (Signature using Sha-256)
    X-BM-TIMESTAMP (Current timestamp in milliseconds when the request is sent)

1.2 Set Request Body Params

    For GET/DELETE requests, the query string is in form format, such as symbol=BMX&side=BUY.
    For POST/PUT requests, the query string is in JSON format, such as {"symbol":"BMX","side":"BUY"}.

2. Example

    Shell Example

Copy Success
echo -n '1589793796145#test001#{"symbol":"BTC_USDT","price":"8600","count":"100"}' | openssl dgst -sha256 -hmac "6c6c98544461bbe71db2bca4c6d7fd0021e0ba9efc215f9c6ad41852df9d9df9"
    (stdin)= c31dc326bf87f38bfb49a3f8494961abfa291bd549d0d98d9578e87516cee46d

    curl --location --request POST 'localhost:8080/spot/v1/test-post'
    --header 'Content-Type: application/json'
    --header 'X-BM-KEY: 80618e45710812162b04892c7ee5ead4a3cc3e56'
    --header 'X-BM-SIGN: c31dc326bf87f38bfb49a3f8494961abfa291bd549d0d98d9578e87516cee46d'
    --header 'X-BM-TIMESTAMP: 1589793796145'
    --d '{"symbol":"BTC_USDT","price":"8600","count":"100"}'

    Request API: /spot/v1/test-post (SIGNED)
    Request method: POST
    Current timestamp: timestamp=1589793796145
    Request body: {"symbol":"BTC_USDT","price":"8600","count":"100"}

Then set the following:

    X-BM-TIMESTAMP=1589793796145
    X-BM-KEY=Your_api_access_key
    X-BM-SIGN= hmac_sha256(Your_api_secret_key, X-BM-TIMESTAMP + '#' + Your_api_memo + '#' + {"symbol":"BTC_USDT","price":"8600","count":"100"})

Assuming the key you applied for is as follows:

    accessKey=80618e45710812162b04892c7ee5ead4a3cc3e56
    secretKey=6c6c98544461bbe71db2bca4c6d7fd0021e0ba9efc215f9c6ad41852df9d9df9
    memo=test001

then the right side is a complete request

You can also refer to the SDK or Quick Start API below to implement

Get Contract Details

Applicable to query contract details
Request URL

GET https://api-cloud-v2.bitmart.com/contract/public/details
Request Limit

See Detailed Rate Limit
Request Parameter

    Request

Copy Success
curl https://api-cloud-v2.bitmart.com/contract/public/details?symbol=BTCUSDT

Field 	Type 	Required? 	Description
symbol 	String 	No 	Symbol of the contract(like BTCUSDT)
Response Data

    Response

Copy Success
{
  "code": 1000,
  "message": "Ok",
  "trace": "9b92a999-9463-4c96-91a4-93ad1cad0d72",
  "data": {
    "symbols": [
      {
        "symbol": "BTCUSDT",
        "product_type": 1,
        "open_timestamp": 1594080000123,
        "expire_timestamp": 0,
        "settle_timestamp": 0,
        "base_currency": "BTC",
        "quote_currency": "USDT",
        "last_price": "23920",
        "volume_24h": "18969368",
        "turnover_24h": "458933659.7858",
        "index_price": "23945.25191635",
        "index_name": "BTCUSDT",
        "contract_size": "0.001",
        "min_leverage": "1",
        "max_leverage": "100",
        "price_precision": "0.1",
        "vol_precision": "1",
        "max_volume": "500000",
        "market_max_volume": "500000",
        "min_volume": "1",
        "funding_rate": "0.0001",
        "expected_funding_rate": "0.00011",
        "open_interest": "4134180870",
        "open_interest_value": "94100888927.0433258",
        "high_24h": "23900",
        "low_24h": "23100",
        "change_24h": "0.004",
        "funding_interval_hours": 8,
        "status": "Delisted",
        "delist_time": 1745830379
      },
      ...
    ]
  }
}

Field 	Type 	Description
symbols 	List 	Array of trading pair details

Description of the trading pair details field:
Trading pair details 	Type 	Description
symbols 	List 	Array of trading pair details
symbol 	String 	Symbol of the contract
product_type 	Int 	Contract type
-1=perpetual
-2=futures
base_currency 	String 	Base currency
quote_currency 	String 	Quote currency
volume_precision 	String 	Volume Precision
price_precision 	String 	Price Precision
max_volume 	String 	Maximum limit order quantity
market_max_volume 	String 	Maximum market order quantity
min_volume 	String 	Minimum order quantity
contract_size 	String 	Contract Size
index_price 	String 	Index Price
index_name 	String 	Index Name
min_leverage 	String 	Minimum leverage ratio
max_leverage 	String 	Maximum leverage ratio
turnover_24h 	String 	24 hours turnover
volume_24h 	String 	24 hours volume
last_price 	String 	Last Price
open_timestamp 	Long 	Opening time for the first time
expire_timestamp 	Long 	Expiration time，If null is returned, it does not expire
settle_timestamp 	Long 	Settlement time，If null is returned, it will not be automatically settlement
funding_rate 	String 	current funding rate
expected_funding_rate 	String 	expect funding rate
open_interest 	String 	Open interest
open_interest_value 	String 	Value of open interest
high_24h 	String 	24h High
low_24h 	String 	24h Low
change_24h 	String 	24h Change
funding_interval_hours 	Int 	Funding interval
status 	String 	Status
-Trading
-Delisted
delist_time 	Int 	Delisting time(status=Trading, Expected delisting time)