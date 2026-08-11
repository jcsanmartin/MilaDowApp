import os
import sys
import urllib.request
import subprocess
import tempfile
import shutil
try:
    import imageio_ffmpeg
    HAS_IMAGEIO_FFMPEG = True
except ImportError:
    HAS_IMAGEIO_FFMPEG = False

import yt_dlp

def get_ffmpeg_path():
    if HAS_IMAGEIO_FFMPEG:
        try:
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass
    return "ffmpeg"

class MediaDownloader:
    def __init__(self, output_dir, format_type="mp4", quality="720p", mode="single", playlist_limit=50,
                 platform="auto", cookies_from_browser=None, cookies_file=None, stop_flag=None,
                 progress_callback=None, log_callback=None, finish_callback=None, error_callback=None,
                 spotify_client_id=None, spotify_client_secret=None):
        self.output_dir = output_dir
        self.format_type = format_type
        self.quality = quality
        self.mode = mode
        self.playlist_limit = playlist_limit
        self.platform = platform
        self.cookies_from_browser = cookies_from_browser
        self.cookies_file = cookies_file
        self.stop_flag = stop_flag  # dict compartido con la UI, key 'stop_requested'
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.finish_callback = finish_callback
        self.error_callback = error_callback
        self.spotify_client_id = spotify_client_id
        self.spotify_client_secret = spotify_client_secret
        self.ffmpeg_path = get_ffmpeg_path()

        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
            except Exception as e:
                self._emit_error(f"Error al crear el directorio: {e}")

    def _emit_log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def _emit_progress(self, d):
        # Abortar si el usuario solicitó detener
        if self.stop_flag and self.stop_flag.get('stop_requested'):
            raise Exception('__STOP_REQUESTED__')

        if d['status'] == 'downloading' and self.progress_callback:
            percent_str = d.get('_percent_str', '0%').strip('\x1b[0;94m').strip('%').strip()
            speed_str = d.get('_speed_str', 'N/A').strip('\x1b[0;32m').strip()
            eta_str = d.get('_eta_str', 'N/A').strip('\x1b[0;33m').strip()
            try:
                percent = float(percent_str) / 100.0
            except ValueError:
                percent = 0.0
            self.progress_callback(percent, speed_str, eta_str)
        elif d['status'] == 'finished':
            self._emit_log("Descarga de fuente finalizada. Procesando archivo único...")

    def _emit_error(self, msg):
        if self.error_callback:
            self.error_callback(msg)

    def _get_common_opts(self):
        """Construye las opciones comunes de yt-dlp."""
        common_opts = {
            'ffmpeg_location': self.ffmpeg_path,
            'ignoreerrors': True,
            'progress_hooks': [self._emit_progress],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            }
        }

        # Inyectar cookies si se especificaron
        if self.cookies_from_browser:
            common_opts['cookiesfrombrowser'] = (self.cookies_from_browser,)
        elif self.cookies_file and os.path.exists(self.cookies_file):
            common_opts['cookiefile'] = self.cookies_file

        # Añadir logger si existe callback
        if self.log_callback:
            common_opts['logger'] = MyLogger(self.log_callback)

        return common_opts

    def _download_spotify(self, url):
        self._emit_log("Iniciando descarga de Spotify...")
        cmd = [sys.executable, "-m", "spotdl", url,
               "--output", self.output_dir,
               "--ffmpeg", self.ffmpeg_path]
        if self.spotify_client_id:
            cmd.extend(["--client-id", self.spotify_client_id])
        if self.spotify_client_secret:
            cmd.extend(["--client-secret", self.spotify_client_secret])

        try:
            self._emit_log("Conectando con Spotify y buscando canción...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # unir stderr en stdout para capturar todo
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            # Leer línea por línea en tiempo real
            for line in process.stdout:
                if self.stop_flag and self.stop_flag.get('stop_requested'):
                    process.terminate()
                    return
                line = line.rstrip()
                if line:
                    self._emit_log(line)

            process.wait()

            if process.returncode == 0:
                self._emit_log("✅ Descarga de Spotify completada.")
                if self.finish_callback:
                    self.finish_callback()
            else:
                self._emit_error("spotdl terminó con error. Revisa los logs de arriba.")
        except Exception as e:
            self._emit_error(f"Error al ejecutar spotdl: {e}")


    def _process_tiktok_photo_post(self, info):
        """Si la publicación es un carrusel de fotos y el formato es MP4, las une con el audio usando FFmpeg en UN SOLO VIDEO MP4."""
        thumbnails = info.get('thumbnails', [])
        photo_urls = []
        for t in thumbnails:
            t_url = t.get('url', '')
            if ('photomode-image' in t_url or 'tplv-photomode' in t_url) and t_url not in photo_urls:
                photo_urls.append(t_url)

        if not photo_urls:
            return

        raw_title = info.get('title', 'tiktok_photo') or 'tiktok_photo'
        base_title = raw_title
        for ch in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
            base_title = base_title.replace(ch, '')
        base_title = base_title[:50].strip() or 'tiktok_photo'

        final_mp4_path = os.path.join(self.output_dir, f"{base_title}.mp4")

        # Si ya existe un video MP4 válido creado directamente por yt-dlp, no necesitamos unir
        if os.path.exists(final_mp4_path) and os.path.getsize(final_mp4_path) > 100000:
            self._emit_log(f"Video MP4 generado exitosamente: {os.path.basename(final_mp4_path)}")
            return

        # Buscar archivo de audio suelto descargado por yt-dlp (.m4a, .mp3, .webm, etc.)
        audio_candidates = [
            os.path.join(self.output_dir, f"{base_title}.m4a"),
            os.path.join(self.output_dir, f"{base_title}.mp3"),
            os.path.join(self.output_dir, f"{base_title}.webm"),
        ]
        found_audio = None
        for candidate in audio_candidates:
            if os.path.exists(candidate):
                found_audio = candidate
                break

        if not found_audio:
            for file in os.listdir(self.output_dir):
                if file.startswith(base_title) and not file.endswith('.mp4'):
                    found_audio = os.path.join(self.output_dir, file)
                    break

        if not found_audio:
            return

        self._emit_log(f"Uniendo {len(photo_urls)} foto(s) HD y audio en un ÚNICO archivo de video MP4...")

        temp_dir = tempfile.mkdtemp()
        try:
            downloaded_photos = []
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
            }

            for idx, img_url in enumerate(photo_urls, 1):
                try:
                    img_temp_path = os.path.join(temp_dir, f"photo_{idx:03d}.jpg")
                    req = urllib.request.Request(img_url, headers=headers)
                    with urllib.request.urlopen(req) as resp, open(img_temp_path, 'wb') as f:
                        f.write(resp.read())
                    downloaded_photos.append(img_temp_path)
                except Exception as img_err:
                    self._emit_log(f"Aviso al descargar foto {idx}: {img_err}")

            if not downloaded_photos:
                return

            num_photos = len(downloaded_photos)
            total_duration = info.get('duration') or 10
            photo_duration = max(3.0, total_duration / num_photos) if total_duration > 0 else 4.0

            if num_photos == 1:
                cmd = [
                    self.ffmpeg_path,
                    '-y',
                    '-loop', '1',
                    '-i', downloaded_photos[0],
                    '-i', found_audio,
                    '-c:v', 'libx264',
                    '-tune', 'stillimage',
                    '-c:a', 'aac',
                    '-b:a', '192k',
                    '-pix_fmt', 'yuv420p',
                    '-shortest',
                    final_mp4_path
                ]
            else:
                concat_file_path = os.path.join(temp_dir, "concat.txt")
                with open(concat_file_path, "w", encoding="utf-8") as f:
                    for p in downloaded_photos:
                        clean_p = p.replace('\\', '/')
                        f.write(f"file '{clean_p}'\n")
                        f.write(f"duration {photo_duration:.2f}\n")
                    clean_last = downloaded_photos[-1].replace('\\', '/')
                    f.write(f"file '{clean_last}'\n")

                cmd = [
                    self.ffmpeg_path,
                    '-y',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', concat_file_path,
                    '-i', found_audio,
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-b:a', '192k',
                    '-pix_fmt', 'yuv420p',
                    '-shortest',
                    final_mp4_path
                ]

            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if process.returncode == 0 and os.path.exists(final_mp4_path):
                self._emit_log(f"¡Unificación completada! Archivo final único: {os.path.basename(final_mp4_path)}")
                # Eliminar archivo de audio suelto para dejar ÚNICAMENTE un archivo MP4
                try:
                    os.remove(found_audio)
                except Exception:
                    pass
            else:
                self._emit_log(f"FFmpeg aviso: {process.stderr[-150:] if process.stderr else 'Proceso finalizado'}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def download(self, url):
        self._emit_log(f"Iniciando descarga: {url}")

        if self.platform == "spotify":
            self._download_spotify(url)
            return

        is_tiktok = ("tiktok.com" in url.lower() or "vt.tiktok.com" in url.lower() or self.platform == "tiktok")
        is_facebook = ("facebook.com" in url.lower() or "fb.watch" in url.lower() or self.platform == "facebook")
        is_youtube_platform = not is_tiktok and not is_facebook

        # Normalizar URLs de publicaciones de fotos de TikTok (/photo/ -> /video/)
        if is_tiktok and "/photo/" in url:
            self._emit_log("Normalizando enlace de foto de TikTok para su procesamiento...")
            url = url.replace("/photo/", "/video/")

        # Para YouTube, si el usuario quiere un solo video, limpiamos el parámetro de playlist (&list=...)
        # para descargar solo el video individual y evitar que baje la playlist completa.
        if is_youtube_platform:
            if self.mode == 'single':
                if 'watch?v=' in url and 'list=' in url:
                    self._emit_log("Modo de descarga: Un solo video. Limpiando lista de reproducción...")
                    parts = url.split('&')
                    clean_parts = [p for p in parts if not p.startswith('list=') and not p.startswith('index=')]
                    url = '&'.join(clean_parts)

        if self.cookies_from_browser:
            self._emit_log(f"Usando cookies del navegador: {self.cookies_from_browser}")
        elif self.cookies_file and os.path.exists(self.cookies_file):
            self._emit_log(f"Usando archivo de cookies: {self.cookies_file}")

        common_opts = self._get_common_opts()

        # Aplicar extractor_args específico de YouTube SOLO para YouTube
        if is_youtube_platform:
            common_opts['extractor_args'] = {
                'youtube': {
                    'player_client': ['android_vr', 'web_embedded']
                }
            }

        if self.mode == 'playlist' and is_youtube_platform:
            outtmpl = os.path.join(self.output_dir, '%(playlist_index)02d - %(title)s.%(ext)s')
        else:
            outtmpl = os.path.join(self.output_dir, '%(title)s.%(ext)s')

        if self.format_type == 'mp3':
            ydl_opts = {
                **common_opts,
                'outtmpl': outtmpl,
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
            }
        else:
            if is_tiktok or is_facebook:
                # TikTok y Facebook: mejor calidad disponible
                ydl_opts = {
                    **common_opts,
                    'outtmpl': outtmpl,
                    'format': 'bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4',
                }
            else:
                # YouTube video MP4 format config
                height = self.quality.replace('p', '')
                ydl_opts = {
                    **common_opts,
                    'outtmpl': outtmpl,
                    'format': (
                        f'bestvideo[height<={height}][vcodec^=avc1]+bestaudio/'
                        f'bestvideo[height<={height}][vcodec^=vp9]+bestaudio/'
                        f'bestvideo[height<={height}]+bestaudio/best'
                    ),
                    'format_sort': [f'res:{height}', 'vcodec:h264', 'filesize', 'br'],
                    'merge_output_format': 'mp4',
                }

        # Para TikTok, Facebook o modo single, forzar sin playlist
        if is_tiktok or is_facebook or self.mode == 'single':
            ydl_opts['noplaylist'] = True
        else:
            ydl_opts['playlistend'] = self.playlist_limit
            ydl_opts['playlistreverse'] = False
            # Forzar a mantener la ordenación original de la playlist de YouTube
            ydl_opts['playlist_items'] = f"1-{self.playlist_limit}"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if is_tiktok and info and self.format_type == 'mp4':
                    self._process_tiktok_photo_post(info)
                if is_facebook and info:
                    self._emit_log(f"✅ Video de Facebook descargado correctamente.")

            if self.stop_flag and self.stop_flag.get('stop_requested'):
                return  # No llamar finish_callback si fue detenido
            if self.finish_callback:
                self.finish_callback()
        except Exception as e:
            error_msg = str(e)
            if '__STOP_REQUESTED__' in error_msg:
                return  # Detención limpia solicitada por el usuario
            elif 'DPAPI' in error_msg or 'failed to load cookies' in error_msg:
                self._emit_error(
                    "Error al leer cookies del navegador (bloqueo DPAPI de Chrome/Brave/Edge).\n"
                    "👉 Solución: En 'Cookies del Navegador', selecciona '📄 Archivo cookies.txt' y carga tu archivo de cookies exportado."
                )
            else:
                self._emit_error(f"Error durante la descarga: {e}")


# Alias para mantener compatibilidad hacia atrás
YoutubeDownloader = MediaDownloader


class MyLogger:
    def __init__(self, log_callback):
        self.log_callback = log_callback

    def debug(self, msg):
        if msg.startswith('[download] '):
            return
        if self.log_callback:
            self.log_callback(msg)

    def info(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def warning(self, msg):
        pass

    def error(self, msg):
        if self.log_callback:
            self.log_callback(f"ERROR: {msg}")
