#!/data/data/com.termux/files/home/.local/bin/python
import pycurl
import json
import io
from datetime import datetime


def get_ip_and_location():
    print("=" * 40)
    print("IP & Location Checker (via VPN) - pycurl")
    print("=" * 40)
    print(f"Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    try:
        buffer = io.BytesIO()
        curl = pycurl.Curl()

        curl.setopt(pycurl.URL, "https://ipnumberia.com/")
        curl.setopt(pycurl.WRITEDATA, buffer)
        curl.setopt(pycurl.FOLLOWLOCATION, True)
        curl.setopt(pycurl.TIMEOUT, 30)
        curl.setopt(pycurl.SSL_VERIFYPEER, False)
        curl.setopt(pycurl.SSL_VERIFYHOST, False)

        curl.setopt(pycurl.USERAGENT, "Mozilla/5.0")

        print("⏳ Fetching data...\n")

        curl.perform()

        http_code = curl.getinfo(pycurl.HTTP_CODE)
        curl.close()

        if http_code != 200:
            print(f"❌ HTTP Error: {http_code}")
            return

        response_data = buffer.getvalue().decode("utf-8")
        data = json.loads(response_data)

        print(f"🌐 IP Address:      {data.get('ip', 'N/A')}")
        print(f"🏙️  City:            {data.get('city', 'N/A')}")
        print(f"🗺️  Region:          {data.get('region', 'N/A')}")
        print(
            f"🌍 Country:         {data.get('country_name', 'N/A')} ({data.get('country_code', 'N/A')})"
        )
        print(
            f"📍 Coordinates:     {data.get('latitude', 'N/A')}, {data.get('longitude', 'N/A')}"
        )
        print(f"🔌 ISP:             {data.get('org', 'N/A')}")
        print(f"🌐 ASN:             {data.get('asn', 'N/A')}")
        print(f"⏰ Timezone:        {data.get('timezone', 'N/A')}")
        print(f"📮 Postal Code:     {data.get('postal', 'N/A')}")

        print("\n" + "=" * 40)

    except pycurl.error as e:
        print(f"❌ pycurl error: {e}")
    except json.JSONDecodeError:
        print("❌ Error parsing JSON response.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    get_ip_and_location()
