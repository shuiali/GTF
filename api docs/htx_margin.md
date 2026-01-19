/v1/margin/loan-info ( Get Loan Interest Rate and Quota（Isolated）)
Request type: GET

Signature verification: Yes

Interface permission: Read

Rate Limit:  20times/2sec

Interface description: The endpoint returns loan interest rates and quota applied on the user.

Request Address
Environment	Address
Online	https://api.huobi.pro
Online  (preferred by aws customers)	https://api-aws.huobi.pro
Request Parameter
Parameter	Data Type	Required	Description
symbols	string	 false	Trading symbol (multiple pairs available, separated by comma)
Response Parameter
Parameter	Data Type	Required	Description
status	string	 false	status
<data>	object	 false	
symbol	string	 false	Trading symbol
<currencies>	object	 false	
currency	string	 false	Currency
interest-rate	string	 false	Basic daily interest rate
min-loan-amt	string	 false	Minimal loanable amount
max-loan-amt	string	 false	Maximum loanable amount
loanable-amt	string	 false	Remaining loanable amount
actual-rate	string	 false	Actual interest rate (if deduction is inapplicable or disabled, return basic daily interest rate)
</currencies>		 false	
</data>		 false	
Request example
curl"https://api.huobi.pro/v1/margin/loan-info?symbol=all"
Response Example
Success Example
{
"status":"ok"
"data":[
0:{
"symbol":"btcusdt"
"currencies":[
0:{
"currency":"btc"
"interest-rate":"0.00098"
"min-loan-amt":"0.020000000000000000"
"max-loan-amt":"550.000000000000000000"
"loanable-amt":"0.045696000000000000"
"actual-rate":"0.00098"
}
1:{
"currency":"usdt"
"interest-rate":"0.00098"
"min-loan-amt":"100.000000000000000000"
"max-loan-amt":"4000000.000000000000000000"
"loanable-amt":"400.000000000000000000"
"actual-rate":"0.00098"
}
]
}
]
}

/v1/cross-margin/loan-info ( Get Loan Interest Rate and Quota（Cross）)
Request type: GET

Signature verification: Yes

Interface permission: Read

Rate Limit:   2times/2s

Interface description:  This endpoint returns loan interest rates and loan quota applied on the user.


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
status	string	 false	status
<data>	object	 false	
currency	string	 false	Currency
interest-rate	string	 false	Basic daily interest rate
min-loan-amt	string	 false	Minimal loanable amount
max-loan-amt	string	 false	Maximum loanable amount
loanable-amt	string	 false	Remaining loanable amount
actual-rate	string	 false	Actual interest rate post deduction (if deduction is inapplicable or disabled, return basic daily interest rate)
</data>		 false	
code	int	 false	status code
Request example
curl"https://api.huobi.pro/v1/cross-margin/loan-info"
Response Example
Success Example
{
"status":"ok"
"data":[
0:{
"currency":"bch"
"interest-rate":"0.00098"
"min-loan-amt":"0.35"
"max-loan-amt":"3500"
"loanable-amt":"0.70405181"
"actual-rate":"0.000343"
}
1:{
"currency":"btc"
"interest-rate":"0.00098"
"min-loan-amt":"0.01"
"max-loan-amt":"100"
"loanable-amt":"0.02281914"
"actual-rate":"0.000343"
}
2:{
"currency":"eos"
"interest-rate":"0.00098"
"min-loan-amt":"30"
"max-loan-amt":"300000"
"loanable-amt":"57.69175296"
"actual-rate":"0.000343"
}
3:{
"currency":"eth"
"interest-rate":"0.00098"
"min-loan-amt":"0.5"
"max-loan-amt":"6000"
"loanable-amt":"1.06712197"
"actual-rate":"0.000343"
}
4:{
"currency":"ltc"
"interest-rate":"0.00098"
"min-loan-amt":"1.5"
"max-loan-amt":"15000"
"loanable-amt":"3.28947368"
"actual-rate":"0.000343"
}
5:{
"currency":"usdt"
"interest-rate":"0.00098"
"min-loan-amt":"100"
"max-loan-amt":"1500000"
"loanable-amt":"200.00000000"
"actual-rate":"0.000343"
}
6:{
"currency":"xrp"
"interest-rate":"0.00098"
"min-loan-amt":"380"
"max-loan-amt":"4000000"
"loanable-amt":"734.21439060"
"actual-rate":"0.000343"
}
]
"code":200
}