# Temperature and humidity sensor tracker

Read periodically values from [DHT-22](https://www.adafruit.com/product/385)
sensor and saves them to local filesystem as CSV and/or send them to [Datadog](https://www.datadoghq.com/)
for data visualization and aggregation.

Dependencies
```bash
pip install datadog
```

Clone, build and install library from Adafruit
https://github.com/adafruit/Adafruit_Python_DHT

Can probably also use any other sensor from Adafruit, but code has to be edited.

## Usage

If you want to use Datadog, you need an account. Get your API key and create a new or existing APP key.
Save those into _credentials.json_ as {"app":"APPKEY", "api": "APIKEY""}.

Connect the sensor and get GPIO __BCM__ pin number.

Start script with
```bash
python3 temperature_dd.py --pin PIN
```

By default the values are sent to cloud and not saved to file system.

Arguments:
```bash
--nocloud       Do not send to cloud (no creds required)
--storefile     Store values to file system as CSVs
--path          Path to directory into which the CSVs are saved
--credentials   Credentials file, default credentials.json
--interval      Interval as seconds at which values are persisted
--pin           Data pin number in BCM numbering scheme
```