import flet as ft
import threading
import asyncio
import os
import time
import json
import sys
from downloader import MediaDownloader
from media_player import MediaLibrary

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
ICON_PNG = os.path.join(BASE_DIR, "app_icon.png")
ICON_ICO = os.path.join(BASE_DIR, "app_icon.ico")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def main(page: ft.Page):
    page.title = "MilaDow - Media Downloader & Player"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 15
    page.spacing = 10
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    if os.path.exists(ICON_ICO):
        try:
            page.window.icon = ICON_ICO
        except Exception:
            pass

    config = load_config()
    last_folder = config.get("last_folder", "")

    # ==========================================
    # SPLASH SCREEN
    # ==========================================
    splash_logo = ft.Image(src=ICON_PNG, width=120, height=120, fit="contain", border_radius=20) \
        if os.path.exists(ICON_PNG) else ft.Icon(ft.Icons.FILE_DOWNLOAD_ROUNDED, size=80, color=ft.Colors.AMBER_400)

    splash_view = ft.Container(
        content=ft.Column(
            [
                ft.Container(height=80),
                splash_logo,
                ft.Container(height=15),
                ft.Text("MilaDow", size=42, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text("Descargador y Reproductor Multimedia", size=14, color=ft.Colors.GREY_400),
                ft.Container(height=30),
                ft.ProgressRing(width=36, height=36, stroke_width=3, color=ft.Colors.AMBER_400),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.Alignment(0, 0),
        expand=True,
        visible=True
    )

    # ==========================================
    # DESCARGADOR MULTIMEDIA
    # ==========================================
    current_platform_val = ["youtube"]

    def set_platform(plat):
        current_platform_val[0] = plat
        btn_yt.style = ft.ButtonStyle(color=ft.Colors.BLACK if plat=="youtube" else ft.Colors.WHITE, bgcolor=ft.Colors.AMBER_400 if plat=="youtube" else ft.Colors.GREY_800)
        btn_tt.style = ft.ButtonStyle(color=ft.Colors.BLACK if plat=="tiktok" else ft.Colors.WHITE, bgcolor=ft.Colors.AMBER_400 if plat=="tiktok" else ft.Colors.GREY_800)
        btn_fb.style = ft.ButtonStyle(color=ft.Colors.BLACK if plat=="facebook" else ft.Colors.WHITE, bgcolor=ft.Colors.AMBER_400 if plat=="facebook" else ft.Colors.GREY_800)
        btn_sp.style = ft.ButtonStyle(color=ft.Colors.BLACK if plat=="spotify" else ft.Colors.WHITE, bgcolor=ft.Colors.AMBER_400 if plat=="spotify" else ft.Colors.GREY_800)
        btn_yt.update()
        btn_tt.update()
        btn_fb.update()
        btn_sp.update()
        on_platform_change(None)

    btn_yt = ft.FilledButton("YouTube", icon=ft.Icons.PLAY_CIRCLE_FILL, style=ft.ButtonStyle(color=ft.Colors.BLACK, bgcolor=ft.Colors.AMBER_400), on_click=lambda e: set_platform("youtube"))
    btn_tt = ft.FilledButton("TikTok", icon=ft.Icons.MUSIC_NOTE, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREY_800), on_click=lambda e: set_platform("tiktok"))
    btn_fb = ft.FilledButton("Facebook", icon=ft.Icons.FACEBOOK, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREY_800), on_click=lambda e: set_platform("facebook"))
    btn_sp = ft.FilledButton("Spotify", icon=ft.Icons.HEADSET, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREY_800), on_click=lambda e: set_platform("spotify"))

    platform_nav_row = ft.Row([btn_yt, btn_tt, btn_fb, btn_sp], alignment=ft.MainAxisAlignment.CENTER, spacing=6, wrap=True)

    url_input = ft.TextField(
        label="URL de YouTube (Video o Playlist)",
        hint_text="https://www.youtube.com/watch?v=...",
        expand=True,
        prefix_icon=ft.Icons.LINK
    )

    android_downloads = "/storage/emulated/0/Download/MilaDow"
    android_music = "/storage/emulated/0/Music/MilaDow"
    android_movies = "/storage/emulated/0/Movies/MilaDow"

    default_dir = last_folder
    if not default_dir or "Users" in default_dir:
        if os.path.exists("/storage/emulated/0/Download"):
            default_dir = android_downloads
        else:
            default_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    path_input = ft.TextField(
        label="Carpeta de Destino",
        value=default_dir,
        hint_text="Ubicación donde se guardan las descargas",
        expand=True,
        prefix_icon=ft.Icons.FOLDER
    )

    def set_folder(path):
        path_input.value = path
        path_input.update()
        save_config({"last_folder": path})
        folder_dialog.open = False
        page.update()

    folder_dialog = ft.AlertDialog(
        title=ft.Text("Ubicación de Descargas"),
        content=ft.Column([
            ft.Text("Selecciona dónde guardar tus descargas en el almacenamiento del celular:", size=13),
            ft.ListTile(leading=ft.Icon(ft.Icons.DOWNLOAD), title=ft.Text("Carpeta Descargas"), subtitle=ft.Text("Download/MilaDow"), on_click=lambda e: set_folder(android_downloads)),
            ft.ListTile(leading=ft.Icon(ft.Icons.MUSIC_NOTE), title=ft.Text("Carpeta Música"), subtitle=ft.Text("Music/MilaDow"), on_click=lambda e: set_folder(android_music)),
            ft.ListTile(leading=ft.Icon(ft.Icons.MOVIE), title=ft.Text("Carpeta Películas/Videos"), subtitle=ft.Text("Movies/MilaDow"), on_click=lambda e: set_folder(android_movies)),
        ], height=220, tight=True),
        actions=[ft.TextButton("Cancelar", on_click=lambda e: setattr(folder_dialog, 'open', False) or page.update())]
    )
    page.overlay.append(folder_dialog)

    folder_btn = ft.IconButton(icon=ft.Icons.FOLDER_OPEN, tooltip="Seleccionar carpeta", on_click=lambda e: setattr(folder_dialog, 'open', True) or page.update())

    mode_dropdown = ft.Dropdown(
        label="Modo de Descarga",
        options=[ft.dropdown.Option("single", text="🎵 Video individual"), ft.dropdown.Option("playlist", text="📋 Playlist completa")],
        value="single",
        width=200,
    )

    format_dropdown = ft.Dropdown(
        label="Formato",
        options=[ft.dropdown.Option("mp4", text="🎬 MP4 (Video)"), ft.dropdown.Option("mp3", text="🎧 MP3 (Audio)")],
        value="mp4",
        width=170,
    )

    quality_dropdown = ft.Dropdown(
        label="Calidad",
        options=[
            ft.dropdown.Option("720p", text="⚡ 720p (Recomendado)"),
            ft.dropdown.Option("best", text="⭐ Mejor calidad"),
            ft.dropdown.Option("1080p", text="🎬 1080p (Full HD)"),
            ft.dropdown.Option("480p", text="📱 480p (Ahorro datos)"),
        ],
        value="720p",
        width=190,
    )

    cookie_browser_dropdown = ft.Dropdown(
        label="🍪 Cookies (Opcional)",
        options=[ft.dropdown.Option("none", text="Sin cookies"), ft.dropdown.Option("file", text="📄 Cargar cookies.txt")],
        value="none",
        width=200,
    )

    cookies_file_path = ft.TextField(label="Archivo cookies.txt", hint_text="Ruta al archivo...", width=280, prefix_icon=ft.Icons.DESCRIPTION, read_only=True)
    cookies_file_btn = ft.IconButton(icon=ft.Icons.FOLDER_OPEN, tooltip="Cargar cookies.txt", on_click=lambda e: None)

    options_container = ft.Column(controls=[], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)

    def get_current_platform():
        return current_platform_val[0]

    def rebuild_options_row():
        current_platform = get_current_platform()
        is_tiktok = current_platform == "tiktok"
        is_facebook = current_platform == "facebook"
        is_spotify = current_platform == "spotify"
        is_youtube = current_platform == "youtube"
        is_playlist = (mode_dropdown.value == "playlist") and is_youtube
        is_file_cookie = (is_tiktok or is_facebook) and (cookie_browser_dropdown.value == "file")
        use_cookies = is_tiktok or is_facebook

        url_labels = {
            "youtube":  ("URL de YouTube (Video o Playlist)", "https://www.youtube.com/watch?v=..."),
            "tiktok":   ("URL de TikTok (Video)", "https://www.tiktok.com/@usuario/video/..."),
            "facebook": ("URL de Facebook (Video)", "https://www.facebook.com/watch?v=..."),
            "spotify":  ("URL de Spotify (Canción o Playlist)", "https://open.spotify.com/track/..."),
        }
        url_input.label, url_input.hint_text = url_labels.get(current_platform, url_labels["youtube"])

        controls = []
        if is_spotify:
            pass
        else:
            row1_items = []
            if is_youtube:
                row1_items.append(mode_dropdown)
            row1_items.append(format_dropdown)
            # Calidad SOLO para YouTube + MP4. Nunca para MP3 (audio no tiene resolución de video)
            if is_youtube and format_dropdown.value == "mp4":
                row1_items.append(quality_dropdown)
            if use_cookies:
                row1_items.append(cookie_browser_dropdown)
            controls.append(ft.Row(row1_items, spacing=8, alignment=ft.MainAxisAlignment.CENTER, wrap=True))


            if is_facebook:
                controls.append(ft.Text("ℹ️ Facebook: pega el enlace del video público.", size=11, color=ft.Colors.BLUE_200, italic=True))
            if is_playlist:
                controls.append(ft.Row([ft.Text("📋 Límite de playlist:", size=12), playlist_limit_input], spacing=8, alignment=ft.MainAxisAlignment.CENTER))
            if is_file_cookie:
                controls.append(ft.Row([cookies_file_path, cookies_file_btn], spacing=5, alignment=ft.MainAxisAlignment.CENTER))

        options_container.controls = controls
        if options_container.page:
            options_container.update()
        if url_input.page:
            url_input.update()

    def on_platform_change(e):
        platform = get_current_platform()
        if platform in ["tiktok", "facebook"]:
            mode_dropdown.options = [ft.dropdown.Option("single", text="📹 Video")]
            mode_dropdown.value = "single"
        elif platform == "spotify":
            mode_dropdown.options = [ft.dropdown.Option("single", text="🎵 Canción"), ft.dropdown.Option("playlist", text="📋 Playlist")]
            mode_dropdown.value = "single"
        else:
            mode_dropdown.options = [ft.dropdown.Option("single", text="🎵 Video individual"), ft.dropdown.Option("playlist", text="📋 Playlist completa")]
        rebuild_options_row()

    mode_dropdown.on_change = lambda e: rebuild_options_row()
    format_dropdown.on_change = lambda e: rebuild_options_row()
    cookie_browser_dropdown.on_change = lambda e: rebuild_options_row()

    progress_bar = ft.ProgressBar(width=500, value=0, visible=False, color=ft.Colors.AMBER_400)
    progress_text = ft.Text("0%", color=ft.Colors.GREY_300)
    status_text = ft.Text("Listo para descargar.", color=ft.Colors.AMBER_200, weight=ft.FontWeight.W_500)
    logs_view = ft.ListView(height=130, spacing=5, auto_scroll=True)

    shared_state = {'percent': 0.0, 'speed': '', 'eta': '', 'logs': [], 'finished': False, 'error': None, 'downloading': False, 'stop_requested': False}
    active_downloader = [None]

    def store_progress(percent, speed, eta):
        shared_state['percent'] = percent
        shared_state['speed'] = speed
        shared_state['eta'] = eta

    def store_log(msg):
        shared_state['logs'].append(msg)

    def store_finish():
        shared_state['finished'] = True

    def store_error(msg):
        shared_state['error'] = msg

    async def ui_update_loop():
        while shared_state['downloading']:
            try:
                progress_bar.value = shared_state['percent']
                progress_text.value = f"{int(shared_state['percent'] * 100)}% - Vel: {shared_state['speed']}"
                while shared_state['logs']:
                    logs_view.controls.append(ft.Text(shared_state['logs'].pop(0), size=12))
                    if len(logs_view.controls) > 60:
                        logs_view.controls.pop(0)

                if shared_state['finished']:
                    progress_bar.value = 1.0
                    progress_text.value = "100%"
                    status_text.value = "¡Descarga Completada!"
                    download_btn.visible = True
                    stop_btn.visible = False
                    logs_view.controls.append(ft.Text("¡Descarga completada exitosamente!", color=ft.Colors.GREEN_400, size=12))
                    page.update()
                    break

                if shared_state['error']:
                    status_text.value = "Error en la descarga."
                    download_btn.visible = True
                    stop_btn.visible = False
                    logs_view.controls.append(ft.Text(f"Error: {shared_state['error']}", color=ft.Colors.RED_400, size=12))
                    page.update()
                    break
                page.update()
                await asyncio.sleep(0.8)
            except Exception:
                break
        shared_state['downloading'] = False

    def btn_click(e):
        url = url_input.value.strip()
        out_dir = path_input.value.strip()
        platform = get_current_platform()
        if not url or not out_dir:
            status_text.value = "Por favor completa la URL y carpeta."
            page.update()
            return

        save_config({"last_folder": out_dir})
        shared_state.update({'percent': 0.0, 'logs': [], 'finished': False, 'error': None, 'downloading': True, 'stop_requested': False})
        download_btn.visible = False
        stop_btn.visible = True
        status_text.value = f"Iniciando descarga desde {platform.upper()}..."
        progress_bar.visible = True
        logs_view.controls.clear()
        page.update()

        downloader = MediaDownloader(
            output_dir=out_dir, format_type=format_dropdown.value, quality=quality_dropdown.value,
            mode=mode_dropdown.value, platform=platform, progress_callback=store_progress,
            log_callback=store_log, finish_callback=store_finish, error_callback=store_error, stop_flag=shared_state
        )
        active_downloader[0] = downloader
        threading.Thread(target=downloader.download, args=(url,), daemon=True).start()
        page.run_task(ui_update_loop)

    download_btn = ft.FilledButton("Descargar Ahora", icon=ft.Icons.DOWNLOAD, style=ft.ButtonStyle(color=ft.Colors.BLACK, bgcolor=ft.Colors.AMBER_400, padding=18), on_click=btn_click)
    stop_btn = ft.FilledButton("⛔ Detener", style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.RED_700, padding=18), on_click=lambda e: setattr(shared_state, 'stop_requested', True), visible=False)

    downloader_content = ft.Column([
        platform_nav_row,
        ft.Container(height=5),
        url_input,
        ft.Container(height=5),
        ft.Row([path_input, folder_btn], alignment=ft.MainAxisAlignment.CENTER),
        ft.Container(height=5),
        options_container,
        ft.Container(height=10),
        progress_bar,
        progress_text,
        ft.Container(height=5),
        ft.Row([download_btn, stop_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
        ft.Container(height=5),
        status_text,
        ft.Divider(height=20, color=ft.Colors.GREY_800),
        ft.Row([ft.Icon(ft.Icons.TERMINAL, size=16), ft.Text("Registro de Actividad (Logs):", size=13, weight=ft.FontWeight.W_500)]),
        ft.Container(content=logs_view, bgcolor=ft.Colors.BLACK54, padding=10, border_radius=8)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # ==========================================
    # REPRODUCTOR MULTIMEDIA & BIBLIOTECA
    # ==========================================
    # REPRODUCTOR MULTIMEDIA (UI PREMIUM)
    # ==========================================
    media_lib = MediaLibrary()
    current_media_filter = ["all"]
    scanned_media = []
    current_track_index = [0]

    playing_state = {
        'file': None, 'is_playing': False,
        'audio_ctrl': None, 'video_ctrl': None,
        'duration': 0, 'position': 0
    }

    # ── Álbum Art ──
    album_art = ft.Container(
        width=200, height=200,
        border_radius=20,
        bgcolor=ft.Colors.GREY_850,
        content=ft.Icon(ft.Icons.MUSIC_NOTE_ROUNDED, size=90, color=ft.Colors.AMBER_400),
        shadow=ft.BoxShadow(blur_radius=30, color=ft.Colors.with_opacity(0.5, ft.Colors.AMBER_700)),
        alignment=ft.Alignment(0, 0),
    )

    # ── Título y Artista ──
    now_playing_title = ft.Text(
        "Sin reproducción", size=17, weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER,
        overflow=ft.TextOverflow.ELLIPSIS, max_lines=1
    )
    now_playing_subtitle = ft.Text(
        "Selecciona una canción abajo", size=13,
        color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER
    )

    # ── Barra de Progreso ──
    progress_slider = ft.Slider(
        min=0, max=100, value=0,
        active_color=ft.Colors.AMBER_400,
        inactive_color=ft.Colors.GREY_700,
        thumb_color=ft.Colors.AMBER_300,
        expand=True,
    )
    time_start = ft.Text("0:00", size=11, color=ft.Colors.GREY_400)
    time_end   = ft.Text("0:00", size=11, color=ft.Colors.GREY_400)

    def fmt_time(secs):
        s = int(secs)
        return f"{s//60}:{s%60:02d}"

    def on_seek(e):
        if playing_state['audio_ctrl'] and playing_state['duration'] > 0:
            pos_secs = (e.control.value / 100) * playing_state['duration']
            try:
                playing_state['audio_ctrl'].seek(int(pos_secs * 1000))
            except Exception:
                pass

    progress_slider.on_change_end = on_seek

    # ── Botones de control ──
    def prev_track(e):
        items = _visible_items()
        if not items:
            return
        idx = current_track_index[0]
        current_track_index[0] = (idx - 1) % len(items)
        play_media_item(items[current_track_index[0]])

    def next_track(e):
        items = _visible_items()
        if not items:
            return
        idx = current_track_index[0]
        current_track_index[0] = (idx + 1) % len(items)
        play_media_item(items[current_track_index[0]])

    def toggle_play_pause(e=None):
        if playing_state['audio_ctrl']:
            if playing_state['is_playing']:
                playing_state['audio_ctrl'].pause()
                playing_state['is_playing'] = False
                play_pause_btn.icon = ft.Icons.PLAY_CIRCLE_ROUNDED
            else:
                playing_state['audio_ctrl'].resume()
                playing_state['is_playing'] = True
                play_pause_btn.icon = ft.Icons.PAUSE_CIRCLE_ROUNDED
            play_pause_btn.update()

    btn_prev = ft.IconButton(
        icon=ft.Icons.SKIP_PREVIOUS_ROUNDED,
        icon_size=38, icon_color=ft.Colors.WHITE,
        on_click=prev_track
    )
    play_pause_btn = ft.IconButton(
        icon=ft.Icons.PLAY_CIRCLE_ROUNDED,
        icon_size=64, icon_color=ft.Colors.AMBER_400,
        on_click=toggle_play_pause
    )
    btn_next = ft.IconButton(
        icon=ft.Icons.SKIP_NEXT_ROUNDED,
        icon_size=38, icon_color=ft.Colors.WHITE,
        on_click=next_track
    )

    # ── Control de Volumen ──
    volume_slider = ft.Slider(
        min=0, max=1, value=1,
        active_color=ft.Colors.AMBER_400,
        inactive_color=ft.Colors.GREY_700,
        thumb_color=ft.Colors.AMBER_300,
        width=140,
    )
    def on_volume_change(e):
        if playing_state['audio_ctrl']:
            try:
                playing_state['audio_ctrl'].volume = e.control.value
                playing_state['audio_ctrl'].update()
            except Exception:
                pass
    volume_slider.on_change = on_volume_change

    # ── Now Playing Card ──
    now_playing_card = ft.Container(
        content=ft.Column([
            ft.Container(content=album_art, alignment=ft.Alignment(0, 0)),
            ft.Container(height=14),
            now_playing_title,
            now_playing_subtitle,
            ft.Container(height=10),
            ft.Row([time_start, progress_slider, time_end],
                   alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=4),
            ft.Row([btn_prev, play_pause_btn, btn_next],
                   alignment=ft.MainAxisAlignment.CENTER, spacing=4),
            ft.Container(height=4),
            ft.Row([
                ft.Icon(ft.Icons.VOLUME_DOWN, color=ft.Colors.GREY_400, size=18),
                volume_slider,
                ft.Icon(ft.Icons.VOLUME_UP, color=ft.Colors.GREY_400, size=18),
            ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
        tight=True,
        ),
        bgcolor=ft.Colors.GREY_900,
        border_radius=20,
        padding=ft.Padding(18, 18, 18, 14),
        shadow=ft.BoxShadow(blur_radius=16, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
    )

    video_container = ft.Container(height=220, visible=False, border_radius=10, bgcolor=ft.Colors.BLACK)

    # ── Audio callbacks ──
    def _on_audio_duration(e):
        dur = (e.data or 0)
        try:
            playing_state['duration'] = int(dur) / 1000
            time_end.value = fmt_time(playing_state['duration'])
            time_end.update()
        except Exception:
            pass

    def _on_audio_position(e):
        try:
            pos_ms = int(e.data or 0)
            pos_s = pos_ms / 1000
            playing_state['position'] = pos_s
            dur = playing_state['duration']
            if dur > 0:
                progress_slider.value = (pos_s / dur) * 100
                time_start.value = fmt_time(pos_s)
                progress_slider.update()
                time_start.update()
        except Exception:
            pass

    def _on_audio_complete(e):
        next_track(None)

    def play_media_item(item):
        playing_state['file'] = item
        name = item['name']
        now_playing_title.value = name
        now_playing_subtitle.value = f"📁 {item['folder']}  •  {item['size_mb']} MB"
        play_pause_btn.icon = ft.Icons.PAUSE_CIRCLE_ROUNDED
        playing_state['is_playing'] = True

        # Detener audio anterior
        if playing_state['audio_ctrl'] and playing_state['audio_ctrl'] in page.overlay:
            try:
                playing_state['audio_ctrl'].pause()
                page.overlay.remove(playing_state['audio_ctrl'])
            except Exception:
                pass

        if item['is_video']:
            video_ctrl = ft.Video(
                media=ft.VideoMedia(item['path']),
                playlist=[ft.VideoMedia(item['path'])],
                autoplay=True, show_controls=True, height=220
            )
            video_container.content = video_ctrl
            video_container.visible = True
            album_art.content = ft.Icon(ft.Icons.MOVIE, size=90, color=ft.Colors.BLUE_400)
            playing_state['video_ctrl'] = video_ctrl
            playing_state['audio_ctrl'] = None
        else:
            video_container.visible = False
            album_art.content = ft.Icon(ft.Icons.MUSIC_NOTE_ROUNDED, size=90, color=ft.Colors.AMBER_400)
            audio_ctrl = ft.Audio(
                src=item['path'], autoplay=True, volume=volume_slider.value,
                on_duration_changed=_on_audio_duration,
                on_position_changed=_on_audio_position,
                on_state_changed=_on_audio_complete,
            )
            page.overlay.append(audio_ctrl)
            playing_state['audio_ctrl'] = audio_ctrl
            playing_state['video_ctrl'] = None
            playing_state['duration'] = 0
            playing_state['position'] = 0
            progress_slider.value = 0
            time_start.value = "0:00"
            time_end.value = "0:00"

        now_playing_title.update()
        now_playing_subtitle.update()
        play_pause_btn.update()
        album_art.update()
        video_container.update()
        progress_slider.update()
        page.update()

    # Highlight de canción activa en la lista
    def _visible_items():
        flt = current_media_filter[0]
        if flt == "music":
            return [m for m in scanned_media if not m['is_video']]
        elif flt == "videos":
            return [m for m in scanned_media if m['is_video']]
        elif flt == "folders":
            return scanned_media
        return scanned_media

    # ── Lista de canciones ──
    media_list_view = ft.ListView(height=280, spacing=2, auto_scroll=False)

    permission_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.SECURITY, size=36, color=ft.Colors.AMBER_400),
                ft.Text("Permisos de Almacenamiento", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("MilaDow requiere permisos para leer archivos multimedia de tu teléfono.", size=12, text_align=ft.TextAlign.CENTER, color=ft.Colors.GREY_400),
                ft.ElevatedButton("Otorgar Permisos", icon=ft.Icons.LOCK_OPEN, style=ft.ButtonStyle(color=ft.Colors.BLACK, bgcolor=ft.Colors.GREEN_400), on_click=lambda e: request_android_permissions())
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            padding=15
        ),
        visible=False
    )

    def render_media_list():
        media_list_view.controls.clear()
        flt = current_media_filter[0]
        items_to_show = _visible_items()

        if flt == "folders":
            folders = {}
            for item in scanned_media:
                f_name = item['folder']
                if f_name not in folders:
                    folders[f_name] = []
                folders[f_name].append(item)
            for f_name, f_items in folders.items():
                folder_tile = ft.ExpansionTile(
                    title=ft.Text(f"📁 {f_name} ({len(f_items)})", weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(f_items[0]['folder_path'], size=11, color=ft.Colors.GREY_400),
                    controls=[
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.VIDEO_LIBRARY if it['is_video'] else ft.Icons.MUSIC_NOTE, color=ft.Colors.AMBER_400 if not it['is_video'] else ft.Colors.BLUE_400),
                            title=ft.Text(it['name'], size=13, overflow=ft.TextOverflow.ELLIPSIS),
                            subtitle=ft.Text(f"{it['size_mb']} MB", size=11),
                            on_click=lambda e, item=it: play_media_item(item)
                        ) for it in f_items
                    ]
                )
                media_list_view.controls.append(folder_tile)
        else:
            if not items_to_show:
                permission_card.visible = True
                media_list_view.controls.append(
                    ft.Container(
                        content=ft.Text("No se encontraron archivos. Pulsa '🔍 Escanear' o otorga permisos.", size=13, color=ft.Colors.GREY_400),
                        padding=15, alignment=ft.Alignment(0, 0)
                    )
                )
            else:
                permission_card.visible = False
                for idx, it in enumerate(items_to_show):
                    is_active = playing_state['file'] == it
                    tile = ft.Container(
                        content=ft.Row([
                            ft.Icon(
                                ft.Icons.VIDEO_LIBRARY if it['is_video'] else ft.Icons.MUSIC_NOTE,
                                color=ft.Colors.BLUE_400 if it['is_video'] else ft.Colors.AMBER_400,
                                size=22
                            ),
                            ft.Column([
                                ft.Text(it['name'], size=13, overflow=ft.TextOverflow.ELLIPSIS, weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL, color=ft.Colors.AMBER_300 if is_active else ft.Colors.WHITE),
                                ft.Text(f"📁 {it['folder']}  •  {it['size_mb']} MB", size=11, color=ft.Colors.GREY_400),
                            ], spacing=2, expand=True),
                            ft.Icon(ft.Icons.EQUALIZER_ROUNDED, color=ft.Colors.AMBER_400, size=18) if is_active else ft.Container(width=18),
                        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.AMBER_400) if is_active else ft.Colors.GREY_900,
                        border_radius=10,
                        padding=ft.Padding(12, 10, 12, 10),
                        on_click=lambda e, item=it, i=idx: [current_track_index.__setitem__(0, i), play_media_item(item)],
                        ink=True,
                    )
                    media_list_view.controls.append(tile)

        if media_list_view.page:
            media_list_view.update()
        if permission_card.page:
            permission_card.update()

    def request_android_permissions():
        """Solicitar permisos nativos de Android vía canales del sistema."""
        permission_card.visible = False
        page.update()
        _request_storage_permissions()
        scan_device_media()
        page.update()

    def _request_storage_permissions():
        """Invocar el dialogo de permisos de Android via el gestor de actividades del sistema."""
        import subprocess
        is_android = os.path.exists("/storage/emulated/0")
        if not is_android:
            return
        perms = [
            "android.permission.READ_MEDIA_AUDIO",
            "android.permission.READ_MEDIA_VIDEO",
            "android.permission.READ_MEDIA_IMAGES",
            "android.permission.READ_EXTERNAL_STORAGE",
            "android.permission.WRITE_EXTERNAL_STORAGE",
        ]
        try:
            pkg = "com.jcsanmartin.miladow"
            for perm in perms:
                subprocess.run(["pm", "grant", pkg, perm], capture_output=True, timeout=3)
        except Exception:
            pass

    def scan_device_media(e=None):
        nonlocal scanned_media
        scanned_media = media_lib.scan_storage()
        render_media_list()

    def set_media_filter(flt):
        current_media_filter[0] = flt
        styles = {
            "all":     (ft.Colors.BLACK, ft.Colors.AMBER_400),
            "folders": (ft.Colors.WHITE, ft.Colors.GREY_800),
            "music":   (ft.Colors.WHITE, ft.Colors.GREY_800),
            "videos":  (ft.Colors.WHITE, ft.Colors.GREY_800),
        }
        active = (ft.Colors.BLACK, ft.Colors.AMBER_400)
        inactive = (ft.Colors.WHITE, ft.Colors.GREY_800)
        for btn, key in [(btn_filter_all,"all"),(btn_filter_folders,"folders"),(btn_filter_music,"music"),(btn_filter_videos,"videos")]:
            c, bg = active if flt == key else inactive
            btn.style = ft.ButtonStyle(color=c, bgcolor=bg)
            if btn.page:
                btn.update()
        render_media_list()

    btn_filter_all     = ft.FilledButton("🌐 Todo",         style=ft.ButtonStyle(color=ft.Colors.BLACK, bgcolor=ft.Colors.AMBER_400), on_click=lambda e: set_media_filter("all"))
    btn_filter_folders = ft.FilledButton("📁 Carpetas",     style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREY_800),  on_click=lambda e: set_media_filter("folders"))
    btn_filter_music   = ft.FilledButton("🎵 Música (MP3)", style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREY_800),  on_click=lambda e: set_media_filter("music"))
    btn_filter_videos  = ft.FilledButton("🎬 Videos (MP4)", style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREY_800),  on_click=lambda e: set_media_filter("videos"))

    filter_row = ft.Row([btn_filter_all, btn_filter_folders, btn_filter_music, btn_filter_videos], spacing=6, wrap=True, alignment=ft.MainAxisAlignment.CENTER)

    player_content = ft.Column([
        now_playing_card,
        ft.Container(height=8),
        video_container,
        ft.Row([
            ft.Text("🎧 Mi Biblioteca", size=15, weight=ft.FontWeight.BOLD),
            ft.IconButton(icon=ft.Icons.REFRESH_ROUNDED, tooltip="Escanear dispositivo", icon_color=ft.Colors.GREY_400, on_click=scan_device_media)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        filter_row,
        permission_card,
        media_list_view,
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)


    # ==========================================
    # BARRA SUPERIOR & MENÚ HAMBURGUESA
    # ==========================================
    view_title = ft.Text("Descargador Multimedia", size=18, weight=ft.FontWeight.BOLD)
    body_container = ft.Container(content=downloader_content, expand=True)

    def navigate_drawer(e):
        idx = e.control.selected_index
        page.drawer.open = False
        if idx == 0:
            view_title.value = "Descargador Multimedia"
            body_container.content = downloader_content
            page.update()
        elif idx == 1:
            view_title.value = "Reproductor Multimedia"
            body_container.content = player_content
            page.update()
            scan_device_media()

    page.drawer = ft.NavigationDrawer(
        controls=[
            ft.Container(height=20),
            ft.Row([
                ft.Icon(ft.Icons.FILE_DOWNLOAD_ROUNDED, color=ft.Colors.AMBER_400, size=32),
                ft.Text("MilaDow Menu", size=22, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(color=ft.Colors.GREY_800),
            ft.NavigationDrawerDestination(icon=ft.Icons.DOWNLOAD, label="Descargador Multimedia"),
            ft.NavigationDrawerDestination(icon=ft.Icons.HEADSET, label="Reproductor Multimedia"),
        ],
        on_change=navigate_drawer
    )

    page.appbar = ft.AppBar(
        leading=ft.IconButton(icon=ft.Icons.MENU, tooltip="Menú Principal", on_click=lambda e: setattr(page.drawer, 'open', True) or page.update()),
        title=view_title,
        center_title=True,
        bgcolor=ft.Colors.GREY_900
    )

    main_view = ft.Column([body_container], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

    page.add(splash_view, main_view)

    async def run_splash_transition():
        await asyncio.sleep(1.8)
        splash_view.visible = False
        main_view.visible = True
        rebuild_options_row()
        page.update()
        # Solicitar permisos de almacenamiento al iniciar la app en Android
        threading.Thread(target=_request_storage_permissions, daemon=True).start()

    page.run_task(run_splash_transition)

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)
