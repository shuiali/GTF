also please integrate ourbit and blofin for futures-futures arbitrage spread finding by best bid/ask prices. 

https://futures.ourbit.com/api/v1/contract/ticker

response:
{
    "success": true,
    "code": 0,
    "data": [
        {
            "contractId": 10,
            "symbol": "BTC_USDT",
            "lastPrice": 69050.1,
            "bid1": 69058.6,
            "ask1": 69058.7,
            "volume24": 1827297950,
            "amount24": 12710494274.54601,
            "holdVol": 452291,
            "lower24Price": 67278.1,
            "high24Price": 71711.5,
            "riseFallRate": -0.001,
            "riseFallValue": -71.9,
            "indexPrice": 69092.3,
            "fairPrice": 69058.6,
            "fundingRate": -0.000015,
            "maxBidPrice": 76001.5,
            "minAskPrice": 62183,
            "timestamp": 1770485194315,
            "riseFallRates": {
                "zone": "UTC+8",
                "r": -0.001,
                "v": -71.9,
                "r7": -0.1503,
                "r30": -0.2389,
                "r90": -0.3342,
                "r180": -0.4258,
                "r365": -0.2972
            },
            "riseFallRatesOfTimezone": [
                -0.0121,
                -0.0211,
                -0.001
            ]
        },
        {
            "contractId": 11,
            "symbol": "ETH_USDT",
            "lastPrice": 2055.29,
            "bid1": 2055.49,
            "ask1": 2055.5,
            "volume24": 556961080,
            "amount24": 11430933890.1555,
            "holdVol": 74653,
            "lower24Price": 1993.92,
            "high24Price": 2123.98,
            "riseFallRate": 0.0018,
            "riseFallValue": 3.8,
            "indexPrice": 2056.4,
            "fairPrice": 2055.6,
            "fundingRate": -0.000009,
            "maxBidPrice": 2262.04,
            "minAskPrice": 1850.76,
            "timestamp": 1770485194314,
            "riseFallRates": {
                "zone": "UTC+8",
                "r": 0.0018,
                "v": 3.8,
                "r7": -0.1884,
                "r30": -0.3376,
                "r90": -0.415,
                "r180": -0.5252,
                "r365": -0.2444
            },
            "riseFallRatesOfTimezone": [
                0.0098,
                -0.0035,
                0.0018
            ]
        },



lbank:


curl.exe ^"https://uuapi.rerrkvifj.com/cfd/instrment/v1/ticker/24hr/intact^" ^
  --compressed ^
  -X POST ^
  -H ^"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0^" ^
  -H ^"Accept: application/json, text/plain, */*^" ^
  -H ^"Accept-Language: en-US^" ^
  -H ^"Accept-Encoding: gzip, deflate, br, zstd^" ^
  -H ^"Referer: https://www.lbank.com/^" ^
  -H ^"ex-browser-name: Firefox^" ^
  -H ^"ex-browser-version: 146.0^" ^
  -H ^"ex-os-name: Windows^" ^
  -H ^"ex-os-version: 10^" ^
  -H ^"ex-client-source: WEB^" ^
  -H ^"ex-client-type: WEB^" ^
  -H ^"ex-language: en-US^" ^
  -H ^"ex-device-id: 1BNZsZ56GMDDMYx96W0DB79akRlVh2EW^" ^
  -H ^"ex-timestamp: 1769186350270^" ^
  -H ^"ex-client-version-code: 20251120^" ^
  -H ^"ex-client-channel: WEB^" ^
  -H ^"source: 4^" ^
  -H ^"versionFlage: true^" ^
  -H ^"businessVersionCode: 202^" ^
  -H ^"ex-signature: ZWE1MWFjYmUzOWM4ZjBiN2RkZTg4YzczMjVlN2VkMTQzMTNjODE5ZGI1NTY5YTQ3NDZmMzU3N2IyNGI1MDI4NQ==^" ^
  -H ^"Content-Type: application/json^" ^
  -H ^"sw8-correlationvalue: traceId:05b6e6865125e6e882a222ffc65470e4.35.17691863502820059,spanId:59,osType:web^" ^
  -H ^"Origin: https://www.lbank.com^" ^
  -H ^"Sec-GPC: 1^" ^
  -H ^"Connection: keep-alive^" ^
  -H ^"Sec-Fetch-Dest: empty^" ^
  -H ^"Sec-Fetch-Mode: cors^" ^
  -H ^"Sec-Fetch-Site: cross-site^" ^
  --data-raw ^"^{^\^"product^\^":^[^\^"FUTURES^\^"^],^\^"area^\^":^\^"usdt^\^"^}^"