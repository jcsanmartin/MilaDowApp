"""
Descargador de medios para YouTube, TikTok, Facebook y Spotify.
Soporta descarga de videos, audio, playlists y publicaciones de fotos de TikTok.
"""
import os
import re
import sys
import urllib.request
import subprocess
import tempfile
import shutil
from typing import Optional, Callable, Dict, Any

try:
    import imageio_ffmpeg
    HAS_IMAGEIO_FFMPEG = True
except ImportError:
    HAS_IMAGEIO_FFMPEG = False

import yt_dlp


def get_ffmpeg_path() -> str:
    """Obtiene la ruta al ejecutable de FFmpeg."""
    if HAS_IMAGEIO_FFMPEG:
        try:
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass
    return "ffmpeg"


class StopDownloadException(Exception):
    """Excepción para detener descargas de forma limpia."""
    pass


class MediaDownloader:
    """Descargador de medios multiplataforma.

    Attributes:
        output_dir: Directorio de salida para archivos descargados.
        format_type: 'mp4' o 'mp3'.
        quality: Calidad de video ('720p', '1080p', 'best', etc.).
        mode: Modo de descarga ('single' o 'playlist').
        platform: Plataforma de origen ('youtube', 'tiktok', 'facebook', 'spotify').
    """

    # Caracteres no permitidos en nombres de archivo (Windows/Unix)
    _INVALID_FILENAME_CHARS = '<>:"/\\|?*'

    # Patrón para validar URLs
    _URL_PATTERN = re.compile(
        r'^https?://'
        r'([\w-]+\.)+[\w-]+'
        r'(:\d+)?'
        r'(/.*)?$'
    )

    def __init__(
        self,
        output_dir: str,
        format_type: str = "mp4",
        quality: str = "720p",
        mode: str = "single",
        playlist_limit: int = 50,
        platform: str = "auto",
        cookies_from_browser: Optional[str] = None,
        cookies_file: Optional[str] = None,
        stop_flag: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable] = None,
        log_callback: Optional[Callable] = None,
        finish_callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None,
        spotify_client_id: Optional[str] = None,
        spotify_client_secret: Optional[str] = None,
    ) -> None:
        self.output_dir = output_dir
        self.format_type = format_type
        self.quality = quality
        self.mode = mode
        self.playlist_limit = playlist_limit
        self.platform = platform
        self.cookies_from_browser = cookies_from_browser
        self.cookies_file = cookies_file
        self.stop_flag = stop_flag
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.finish_callback = finish_callback
        self.error_callback = error_callback
        self.spotify_client_id = spotify_client_id
        self.spotify_client_secret = spotify_client_secret
        self.ffmpeg_path = get_ffmpeg_path()

        self._ensure_output_dir()

    # ──────────────────────────────────────────
    # Utilidades internas
    # ──────────────────────────────────────────

    def _ensure_output_dir(self) -> None:
        """Verifica que el directorio de salida exista y sea escribible."""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            test_file = os.path.join(self.output_dir, ".perm_test")
            with open(test_file, "w") as f:
                f.write("ok")
            os.remove(test_file)
        except Exception:
            fallback = "/storage/emulated/0/Download"
            if not os.path.exists(fallback):
                try:
                    os.makedirs(fallback, exist_ok=True)
                except Exception:
                    fallback = tempfile.gettempdir()
            self._emit_log(f"⚠️ Sin permisos en '{self.output_dir}'. Usando '{fallback}'.")
            self.output_dir = fallback

    def _clean_filename(self, title: str, max_length: int = 50) -> str:
        """Limpia un título para usarlo como nombre de archivo seguro."""
        if not title:
            return "media"
        cleaned = "".join(c for c in title if c not in self._INVALID_FILENAME_CHARS)
        cleaned = cleaned.strip(". ")
        return cleaned[:max_length] or "media"

    def _validate_url(self, url: str) -> bool:
        """Valida que la URL tenga un formato básico correcto."""
        return bool(self._URL_PATTERN.match(url.strip()))

    def _check_stop(self) -> None:
        """Lanza StopDownloadException si el usuario pidió detener."""
        if self.stop_flag and self.stop_flag.get("stop_requested"):
            self._emit_log("⏹️ Descarga detenida por el usuario.")
            raise StopDownloadException()

    def _run_ffmpeg(self, cmd: list, context: str = "") -> bool:
        """Ejecuta un comando FFmpeg con manejo robusto de errores y timeout."""
        try:
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,
            )
            if process.returncode != 0:
                error_msg = process.stderr[-500:] if process.stderr else "Error desconocido"
                self._emit_error(f"Error FFmpeg ({context}): {error_msg}")
                return False
            return True
        except subprocess.TimeoutExpired:
            self._emit_error(f"Timeout en FFmpeg ({context}): superó 5 minutos.")
            return False
        except Exception as e:
            self._emit_error(f"Excepción FFmpeg ({context}): {e}")
            return False

    # ──────────────────────────────────────────
    # Callbacks de emisión
    # ──────────────────────────────────────────

    def _emit_log(self, msg: str) -> None:
        if self.log_callback:
            self.log_callback(msg)

    def _emit_error(self, msg: str) -> None:
        if self.error_callback:
            self.error_callback(msg)

    def _emit_progress(self, d: dict) -> None:
        self._check_stop()

        if d["status"] == "downloading" and self.progress_callback:
            percent_str = d.get("_percent_str", "0%").strip("\x1b[0;94m").strip("%").strip()
            speed_str = d.get("_speed_str", "N/A").strip("\x1b[0;32m").strip()
            eta_str = d.get("_eta_str", "N/A").strip("\x1b[0;33m").strip()
            try:
                percent = float(percent_str) / 100.0
            except ValueError:
                percent = 0.0
            self.progress_callback(percent, speed_str, eta_str)
        elif d["status"] == "finished":
            self._emit_log("Fuente descargada. Procesando archivo...")

    # ──────────────────────────────────────────
    # Opciones comunes de yt-dlp
    # ──────────────────────────────────────────

    def _get_common_opts(self) -> dict:
        """Construye las opciones comunes de yt-dlp."""
        opts: Dict[str, Any] = {
            "ffmpeg_location": self.ffmpeg_path,
            "ignoreerrors": True,
            "progress_hooks": [self._emit_progress],
            "concurrent_fragment_downloads": 4,
            "buffersize": 1024 * 64,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Linux; Android 13; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            },
        }

        if self.cookies_from_browser:
            opts["cookiesfrombrowser"] = (self.cookies_from_browser,)
        elif self.cookies_file and os.path.exists(self.cookies_file):
            opts["cookiefile"] = self.cookies_file

        if self.log_callback:
            opts["logger"] = _YtDlpLogger(self.log_callback)

        return opts

    # ──────────────────────────────────────────
    # Descarga de Spotify
    # ──────────────────────────────────────────

    def _download_spotify(self, url: str) -> None:
        """Descarga canciones/playlists de Spotify usando spotdl."""
        self._emit_log("Iniciando descarga de Spotify...")
        cmd = [
            sys.executable, "-m", "spotdl", url,
            "--output", self.output_dir,
            "--ffmpeg", self.ffmpeg_path,
        ]
        if self.spotify_client_id:
            cmd.extend(["--client-id", self.spotify_client_id])
        if self.spotify_client_secret:
            cmd.extend(["--client-secret", self.spotify_client_secret])

        try:
            self._emit_log("Conectando con Spotify...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            for line in process.stdout:
                self._check_stop()
                line = line.rstrip()
                if line:
                    self._emit_log(line)

            process.wait()

            if process.returncode == 0:
                self._emit_log("✅ Descarga de Spotify completada.")
                if self.finish_callback:
                    self.finish_callback()
            else:
                self._emit_error("spotdl terminó con error. Revisa los logs.")
        except StopDownloadException:
            process.terminate()
        except Exception as e:
            self._emit_error(f"Error al ejecutar spotdl: {e}")

    # ──────────────────────────────────────────
    # TikTok: Procesamiento de publicaciones de fotos
    # ──────────────────────────────────────────

    def _process_tiktok_photo_post(self, info: dict) -> None:
        """Une fotos de un carrusel de TikTok con audio en un único MP4 usando FFmpeg."""
        photo_urls = []
        for t in info.get("thumbnails", []):
            t_url = t.get("url", "")
            if ("photomode-image" in t_url or "tplv-photomode" in t_url) and t_url not in photo_urls:
                photo_urls.append(t_url)

        if not photo_urls:
            return

        base_title = self._clean_filename(info.get("title", "tiktok_photo") or "tiktok_photo")
        final_mp4 = os.path.join(self.output_dir, f"{base_title}.mp4")

        # Si yt-dlp ya generó un MP4 funcional, no rehacer nada
        if os.path.exists(final_mp4) and os.path.getsize(final_mp4) > 10000:
            self._emit_log(f"Video MP4 listo: {os.path.basename(final_mp4)}")
            return

        # Buscar archivo de audio suelto descargado por yt-dlp
        found_audio = self._find_audio_file(base_title)
        if not found_audio:
            return

        self._emit_log(f"Uniendo {len(photo_urls)} foto(s) + audio en video MP4...")

        temp_dir = tempfile.mkdtemp()
        try:
            downloaded = self._download_photos(photo_urls, temp_dir)
            if not downloaded:
                return

            total_duration = info.get("duration") or 10
            photo_duration = max(3.0, total_duration / len(downloaded)) if total_duration > 0 else 4.0

            if len(downloaded) == 1:
                cmd = [
                    self.ffmpeg_path, "-y",
                    "-loop", "1", "-i", downloaded[0],
                    "-i", found_audio,
                    "-c:v", "libx264", "-tune", "stillimage",
                    "-c:a", "aac", "-b:a", "192k",
                    "-pix_fmt", "yuv420p", "-shortest",
                    final_mp4,
                ]
            else:
                concat_file = os.path.join(temp_dir, "concat.txt")
                with open(concat_file, "w", encoding="utf-8") as f:
                    for p in downloaded:
                        f.write(f"file '{p.replace(chr(92), '/')}'\n")
                        f.write(f"duration {photo_duration:.2f}\n")
                    f.write(f"file '{downloaded[-1].replace(chr(92), '/')}'\n")

                cmd = [
                    self.ffmpeg_path, "-y",
                    "-f", "concat", "-safe", "0", "-i", concat_file,
                    "-i", found_audio,
                    "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
                    "-pix_fmt", "yuv420p", "-shortest",
                    final_mp4,
                ]

            success = self._run_ffmpeg(cmd, context="unir fotos TikTok")

            if success and os.path.exists(final_mp4):
                self._emit_log(f"✅ Video final: {os.path.basename(final_mp4)}")
                try:
                    os.remove(found_audio)
                except Exception:
                    pass
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _find_audio_file(self, base_title: str) -> Optional[str]:
        """Busca el archivo de audio asociado a un título descargado."""
        for ext in (".m4a", ".mp3", ".webm"):
            candidate = os.path.join(self.output_dir, f"{base_title}{ext}")
            if os.path.exists(candidate):
                return candidate

        # Fallback: buscar cualquier archivo que empiece con el título
        for f in os.listdir(self.output_dir):
            if f.startswith(base_title) and not f.endswith(".mp4"):
                return os.path.join(self.output_dir, f)
        return None

    def _download_photos(self, photo_urls: list, temp_dir: str) -> list:
        """Descarga una lista de URLs de fotos a un directorio temporal."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        downloaded = []
        for idx, img_url in enumerate(photo_urls, 1):
            try:
                img_path = os.path.join(temp_dir, f"photo_{idx:03d}.jpg")
                req = urllib.request.Request(img_url, headers=headers)
                with urllib.request.urlopen(req) as resp, open(img_path, "wb") as f:
                    f.write(resp.read())
                downloaded.append(img_path)
            except Exception as e:
                self._emit_log(f"Aviso al descargar foto {idx}: {e}")
        return downloaded

    # ──────────────────────────────────────────
    # Preparación de URL
    # ──────────────────────────────────────────

    def _prepare_url(self, url: str, is_tiktok: bool, is_facebook: bool) -> str:
        """Normaliza y limpia la URL antes de procesar."""
        # Normalizar enlaces de fotos TikTok
        if is_tiktok and "/photo/" in url:
            self._emit_log("Normalizando enlace de foto TikTok...")
            url = url.replace("/photo/", "/video/")

        # YouTube modo single: limpiar parámetros de playlist
        if not is_tiktok and not is_facebook and self.mode == "single":
            if "watch?v=" in url and "list=" in url:
                self._emit_log("Modo single: limpiando parámetros de playlist...")
                parts = url.split("&")
                url = "&".join(p for p in parts if not p.startswith("list=") and not p.startswith("index="))

        # Resolver enlaces cortos de TikTok
        if is_tiktok and ("vt.tiktok.com" in url.lower() or "vm.tiktok.com" in url.lower()):
            try:
                self._emit_log("Resolviendo enlace corto TikTok...")
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Linux; Android 13; K)"})
                with urllib.request.urlopen(req) as resp:
                    url = resp.geturl()
                self._emit_log(f"Enlace resuelto: {url}")
            except Exception as e:
                self._emit_log(f"Aviso al resolver enlace: {e}")

        return url

    # ──────────────────────────────────────────
    # Configuración de opciones de descarga
    # ──────────────────────────────────────────

    def _build_ydl_opts(self, is_tiktok: bool, is_facebook: bool, is_youtube: bool) -> dict:
        """Construye las opciones finales de yt-dlp según plataforma y formato."""
        opts = self._get_common_opts()

        if is_youtube:
            opts["extractor_args"] = {"youtube": {"player_client": ["mweb", "android", "ios"]}}

        # Template de nombre de archivo
        if self.mode == "playlist" and is_youtube:
            outtmpl = os.path.join(self.output_dir, "%(playlist_index)02d - %(title)s.%(ext)s")
        else:
            outtmpl = os.path.join(self.output_dir, "%(title)s.%(ext)s")

        opts["outtmpl"] = outtmpl

        # Formato según tipo
        if self.format_type == "mp3":
            opts["format"] = "bestaudio[ext=mp3]/bestaudio[ext=m4a]/bestaudio/best"
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }]
        elif is_tiktok or is_facebook:
            opts["format"] = "bestvideo+bestaudio/bestvideo/best"
            opts["merge_output_format"] = "mp4"
        else:
            # YouTube MP4
            if self.quality == "best":
                opts["format"] = "bestvideo[vcodec^=avc1]+bestaudio/bestvideo+bestaudio/best"
                opts["format_sort"] = ["res", "vcodec:h264", "filesize", "br"]
            else:
                h = self.quality.replace("p", "")
                opts["format"] = (
                    f"bestvideo[height<={h}][vcodec^=avc1]+bestaudio/"
                    f"bestvideo[height<={h}][vcodec^=vp9]+bestaudio/"
                    f"bestvideo[height<={h}]+bestaudio/best"
                )
                opts["format_sort"] = [f"res:{h}", "vcodec:h264", "filesize", "br"]
            opts["merge_output_format"] = "mp4"

        # Playlist vs single
        if is_tiktok or is_facebook or self.mode == "single":
            opts["noplaylist"] = True
        else:
            opts["playlistend"] = self.playlist_limit
            opts["playlistreverse"] = False
            opts["playlist_items"] = f"1-{self.playlist_limit}"

        return opts

    # ──────────────────────────────────────────
    # Punto de entrada principal
    # ──────────────────────────────────────────

    def download(self, url: str) -> None:
        """Inicia la descarga del contenido multimedia.

        Args:
            url: URL del video, canción o playlist a descargar.
        """
        url = url.strip()

        if not self._validate_url(url):
            self._emit_error("La URL ingresada no tiene un formato válido.")
            return

        self._emit_log(f"Iniciando descarga: {url}")

        if self.platform == "spotify":
            self._download_spotify(url)
            return

        is_tiktok = "tiktok.com" in url.lower() or "vt.tiktok.com" in url.lower() or self.platform == "tiktok"
        is_facebook = "facebook.com" in url.lower() or "fb.watch" in url.lower() or self.platform == "facebook"
        is_youtube = not is_tiktok and not is_facebook

        url = self._prepare_url(url, is_tiktok, is_facebook)

        if self.cookies_from_browser:
            self._emit_log(f"Usando cookies del navegador: {self.cookies_from_browser}")
        elif self.cookies_file and os.path.exists(self.cookies_file):
            self._emit_log(f"Usando archivo de cookies: {self.cookies_file}")

        ydl_opts = self._build_ydl_opts(is_tiktok, is_facebook, is_youtube)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if is_tiktok and info and self.format_type == "mp4":
                    self._process_tiktok_photo_post(info)
                if is_facebook and info:
                    self._emit_log("✅ Video de Facebook descargado correctamente.")

            self._check_stop()
            if self.finish_callback:
                self.finish_callback()
        except StopDownloadException:
            return
        except Exception as e:
            error_msg = str(e)
            if "__STOP_REQUESTED__" in error_msg:
                return
            if "DPAPI" in error_msg or "failed to load cookies" in error_msg:
                self._emit_error(
                    "Error al leer cookies del navegador (bloqueo DPAPI).\n"
                    "👉 Solución: selecciona '📄 Archivo cookies.txt' y carga tu archivo de cookies exportado."
                )
            else:
                self._emit_error(f"Error durante la descarga: {e}")


# Alias para compatibilidad
YoutubeDownloader = MediaDownloader


class _YtDlpLogger:
    """Logger personalizado para yt-dlp que redirige al callback de la UI."""

    def __init__(self, log_callback: Callable) -> None:
        self.log_callback = log_callback

    def debug(self, msg: str) -> None:
        if msg.startswith("[download] "):
            return
        if self.log_callback:
            self.log_callback(msg)

    def info(self, msg: str) -> None:
        if self.log_callback:
            self.log_callback(msg)

    def warning(self, msg: str) -> None:
        pass

    def error(self, msg: str) -> None:
        if self.log_callback:
            self.log_callback(f"ERROR: {msg}")
