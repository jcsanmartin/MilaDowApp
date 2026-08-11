import flet as ft
import threading
import asyncio
import os
import time
import json
import sys
from downloader import MediaDownloader

# Obtener ruta base (funciona tanto en desarrollo como en ejecutable PyInstaller)
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
    page.title = "MilaDow - Media Downloader (YouTube & TikTok)"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.spacing = 10
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.START

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
                ft.Text("Tu descargador multimedia rápido y confiable", size=14, color=ft.Colors.GREY_400),
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
    # CONTROLES PRINCIPALES
    # ==========================================
    header_logo = ft.Image(src=ICON_PNG, width=44, height=44, fit="contain", border_radius=8) \
        if os.path.exists(ICON_PNG) else ft.Icon(ft.Icons.FILE_DOWNLOAD_ROUNDED, color=ft.Colors.AMBER_400, size=36)

    platform_selector = ft.SegmentedButton(
        segments=[
            ft.Segment(value="youtube", label=ft.Text("YouTube"), icon=ft.Icon(ft.Icons.PLAY_CIRCLE_FILL)),
            ft.Segment(value="tiktok", label=ft.Text("TikTok"), icon=ft.Icon(ft.Icons.MUSIC_NOTE)),
            ft.Segment(value="facebook", label=ft.Text("FB"), icon=ft.Icon(ft.Icons.FACEBOOK)),
            ft.Segment(value="spotify", label=ft.Text("Spotify"), icon=ft.Icon(ft.Icons.HEADSET)),
        ],
        selected={"youtube"},
        allow_multiple_selection=False,
    )

    url_input = ft.TextField(
        label="URL de YouTube (Video o Playlist)",
        hint_text="https://www.youtube.com/watch?v=...",
        expand=True,
        prefix_icon=ft.Icons.LINK
    )

    # Lista de ubicaciones predefinidas en Android / Móvil
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
            ft.ListTile(
                leading=ft.Icon(ft.Icons.DOWNLOAD),
                title=ft.Text("Carpeta Descargas"),
                subtitle=ft.Text("Download/MilaDow"),
                on_click=lambda e: set_folder(android_downloads)
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.MUSIC_NOTE),
                title=ft.Text("Carpeta Música"),
                subtitle=ft.Text("Music/MilaDow"),
                on_click=lambda e: set_folder(android_music)
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.MOVIE),
                title=ft.Text("Carpeta Películas/Videos"),
                subtitle=ft.Text("Movies/MilaDow"),
                on_click=lambda e: set_folder(android_movies)
            ),
        ], height=220, tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: setattr(folder_dialog, 'open', False) or page.update())
        ]
    )
    page.overlay.append(folder_dialog)

    def pick_folder(e):
        folder_dialog.open = True
        page.update()

    folder_btn = ft.IconButton(icon=ft.Icons.FOLDER_OPEN, tooltip="Seleccionar carpeta", on_click=pick_folder)

    mode_dropdown = ft.Dropdown(
        label="Modo de Descarga",
        options=[
            ft.dropdown.Option("single", text="🎵 Un solo video"),
            ft.dropdown.Option("playlist", text="📋 Playlist completa"),
        ],
        value="single",
        width=210,
    )

    format_dropdown = ft.Dropdown(
        label="Formato",
        options=[
            ft.dropdown.Option("mp4", text="🎬 MP4 (Video)"),
            ft.dropdown.Option("mp3", text="🎧 MP3 (Audio)"),
        ],
        value="mp4",
        width=180,
    )

    quality_dropdown = ft.Dropdown(
        label="Calidad",
        options=[
            ft.dropdown.Option("1080p"),
            ft.dropdown.Option("720p"),
            ft.dropdown.Option("480p"),
            ft.dropdown.Option("360p"),
        ],
        value="720p",
        width=150,
    )

    spotify_client_id_input = ft.TextField(
        label="Spotify Client ID",
        hint_text="Ingresa tu Client ID (opcional)",
        width=380,
        visible=False,
    )

    spotify_client_secret_input = ft.TextField(
        label="Spotify Client Secret",
        hint_text="Ingresa tu Client Secret (opcional)",
        width=380,
        password=True,
        visible=False,
    )

    playlist_limit_input = ft.TextField(
        label="Número de videos a descargar",
        value="10",
        width=240,
        keyboard_type=ft.KeyboardType.NUMBER,
        prefix_icon=ft.Icons.NUMBERS,
        hint_text="Ej: 10, 25, 50...",
    )

    cookie_browser_dropdown = ft.Dropdown(
        label="🍪 Cookies del Navegador",
        options=[
            ft.dropdown.Option("none", text="Sin cookies"),
            ft.dropdown.Option("chrome", text="Google Chrome"),
            ft.dropdown.Option("edge", text="Microsoft Edge"),
            ft.dropdown.Option("firefox", text="Mozilla Firefox"),
            ft.dropdown.Option("opera", text="Opera"),
            ft.dropdown.Option("brave", text="Brave"),
            ft.dropdown.Option("file", text="📄 Archivo cookies.txt"),
        ],
        value="none",
        width=220,
        tooltip="Usa cookies si el video de TikTok es privado/restringido"
    )

    cookies_file_path = ft.TextField(
        label="Archivo cookies.txt",
        hint_text="Ruta al archivo cookies.txt...",
        width=300,
        prefix_icon=ft.Icons.DESCRIPTION,
        read_only=True
    )

    cookies_file_btn = ft.IconButton(icon=ft.Icons.FOLDER_OPEN, tooltip="Archivos cookies.txt", on_click=lambda e: None)

    # Contenedor dinámico que se reconstruye cuando cambia la plataforma o modo
    options_container = ft.Column(
        controls=[],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
    )

    def get_current_platform():
        if isinstance(platform_selector.selected, set) and len(platform_selector.selected) > 0:
            return list(platform_selector.selected)[0]
        return "youtube"

    def rebuild_options_row(is_tiktok_override=None):
        """Reconstruye dinámicamente la sección de opciones según la plataforma y modo actuales."""
        current_platform = get_current_platform()
        is_tiktok = current_platform == "tiktok"
        is_facebook = current_platform == "facebook"
        is_spotify = current_platform == "spotify"
        is_youtube = current_platform == "youtube"
        is_playlist = (mode_dropdown.value == "playlist") and is_youtube
        is_file_cookie = (is_tiktok or is_facebook) and (cookie_browser_dropdown.value == "file")
        use_cookies = is_tiktok or is_facebook

        # Actualizar label/hint de URL
        url_labels = {
            "youtube":  ("URL de YouTube (Video o Playlist)", "https://www.youtube.com/watch?v=..."),
            "tiktok":   ("URL de TikTok (Video)", "https://www.tiktok.com/@usuario/video/..."),
            "facebook": ("URL de Facebook (Video)", "https://www.facebook.com/watch?v=..."),
            "spotify":  ("URL de Spotify (Canción o Playlist)", "https://open.spotify.com/track/..."),
        }
        url_input.label, url_input.hint_text = url_labels.get(current_platform, url_labels["youtube"])

        controls = []

        if is_spotify:
            controls.append(
                ft.Text("📌 Credenciales de Spotify (opcional)", size=11, color=ft.Colors.GREY_400, italic=True)
            )
            controls.append(spotify_client_id_input)
            controls.append(spotify_client_secret_input)
            spotify_client_id_input.visible = True
            spotify_client_secret_input.visible = True
        else:
            spotify_client_id_input.visible = False
            spotify_client_secret_input.visible = False

            row1_items = []
            if is_youtube:
                row1_items.append(mode_dropdown)
            row1_items.append(format_dropdown)
            if is_youtube:
                quality_dropdown.disabled = (format_dropdown.value == "mp3")
                row1_items.append(quality_dropdown)
            if use_cookies:
                row1_items.append(cookie_browser_dropdown)
            controls.append(ft.Row(row1_items, spacing=8, alignment=ft.MainAxisAlignment.CENTER, wrap=True))

            if is_facebook:
                controls.append(
                    ft.Text("ℹ️ Facebook: pega el enlace del video público.", size=11, color=ft.Colors.BLUE_200, italic=True, text_align=ft.TextAlign.CENTER)
                )

            if is_playlist:
                controls.append(
                    ft.Row([ft.Text("📋 Límite de playlist:", size=12), playlist_limit_input], spacing=8, alignment=ft.MainAxisAlignment.CENTER)
                )

            if is_file_cookie:
                controls.append(
                    ft.Row([cookies_file_path, cookies_file_btn], spacing=5, alignment=ft.MainAxisAlignment.CENTER)
                )

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
            mode_dropdown.options = [
                ft.dropdown.Option("single", text="🎵 Canción"),
                ft.dropdown.Option("playlist", text="📋 Playlist"),
            ]
            mode_dropdown.value = "single"
        else:  # youtube
            mode_dropdown.options = [
                ft.dropdown.Option("single", text="🎵 Video individual"),
                ft.dropdown.Option("playlist", text="📋 Playlist completa"),
            ]
        rebuild_options_row()

    platform_selector.on_change = on_platform_change

    # Asignar on_change después de definir rebuild_options_row
    mode_dropdown.on_change = lambda e: rebuild_options_row()
    format_dropdown.on_change = lambda e: rebuild_options_row()
    cookie_browser_dropdown.on_change = lambda e: rebuild_options_row()

    # ==========================================
    # ESTADO COMPARTIDO Y CONTROL DE DESCARGA
    # ==========================================
    progress_bar = ft.ProgressBar(width=500, value=0, visible=False, color=ft.Colors.AMBER_400)
    progress_text = ft.Text("0%", color=ft.Colors.GREY_300)
    status_text = ft.Text("Listo para descargar.", color=ft.Colors.AMBER_200, weight=ft.FontWeight.W_500)
    logs_view = ft.ListView(height=140, spacing=5, auto_scroll=True)

    shared_state = {
        'percent': 0.0,
        'speed': '',
        'eta': '',
        'logs': [],
        'finished': False,
        'error': None,
        'downloading': False,
        'stop_requested': False,
    }

    active_downloader = [None]  # lista para poder mutar desde closures

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
                percent = shared_state['percent']
                speed = shared_state['speed']
                eta = shared_state['eta']

                progress_bar.value = percent
                progress_text.value = f"{int(percent * 100)}% - Vel: {speed} - Faltan: {eta}"

                while shared_state['logs']:
                    msg = shared_state['logs'].pop(0)
                    logs_view.controls.append(ft.Text(msg, size=12))
                    if len(logs_view.controls) > 60:
                        logs_view.controls.pop(0)

                if shared_state['stop_requested']:
                    status_text.value = "⛔ Descarga cancelada por el usuario."
                    progress_bar.value = 0
                    download_btn.disabled = False
                    download_btn.visible = True
                    stop_btn.visible = False
                    logs_view.controls.append(ft.Text("⛔ Descarga detenida.", color=ft.Colors.ORANGE_400, size=12))
                    page.update()
                    break

                if shared_state['finished']:
                    progress_bar.value = 1.0
                    progress_text.value = "100%"
                    status_text.value = "¡Descarga Completada!"
                    download_btn.disabled = False
                    download_btn.visible = True
                    stop_btn.visible = False
                    logs_view.controls.append(ft.Text("¡Descarga completada exitosamente!", color=ft.Colors.GREEN_400, size=12))
                    page.update()
                    break

                if shared_state['error']:
                    status_text.value = "Error en la descarga."
                    download_btn.disabled = False
                    download_btn.visible = True
                    stop_btn.visible = False
                    logs_view.controls.append(ft.Text(f"Error: {shared_state['error']}", color=ft.Colors.RED_400, size=12))
                    page.update()
                    break

                page.update()
                await asyncio.sleep(0.8)
            except Exception:
                # Si la sesión se destruye al cerrar la ventana, salimos del bucle limpiamente
                break

        shared_state['downloading'] = False

    def btn_click(e):
        url = url_input.value.strip()
        out_dir = path_input.value.strip()
        platform = get_current_platform()
        is_tiktok = platform == "tiktok"
        is_facebook = platform == "facebook"
        platform_name = {"tiktok": "TikTok", "youtube": "YouTube", "spotify": "Spotify", "facebook": "Facebook"}[platform]

        if not url:
            status_text.value = f"Por favor ingresa una URL válida de {platform_name}."
            page.update()
            return

        if not out_dir:
            status_text.value = "Por favor selecciona una carpeta de destino primero."
            page.update()
            return

        playlist_limit = 50
        if platform == "youtube" and mode_dropdown.value == "playlist":
            try:
                playlist_limit = int(playlist_limit_input.value.strip())
                if playlist_limit <= 0:
                    playlist_limit = 50
            except ValueError:
                playlist_limit = 50

        save_config({"last_folder": out_dir})

        # Reset de estado
        shared_state['percent'] = 0.0
        shared_state['speed'] = ''
        shared_state['eta'] = ''
        shared_state['logs'] = []
        shared_state['finished'] = False
        shared_state['error'] = None
        shared_state['downloading'] = True
        shared_state['stop_requested'] = False

        download_btn.disabled = True
        download_btn.visible = False
        stop_btn.visible = True
        status_text.value = f"Iniciando descarga desde {platform_name}..."
        progress_bar.visible = True
        progress_bar.value = 0
        progress_text.value = "0%"
        logs_view.controls.clear()
        page.update()

        # Determinar cookies (TikTok y Facebook las soportan)
        cookies_browser = None
        cookies_file = None
        if (is_tiktok or is_facebook) and cookie_browser_dropdown.value:
            if cookie_browser_dropdown.value == "file":
                cookies_file = cookies_file_path.value.strip() if cookies_file_path.value else None
            elif cookie_browser_dropdown.value != "none":
                cookies_browser = cookie_browser_dropdown.value

        downloader = MediaDownloader(
            output_dir=out_dir,
            format_type=format_dropdown.value,
            quality=quality_dropdown.value,
            mode="single" if (is_tiktok or is_facebook) else mode_dropdown.value,
            playlist_limit=playlist_limit,
            platform=platform,
            cookies_from_browser=cookies_browser,
            cookies_file=cookies_file,
            spotify_client_id=spotify_client_id_input.value.strip() if spotify_client_id_input.value else None,
            spotify_client_secret=spotify_client_secret_input.value.strip() if spotify_client_secret_input.value else None,
            progress_callback=store_progress,
            log_callback=store_log,
            finish_callback=store_finish,
            error_callback=store_error,
            stop_flag=shared_state,
        )
        active_downloader[0] = downloader

        thread = threading.Thread(target=downloader.download, args=(url,), daemon=True)
        thread.start()
        page.run_task(ui_update_loop)

    def stop_click(e):
        shared_state['stop_requested'] = True
        status_text.value = "⛔ Deteniendo descarga..."
        stop_btn.disabled = True
        page.update()

    download_btn = ft.FilledButton(
        "Descargar Ahora",
        icon=ft.Icons.DOWNLOAD,
        style=ft.ButtonStyle(
            color=ft.Colors.BLACK,
            bgcolor=ft.Colors.AMBER_400,
            padding=18,
        ),
        on_click=btn_click
    )

    stop_btn = ft.FilledButton(
        "⛔ Detener Descarga",
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_700,
            padding=18,
        ),
        on_click=stop_click,
        visible=False,
    )

    main_view = ft.Column(
        [
            ft.Row(
                [header_logo, ft.Text("MilaDow", size=32, weight=ft.FontWeight.BOLD)],
                alignment=ft.MainAxisAlignment.CENTER
            ),
            ft.Text("Tu descargador multimedia (YouTube, TikTok & Spotify)", size=13, color=ft.Colors.GREY_400),
            ft.Container(height=5),
            platform_selector,
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
            ft.Row(
                [download_btn, stop_btn],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=15,
            ),
            ft.Container(height=5),
            status_text,
            ft.Divider(height=20, color=ft.Colors.GREY_800),
            ft.Row([ft.Icon(ft.Icons.TERMINAL, size=16), ft.Text("Registro de Actividad (Logs):", size=13, weight=ft.FontWeight.W_500)]),
            ft.Container(
                content=logs_view,
                bgcolor=ft.Colors.BLACK54,
                padding=10,
                border_radius=8
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        visible=False
    )

    page.add(splash_view, main_view)

    async def run_splash_transition():
        await asyncio.sleep(1.8)
        splash_view.visible = False
        main_view.visible = True
        rebuild_options_row()
        page.update()

    page.run_task(run_splash_transition)

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)
