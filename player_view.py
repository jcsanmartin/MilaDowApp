import flet as ft
import flet_permission_handler as fph
import os
import asyncio
from media_player import MediaLibrary

def get_player_view(page: ft.Page, ph: fph.PermissionHandler):
    # ==========================================
    # REPRODUCTOR MULTIMEDIA & BIBLIOTECA
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
        bgcolor=ft.Colors.GREY_800,
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
                ft.ElevatedButton("Otorgar Permisos", icon=ft.Icons.LOCK_OPEN, style=ft.ButtonStyle(color=ft.Colors.BLACK, bgcolor=ft.Colors.GREEN_400), on_click=lambda e: page.run_task(request_android_permissions))
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

    async def request_android_permissions(e=None):
        permission_card.visible = False
        page.update()
        await _request_storage_permissions()
        scan_device_media()
        page.update()

    async def _request_storage_permissions():
        try:
            await ph.request(fph.Permission.STORAGE)
            await ph.request(fph.Permission.AUDIO)
            await ph.request(fph.Permission.VIDEOS)
            await ph.request(fph.Permission.PHOTOS)
            await ph.request(fph.Permission.MANAGE_EXTERNAL_STORAGE)
        except Exception as ex:
            print(f"Error al solicitar permisos: {ex}")

    def scan_device_media(e=None):
        nonlocal scanned_media
        scanned_media = media_lib.scan_storage()
        render_media_list()

    def set_media_filter(flt):
        current_media_filter[0] = flt
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

    # Escaneo inicial al cargar el reproductor
    scan_device_media()

    return player_content
