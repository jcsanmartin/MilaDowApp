import subprocess
import os
import imageio_ffmpeg
import sys

try:
    import SpotipyFree.Formatter
    original_formatTrack = SpotipyFree.Formatter.SpotifyFormatter.formatTrack
    
    def patched_formatTrack(track, formattedArtists, songId=None, album=[]):
        print("Track fields:", list(track.keys()) if isinstance(track, dict) else "Not a dict")
        print("Track content:", track)
        return original_formatTrack(track, formattedArtists, songId, album)
        
    SpotipyFree.Formatter.SpotifyFormatter.formatTrack = patched_formatTrack
    print("Successfully monkey-patched SpotipyFree.Formatter.SpotifyFormatter.formatTrack!")
except Exception as e:
    print("Could not monkey-patch SpotipyFree on import:", e)

def get_ffmpeg_path():
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

def test_spotdl():
    url = "https://open.spotify.com/track/4PTG3Z6ehGkBF3zI7Ywt1D" # Blinding Lights
    output_dir = "test_downloads"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    ffmpeg_path = get_ffmpeg_path()
    
    from spotdl.console.entry_point import console_entry_point
    sys.argv = [
        "spotdl", "download", url,
        "--output", os.path.join(output_dir, "{title} - {artist}.{ext}"),
        "--ffmpeg", ffmpeg_path
    ]
    
    try:
        console_entry_point()
    except Exception as e:
        print("Error running spotdl programmatically:", e)

if __name__ == '__main__':
    test_spotdl()
