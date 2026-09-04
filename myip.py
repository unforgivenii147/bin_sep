#!/data/data/com.termux/files/home/.local/bin/python
import pycurl
import io
from bs4 import BeautifulSoup


def get_my_ip():
    buffer = io.BytesIO()

    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, "https://ipnumberia.com")

        curl.setopt(pycurl.TIMEOUT, 30)

        curl.setopt(
            pycurl.USERAGENT,
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )

        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.setopt(pycurl.FOLLOWLOCATION, True)

        curl.perform()

        response_code = curl.getinfo(pycurl.RESPONSE_CODE)

        if response_code == 200:
            response_content = buffer.getvalue().decode("utf-8")

            soup = BeautifulSoup(response_content, "html.parser")

            ip_div = soup.find("div", class_="ip")

            if ip_div:
                ip_address = ip_div.get_text(strip=True)
                print(f"✓ Your IP Address: {ip_address}")
                return ip_address
            else:
                print("✗ Could not find IP address in the response")
                return None
        else:
            print(f"✗ HTTP Error: {response_code}")
            return None

    except pycurl.error as e:
        error_code, error_msg = e.args
        print(f"✗ Curl Error ({error_code}): {error_msg}")
        return None
    finally:
        curl.close()


if __name__ == "__main__":
    get_my_ip()
