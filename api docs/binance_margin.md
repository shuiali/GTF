Public API Definitions
Terminology
These terms will be used throughout the documentation, so it is recommended especially for new users to read to help their understanding of the API.

base asset refers to the asset that is the quantity of a symbol. For the symbol BTCUSDT, BTC would be the base asset.
quote asset refers to the asset that is the price of a symbol. For the symbol BTCUSDT, USDT would be the quote asset.
ENUM definitions
Symbol status (status):

PRE_TRADING
TRADING
POST_TRADING
END_OF_DAY
HALT
AUCTION_MATCH
BREAK

Account and Symbol Permissions (permissions):

SPOT
MARGIN
LEVERAGED
TRD_GRP_002
TRD_GRP_003
TRD_GRP_004
TRD_GRP_005
TRD_GRP_006
TRD_GRP_007
TRD_GRP_008
TRD_GRP_009
TRD_GRP_010
TRD_GRP_011
TRD_GRP_012
TRD_GRP_013
TRD_GRP_014
Order status (status):

Status	Description
NEW	The order has been accepted by the engine.
PARTIALLY_FILLED	A part of the order has been filled.
FILLED	The order has been completed.
CANCELED	The order has been canceled by the user.
PENDING_CANCEL	Currently unused
REJECTED	The order was not accepted by the engine and not processed.
EXPIRED	The order was canceled according to the order type's rules (e.g. LIMIT FOK orders with no fill, LIMIT IOC or MARKET orders that partially fill) or by the exchange, (e.g. orders canceled during liquidation, orders canceled during maintenance)
EXPIRED_IN_MATCH	The order was canceled by the exchange due to STP trigger. (e.g. an order with EXPIRE_TAKER will match with existing orders on the book with the same account or same tradeGroupId)
OCO Status (listStatusType):

Status	Description
RESPONSE	This is used when the ListStatus is responding to a failed action. (E.g. Orderlist placement or cancellation)
EXEC_STARTED	The order list has been placed or there is an update to the order list status.
ALL_DONE	The order list has finished executing and thus no longer active.
OCO Order Status (listOrderStatus):

Status	Description
EXECUTING	Either an order list has been placed or there is an update to the status of the list.
ALL_DONE	An order list has completed execution and thus no longer active.
REJECT	The List Status is responding to a failed action either during order placement or order canceled.)
ContingencyType

OCO
AllocationType

SOR
WorkingFloor

EXCHANGE
SOR
Order types (orderTypes, type):

LIMIT
MARKET
STOP_LOSS
STOP_LOSS_LIMIT
TAKE_PROFIT
TAKE_PROFIT_LIMIT
LIMIT_MAKER
Order Response Type (newOrderRespType):

ACK
RESULT
FULL
Order side (side):

BUY
SELL
Time in force (timeInForce):

This sets how long an order will be active before expiration.

Status	Description
GTC	Good Til Canceled

An order will be on the book unless the order is canceled.
IOC	Immediate Or Cancel

An order will try to fill the order as much as it can before the order expires.
FOK	Fill or Kill

An order will expire if the full order cannot be filled upon execution.
Kline/Candlestick chart intervals:

s-> seconds; m -> minutes; h -> hours; d -> days; w -> weeks; M -> months

1s
1m
3m
5m
15m
30m
1h
2h
4h
6h
8h
12h
1d
3d
1w
1M
Rate limiters (rateLimitType)

REQUEST_WEIGHT

    {
      "rateLimitType": "REQUEST_WEIGHT",
      "interval": "MINUTE",
      "intervalNum": 1,
      "limit": 6000
    }

ORDERS

    {
      "rateLimitType": "ORDERS",
      "interval": "SECOND",
      "intervalNum": 10,
      "limit": 100
    },
    {
      "rateLimitType": "ORDERS",
      "interval": "DAY",
      "intervalNum": 1,
      "limit": 200000
    }

RAW_REQUESTS

    {
      "rateLimitType": "RAW_REQUESTS",
      "interval": "MINUTE",
      "intervalNum": 5,
      "limit": 5000
    }

REQUEST_WEIGHT

ORDERS

RAW_REQUESTS

Rate limit intervals (interval)

SECOND
MINUTE
DAY
Filters
Filters define trading rules on a symbol or an exchange. Filters come in two forms: symbol filters and exchange filters.

Symbol Filters
PRICE_FILTER
ExchangeInfo format:

  {
    "filterType": "PRICE_FILTER",
    "minPrice": "0.00000100",
    "maxPrice": "100000.00000000",
    "tickSize": "0.00000100"
  }

The PRICE_FILTER defines the price rules for a symbol. There are 3 parts:

minPrice defines the minimum price/stopPrice allowed; disabled on minPrice == 0.
maxPrice defines the maximum price/stopPrice allowed; disabled on maxPrice == 0.
tickSize defines the intervals that a price/stopPrice can be increased/decreased by; disabled on tickSize == 0.
Any of the above variables can be set to 0, which disables that rule in the price filter. In order to pass the price filter, the following must be true for price/stopPrice of the enabled rules:

price >= minPrice
price <= maxPrice
price % tickSize == 0
PERCENT_PRICE
ExchangeInfo format:

  {
    "filterType": "PERCENT_PRICE",
    "multiplierUp": "1.3000",
    "multiplierDown": "0.7000",
    "avgPriceMins": 5
  }

The PERCENT_PRICE filter defines the valid range for the price based on the average of the previous trades. avgPriceMins is the number of minutes the average price is calculated over. 0 means the last price is used.

In order to pass the percent price, the following must be true for price:

price <= weightedAveragePrice * multiplierUp
price >= weightedAveragePrice * multiplierDown
PERCENT_PRICE_BY_SIDE
ExchangeInfo format:

    {
          "filterType": "PERCENT_PRICE_BY_SIDE",
          "bidMultiplierUp": "1.2",
          "bidMultiplierDown": "0.2",
          "askMultiplierUp": "5",
          "askMultiplierDown": "0.8",
          "avgPriceMins": 1
    }

The PERCENT_PRICE_BY_SIDE filter defines the valid range for the price based on the average of the previous trades.

avgPriceMins is the number of minutes the average price is calculated over. 0 means the last price is used.


There is a different range depending on whether the order is placed on the BUY side or the SELL side.

Buy orders will succeed on this filter if:

Order price <= weightedAveragePrice * bidMultiplierUp
Order price >= weightedAveragePrice * bidMultiplierDown
Sell orders will succeed on this filter if:

Order Price <= weightedAveragePrice * askMultiplierUp
Order Price >= weightedAveragePrice * askMultiplierDown
LOT_SIZE
ExchangeInfo format:

  {
    "filterType": "LOT_SIZE",
    "minQty": "0.00100000",
    "maxQty": "100000.00000000",
    "stepSize": "0.00100000"
  }

The LOT_SIZE filter defines the quantity (aka "lots" in auction terms) rules for a symbol. There are 3 parts:

minQty defines the minimum quantity/icebergQty allowed.
maxQty defines the maximum quantity/icebergQty allowed.
stepSize defines the intervals that a quantity/icebergQty can be increased/decreased by.
In order to pass the lot size, the following must be true for quantity/icebergQty:

quantity >= minQty
quantity <= maxQty
quantity % stepSize == 0
MIN_NOTIONAL
ExchangeInfo format:

  {
    "filterType": "MIN_NOTIONAL",
    "minNotional": "0.00100000",
    "applyToMarket": true,
    "avgPriceMins": 5
  }

The MIN_NOTIONAL filter defines the minimum notional value allowed for an order on a symbol. An order's notional value is the price * quantity. If the order is an Algo order (e.g. STOP_LOSS_LIMIT), then the notional value of the stopPrice * quantity will also be evaluated. If the order is an Iceberg Order, then the notional value of the price * icebergQty will also be evaluated. applyToMarket determines whether or not the MIN_NOTIONAL filter will also be applied to MARKET orders. Since MARKET orders have no price, the average price is used over the last avgPriceMins minutes. avgPriceMins is the number of minutes the average price is calculated over. 0 means the last price is used.

NOTIONAL
ExchangeInfo format:

{
   "filterType": "NOTIONAL",
   "minNotional": "10.00000000",
   "applyMinToMarket": false,
   "maxNotional": "10000.00000000",
   "applyMaxToMarket": false,
   "avgPriceMins": 5
}

The NOTIONAL filter defines the acceptable notional range allowed for an order on a symbol.



applyMinToMarket determines whether the minNotional will be applied to MARKET orders.

applyMaxToMarket determines whether the maxNotional will be applied to MARKET orders.

In order to pass this filter, the notional (price * quantity) has to pass the following conditions:

price * quantity <= maxNotional
price * quantity >= minNotional
For MARKET orders, the average price used over the last avgPriceMins minutes will be used for calculation.

If the avgPriceMins is 0, then the last price will be used.

ICEBERG_PARTS
ExchangeInfo format:

  {
    "filterType": "ICEBERG_PARTS",
    "limit": 10
  }

The ICEBERG_PARTS filter defines the maximum parts an iceberg order can have. The number of ICEBERG_PARTS is defined as CEIL(qty / icebergQty).

MARKET_LOT_SIZE
ExchangeInfo format:

  {
    "filterType": "MARKET_LOT_SIZE",
    "minQty": "0.00100000",
    "maxQty": "100000.00000000",
    "stepSize": "0.00100000"
  }

The MARKET_LOT_SIZE filter defines the quantity (aka "lots" in auction terms) rules for MARKET orders on a symbol. There are 3 parts:

minQty defines the minimum quantity allowed.
maxQty defines the maximum quantity allowed.
stepSize defines the intervals that a quantity can be increased/decreased by.
In order to pass the market lot size, the following must be true for quantity:

quantity >= minQty
quantity <= maxQty
quantity % stepSize == 0
MAX_NUM_ORDERS
ExchangeInfo format:

  {
    "filterType": "MAX_NUM_ORDERS",
    "maxNumOrders": 25
  }

The MAX_NUM_ORDERS filter defines the maximum number of orders an account is allowed to have open on a symbol. Note that both "algo" orders and normal orders are counted for this filter.

MAX_NUM_ALGO_ORDERS
ExchangeInfo format:

  {
    "filterType": "MAX_NUM_ALGO_ORDERS",
    "maxNumAlgoOrders": 5
  }

The MAX_NUM_ALGO_ORDERS filter defines the maximum number of "algo" orders an account is allowed to have open on a symbol. "Algo" orders are STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, and TAKE_PROFIT_LIMIT orders.

MAX_NUM_ICEBERG_ORDERS
The MAX_NUM_ICEBERG_ORDERS filter defines the maximum number of ICEBERG orders an account is allowed to have open on a symbol. An ICEBERG order is any order where the icebergQty is > 0.

ExchangeInfo format:

  {
    "filterType": "MAX_NUM_ICEBERG_ORDERS",
    "maxNumIcebergOrders": 5
  }

MAX_POSITION
The MAX_POSITION filter defines the allowed maximum position an account can have on the base asset of a symbol. An account's position defined as the sum of the account's:

free balance of the base asset
locked balance of the base asset
sum of the qty of all open BUY orders
BUY orders will be rejected if the account's position is greater than the maximum position allowed.

If an order's quantity can cause the position to overflow, this will also fail the MAX_POSITION filter.

ExchangeInfo format:

{
  "filterType":"MAX_POSITION",
  "maxPosition":"10.00000000"
}

TRAILING_DELTA
ExchangeInfo format:

    {
          "filterType": "TRAILING_DELTA",
          "minTrailingAboveDelta": 10,
          "maxTrailingAboveDelta": 2000,
          "minTrailingBelowDelta": 10,
          "maxTrailingBelowDelta": 2000
   }

The TRAILING_DELTA filter defines the minimum and maximum value for the parameter trailingDelta.

In order for a trailing stop order to pass this filter, the following must be true:

For STOP_LOSS BUY, STOP_LOSS_LIMIT_BUY,TAKE_PROFIT SELL and TAKE_PROFIT_LIMIT SELL orders:

trailingDelta >= minTrailingAboveDelta
trailingDelta <= maxTrailingAboveDelta
For STOP_LOSS SELL, STOP_LOSS_LIMIT SELL, TAKE_PROFIT BUY, and TAKE_PROFIT_LIMIT BUY orders:

trailingDelta >= minTrailingBelowDelta
trailingDelta <= maxTrailingBelowDelta
Exchange Filters
EXCHANGE_MAX_NUM_ORDERS
ExchangeInfo format:

  {
    "filterType": "EXCHANGE_MAX_NUM_ORDERS",
    "maxNumOrders": 1000
  }

The EXCHANGE_MAX_NUM_ORDERS filter defines the maximum number of orders an account is allowed to have open on the exchange. Note that both "algo" orders and normal orders are counted for this filter.

EXCHANGE_MAX_NUM_ALGO_ORDERS
ExchangeInfo format:

  {
    "filterType": "EXCHANGE_MAX_NUM_ALGO_ORDERS",
    "maxNumAlgoOrders": 200
  }

The EXCHANGE_MAX_NUM_ALGO_ORDERS filter defines the maximum number of "algo" orders an account is allowed to have open on the exchange. "Algo" orders are STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, and TAKE_PROFIT_LIMIT orders.

EXCHANGE_MAX_NUM_ICEBERG_ORDERS
The EXCHANGE_MAX_NUM_ICEBERG_ORDERS filter defines the maximum number of iceberg orders an account is allowed to have open on the exchange.

ExchangeInfo format:

{
  "filterType": "EXCHANGE_MAX_NUM_ICEBERG_ORDERS",
  "maxNumIcebergOrders": 10000
}

Get All Isolated Margin Symbol(MARKET_DATA)
API Description
Get All Isolated Margin Symbol

HTTP Request
GET /sapi/v1/margin/isolated/allPairs

Request Weight
10(IP)

Request Parameters
Name	Type	Mandatory	Description
symbol	STRING	NO	
recvWindow	LONG	NO	No more than 60000
timestamp	LONG	YES	
Response Example
[
    {
        "base": "BNB",
        "isBuyAllowed": true,
        "isMarginTrade": true,
        "isSellAllowed": true,
        "quote": "BTC",
        "symbol": "BNBBTC"     
    },
    {
        "base": "TRX",
        "isBuyAllowed": true,
        "isMarginTrade": true,
        "isSellAllowed": true,
        "quote": "BTC",
        "symbol": "TRXBTC"    
    }
]

Get All Cross Margin Pairs (MARKET_DATA)
API Description
Get All Cross Margin Pairs

HTTP Request
GET /sapi/v1/margin/allPairs

Request Weight
1(IP)

Request Parameters
Name	Type	Mandatory	Description
symbol	STRING	NO	
Response Example
[
    {
        "base": "BNB",
        "id": 351637150141315861,
        "isBuyAllowed": true,
        "isMarginTrade": true,
        "isSellAllowed": true,
        "quote": "BTC",
        "symbol": "BNBBTC"
    },
    {
        "base": "TRX",
        "id": 351637923235429141,
        "isBuyAllowed": true,
        "isMarginTrade": true,
        "isSellAllowed": true,
        "quote": "BTC",
        "symbol": "TRXBTC",
        "delistTime": 1704973040
    },
    {
        "base": "XRP",
        "id": 351638112213990165,
        "isBuyAllowed": true,
        "isMarginTrade": true,
        "isSellAllowed": true,
        "quote": "BTC",
        "symbol": "XRPBTC"
    },
    {
        "base": "ETH",
        "id": 351638524530850581,
        "isBuyAllowed": true,
        "isMarginTrade": true,
        "isSellAllowed": true,
        "quote": "BTC",
        "symbol": "ETHBTC"
    }
]

Margin account borrow/repay(MARGIN)
API Description
Margin account borrow/repay(MARGIN)

HTTP Request
POST /sapi/v1/margin/borrow-repay

Request Weight
1500

Request Parameters
Name	Type	Mandatory	Description
asset	STRING	YES	
isIsolated	STRING	YES	TRUE for Isolated Margin, FALSE for Cross Margin, Default FALSE
symbol	STRING	YES	Only for Isolated margin
amount	STRING	YES	
type	STRING	YES	BORROW or REPAY
recvWindow	LONG	NO	The value cannot be greater than 60000
timestamp	LONG	YES	
Response Example
{
  //transaction id
  "tranId": 100000001
}

**Error Code Description: **

INSUFFICIENT_INVENTORY

The error {"code": -3045, "msg": "The system does not have enough asset now."} can occur to both manual Margin borrow requests and auto-borrow Margin orders that require actual borrowing. The error can be due to:

The Margin system's available assets are below the requested borrowing amount.
The system's inventory is critically low, leading to the rejection of all borrowing requests, irrespective of the amount.
We recommend monitoring the system status and adjusting your borrowing strategies accordingly.

EXCEED_MAX_BORROWABLE

The error {"code": -3006, "msg": "Your borrow amount has exceed maximum borrow amount."} occurs when your borrow request exceeds the maximum allowable amount. You can check the maximum borrowable amount using GET /sapi/v1/margin/maxBorrowable and adjust your request accordingly.

REPAY_EXCEED_LIABILITY

When repaying your debt, ensure that your repayment does not exceed the outstanding borrowed amount. Otherwise, the error {“code”: -3015, “msg”: “Repay amount exceeds borrow amount.”} will occur.

ASSET_ADMIN_BAN_BORROW

This error {“code”: -3012, “msg”: “Borrow is banned for this asset.”} indicates that borrowing is currently prohibited for the specified asset. You can check the availability of borrowing via GET /sapi/v1/margin/allAssets. You can also check if there are any announcements or updates regarding the asset's borrowing status on Binance's official channels.

FEW_LIABILITY_LEFT

If you get an error {"code": -3015, "msg": "The unpaid debt is too small after this repayment."}, this means your repayment would leave a remaining debt below Binance's minimum threshold. You can resolve this by adjusting the repayment to meet the minimum requirement.

HAS_PENDING_TRANSACTION

This error {“code”: -3007, “msg”: “You have pending transaction, please try again later.”} indicates that there is an ongoing borrow or repayment process in your account, preventing new borrow or repayment actions. This can occur in both manual and auto-borrow margin orders. Key points to consider:

Concurrent Transactions: The system processes borrow and repay requests sequentially, even if they involve different assets. An ongoing transaction can block new requests temporarily.
Processing Time: Typically, these borrow/repay complete within 100 milliseconds. To lower the potential of encountering this error, you may wish to set your requests apart with at least 100 milliseconds intervals.
Auto Repayment: Auto-repay orders might fail silently due to the same issue, without generating an error message. We suggest you check your outstanding loan once the auto-repay orders are triggered.

Margin Account New Order (TRADE)
API Description
Post a new order for margin account.

HTTP Request
POST /sapi/v1/margin/order

Request Weight
6(UID)

Request Parameters
Name	Type	Mandatory	Description
symbol	STRING	YES	
isIsolated	STRING	NO	for isolated margin or not, "TRUE", "FALSE"，default "FALSE"
side	ENUM	YES	BUY

SELL
type	ENUM	YES	
quantity	DECIMAL	NO	
quoteOrderQty	DECIMAL	NO	
price	DECIMAL	NO	
stopPrice	DECIMAL	NO	Used with STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, and TAKE_PROFIT_LIMIT orders.
newClientOrderId	STRING	NO	A unique id among open orders. Automatically generated if not sent.
icebergQty	DECIMAL	NO	Used with LIMIT, STOP_LOSS_LIMIT, and TAKE_PROFIT_LIMIT to create an iceberg order.
newOrderRespType	ENUM	NO	Set the response JSON. ACK, RESULT, or FULL; MARKET and LIMIT order types default to FULL, all other orders default to ACK.
sideEffectType	ENUM	NO	NO_SIDE_EFFECT, MARGIN_BUY, AUTO_REPAY,AUTO_BORROW_REPAY; default NO_SIDE_EFFECT. More info in FAQ
timeInForce	ENUM	NO	GTC,IOC,FOK
selfTradePreventionMode	ENUM	NO	The allowed enums is dependent on what is configured on the symbol. The possible supported values are EXPIRE_TAKER, EXPIRE_MAKER, EXPIRE_BOTH, NONE
autoRepayAtCancel	BOOLEAN	NO	Only when MARGIN_BUY or AUTO_BORROW_REPAY order takes effect, true means that the debt generated by the order needs to be repay after the order is cancelled. The default is true
recvWindow	LONG	NO	The value cannot be greater than 60000
timestamp	LONG	YES	
autoRepayAtCancel is suggested to set as “FALSE” to keep liability unrepaid under high frequent new order/cancel order execution
Response Example
Response ACK:

{
  "symbol": "BTCUSDT",
  "orderId": 28,
  "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
  "isIsolated": true,       // if isolated margin
  "transactTime": 1507725176595

}

Response RESULT:

{
    "symbol": "BTCUSDT",
    "orderId": 26769564559,
    "clientOrderId": "E156O3KP4gOif65bjuUK5V",
    "transactTime": 1713873075893,
    "price": "0",
    "origQty": "0.001",
    "executedQty": "0.001",
    "cummulativeQuoteQty": "65982.53",
    "status": "FILLED",
    "timeInForce": "GTC",
    "type": "MARKET",
    "side": "SELL",
    "isIsolated": false,   // if isolated margin
    "selfTradePreventionMode": "EXPIRE_MAKER"
}

Response FULL:

{
  "symbol": "BTCUSDT",
  "orderId": 26769564559,
  "clientOrderId": "E156O3KP4gOif65bjuUK5V",
  "transactTime": 1713873075893,
  "price": "0",
  "origQty": "0.001",
  "executedQty": "0.001",
  "cummulativeQuoteQty": "65.98253",
  "status": "FILLED",
  "timeInForce": "GTC",
  "type": "MARKET",
  "side": "SELL",
  "marginBuyBorrowAmount": 5,       // will not return if no margin trade happens
  "marginBuyBorrowAsset": "BTC",    // will not return if no margin trade happens
  "isIsolated": true,       // if isolated margin
  "selfTradePreventionMode": "NONE",
  "fills": [
        {
            "price": "65982.53",
            "qty": "0.001",
            "commission": "0.06598253",
            "commissionAsset": "USDT",
            "tradeId": 3570680726
        }
    ],
  "isIsolated": false,
  "selfTradePreventionMode": "EXPIRE_MAKER"
}

Error Code Description:

ASSET_BAN_TRADE

This error {“code”: -3067, “msg”: “This asset is currently not a supported margin asset, please try another asset.”} indicates that the asset is currently restricted. This restriction can be due to various reasons, such as the asset may be subject to regulatory restrictions that prevent it from being borrowed, etc.

You can verify if there are any announcements or updates regarding the asset's borrowing status on Binance's official channels.

NOT_VALID_MARGIN_ASSET

This error {“code”: -3027, “msg”: “Not a valid margin asset.”} occurs when a user requests an asset that is either delisted or is not supported on the margin product. Users can check the margin symbol info (GET /sapi/v1/margin/allAssets) to find all supported margin assets before trading.

BALANCE_NOT_CLEARED

This error {“code”: -3041, “msg”: “Balance is not enough.”} indicates that your account balance is insufficient to complete the requested transaction.

TOO_MANY_ORDERS

This error {“code”: -1015, “msg”: “Too many new orders; current limit is %s orders per %s.”} means that you have reached the limit for the number of orders you can place within a certain timeframe. To address this issue:

Review Open Orders: Check your current open orders and consider canceling any unnecessary ones to free up capacity.
Space Out Orders: If possible, space out your order placements to prevent hitting the limit.
Filter failure: NOTIONAL

This error {“code”:-20204, “msg”: “Filter failure: NOTIONAL.”} occurs when your request is blocked before reaching the Matching Engine, often due to the order value not meeting the minimum notional value requirement. By carefully reviewing your order request, you can identify and correct the issues causing the request rejection.

NOT_VALID_MARGIN_PAIR

This error {“code”: -3028, “msg”: “Not a valid margin pair.”} occurs when a user requests an asset that is either delisted or is not supported on the margin product. Users can check the margin symbol info (GET /sapi/v1/margin/allAssets) to find all supported margin assets before trading.

NEW_ORDER_REJECTED

This error {“code”: -2010, “msg”: “NEW_ORDER_REJECTED”} often occurs for two reasons:

When a limit order is placed at a price that would immediately execute as a market order. You can adjust your limit order price to ensure it does not match the current market price if you intend to avoid taker fees.
Your account does not have enough funds to cover the order. You can resolve this by transferring additional funds if necessary or reduce the order size to fit your available balance.
EXCEED_PRICE_LIMIT

This error {“code”: -3064, “msg”: “Limit price needs to be within (-15%,15%) of current index price for this margin trading pair.”} often occurs when the limit price is not allowed. For certain low liquidity pairs or stablecoin to stablecoin pairs on Margin (e.g. USDT/DAI), there will be a price bracket of [-15%, 15%] (which is subject to changes).

That is, when a BUY Margin order’s limit price is more than 15% higher than the current index price or a SELL Margin order’s limit price is more than 15% lower than the current index price, it will trigger this error message.

Margin Account Cancel Order (TRADE)
API Description
Cancel an active order for margin account.

HTTP Request
DELETE /sapi/v1/margin/order

Request Weight
10(IP)

Request Parameters
Name	Type	Mandatory	Description
symbol	STRING	YES	
isIsolated	STRING	NO	for isolated margin or not, "TRUE", "FALSE"，default "FALSE"
orderId	LONG	NO	
origClientOrderId	STRING	NO	
newClientOrderId	STRING	NO	Used to uniquely identify this cancel. Automatically generated by default.
recvWindow	LONG	NO	The value cannot be greater than 60000
timestamp	LONG	YES	
Either orderId or origClientOrderId must be sent.
Response Example
{
  "symbol": "LTCBTC",
  "isIsolated": true,       // if isolated margin
  "orderId": "28",
  "origClientOrderId": "myOrder1",
  "clientOrderId": "cancelMyOrder1",
  "price": "1.00000000",
  "origQty": "10.00000000",
  "executedQty": "8.00000000",
  "cummulativeQuoteQty": "8.00000000",
  "status": "CANCELED",
  "timeInForce": "GTC",
  "type": "LIMIT",
  "side": "SELL"
}

Error Code Description:

CANCEL_REJECTED

This error {“code”: -2011, “msg”: “Unknown order sent.”} occurs when the order (by either orderId, clientOrderId, origClientOrderId) could not be found in the matching engine. It often results from your attempt to cancel an order that has already been processed. You can review all orders(GET /sapi/v1/margin/allOrders) to confirm the status of the order.

Query Margin Account's Order (USER_DATA)
API Description
Query Margin Account's Order

HTTP Request
GET /sapi/v1/margin/order

Request Weight
10(IP)

Request Parameters
Name	Type	Mandatory	Description
symbol	STRING	YES	
isIsolated	STRING	NO	for isolated margin or not, "TRUE", "FALSE"，default "FALSE"
orderId	LONG	NO	
origClientOrderId	STRING	NO	
recvWindow	LONG	NO	The value cannot be greater than 60000
timestamp	LONG	YES	
Either orderId or origClientOrderId must be sent.
For some historical orders cummulativeQuoteQty will be < 0, meaning the data is not available at this time.
Response Example
{
   "clientOrderId": "ZwfQzuDIGpceVhKW5DvCmO",
   "cummulativeQuoteQty": "0.00000000",
   "executedQty": "0.00000000",
   "icebergQty": "0.00000000",
   "isWorking": true,
   "orderId": 213205622,
   "origQty": "0.30000000",
   "price": "0.00493630",
   "side": "SELL",
   "status": "NEW",
   "stopPrice": "0.00000000",
   "symbol": "BNBBTC",
   "isIsolated": true,
   "time": 1562133008725,
   "timeInForce": "GTC",
   "type": "LIMIT",
   "selfTradePreventionMode": "NONE",
   "updateTime": 1562133008725
}

Payload: Order update
Event Description
Orders are updated with the executionReport event.

Execution types:

NEW - The order has been accepted into the engine.
CANCELED - The order has been canceled by the user.
REPLACED (currently unused)
REJECTED - The order has been rejected and was not processed (This message appears only with Cancel Replace Orders wherein the new order placement is rejected but the request to cancel request succeeds.)
TRADE - Part of the order or all of the order's quantity has filled.
EXPIRED - The order was canceled according to the order type's rules (e.g. LIMIT FOK orders with no fill, LIMIT IOC or MARKET orders that partially fill) or by the exchange, (e.g. orders canceled during liquidation, orders canceled during maintenance).
TRADE_PREVENTION - The order has expired due to STP trigger.
Check the Public API Definitions for more relevant enum definitions.

These are fields that appear in the payload only if certain conditions are met.

Field	Name	Description	Examples
d	Trailing Delta	Appears only for trailing stop orders.	"d": 4
D	Trailing Time	"D": 1668680518494
j	Strategy Id	Appears only if the strategyId parameter was provided upon order placement.	"j": 1
J	Strategy Type	Appears only if the strategyType parameter was provided upon order placement.	"J": 1000000
v	Prevented Match Id	Appears only for orders that expired due to STP.	"v": 3
A	Prevented Quantity	"A":"3.000000"
B	Last Prevented Quantity	"B":"3.000000"
u	Trade Group Id	"u":1
U	Counter Order Id	"U":37
Cs	Counter Symbol	"Cs": "BTCUSDT"
pl	Prevented Execution Quantity	"pl":"2.123456"
pL	Prevented Execution Price	"pL":"0.10000001"
pY	Prevented Execution Quote Qty	"pY":"0.21234562"
W	Working Time	Appears when the order is working on the book	"W": 1668683798379
b	Match Type	Appears for orders that have allocations	"b":"ONE_PARTY_TRADE_REPORT"
a	Allocation ID	"a":1234
k	Working Floor	Appears for orders that could potentially have allocations	"k":"SOR"
uS	UsedSor	Appears for orders that used SOR	"uS":true
Event Name
executionReport

Response Example
Payload:

{
  "e": "executionReport",        // Event type
  "E": 1499405658658,            // Event time
  "s": "ETHBTC",                 // Symbol
  "c": "mUvoqJxFIILMdfAW5iGSOW", // Client order ID
  "S": "BUY",                    // Side
  "o": "LIMIT",                  // Order type
  "f": "GTC",                    // Time in force
  "q": "1.00000000",             // Order quantity
  "p": "0.10264410",             // Order price
  "P": "0.00000000",             // Stop price
  "F": "0.00000000",             // Iceberg quantity
  "g": -1,                       // OrderListId
  "C": "",                       // Original client order ID; This is the ID of the order being canceled
  "x": "NEW",                    // Current execution type
  "X": "NEW",                    // Current order status
  "r": "NONE",                   // Order reject reason; will be an error code.
  "i": 4293153,                  // Order ID
  "l": "0.00000000",             // Last executed quantity
  "z": "0.00000000",             // Cumulative filled quantity
  "L": "0.00000000",             // Last executed price
  "n": "0",                      // Commission amount
  "N": null,                     // Commission asset
  "T": 1499405658657,            // Transaction time
  "t": -1,                       // Trade ID
  "I": 8641984,                  // Ignore
  "w": true,                     // Is the order on the book?
  "m": false,                    // Is this trade the maker side?
  "M": false,                    // Ignore
  "O": 1499405658657,            // Order creation time
  "Z": "0.00000000",             // Cumulative quote asset transacted quantity
  "Y": "0.00000000",             // Last quote asset transacted quantity (i.e. lastPrice * lastQty)
  "Q": "0.00000000",             // Quote Order Quantity
  "W": 1499405658657,            // Working Time; This is only visible if the order has been placed on the book.
  "V": "NONE"                    // selfTradePreventionMode
}

If the order is an OCO, an event will be displayed named ListStatus in addition to the executionReport event.

{
  "e": "listStatus",                //Event Type
  "E": 1564035303637,               //Event Time
  "s": "ETHBTC",                    //Symbol
  "g": 2,                           //OrderListId
  "c": "OCO",                       //Contingency Type
  "l": "EXEC_STARTED",              //List Status Type
  "L": "EXECUTING",                 //List Order Status
  "r": "NONE",                      //List Reject Reason
  "C": "F4QN4G8DlFATFlIUQ0cjdD",    //List Client Order ID
  "T": 1564035303625,               //Transaction Time
  "O": [                            //An array of objects
    {
      "s": "ETHBTC",                //Symbol
      "i": 17,                      // orderId
      "c": "AJYsMjErWJesZvqlJCTUgL" //ClientOrderId
    },
    {
      "s": "ETHBTC",
      "i": 18,
      "c": "bfYPSQdLoqAJeNrOr9adzq"
    }
  ]
}