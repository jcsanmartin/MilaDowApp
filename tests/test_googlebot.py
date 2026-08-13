import urllib.request
import re
import ssl

def fetch_with_googlebot(url):
    # Googlebot User-Agent to trigger SSR pre-rendering
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    }
    context = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=context) as response:
            html = response.read().decode('utf-8')
        
        print(f"URL: {url}")
        print(f"HTML Length: {len(html)}")
        
        # Check for title
        title_match = re.search(r'<title>(.*?)</title>', html)
        if title_match:
            print("Title:", title_match.group(1))
            
        # Check for og:title
        og_title = re.search(r'<meta\s+property="og:title"\s+content="(.*?)"', html)
        if og_title:
            print("og:title:", og_title.group(1))
            
        # Check for og:description
        og_desc = re.search(r'<meta\s+property="og:description"\s+content="(.*?)"', html)
        if og_desc:
            print("og:description:", og_desc.group(1))
            
        # Check for playlist track list. Spotify pre-renders track list inside table or list tags for SEO.
        # Let's save a snippet to analyze or find links containing /track/
        track_links = re.findall(r'href="https://open\.spotify\.com/track/([a-zA-Z0-9]+)"', html)
        print(f"Found {len(track_links)} track links in HTML")
        
        # Let's write the HTML to a debug file to inspect
        filename = "googlebot_track.html" if "track" in url else "googlebot_playlist.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved HTML to {filename}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    print("--- Track ---")
    fetch_with_googlebot("https://open.spotify.com/track/4PTG3Z6ehGkBF3zI7Ywt1D")
    print("\n--- Playlist ---")
    fetch_with_googlebot("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGsyNa7T")
