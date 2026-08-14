import flet as ft
import os
import math
from media_player import MediaLibrary

def get_player_view(page: ft.Page):
    media_lib = MediaLibrary()
    scanned_media = []
    
    # ── ESTADO DEL REPRODUCTOR ──
    playing_state = {
        'file': None, 'is_playing': False,
        'audio_ctrl': None, 'video_ctrl': None,
        'duration': 0, 'position': 0,
        'index': -1,
        'playlist': []
    }

    # Contenedor principal que alternará entre ListView y NowPlayingView
    main_container = ft.Container(expand=True)

    # ==========================================
    # COMPONENTES COMPARTIDOS
    # ==========================================
    
    def fmt_time(secs):
        if not secs or math.isnan(secs):
            return "0:00"
        s = int(secs)
        return f"{s//60}:{s%60:02d}"

    # Controles de Audio/Video invisibles inyectados a la página
    def on_audio_position(e):
        playing_state['position'] = int(e.data) / 1000.0
        update_progress_ui()

    def on_audio_duration(e):
        playing_state['duration'] = int(e.data) / 1000.0
        update_progress_ui()

    def on_audio_complete(e):
        if e.data == "completed":
            next_track()

    # ==========================================
    # VISTA NOW PLAYING (PANTALLA COMPLETA)
    # ==========================================
    
    np_title = ft.Text("Artista desconocido", size=18, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, expand=True)
    np_subtitle = ft.Text("Desconocido", size=14, color=ft.Colors.GREY_400)
    
    np_progress_slider = ft.Slider(
        min=0, max=100, value=0,
        active_color=ft.Colors.WHITE, inactive_color=ft.Colors.GREY_800, thumb_color=ft.Colors.WHITE, expand=True
    )
    np_time_start = ft.Text("0:00", size=12, color=ft.Colors.GREY_400)
    np_time_end = ft.Text("0:00", size=12, color=ft.Colors.GREY_400)

    def on_seek(e):
        if playing_state['audio_ctrl'] and playing_state['duration'] > 0:
            pos_secs = (e.control.value / 100) * playing_state['duration']
            try:
                playing_state['audio_ctrl'].seek(int(pos_secs * 1000))
            except Exception:
                pass

    np_progress_slider.on_change_end = on_seek

    np_play_btn = ft.IconButton(icon=ft.Icons.PLAY_ARROW_ROUNDED, icon_size=42, icon_color=ft.Colors.WHITE, bgcolor=ft.Colors.GREY_800, on_click=lambda e: toggle_play_pause())
    
    # Arte del álbum estilo cassette moderno
    np_album_art = ft.Container(
        width=300, height=300, border_radius=20, bgcolor=ft.Colors.GREY_800,
        content=ft.Icon(ft.Icons.ALBUM, size=150, color=ft.Colors.GREY_600),
        shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
        alignment=ft.Alignment(0, 0),
        margin=ft.Margin(0, 20, 0, 20)
    )

    now_playing_view = ft.Container(
        expand=True,
        bgcolor="#121212",
        padding=20,
        content=ft.Column([
            # Top bar
            ft.Row([
                ft.IconButton(ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED, icon_size=32, icon_color=ft.Colors.WHITE, on_click=lambda e: show_list_view()),
                ft.Row([
                    ft.IconButton(ft.Icons.CAST, icon_color=ft.Colors.WHITE),
                    ft.IconButton(ft.Icons.TUNE, icon_color=ft.Colors.WHITE),
                    ft.IconButton(ft.Icons.MORE_VERT, icon_color=ft.Colors.WHITE),
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # Album Art
            ft.Row([np_album_art], alignment=ft.MainAxisAlignment.CENTER),
            
            # Info
            ft.Row([
                ft.Column([np_title, np_subtitle], spacing=2, expand=True),
                ft.IconButton(ft.Icons.STAR_BORDER_ROUNDED, icon_size=28, icon_color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Container(height=20),
            
            # Progress
            np_progress_slider,
            ft.Row([np_time_start, np_time_end], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Container(height=10),
            
            # Controls
            ft.Row([
                ft.IconButton(ft.Icons.SHUFFLE, icon_color=ft.Colors.WHITE, icon_size=24),
                ft.IconButton(ft.Icons.SKIP_PREVIOUS_ROUNDED, icon_color=ft.Colors.WHITE, icon_size=36, on_click=lambda e: prev_track()),
                np_play_btn,
                ft.IconButton(ft.Icons.SKIP_NEXT_ROUNDED, icon_color=ft.Colors.WHITE, icon_size=36, on_click=lambda e: next_track()),
                ft.IconButton(ft.Icons.REPEAT, icon_color=ft.Colors.WHITE, icon_size=24),
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)
        ])
    )

    # ==========================================
    # VISTA DE LISTA (PRINCIPAL)
    # ==========================================

    # ── Mini Player Inferior ──
    mini_title = ft.Text("Sin reproducción", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
    mini_subtitle = ft.Text("", size=11, color=ft.Colors.WHITE70)
    mini_play_btn = ft.IconButton(ft.Icons.PLAY_ARROW_ROUNDED, icon_color=ft.Colors.WHITE, on_click=lambda e: toggle_play_pause())
    mini_progress = ft.ProgressBar(value=0, color=ft.Colors.WHITE, bgcolor=ft.Colors.TRANSPARENT, height=2)
    
    mini_player = ft.Container(
        visible=False,
        bgcolor="#6A90A4", # Color suave
        border_radius=10,
        padding=ft.Padding(10, 5, 10, 5),
        margin=ft.Margin(10, 0, 10, 10),
        on_click=lambda e: show_now_playing_view(),
        content=ft.Column([
            ft.Row([
                ft.Container(
                    width=40, height=40, border_radius=5, bgcolor=ft.Colors.GREY_800,
                    content=ft.Icon(ft.Icons.MUSIC_NOTE, size=20, color=ft.Colors.WHITE),
                ),
                ft.Column([mini_title, mini_subtitle], spacing=0, expand=True),
                mini_play_btn,
                ft.IconButton(ft.Icons.SKIP_NEXT_ROUNDED, icon_color=ft.Colors.WHITE, on_click=lambda e: next_track()),
            ], spacing=10),
            mini_progress
        ], spacing=0)
    )

    # ── Botones de navegación (Bottom Nav) ──
    bottom_nav = ft.Container(
        bgcolor="#000000", padding=10,
        content=ft.Row([
            ft.Column([ft.Icon(ft.Icons.HEADSET, color=ft.Colors.WHITE), ft.Text("Mi música", size=10, color=ft.Colors.WHITE)], spacing=2, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            ft.Column([ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINE, color=ft.Colors.GREY_600), ft.Text("Ver", size=10, color=ft.Colors.GREY_600)], spacing=2, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
        ])
    )

    list_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=15)
    
    list_view_container = ft.Container(
        expand=True,
        bgcolor="#000000",
        content=ft.Column([
            ft.Container(
                padding=ft.Padding(10, 10, 10, 0),
                content=list_container,
                expand=True
            ),
            mini_player,
            bottom_nav
        ], spacing=0)
    )

    # ==========================================
    # FUNCIONES DE REPRODUCCIÓN
    # ==========================================
    
    def show_list_view():
        main_container.content = list_view_container
        if main_container.page: main_container.update()

    def show_now_playing_view():
        main_container.content = now_playing_view
        if main_container.page: main_container.update()

    def play_media_item(item):
        if not item: return
        
        # Detener anterior
        if playing_state['audio_ctrl']:
            try:
                playing_state['audio_ctrl'].pause()
                if playing_state['audio_ctrl'] in page.overlay:
                    page.overlay.remove(playing_state['audio_ctrl'])
            except Exception: pass
            
        playing_state['file'] = item
        playing_state['is_playing'] = True
        playing_state['duration'] = 0
        playing_state['position'] = 0
        
        # Encontrar índice en playlist actual
        try:
            playing_state['index'] = playing_state['playlist'].index(item)
        except ValueError:
            playing_state['playlist'] = scanned_media
            try: playing_state['index'] = playing_state['playlist'].index(item)
            except ValueError: playing_state['index'] = 0

        # UI Updates
        name_no_ext = os.path.splitext(item['name'])[0]
        np_title.value = name_no_ext
        mini_title.value = name_no_ext
        
        if item['is_video']:
            np_subtitle.value = "Video"
            mini_subtitle.value = "Video"
            np_album_art.content = ft.Icon(ft.Icons.MOVIE, size=100, color=ft.Colors.GREY_600)
            # Todo: Para simplificar, videos se reproducen como audio en background por ahora o requerirían control de video
        else:
            np_subtitle.value = "Artista desconocido"
            mini_subtitle.value = "Artista desconocido"
            np_album_art.content = ft.Icon(ft.Icons.ALBUM, size=150, color=ft.Colors.GREY_600)

        # Crear nuevo control de audio
        audio_ctrl = ft.Audio(
            src=item['path'], autoplay=True,
            on_duration_changed=on_audio_duration,
            on_position_changed=on_audio_position,
            on_state_changed=on_audio_complete,
        )
        page.overlay.append(audio_ctrl)
        playing_state['audio_ctrl'] = audio_ctrl
        
        update_play_pause_buttons()
        mini_player.visible = True
        
        if main_container.page:
            mini_player.update()
            now_playing_view.update()
            
        # Refresh lista para highlight (opcional)
        # render_media_list()

    def toggle_play_pause():
        if playing_state['audio_ctrl']:
            if playing_state['is_playing']:
                playing_state['audio_ctrl'].pause()
                playing_state['is_playing'] = False
            else:
                playing_state['audio_ctrl'].resume()
                playing_state['is_playing'] = True
            update_play_pause_buttons()

    def update_play_pause_buttons():
        icon = ft.Icons.PAUSE_ROUNDED if playing_state['is_playing'] else ft.Icons.PLAY_ARROW_ROUNDED
        mini_play_btn.icon = icon
        np_play_btn.icon = ft.Icons.PAUSE_CIRCLE_FILLED_ROUNDED if playing_state['is_playing'] else ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED
        if mini_play_btn.page: mini_play_btn.update()
        if np_play_btn.page: np_play_btn.update()

    def update_progress_ui():
        if playing_state['duration'] > 0:
            prog = playing_state['position'] / playing_state['duration']
            mini_progress.value = prog
            np_progress_slider.value = prog * 100
            np_time_start.value = fmt_time(playing_state['position'])
            np_time_end.value = fmt_time(playing_state['duration'])
            
            # Solo actualizar si están visibles para evitar carga
            if main_container.page:
                if main_container.content == list_view_container:
                    mini_progress.update()
                else:
                    np_progress_slider.update()
                    np_time_start.update()
                    np_time_end.update()

    def prev_track():
        if not playing_state['playlist']: return
        idx = playing_state['index'] - 1
        if idx < 0: idx = len(playing_state['playlist']) - 1
        play_media_item(playing_state['playlist'][idx])

    def next_track():
        if not playing_state['playlist']: return
        idx = playing_state['index'] + 1
        if idx >= len(playing_state['playlist']): idx = 0
        play_media_item(playing_state['playlist'][idx])

    # ==========================================
    # CONSTRUCCIÓN DE LA LISTA
    # ==========================================

    def render_media_list():
        list_container.controls.clear()
        
        # 1. Search Bar & Top Buttons
        search_bar = ft.TextField(
            hint_text="Buscar canciones, listas de reprodu...",
            prefix_icon=ft.Icons.SEARCH,
            bgcolor=ft.Colors.GREY_900,
            border=ft.InputBorder.NONE,
            border_radius=20,
            height=45,
            content_padding=ft.Padding(10, 0, 10, 0)
        )
        list_container.controls.append(ft.Row([
            ft.IconButton(ft.Icons.TUNE, icon_color=ft.Colors.WHITE),
            ft.Container(search_bar, expand=True)
        ]))

        # 2. Colored Cards
        list_container.controls.append(
            ft.Row([
                ft.Container(content=ft.Column([ft.Icon(ft.Icons.FAVORITE, color=ft.Colors.WHITE), ft.Text("Favoritos", weight=ft.FontWeight.BOLD)], spacing=5),
                             bgcolor="#883355", border_radius=10, padding=10, expand=True, height=80),
                ft.Container(content=ft.Column([ft.Icon(ft.Icons.QUEUE_MUSIC, color=ft.Colors.WHITE), ft.Text("Listas de\nreproducción", weight=ft.FontWeight.BOLD, size=11)], spacing=5),
                             bgcolor="#336677", border_radius=10, padding=10, expand=True, height=80),
                ft.Container(content=ft.Column([ft.Icon(ft.Icons.ACCESS_TIME, color=ft.Colors.WHITE), ft.Text("Recientes", weight=ft.FontWeight.BOLD)], spacing=5),
                             bgcolor="#443377", border_radius=10, padding=10, expand=True, height=80),
            ], spacing=10)
        )

        # 3. Tabs
        list_container.controls.append(
            ft.Row([
                ft.Container(content=ft.Text("Artistas", color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD), bgcolor=ft.Colors.WHITE, padding=ft.Padding(15, 5, 15, 5), border_radius=20),
                ft.Text("Álbumes", color=ft.Colors.GREY_400),
                ft.Text("Carpetas", color=ft.Colors.GREY_400),
            ], spacing=20, alignment=ft.MainAxisAlignment.START)
        )

        # 4. Shuffle play
        list_container.controls.append(
            ft.Row([
                ft.Icon(ft.Icons.PLAY_CIRCLE_FILLED, color=ft.Colors.WHITE, size=32),
                ft.Text("Reproducción aleatoria", weight=ft.FontWeight.BOLD, size=14)
            ])
        )
        
        # Si no hay archivos, sugerir escaneo/permisos
        if not scanned_media:
            list_container.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.FOLDER_OFF, size=50, color=ft.Colors.GREY_800),
                        ft.Text("No se encontró música", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400),
                        ft.Text("Verifica los permisos de almacenamiento de la app en Configuración > Aplicaciones.", text_align=ft.TextAlign.CENTER, color=ft.Colors.GREY_600, size=12),
                        ft.ElevatedButton("Escanear de nuevo", on_click=lambda e: scan_device_media())
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.Alignment(0, 0), padding=40
                )
            )
            try:
                list_container.update()
            except Exception:
                pass
            return

        # 5. Lista Alfabética
        current_letter = ""
        for item in scanned_media:
            name = item['name']
            letter = name[0].upper() if name else "?"
            if not letter.isalpha(): letter = "#"
            
            if letter != current_letter:
                current_letter = letter
                list_container.controls.append(
                    ft.Text(current_letter, weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.GREY_600)
                )
            
            tile = ft.Container(
                content=ft.Row([
                    ft.Container(
                        width=45, height=45, border_radius=25, bgcolor=ft.Colors.GREY_800,
                        content=ft.Icon(ft.Icons.MUSIC_NOTE, color=ft.Colors.WHITE, size=24),
                        alignment=ft.Alignment(0, 0)
                    ),
                    ft.Column([
                        ft.Text(os.path.splitext(name)[0], size=14, weight=ft.FontWeight.W_500, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(f"{item['size_mb']} MB • {item['folder']}", size=12, color=ft.Colors.GREY_500)
                    ], spacing=2, expand=True),
                    ft.IconButton(ft.Icons.MORE_VERT, icon_color=ft.Colors.GREY_600)
                ]),
                ink=True,
                padding=ft.Padding(0, 5, 0, 5),
                on_click=lambda e, it=item: play_media_item(it)
            )
            list_container.controls.append(tile)

        # Solo actualizar si ya está montada en la página
        try:
            list_container.update()
        except Exception:
            pass  # Aún no montado — los controles ya están listos para cuando se renderice

    def scan_device_media():
        nonlocal scanned_media
        scanned_media = media_lib.scan_storage()
        # Ordenar alfabéticamente
        scanned_media.sort(key=lambda x: x['name'].lower())
        playing_state['playlist'] = scanned_media
        render_media_list()

    # Inicializar estado visual — NO llamar scan aquí, el container aún no está en la página.
    # scan_device_media() se llama desde el botón 'Escanear' o se puede agregar en page.on_mount.
    main_container.content = list_view_container
    render_media_list()  # render vacío inicial (sin archivos)

    return main_container
