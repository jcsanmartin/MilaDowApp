import urllib.request
import urllib.parse
import json
import ssl

def fetch_oembed(url):
    context = ssl._create_unverified_context()
    encoded_url = urllib.parse.quote(url)
    oembed_url = f"https://open.spotify.com/oembed?url={encoded_url}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    try:
        req = urllib.request.Request(oembed_url, headers=headers)
        with urllib.request.urlopen(req, context=context) as response:
            data = json.loads(response.read().decode('utf-8'))
            print(f"\nURL: {url}")
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error for {url}: {e}")

if __name__ == '__main__':
    fetch_oembed("https://open.spotify.com/track/4PTG3Z6ehGkBF3zI7Ywt1D")
    fetch_oembed("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGsyNa7T")
