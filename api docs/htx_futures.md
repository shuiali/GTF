/linear-swap-ex/market/depth ([General] Get Market Depth)
Request type: GET

Signature verification: No

Interface permission: Read

Rate Limit: For public interface to get market data such as Get Kline data, Get Market Data Overview, Get Contract Information,Get market in-depth data, Get premium index Kline, Get real-time forecast capital rate kline, Get basis data, Get the last Trade of a Contract and so on：

（1）For restful interfaces, products, (future, coin margined swap, usdt margined Contracts)800 times/second for one IP at most

Interface description: The interface supports cross margin mode and isolated margin mode.

The request parameter "contract_code" supports the contract code of futures, in that the format is BTC-USDT-210625; and supports contract type: BTC-USDT, BTC-USDT-CW, BTC-USDT-NW, BTC-USDT-CQ, BTC-USDT-NQ.

Request Address
Environment	Address
Online	https://api.hbdm.com
Online  (preferred by aws customers)	https://api.hbdm.vn
Request Parameter
Parameter	Data Type	Required	Description
contract_code	string	 true	swap: "BTC-USDT"... , future: "BTC-USDT-220325" ... or BTC-USDT-CW, BTC-USDT-NW, BTC-USDT-CQ, BTC-USDT-NQ
type	string	 true	Get depth data within step 150, use step0, step1, step2, step3, step4, step5, step14, step15, step16, step17（merged depth data 0-5,14-17）；when step is 0，depth data will not be merged; Get depth data within step 20, use step6, step7, step8, step9, step10, step11, step12, step13, step18, step19(merged depth data 7-13,18-19); when step is 6, depth data will not be merged.
Notes: 
step16, step17, step18, and step19 are only for SHIB-USDT contract, and the other contracts is not supported now.

Response Parameter
Parameter	Data Type	Required	Description	Value Range
ch	string	 true	Data belonged channel，Format： market.period		
status	string	 true	Request Processing Result		
ts	long	 true	Time of Respond Generation，Unit：Millisecond		"ok" , "error"
<tick>		object array	 false		
mrid		long	 true	Order ID		
id	long	 true	tick ID		
asks	object	 false	Sell,[price(Ask price), vol(Ask orders (cont.) )], price in ascending sequence		
bids	object	 false	Buy,[price(Bid price), vol(Bid orders(Cont.))], Price in descending sequence		
ts	long	 true	Time of Respond Generation, Unit: Millisecond		
version	long	 true	version ID		
ch	string	 true	Data channel, Format： market.period		
</tick>			 false		
Request example
curl "https://api.hbdm.com/linear-swap-ex/market/depth?contract_code=BTC-USDT&type=step0"
Response Example
Success Example
{
"ch":"market.BTC-USDT-CQ.depth.step6"
"status":"ok"
"tick":{
"asks":[
0:[
0:48611.5
1:741
]
1:[
0:48635.2
1:792
]
]
"bids":[
0:[
0:48596.4
1:90
]
1:[
0:48585.7
1:180
]
]
"ch":"market.BTC-USDT-CQ.depth.step6"
"id":1638754215
"mrid":1250406
"ts":1638754215640
"version":1638754215
}
"ts":1638754216092
}

/linear-swap-ex/market/bbo ([General]Get Market BBO Data)
Request type: GET

Signature verification: No

Interface permission: Read

Rate Limit: For public interface to get market data such as Get Kline data, Get Market Data Overview, Get Contract Information,Get market in-depth data, Get premium index Kline, Get real-time forecast capital rate kline, Get basis data, Get the last Trade of a Contract and so on：

（1）For restful interfaces, products, (future, coin margined swap, usdt margined Contracts)800 times/second for one IP at most

Interface description: he interface supports cross margin mode and isolated margin mode.

The request parameter "contract_code" supports the contract code of futures, in that the format is BTC-USDT-210625; and supports contract type: BTC-USDT, BTC-USDT-CW, BTC-USDT-NW, BTC-USDT-CQ, BTC-USDT-NQ.

business_type is a required parameter when query info of futures contract, and its value must be futures or all.

Request Address
Environment	Address
Online	https://api.hbdm.com
Online  (preferred by aws customers)	https://api.hbdm.vn
Request Parameter
Parameter	Data Type	Required	Description	Value Range
contract_code	string	 false	contract code or contract type	swap: "BTC-USDT"... , future: "BTC-USDT-220325" ... or BTC-USDT-CW, BTC-USDT-NW, BTC-USDT-CQ, BTC-USDT-NQ
business_type	string	 false	business type, default is swap	futures, swap, all
Response Parameter
Parameter	Data Type	Required	Description	Value Range
status	string	 true	the result of server handling to request	"ok" , "error"
<ticks>	object array	 true		
contract_code	string	 true	contract code or contract type	swap: "BTC-USDT"... , future: "BTC-USDT-220325" ... or BTC-USDT-CW, BTC-USDT-NW, BTC-USDT-CQ, BTC-USDT-NQ
business_type	string	 true	business type	futures, swap
mrid	long	 true	Match ID, unique identification	
ask	array	 false	[Ask 1 price, Ask 1 qty (cont)]	
bid	array	 false	[Bid 1 price, Bid 1 qty (cont)]	
ts	long	 true	The system detects the orderbook time point, unit: milliseconds	
</ticks>		 false		
ts	long	 true	Time of Respond Generation, Unit: Millisecond	
Request example
curl"https://api.hbdm.com/linear-swap-ex/market/bbo?contract_code=BTC-USDT&pair=BTC-USDT&contract_type=swap&business_type=swap"
Response Example
Success Example
{
"status":"ok"
"ticks":[
0:{
"business_type":"futures"
"contract_code":"BTC-USDT-CW"
"ask":[
0:48637.3
1:746
]
"bid":[
0:48482.5
1:385
]
"mrid":1251224
"ts":1638754357868
}
1:{
"business_type":"futures"
"contract_code":"BTC-USDT-NW"
"ask":[
0:48620.1
1:1000
]
"bid":[
0:48461
1:524
]
"mrid":1251162
"ts":1638754344746
}
2:{
"business_type":"futures"
"contract_code":"BTC-USDT-CQ"
"ask":[
0:48630.9
1:868
]
"bid":[
0:48577.1
1:63
]
"mrid":1251236
"ts":1638754359301
}
3:{
"business_type":"swap"
"contract_code":"BTC-USDT"
"ask":[
0:48511.6
1:91
]
"bid":[
0:48508.9
1:95
]
"mrid":334931
"ts":1638754361719
}
]
"ts":1638754363648
}

/linear-swap-ex/market/history/kline ([General] Get KLine Data)
Request type: GET

Signature verification: No

Interface permission: Read

Rate Limit: For public interface to get market data such as Get Kline data, Get Market Data Overview, Get Contract Information,Get market in-depth data, Get premium index Kline, Get real-time forecast capital rate kline, Get basis data, Get the last Trade of a Contract and so on：

（1）For restful interfaces, products, (future, coin margined swap, usdt margined Contracts)800 times/second for one IP at most

Interface description: The interface supports cross margin mode and isolated margin mode.

The request parameter "contract_code" supports the contract code of futures, in that the format is BTC-USDT-210625; and supports contract type: BTC-USDT, BTC-USDT-CW, BTC-USDT-NW, BTC-USDT-CQ, BTC-USDT-NQ.

Request Address
Environment	Address
Online	https://api.hbdm.com
Online  (preferred by aws customers)	https://api.hbdm.vn
Request Parameter
Parameter	Data Type	Required	Description	Value Range	Default Value
contract_code	string	 true	contract code or contract type	swap: "BTC-USDT"... , future: "BTC-USDT-220325" ... or BTC-USDT-CW, BTC-USDT-NW, BTC-USDT-CQ, BTC-USDT-NQ	
period	string	 true	KLine Type	1min, 5min, 15min, 30min, 60min, 1hour,4hour,1day, 1mon	
size	int	 false	Acquisition Quantity	[1,2000]	150
from	long	 false	start timestamp seconds.		
to	long	 false	end timestamp seconds		
Notes: 
Either size field or from and to fields need to be filled.
If size field and from/to fields are not filled, It will return error messages.
If from field is filled, to field need to filled too.
The api can mostly return the klines of last two years.
If from to size are all filled,'from' and 'to' will be ignored.

Response Parameter
Parameter	Data Type	Required	Description
ch	string	 true	Data belonged channel，Format： market.period
status	string	 true	Request Processing Result
ts	long	 true	Time of Respond Generation, Unit: Millisecond
<data>	kline data	 false	
id	long	 true	kline id,the same as kline timestamp, kline start timestamp
vol	decimal	 true	Trade Volume(Cont.) . Sum of both buy and sell sides
count	decimal	 true	Order Quantity. Sum of both buy and sell sides
open	decimal	 true	Open Price
close	decimal	 true	Clos Price, the price in the last kline is the latest order price
low	decimal	 true	Low Price
high	decimal	 true	High Price
amount	decimal	 true	Trade Amount(Coin), trade amount(coin)=sum(order quantity of a single order * face value of the coin/order price). Sum of both buy and sell sides
trade_turnover	decimal	 true	Transaction amount, that is, sum (transaction quantity * contract face value * transaction price). Sum of both buy and sell sides
</data>		 false	
Request example
curl "https://api.hbdm.com/linear-swap-ex/market/history/kline?contract_code=BTC-USDT&period=1day&from=1587052800&to=1591286400"
Response Example
Success Example
{
"ch":"market.BTC-USDT.kline.1min"
"data":[
0:{
"amount":0.004
"close":13076.8
"count":1
"high":13076.8
"id":1603695060
"low":13076.8
"open":13076.8
"trade_turnover":52.3072
"vol":4
}
]
"status":"ok"
"ts":1603695099234
}

market.$contract_code.kline.$period ([General] Subscribe Kline data)
Signature verification: No

Interface permission: Read

Rate Limit: For public interface to get market data such as Get Kline data, Get Market Data Overview, Get Contract Information,Get market in-depth data, Get premium index Kline, Get real-time forecast capital rate kline, Get basis data, Get the last Trade of a Contract and so on：
For websocket: The rate limit for “req” request is 50 times at once. No limit for “sub” request as the data will be pushed by sever voluntarily.

Interface description: The interface supports cross margin mode and isolated margin mode.

The request parameter "contract_code" supports the contract code of futures, in that the format is BTC-USDT-210625; and supports contract type: BTC-USDT, BTC-USDT-CW, BTC-USDT-NW, BTC-USDT-CQ, BTC-USDT-NQ.

Subscription Address
Environment	Address
Online	wss://api.hbdm.com/linear-swap-ws
Online  (preferred by aws customers)	wss://api.hbdm.vn/linear-swap-ws
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
contract_code	string	 true	contract code or contract type	swap: "BTC-USDT"... , future: "BTC-USDT-210625" ... or BTC-USDT-CW, BTC-USDT-NW, BTC-USDT-CQ, BTC-USDT-NQ
period	string	 true	Kline Period	1min, 5min, 15min, 30min, 60min,4hour,1day,1week, 1mon
Data Update
Parameter	Data Type	Required	Description
ch	string	 true	Request Parameter
ts	long	 true	Time of Respond Generation，Unit：Millisecond
<tick>		 false	
id	long	 true	kline id,the same as kline timestamp, kline start timestamp
mrid	long	 true	ID Order ID
vol	decimal	 true	Trade Volume(Cont.). Sum of both buy and sell sides
count	decimal	 true	Order Quantity. Sum of both buy and sell sides
open	decimal	 true	Open Price
close	decimal	 true	Clos Price, the price in the last kline is the latest order price
low	decimal	 true	Low Price
high	decimal	 true	High Price
amount	decimal	 true	Trade Amount(Coin), trade amount(coin)=sum(order quantity of a single order * face value of the coin/order price). Sum of both buy and sell sides
trade_turnover	decimal	 true	Transaction amount, that is, sum (transaction quantity * contract face value * transaction price). Sum of both buy and sell sides
</tick>		 false	
Subscription Example
{
"sub":"market.BTC-USDT.kline.1min"
"id":"id1"
}
Example of a Successful Subscription
{
"id":"id1"
"status":"ok"
"subbed":"market.BTC-USDT.kline.1min"
"ts":1489474081631
}
Example of a Data Update
{
"ch":"market.BTC-USDT.kline.1min"
"ts":1603707124366
"tick":{
"id":1603707120
"mrid":131592424
"open":13067.7
"close":13067.7
"high":13067.7
"low":13067.7
"amount":0.004
"vol":4
"trade_turnover":52.2708
"count":1
}
}
Example of a Subscription Cancellation
{
"unsub":"market.BTC-USDT.kline.1min"
"id":"id1"
}

market.$contract_code.depth.$type ([General] Subscribe Market Depth Data)
Signature verification: No

Interface permission: Read

Rate Limit: For public interface to get market data such as Get Kline data, Get Market Data Overview, Get Contract Information,Get market in-depth data, Get premium index Kline, Get real-time forecast capital rate kline, Get basis data, Get the last Trade of a Contract and so on：
For websocket: The rate limit for “req” request is 50 times at once. No limit for “sub” request as the data will be pushed by sever voluntarily.

Interface description: The interface supports cross margin mode and isolated margin mode.

The request parameter "contract_code" supports the contract code of futures, in that the format is BTC-USDT-210625; and supports contract type: BTC-USDT, BTC-USDT-CW, BTC-USDT-NW, BTC-USDT-CQ, BTC-USDT-NQ.

Subscription Address
Environment	Address
Online	wss://api.hbdm.com/linear-swap-ws
Online  (preferred by aws customers)	wss://api.hbdm.vn/linear-swap-ws
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
contract_code	string	 true	contract code or contract type	swap: "BTC-USDT"... , future: "BTC-USDT-210625" ... or BTC-USDT-CW, BTC-USDT-NW, BTC-USDT-CQ, BTC-USDT-NQ
type	string	 true	Depth Type	(Non-Aggregated Depth)
step0: 150 levels
step6: 20 levels 30 levels→
(Aggregated Depth)
step1, step2, step3, step4, step5, step14, step15, step16, step17: 150 levels.
step6, step7, step8, step9, step10, step11, step12, step13, step18, step19: 20 levels 30→
levels.
Notes: 
When clients choose merged depth data, WebSocket server will only display the merged price within price steps in order book. Please note that the merged depth price will not make any change on the actual order price.
step16, step17, step18, and step19 are only for SHIB-USDT contract, and the other contracts is not supported now.
steps between step1 and step5, step14 and step17 are merged orderbook data of step 150. steps between step7 and step13, step18, step19 are merged orderbook data of step 20. Details are below:
Depth	precision
step16、step18	0.0000001
step17、step19	0.000001
step1、step7	0.00001
step2、step8	0.0001
step3、step9	0.001
step4、step10	0.01
step5、step11	0.1
step14、step12	1
step15、step13	10

Data Update
Parameter	Data Type	Required	Description
ts	string	 true	Time of Respond Generation, Unit: Millisecond
ch	long	 true	Data channel, Format： market.period
<tick>		 false	
mrid	long	 true	Order ID
id	long	 true	tick ID
asks	object	 false	Sell,[price(Ask price), vol(Ask orders (cont.) )], price in ascending sequence
bids	object	 false	Buy,[price(Bid price), vol(Bid orders(Cont.))], Price in descending sequence
ts	long	 true	Timestamp for depth generation; generated once every 100ms, unit: millisecond
version	long	 true	version ID
ch	string	 true	Data channel, Format： market.period
</tick>		 false	
Subscription Example
{
"sub":"market.BTC-USDT.depth.step0"
"id":"id5"
}
Example of a Successful Subscription
{
"id":"id1"
"status":"ok"
"subbed":"market.BTC-USDT.depth.step0"
"ts":1489474081631
}
Example of a Data Update
{
"ch":"market.BTC-USDT.depth.step6"
"ts":1603707576468
"tick":{
"mrid":131596447
"id":1603707576
"bids":[
0:[
0:13071.9
1:38
]
1:[
0:13068
1:5
]
]
"asks":[
0:[
0:13081.9
1:197
]
1:[
0:13099.7
1:371
]
]
"ts":1603707576467
"version":1603707576
"ch":"market.BTC-USDT.depth.step6"
}
}
Example of a Subscription Cancellation
{
"unsub":"market.BTC-USDT.depth.step0"
"id":"id5"
}

market.$contract_code.bbo ([General] Subscribe market BBO data push)
Signature verification: No

Interface permission: Read

Rate Limit: For public interface to get market data such as Get Kline data, Get Market Data Overview, Get Contract Information,Get market in-depth data, Get premium index Kline, Get real-time forecast capital rate kline, Get basis data, Get the last Trade of a Contract and so on：
For websocket: The rate limit for “req” request is 50 times at once. No limit for “sub” request as the data will be pushed by sever voluntarily.

Interface description: The interface supports cross margin mode and isolated margin mode.

Subscription Address
Environment	Address
Online	wss://api.hbdm.com/linear-swap-ws
Online  (preferred by aws customers)	wss://api.hbdm.vn/linear-swap-ws
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
contract_code	string	 true	contract code or contract type	swap: "BTC-USDT"... , future: "BTC-USDT-210625" ... or BTC-USDT-CW, BTC-USDT-NW, BTC-USDT-CQ, BTC-USDT-NQ
Data Update
Parameter	Data Type	Required	Description
ch	string	 true	Data channel, Format： market.$contract_code.bbo
ts	long	 true	Timestamp of Respond Generation, Unit: Millisecond
<tick>	object	 true	
ch	string	 true	Data channel, Format： market.$contract_code.bbo
mrid	string	 true	Order ID
id	long	 true	tick ID
ask	array	 false	Best Ask Quotation,[price(Ask price), vol(Ask order (cont.) )]
bid	array	 false	Best Bid Quotation,[price(Bid price), vol(Bid order(Cont.))]
version	long	 true	version ID.
ts	long	 true	Time of Respond Generation, Unit: Millisecond
<\tick>		 false	
Notes: 
When any one of the buy_one price, buy_one quantity, sell_one price and sell_one quantity changes, the system will push BBO price.
If there are multiple changes in the price or quantity of buy_one or sell_one at the same time, the system will push the latest price and quantity of buy_one and sell one with the intermediate data discarded.
When the data received by the client is failed or delayed, the old data buffer in the server will be discarded.The latest BBO will be pushed.
version（version number). Use match id directly to ensure it is globally unique and the value of version number pushed is the largest.

Subscription Example
{
"sub":"market.BTC-USDT.bbo"
"id":"id8"
}
Example of a Successful Subscription
{
"id":"id8"
"status":"ok"
"subbed":"market.BTC-USDT.bbo"
"ts":1489474081631
}
Example of a Data Update
{
"ch":"market.BTC-USDT.bbo"
"ts":1603707934525
"tick":{
"mrid":131599726
"id":1603707934
"bid":[
0:13064
1:38
]
"ask":[
0:13072.3
1:205
]
"ts":1603707934525
"version":131599726
"ch":"market.BTC-USDT.bbo"
}
}
Example of a Subscription Cancellation
{
"unsub":"market.BTC-USDT.bbo"
"id":"id8"
}