import urllib.request
import re
import json
import ssl

def fetch_embed_metadata(url):
    # Convert standard Spotify URL to embed URL if needed
    # https://open.spotify.com/track/4PTG3Z6ehGkBF3zI7Ywt1D -> https://open.spotify.com/embed/track/4PTG3Z6ehGkBF3zI7Ywt1D
    # https://open.spotify.com/playlist/37i9dQZF1DXcBWIGsyNa7T -> https://open.spotify.com/embed/playlist/37i9dQZF1DXcBWIGsyNa7T
    embed_url = url
    if "spotify.com" in url and "/embed/" not in url:
        embed_url = url.replace("spotify.com/", "spotify.com/embed/")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    context = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(embed_url, headers=headers)
        with urllib.request.urlopen(req, context=context) as response:
            html = response.read().decode('utf-8')
        
        print(f"Embed URL: {embed_url}")
        print(f"HTML Length: {len(html)}")
        
        # In embed pages, Spotify usually stores the metadata in a script tag with id "resource" or in a JSON-LD script,
        # or inside a script tag like: <script id="initial-state" type="text/json">...</script>
        # Let's inspect the script tags
        script_matches = re.findall(r'<script\b[^>]*>(.*?)</script>', html, re.DOTALL)
        print(f"Found {len(script_matches)} script tags")
        
        # Let's write the first 1000 characters of each script tag to see if it looks like metadata
        for idx, script in enumerate(script_matches):
            snippet = script.strip()[:200]
            if snippet:
                print(f"Script {idx}: {snippet}...")
                
            # If the script contains JSON metadata
            if 'resource' in script or 'track' in script or 'playlist' in script:
                # Let's save the script content to a file to examine
                with open(f"embed_script_{idx}.txt", "w", encoding="utf-8") as f:
                    f.write(script)
                print(f"--> Saved script {idx} containing potential data to embed_script_{idx}.txt")
                
    except Exception as e:
        print("Error fetching embed URL:", e)

print("--- Testing track embed ---")
fetch_embed_metadata("https://open.spotify.com/track/4PTG3Z6ehGkBF3zI7Ywt1D")

print("\n--- Testing playlist embed ---")
fetch_embed_metadata("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGsyNa7T")
