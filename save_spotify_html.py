import urllib.request
import urllib.parse
import ssl

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}
context = ssl._create_unverified_context()
req = urllib.request.Request("https://open.spotify.com/track/4PTG3Z6ehGkBF3zI7Ywt1D", headers=headers)
with urllib.request.urlopen(req, context=context) as response:
    html = response.read().decode('utf-8')

with open("spotify_track_page.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Saved HTML of length:", len(html))
