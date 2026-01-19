/market/history/kline ( Get Klines(Candles))
Request type: GET

Signature verification: No

Rate Limit:  4,500 5 minutes

Interface description:  This endpoint retrieves all klines in a specific range.


Request Address
Environment	Address
Online	https://api.huobi.pro
Online  (preferred by aws customers)	https://api-aws.huobi.pro
Request Parameter
Parameter	Data Type	Required	Description	Value Range	Default Value
symbol	string	 false	The trading symbol to query	All trading symbol supported, e.g. btcusdt, bccbtcn (to retrieve candlesticks for ETP NAV, symbol = ETP trading symbol + suffix 'nav'，for example: btc3lusdtnav)	
period	string	 false	The period of each candle	1min, 5min, 15min, 30min, 60min, 4hour, 1day, 1mon, 1week, 1year	
size	integer	 false	The number of data returns	[1-2000]	150
Response Parameter
Parameter	Data Type	Required	Description
status	string	 false	Request Processing Result "ok","error"
ch	string	 false	Data belonged channel，Format：market.$symbol.kline.$period
ts	long	 false	Time of Respond Generation, Unit: Millisecond
<data>	object	 false	
id	long	 false	The UNIX timestamp in seconds as response id
amount	float	 false	Accumulated trading volume, in base currency
count	integer	 false	The number of completed trades
open	float	 false	The opening price
close	float	 false	The closing price
low	float	 false	The low price
high	float	 false	The high price
vol	float	 false	Accumulated trading value, in quote currency
</data>		 false	
Request example
curl"https://api.huobi.pro/market/history/kline?period=1day&size=200&symbol=btcusdt"
Response Example
Success Example
{
"ch":"market.btcusdt.kline.5min"
"status":"ok"
"ts":1629769247172
"data":[
0:{
"id":1629769200
"open":49056.37
"close":49025.51
"low":49022.86
"high":49056.38
"amount":3.946281917950917
"vol":193489.67275732
"count":196
}
1:{
"id":1629768900
"open":48994.61
"close":49056.37
"low":48966.72
"high":49072.46
"amount":30.72223099519689
"vol":1505870.732227976
"count":1504
}
]
}

/market/tickers ( Get Latest Tickers for All Pairs)
Request type: GET

Signature verification: No

Rate Limit:  4,500 5 minutes

Interface description:  This endpoint retrieves the latest tickers for all supported pairs.

Request Address
Environment	Address
Online	https://api.huobi.pro
Online  (preferred by aws customers)	https://api-aws.huobi.pro
Request Parameter
Parameter	Data Type	Required	Description

No data

Notes:  
No parameters are needed for this endpoint.

Response Parameter
Parameter	Data Type	Required	Description
status	string	 false	Request Processing Result "ok","error"
ts	long	 false	Time of Respond Generation, Unit: Millisecond
<data>	object	 false	
amount	float	 false	The aggregated trading volume in last 24 hours (rotating 24h)
count	integer	 false	The number of completed trades of last 24 hours (rotating 24h)
open	float	 false	The opening price of a nature day (Singapore time)
close	float	 false	The closing price of a nature day (Singapore time)
low	float	 false	The lowest price of a nature day (Singapore time)
high	float	 false	The highest price of a nature day (Singapore time)
vol	float	 false	The aggregated trading value in last 24 hours (rotating 24h)
symbol	string	 false	The trading symbol of this object, e.g. btcusdt, bccbtc
bid	float	 false	Best bid price
bidSize	float	 false	Best bid size
ask	float	 false	Best ask price
askSize	float	 false	Best ask size
</data>		 false	
Request example
curl"https://api.huobi.pro/market/tickers"
Response Example
Success Example
{
"status":"ok"
"ts":1629789355531
"data":[
0:{
"symbol":"smtusdt"
"open":0.004659
"high":0.004696
"low":0.0046
"close":0.00468
"amount":36551302.17544405
"vol":170526.0643855023
"count":1709
"bid":0.004651
"bidSize":54300.341
"ask":0.004679
"askSize":1923.4879
}
1:{
"symbol":"ltcht"
"open":12.795626
"high":12.918053
"low":12.568926
"close":12.918053
"amount":1131.801675005825
"vol":14506.9381937385
"count":923
"bid":12.912687
"bidSize":0.1068
"ask":12.927032
"askSize":5.3228
}
]
}

/market/depth ( Get Market Depth)
Request type: GET

Signature verification: No

Rate Limit: 4,000 5 minutes

Interface description:  This endpoint retrieves the current order book of a specific pair.

Request Address
Environment	Address
Online	https://api.huobi.pro
Online  (preferred by aws customers)	https://api-aws.huobi.pro
Request Parameter
Parameter	Data Type	Required	Description	Value Range	Default Value
symbol	string	 false	The trading symbol to query	Refer to GET /v1/common/symbols	
depth	integer	 false	The number of market depth to return on each side	5, 10, 20，30	20
type	string	 false	Market depth aggregation level, details below	step0: no aggregation; returns 150 levels of data by default.
step1: aggregation = quote precision × 10; returns 20 levels of data by default.
step2: aggregation = quote precision × 100; returns 20 levels of data by default.
step3: aggregation = quote precision × 1,000; returns 20 levels of data by default.
step4: aggregation = quote precision × 5,000; returns 20 levels of data by default.
step5: aggregation = quote precision × 100,000; returns 20 levels of data by default.	step0
Notes: 
When the type value is 'step0', if 'depth' is not entered, the default value is 150。

Response Parameter
Parameter	Data Type	Required	Description
status	string	 false	Request Processing Result "ok","error"
ch	string	 false	Data belonged channel，Format： market.$symbol.depth.$type
ts	long	 false	Time of Respond Generation, Unit: Millisecond
<tick>	object	 false	
ts	integer	 false	The UNIX timestamp in milliseconds is adjusted to Singapore time
version	integer	 false	Internal data
bids	object	 false	The current all bids in format [price, size]
asks	object	 false	The current all asks in format [price, size]
</tick>		 false	
Request example
curl"https://api.huobi.pro/market/depth?symbol=btcusdt&depth=5&type=step0"
Response Example
Success Example
{
"ch":"market.btcusdt.depth.step0"
"status":"ok"
"ts":1629790438801
"tick":{
"ts":1629790438215
"version":136107114472
"bids":[
0:[
0:49790.87
1:0.779876
]
1:[
0:49785.9
1:0.000182
]
2:[
0:49784.48
1:0.002758
]
3:[
0:49784.29
1:0.05
]
4:[
0:49783.06
1:0.005038
]
]
"asks":[
0:[
0:49790.88
1:2.980472
]
1:[
0:49790.89
1:0.006613
]
2:[
0:49792.16
1:0.080302
]
3:[
0:49792.67
1:0.030112
]
4:[
0:49793.23
1:0.043103
]
]
}
}

market.$symbol.depth.$type ( Market Depth)
Signature verification: No

Interface description:  This topic sends the latest market by price order book in snapshot mode at 1-second interval.

Subscription Address
Environment	Address
Online	wss://api.huobi.pro/ws
Online  (preferred by aws customers)	wss://api-aws.huobi.pro/ws
Request Parameter
Field Name	Type	Description
ch	string	Required； Operator Name， sub、unsub;
params	string	parameters
cid	string	parameters
Rule description
Subscribe(sub)	Unsubscribe( unsub )	Rule
"market.btcusdt.depth.step0",	"market.btcusdt.depth.step0",	Allowed
"market.btcusdt.depth.step0","market.ethusdt.depth.step0","market.trxusdt.depth.step0"	"market.btcusdt.depth.step0","market.ethusdt.depth.step0","market.trxusdt.depth.step0"	Allowed
"market.btcusdt.depth.step0","market.ethusdt.depth.step0","market.trxusdt.depth.step0"	"market.bnbusdt.depth.step0",	Not Allowed
Subscription Parameter
Parameter	Data Type	Required	Description	Value Range	Default Value
symbol	Array	 false	Trading symbol	Refer to GET /v1/common/symbols	
type	String	 false	Market depth aggregation level, details below	step0: no aggregation; returns 150 levels of data.
step1: aggregation = quote precision × 10.
step2: aggregation = quote precision × 100.
step3: aggregation = quote precision × 1,000.
step4: aggregation = quote precision × 5,000.
step5: aggregation = quote precision × 100,000.	step0
cid	string	 false	Current request's ID		
Data Update
Parameter	Data Type	Required	Description
ch	string	 false	Data belonged channel，Format：market.$symbol.depth.$type
ts	long	 false	Time of Respond Generation, Unit: Millisecond
<tick>	object	 false	
bids	object	 false	The current all bids in format [price, size]
asks	object	 false	The current all asks in format [price, size]
version	integer	 false	Internal data
ts	integer	 false	The UNIX timestamp in milliseconds adjusted to Singapore time
</tick>		 false	
Subscription Example
{
"sub":[
0:"market.btcusdt.depth.step0"
1:"market.ethusdt.depth.step0"
2:"market.trxusdt.depth.step0"
]
"id":"id1"
}
Example of a Successful Subscription
{
"id":"id1"
"status":"ok"
"subbed":"market.btcusdt.depth.step0"
"ts":1489474081631
}
Example of a Data Update
{
"ch":"market.btcusdt.depth.step0"
"ts":1630983549503
"tick":{
"bids":[
0:[
0:52690.69
1:0.36281
]
1:[
0:52690.68
1:0.2
]
]
"asks":[
0:[
0:52690.7
1:0.372591
]
1:[
0:52691.26
1:0.13
]
]
"version":136998124622
"ts":1630983549500
}
}
Example of a Subscription Cancellation
{
"unsub":"market.btcusdt.mbp.refresh.20"
"id":"id1"
}

market.$symbol.ticker ( Market Ticker)
Signature verification: No

Interface description:  Retrieve the market ticker,data is pushed every 100ms.

Subscription Address
Environment	Address
Online	wss://api.huobi.pro/ws
Online  (preferred by aws customers)	wss://api-aws.huobi.pro/ws
Request Parameter
Field Name	Type	Description
ch	string	Required； Operator Name， sub、unsub;
params	string	parameters
cid	string	request id
Rule description
Subscribe(sub)	Unsubscribe( unsub )	Rule
"market.btcusdt.mbp.refresh.20"	"market.btcusdt.mbp.refresh.20"	Allowed
"market.btcusdt.mbp.refresh.20","market.ethusdt.mbp.refresh.20","market.htxusdt.mbp.refresh.20"	"market.btcusdt.mbp.refresh.20","market.ethusdt.mbp.refresh.20","market.htxusdt.mbp.refresh.20"	Allowed
"market.btcusdt.mbp.refresh.20","market.ethusdt.mbp.refresh.20","market.htxusdt.mbp.refresh.20"	"market.bnbusdt.mbp.5"	Not Allowed
Subscription Parameter
Parameter	Data Type	Required	Description	Value Range
symbol	Array	 false	The trading symbol to query	All supported trading symbol, e.g. btcusdt, bccbtc.Refer to /v1/common/symbols
cid	string	 false	Current request's ID	
Data Update
Parameter	Data Type	Required	Description
ch	string	 false	Data belonged channel，Format：market.$symbol.ticker
ts	long	 false	Time of Respond Generation, Unit: Millisecond
<tick>	object	 false	
amount	float	 false	Accumulated trading volume of last 24 hours (rotating 24h), in base currency
count	integer	 false	The number of completed trades (rotating 24h)
open	float	 false	The opening price of last 24 hours (rotating 24h)
close	float	 false	The last price of last 24 hours (rotating 24h)
low	float	 false	The lowest price of last 24 hours (rotating 24h)
high	float	 false	The highest price of last 24 hours (rotating 24h)
vol	float	 false	Accumulated trading value of last 24 hours (rotating 24h), in quote currency
bid	float	 false	Best bid price
bidSize	float	 false	Best bid size
ask	float	 false	Best ask price
askSize	float	 false	Best ask size
lastPrice	float	 false	Last traded price
lastSize	float	 false	Last traded size
</tick>		 false	
Subscription Example
{
"sub":[
0:"market.btcusdt.mbp.refresh.20"
1:"market.ethusdt.mbp.refresh.20"
2:"market.htxusdt.mbp.refresh.20"
]
}
Example of a Successful Subscription
{
"id":"id1"
"status":"ok"
"subbed":"market.btcusdt.ticker"
"ts":1489474081631
}
Example of a Data Update
{
"ch":"market.btcusdt.ticker"
"ts":1630982370526
"tick":{
"open":51732
"high":52785.64
"low":51000
"close":52735.63
"amount":13259.24137056181
"vol":687640987.4125315
"count":448737
"bid":52732.88
"bidSize":0.036
"ask":52732.89
"askSize":0.583653
"lastPrice":52735.63
"lastSize":0.03
}
}
Example of a Subscription Cancellation
{
"unsub":"market.btcusdt.ticker"
}

market.$symbol.mbp.refresh.$levels ( Market By Price (refresh update))
Signature verification: No

Interface description:  User could subscribe to this channel to receive refresh update of Market By Price order book. The update interval is around 100ms.

Subscription Address
Environment	Address
Online	wss://api.huobi.pro/feed
Online  (preferred by aws customers)	wss://api-aws.huobi.pro/feed
Notes: Originally, the wss://api.huobi.pro/ws and wss://api-aws.huobi.pro/ws addresses will still provide services, but may be offline in the future.

Request Parameter
Field Name	Type	Description
ch	string	Required； Operator Name， sub、unsub;
params	string	parameters
cid	string	request id
Rule description
Subscribe(sub)	Unsubscribe( unsub )	Rule
"market.btcusdt.mbp.refresh.20"	"market.btcusdt.mbp.refresh.20"	Allowed
"market.btcusdt.mbp.refresh.20","market.ethusdt.mbp.refresh.20","market.htxusdt.mbp.refresh.20"	"market.btcusdt.mbp.refresh.20","market.ethusdt.mbp.refresh.20","market.htxusdt.mbp.refresh.20"	Allowed
"market.btcusdt.mbp.refresh.20","market.ethusdt.mbp.refresh.20","market.htxusdt.mbp.refresh.20"	"market.bnbusdt.mbp.5"	Not Allowed
Subscription Parameter
Parameter	Data Type	Required	Description	Value Range
symbol	Array	 false	Trading symbol (wildcard inacceptable)	
levels	Array	 false	Number of price levels	5,10,20
cid	string	 false	Current request's ID	
Data Update
Parameter	Data Type	Required	Description
seqNum	integer	 false	Sequence number of the message
bids	object	 false	Bid side, (in descending order of "price"), ["price","size"]
asks	object	 false	Ask side, (in ascending order of "price"), ["price","size"]
Subscription Example
{
"sub":[
0:"market.btcusdt.mbp.refresh.20"
1:"market.ethusdt.mbp.refresh.20"
2:"market.htxusdt.mbp.refresh.20"
]
"id":"id1"
}
Example of a Successful Subscription
{
"id":"id1"
"status":"ok"
"subbed":"market.btcusdt.mbp.refresh.20"
"ts":1489474081631
}
Example of a Data Update
{
"ch":"market.btcusdt.mbp.refresh.20"
"ts":1573199608679
"tick":{
"seqNum":100020142010
"bids":[
0:[
0:618.37
1:71.594
]
1:[
0:423.33
1:77.726
]
2:[
0:223.18
1:47.997
]
3:[
0:219.34
1:24.82
]
4:[
0:210.34
1:94.463
]
]
"asks":[
0:[
0:650.59
1:14.909733438479636
]
1:[
0:650.63
1:97.996
]
2:[
0:650.77
1:97.465
]
3:[
0:651.23
1:83.973
]
4:[
0:651.42
1:34.465
]
]
}
}
Example of a Subscription Cancellation
{
"unsub":"market.btcusdt.mbp.refresh.20"
"id":"id1"
}