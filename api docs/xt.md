Basic Information of the Interface
Base URLs

    USDT-M: https://fapi.xt.com (for USDT-margined futures)
    Coin-M: https://dapi.xt.com (for Coin-margined futures)

Network Recommendation

It is not recommended to access XT APIs via proxy due to high latency and poor stability.
Request Methods

    GET requests: Parameters should be passed in the QueryString.
    POST requests: Parameters can be passed in the RequestBody or QueryString.

When parameters are in the QueryString

Include the following header:

Content-Type: application/x-www-form-urlencoded

When parameters are in the RequestBody

Include the following header:

Content-Type: application/json

API Categories

XT API endpoints are divided into Public Interfaces and User Interfaces.
🟢 Public Interfaces

    No authentication required.
    Parameters are placed in the QueryString.
    Usually use the GET method.

Example:

curl -G "https://fapi.xt.com/future/market/v1/public/symbol/detail?symbol=btc_usdt"

or:

curl -G "https://fapi.xt.com/future/market/v1/public/symbol/detail" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "symbol=btc_usdt"

🔒 User Interfaces

    Require authentication via HTTP headers.
    Along with QueryString or RequestBody parameters, the following four headers are required:

Header	Description
validate-appkey	User API key
validate-timestamp	Current timestamp (in milliseconds)
validate-signature	Request signature
Content-Type	Request content type (application/json or application/x-www-form-urlencoded)

GET Example:

curl -G "https://fapi.xt.com/future/user/v1/compat/balance/list" \
  -H "validate-appkey: $APPKEY" \
  -H "validate-timestamp: $TIMESTAMP" \
  -H "validate-signature: $SIGNATURE" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "queryAccountId=1234567890"

POST Example:

curl -X POST "https://fapi.xt.com/future/user/v1/user/collection/add" \
  -H "validate-appkey: $APPKEY" \
  -H "validate-timestamp: $TIMESTAMP" \
  -H "validate-signature: $SIGNATURE" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"btc_usdt"}'

    Endpoints that do not require signature authentication will be explicitly indicated.

Authentication References

    How to obtain an APPKEY: Access Guide → Apply for API Key
    How to generate a signature: Access Guide → Generate Signature

Rate Limits

    Asset-related endpoints: Up to 3 requests per second.
    Other endpoints: Up to 10 requests per second per user, and 1000 requests per minute per IP.

    If the frequency limit is exceeded, the account will be locked for 10 minutes.

Signature Statement
Signature Parameters Description

Since XT provides open APIs to third-party platforms, data security must be ensured — for example, preventing data tampering, avoiding outdated data, blocking duplicate submissions, and controlling request frequency. Among these, data integrity verification is the most crucial aspect.
Signature Parameters

    validate-appkey — Public key obtained after applying for the API Key
    validate-timestamp — Request timestamp in milliseconds (Unix time). Request validity is determined based on this value and validate-recvwindow
    validate-signature — Some API requests require a signature. See details in ([Access Description -> Signature](../Access Description/Signature))
    validate-recvwindow — Defines the validity period of a request. Default is 5 seconds; maximum is 60 seconds
        If the timestamp is more than 5000ms earlier than server time, the request is invalid
        If the client timestamp is more than 1 second ahead of server time, the request will also be rejected
        It is not recommended to exceed 5 seconds, as this helps handle network jitter and ensures timeliness in high-frequency trading
    validate-algorithms — Signature is generated using an HSC-based algorithm
        Default: HmacSHA256
        Supported: HmacMD5, HmacSHA1, HmacSHA224, HmacSHA256, HmacSHA384, HmacSHA512

Request Header Signature Parameters
Name	Required	Example	Description
validate-appkey	TRUE	dbefbc809e3e83c283a984c3a1459732ea7db1360ca80c5c2c8867408d28cc83	Public key
validate-timestamp	TRUE	1641446237201	Unix timestamp (milliseconds)
validate-signature	TRUE	0a7d0b5e802eb5e52ac0cfcd6311b0faba6e2503a9a8d1e2364b38617877574d	Generated signature
validate-recvwindow	FALSE	5000 (ms)	Validity time window
validate-algorithms	FALSE	HmacSHA256	Default HmacSHA256
api-version	FALSE	1	Reserved field, API version number
validate-signversion	FALSE	1	Reserved field, signature version

Obtain Signature
Generate Signature

    Note: ${?} and $? refer to variable substitution.

To generate a signature (signature), use the SECRET KEY obtained with your API Key to encrypt the unencrypted_string.
Rules

    If HTTP request parameters are in QueryString: unencrypted_string = ${fixed_header}#${end_point}#${query_string} When multiple key-value pairs exist in query_string, sort the keys alphabetically and concatenate with &, for example: keya=value&keyb=value&keyc=value

    If HTTP request parameters are in RequestBody: unencrypted_string = ${fixed_header}#${end_point}#${request_body}

fixed_header Format

fixed_header = "validate-appkey=${your_appkey}&validate-timestamp=${current_timestamp}"

Each part of unencrypted_string is joined with #.
Example

curl -G "https://fapi.xt.com/future/user/v1/balance/detail" \
  -H "validate-appkey: $APPKEY" \
  -H "validate-timestamp: $TIMESTAMP" \
  -H "validate-singature: $SIGNATURE" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "coin=btc"

Example Breakdown:

# Suppose current timestamp = ***** and your APPKEY = ++++++
fixed_header="validate-appkey=++++++&validate-timestamp=*****"
end_point="/future/user/v1/balance/detail"
query_string="coin=btc"

# Then
unencrypted_string="validate-appkey=++++++&validate-timestamp=*****#/future/user/v1/balance/detail#coin=btc"

Generate the Signature

After obtaining the unencrypted_string, you can use the encryption algorithm along with the SECRETKEY to obtain the signature SIGNATURE for the unencrypted_string.

SIGNATURE=$(echo -n "$unencrypted_string" | openssl dgst -sha256 -hmac "$SECRETKEY" | awk '{print $2}')
echo $SIGNATURE

After generating the signature, include SIGNATURE in the HTTP request header as the value of validate-signature.


Get Aggregated Market Information for All Trading Pairs

Type: GET

Description: /future/market/v1/public/q/agg-tickers
Note：

This method does not require a signature.
Limit flow rules

None
Parameters

None
Request Example
Request

{
  curl -G "https://fapi.xt.com/future/market/v1/public/q/agg-tickers" \
}

Response Example
Java

public void getKLine() {
  String text = HttpUtil.get(URL + "/data/api/future/market/v1/getKLine?market=btc_usdt&type=1min&since=0");
  System.out.println(text);
}

Response

{
"error": {
  "code": "",
  "msg": ""
},
"msgInfo": "",
"result": [
  {
    "a": "",  // 24h volume
    "ap": "", // ask price
    "bp": "", // bid price
    "c": "",  // Latest price
    "h": "",  // Highest price in 24 hours
    "i": "",  // index price
    "l": "",  // Lowest price in 24 hours
    "m": "",  // mark price
    "o": "",  // The first transaction price 24 hours ago
    "r": "",  // 24h price fluctuation limit
    "s": "",  // Trading pair
    "t": 0,   // Time
    "v": ""   // 24h Turnover
  }
],
"returnCode": 0
}