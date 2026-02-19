Integration Guide

The following is a brief introduction to quickly get started using the API services in this centralized cryptocurrency exchange:
Get API Key

Before applying for an API key, you need to apply for an account at CoinEx. For the specific application process, please refer to Help Center.

Once you have your account ready, you can generate the API key in the Developer Console to ensure that you have the necessary permissions.
Prepare for API Calls

Depending on your requirements, select the appropriate API endpoint and refer to the corresponding API documentation to understand the request methods, parameters, and response results.

For details, you can explore the Module Grouping, and find the corresponding module and its corresponding API endpoint, or use the search function to quickly find it.
Build Requests

Use the programming language of your choice to construct a request that meets the API requirements, including setting the request method, URL, request headers and parameters, etc.
Info

The base URL of HTTP is: https://api.coinex.com/v2

The base URL for spot and futures WS are different, as follows:

    Spot: wss://socket.coinex.com/v2/spot
    Futures: wss://socket.coinex.com/v2/futures

Public Parameter:
Info

HTTP endpoints marked with signature required needs to use the following two public HTTP HEADER parameters for request authentication. For specific usage methods, please refer to Authentication

    X-COINEX-KEY
    X-COINEX-SIGN

Info

If you need to limit the validity time of the request, you can restrict the validity period through the following public HTTP HEADER parameters in all HTTP endpoints.

When the server receives the request, it will check the timestamp provided in the X-COINEX-TIMESTAMP. If the request was sent more than 5000 milliseconds (default value) ago, it will be considered invalid.This time window value can be customized by sending the optional parameter X-COINEX-WINDOWTIME.

    X-COINEX-TIMESTAMP.Required parameter, used to indicate the time at which the request is being sent.
    X-COINEX-WINDOWTIME.Optional parameter, used to indicate a time window for which the request is valid. The default value is 5000 milliseconds.

Info

In all APIs, time request parameters and response fields are millisecond-level timestamps.
Response Processing

Parse the response data returned by the API and perform corresponding processing as needed, such as error handling, data extraction, etc.
HTTP Response Processing

    For HTTP responses, please determine at first whether the status_code is 200, and then proceed to the next step of processing.
    A normal HTTP response will have a unified response structure. You need to determine whether the response is normal by judging the code field in the structure. code should be 0 under normal circumstances.

The unified structure of HTTP normal response is as follows:

{
    "code": 0,
    "data": ...
    "message": "OK"
}

WS Response Processing

    In the WS protocol, it is recommended to handle the response to subscription requests before proceeding further. Upon sending a subscription request, the server will respond with a subscription result. The response from the WS server is compressed using zip and must be decompressed first.
    It's necessary to determine if the 'code' field in the response result is 0.

The unified structure of WS normal response is as follows:

{
  "id": 4,
  "message": "OK",
  "code": 0
}

    After a successful subscription, the server will push the data when it is updated, and the pushed data can be processed according to your needs.

For specific error explanations, please refer to Error Handling

Authentication
User Guide: HTTP and WebSocket Endpoint Authentication Process

The following is a user guide for the authentication process of the HTTP and WebSocket endpoints on CoinEx exchange.
Step 1: Obtain API key
Warning

Please do not directly transmit the secret_key obtained from Step 1 in any network request, as this may result in potential asset loss.

    Log in to CoinEx.Navigate to the API management page.Create a new API or use an existing API.
    Get access_id and secret_key from the created API record.

Step 2: Generate authentication parameters
Generation method for HTTP endpoints

    Splice the data into a string according to the format of method + request_path + body(optional) + timestamp. The example is as follows:

prepared_str = "GET"+"/v2/spot/pending-order?market=BTCUSDT&market_type=SPOT&side=buy&page=1&limit=10"+"1700490703564"

As shown in the above example:

    method represents the HTTP request method in uppercase letters, such as: GET/POST
    request_path represents the path of the requested endpoint, including request parameters(query_string) if applicable, for example: /v2/spot/pending-order?market=BTCUSDT&market_type=SPOT&side=buy&page=1&limit=10.If there is no request parameter (query_string), only the request path needs to be included, for example: /v2/spot/pending-order
    body represents the HTTP request body. As in the above example, if there is no request body in some methods (GET/DELETE), it can be omitted.An example of the request body is as follows: '{"market": "BTCUSDT", "type": "buy", "amount": "0.001", "price": "10000"}'
    timestamp represents the time when the request was sent, and its value is taken from X-COINEX-TIMESTAMP

    Using 'secret_key' as the key. Create your HMAC-SHA256 signature using the above string and convert it to lowercase hexadecimal format with a length of 64 characters. The pseudocode is as follows:

signed_str = hmac.new(bytes(secret_key, 'latin-1'), msg=bytes(prepared_str, 'latin-1'), digestmod=hashlib.sha256).hexdigest().lower()

Generation method for WebSocket endpoints

    Splice the data into a string according to the format of timestamp. The example is as follows:

prepared_str = "1700490703564"

    Using 'secret_key' as the key. Create your HMAC-SHA256 signature using the above string and convert it to lowercase hexadecimal format with a length of 64 characters. The pseudocode is as follows:

signed_str = hmac.new(bytes(secret_key, 'latin-1'), msg=bytes(prepared_str, 'latin-1'), digestmod=hashlib.sha256).hexdigest().lower()

Step 3: Build authentication request
HTTP Authentication Request

When constructing an HTTP authentication request, the following public parameters are required:

    X-COINEX-KEY.The access_id obtained from Step 1
    X-COINEX-SIGN.The signed_str generated in Step 2
    X-COINEX-TIMESTAMP. The parameter mentioned in the Integration Guide that indicates the time when the request is sent.

An example is as follows:

GET /assets/spot/balance HTTP/1.1
Host: api.coinex.com
-H 'X-COINEX-KEY: XXXXXXXXXX' \
-H 'X-COINEX-SIGN: XXXXXXXXXX' \
-H 'X-COINEX-TIMESTAMP: 1700490703564

WebSocket Authentication Request

Before accessing the WebSocket endpoint that requires authentication, you need to call the authentication method named server.sign. You can view the endpoint details through this link.

The corresponding request fields are as follows:

    access_id.The access_id obtained from Step 1
    signed_str.The signed_str generated in Step 2
    timestamp.The current timestamp in milliseconds.

An example is as follows:

{
    "id": 15,
    "method": "server.sign",
    "params": {
        "access_id": "XXXXXXXXXX",
        "signed_str": "XXXXXXXXXX",
        "timestamp": 1234567890123
    }
}

Get Market Information
HTTP request

GET /futures/ticker
Request parameters
Parameter Name	Required	Type	Notes
market	false	string	List of market names. Use "," to separate multiple market names, a maximum of 10 markets are allowed. An empty string or pass to query all markets.
Return parameters
Parameter Name	Type	Notes
market	string	Market name
last	string	Latest price
open	string	Opening price
close	string	Closing price
high	string	Highest price
low	string	Lowest price
volume	string	Filled volume
value	string	Filled value
volume_sell	string	Taker sell volume
volume_buy	string	Taker buy volume
index_price	string	Index price
mark_price	string	Mark price
open_interest_volume	string	Futures position size
period	int	Period, fixed at 86400, indicates that the data is a one-day value
Response example

GET /futures/ticker?market=LATUSDT,ELONUSDT
Response example

{
    "code": 0,
    "data": [
        {
            "market": "LATUSDT",
            "last": "0.008157",
            "open": "0.008286",
            "close": "0.008157",
            "high": "0.008390",
            "low": "0.008106",
            "volume": "807714.49139758",
            "volume_sell": "286170.69645599",
            "volume_buy": "266161.23236408",
            "value": "6689.21644207",
            "index_price": "0.008158",
            "mark_price": "0.008158",
            "open_interest_volume": "2423143.47419274",
            "period": 86400
        },
        {
            "market": "ELONUSDT",
            "last": "0.000000152823",
            "open": "0.000000158650",
            "close": "0.000000152823",
            "high": "0.000000159474",
            "low": "0.000000147026",
            "volume": "88014042237.15",
            "volume_sell": "11455578769.13",
            "volume_buy": "17047669612.10",
            "value": "13345.65122447",
            "index_price": "0.000000152821",
            "mark_price": "0.000000152821",
            "open_interest_volume": "264042126711.45",
            "period": 86400,
        }
    ],
    "message": "OK"
}
