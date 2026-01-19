Margin account list

GET /margin/accounts

Margin account list

Parameters
Name	In	Type	Required	Description
currency_pair	query	string	false	Currency pair
Responses
Status	Meaning	Description	Schema
200	OK(opens new window)	List retrieved successfully	[Inline]
Response Schema
Status Code 200

Name	Type	Description
None	array	[Margin account information for a trading pair. base corresponds to base currency account information, quote corresponds to quote currency account information]
» None	object	Margin account information for a trading pair. base corresponds to base currency account information, quote corresponds to quote currency account information
»» currency_pair	string	Currency pair
»» account_type	string	Account Type mmr: maintenance margin rate account;inactive: market not activated
»» leverage	string	User's current market leverage multiplier
»» locked	boolean	Whether the account is locked
»» risk	string	Deprecated
»» mmr	string	Current Maintenance Margin Rate of the account
»» base	object	Currency account information
»»» currency	string	Currency name
»»» available	string	Amount available for margin trading, available = margin + borrowed
»»» locked	string	Frozen funds, such as amounts already placed in margin market for order trading
»»» borrowed	string	Borrowed funds
»»» interest	string	Unpaid interest
»» quote	object	Currency account information
»»» currency	string	Currency name
»»» available	string	Amount available for margin trading, available = margin + borrowed
»»» locked	string	Frozen funds, such as amounts already placed in margin market for order trading
»»» borrowed	string	Borrowed funds
»»» interest	string	Unpaid interest
To perform this operation, you must be authenticated by API key and secret

Code samples

# coding: utf-8
import requests
import time
import hashlib
import hmac

host = "https://api.gateio.ws"
prefix = "/api/v4"
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

url = '/margin/accounts'
query_param = ''
# for `gen_sign` implementation, refer to section `Authentication` above
sign_headers = gen_sign('GET', prefix + url, query_param)
headers.update(sign_headers)
r = requests.request('GET', host + prefix + url, headers=headers)
print(r.json())

Example responses

200 Response

[
  {
    "currency_pair": "BTC_USDT",
    "account_type": "mmr",
    "leverage": "20",
    "locked": false,
    "risk": "1.3318",
    "mmr": "16.5949188975473644",
    "base": {
      "currency": "BTC",
      "available": "0.047060413211",
      "locked": "0",
      "borrowed": "0.047233",
      "interest": "0"
    },
    "quote": {
      "currency": "USDT",
      "available": "1234",
      "locked": "0",
      "borrowed": "0",
      "interest": "0"
    }
  }
]