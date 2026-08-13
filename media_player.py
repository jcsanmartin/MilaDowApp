import os
import glob
import flet as ft

class MediaLibrary:
    def __init__(self):
        self.supported_audio = ['.mp3', '.m4a', '.wav', '.flac', '.ogg']
        self.supported_video = ['.mp4', '.mkv', '.webm', '.avi']

    def scan_storage(self):
        """Escanea carpetas en Android / PC en busca de archivos de audio y video."""
        search_dirs = [
            "/storage/emulated/0/Download",
            "/storage/emulated/0/Music",
            "/storage/emulated/0/Movies",
            "/storage/emulated/0/DCIM",
            "/storage/emulated/0/WhatsApp/Media",
            "/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media",
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Music"),
            os.path.expanduser("~/Videos")
        ]

        media_files = []
        visited = set()

        for base_dir in search_dirs:
            if not os.path.exists(base_dir):
                continue
            for root, dirs, files in os.walk(base_dir):
                if root in visited:
                    continue
                visited.add(root)
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in self.supported_audio or ext in self.supported_video:
                        full_path = os.path.join(root, file)
                        is_video = ext in self.supported_video
                        folder_name = os.path.basename(root) or root
                        media_files.append({
                            'name': file,
                            'path': full_path,
                            'folder': folder_name,
                            'folder_path': root,
                            'is_video': is_video,
                            'ext': ext,
                            'size_mb': round(os.path.getsize(full_path) / (1024 * 1024), 2) if os.path.exists(full_path) else 0
                        })
        return media_files
