import urllib.request
import urllib.parse
import re
import json
import ssl

def fetch_spotify_metadata(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    # Bypass SSL verification
    context = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=context) as response:
            html = response.read().decode('utf-8')
        
        print("Length of HTML:", len(html))
        
        # Look for JSON-LD scripts first
        ld_json_matches = re.findall(r'<script\s+type="application/ld\+json"\s*>(.*?)</script>', html, re.DOTALL)
        if ld_json_matches:
            for match in ld_json_matches:
                try:
                    data = json.loads(match.strip())
                    print("Found JSON-LD data type:", data.get('@type'))
                    if data.get('@type') == 'MusicRecording':
                        # Track metadata
                        name = data.get('name')
                        artists = [a.get('name') for a in data.get('byArtist', [])]
                        print(f"Track: {name} by {', '.join(artists)}")
                        return {"type": "track", "name": name, "artists": artists}
                    elif data.get('@type') == 'MusicPlaylist':
                        # Playlist metadata
                        name = data.get('name')
                        tracks = []
                        track_items = data.get('track', [])
                        for item in track_items:
                            if item.get('@type') == 'MusicRecording':
                                t_name = item.get('name')
                                t_artists = [a.get('name') for a in item.get('byArtist', [])]
                                tracks.append({"name": t_name, "artists": t_artists})
                        print(f"Playlist: {name} with {len(tracks)} tracks")
                        return {"type": "playlist", "name": name, "tracks": tracks}
                except Exception as ex:
                    print("Error parsing JSON-LD:", ex)
                    
        # Let's search for "initial-state" or script hydration
        initial_state_match = re.search(r'<script\s+id="initial-state"\s+type="text/json"\s*>(.*?)</script>', html, re.DOTALL)
        if initial_state_match:
            try:
                state_data = json.loads(urllib.parse.unquote(initial_state_match.group(1).strip()))
                print("Found initial-state keys:", list(state_data.keys()))
            except Exception as ex:
                print("Error parsing initial-state:", ex)
                
    except Exception as e:
        print("Error fetching URL:", e)

# Test with a public track and playlist
if __name__ == '__main__':
    print("Testing Spotify track extraction...")
    fetch_spotify_metadata("https://open.spotify.com/track/4PTG3Z6ehGkBF3zI7Ywt1D")
    print("\nTesting Spotify playlist extraction...")
    fetch_spotify_metadata("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGsyNa7T")
