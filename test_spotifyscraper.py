from spotify_scraper import SpotifyClient
import sys

def test_track(url):
    try:
        with SpotifyClient() as client:
            track = client.get_track(url)
            print("Track data:")
            print("Name:", track.name)
            print("Artists:", [a.name for a in track.artists])
            print("Duration ms:", track.duration_ms)
    except Exception as e:
        print("Track fetch error:", e)

def test_playlist(url):
    try:
        with SpotifyClient() as client:
            playlist = client.get_playlist(url)
            print("\nPlaylist data:")
            print("Name:", playlist.name)
            print("Tracks count:", len(playlist.tracks))
            for i, t in enumerate(playlist.tracks[:5]):
                print(f"Track {i+1}: {t.name} - {[a.name for a in t.artists]}")
    except Exception as e:
        print("Playlist fetch error:", e)

if __name__ == '__main__':
    print("Testing spotifyscraper...")
    test_track("https://open.spotify.com/track/4PTG3Z6ehGkBF3zI7Ywt1D")
    test_playlist("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGsyNa7T")
