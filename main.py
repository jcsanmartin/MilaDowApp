import flet as ft
import asyncio
import os
import json
import sys

from downloader_view import get_downloader_view
from player_view import get_player_view

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
    # El plugin de permisos flet_permission_handler fue removido temporalmente
    # debido a problemas de compatibilidad (Unknown control) en el empaquetado.

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
    # VISTAS DINÁMICAS Y NAVEGACIÓN
    # ==========================================
    view_title = ft.Text("Descargador Multimedia", size=18, weight=ft.FontWeight.BOLD)
    body_container = ft.Container(expand=True)

    def navigate_drawer(e):
        idx = e.control.selected_index
        page.drawer.open = False
        if idx == 0:
            view_title.value = "Descargador Multimedia"
            body_container.content = get_downloader_view(page)
            page.update()
        elif idx == 1:
            view_title.value = "Reproductor Multimedia"
            body_container.content = get_player_view(page)
            page.update()

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

    def open_drawer(e):
        page.drawer.open = True
        page.update()

    page.appbar = ft.AppBar(
        leading=ft.IconButton(
            icon=ft.Icons.MENU,
            tooltip="Menú Principal",
            on_click=open_drawer,
            icon_color=ft.Colors.WHITE,
        ),
        title=view_title,
        center_title=True,
        bgcolor=ft.Colors.GREY_900
    )

    main_view = ft.Column([body_container], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

    page.add(splash_view, main_view)

    async def run_splash_transition():
        # Cargar vista del descargador por defecto
        body_container.content = get_downloader_view(page)
        
        await asyncio.sleep(1.8)
        splash_view.visible = False
        main_view.visible = True
        page.update()

        # Solicitar permisos nativos en Android de manera asíncrona al iniciar
        try:
            await ph.request(fph.Permission.STORAGE)
            await ph.request(fph.Permission.AUDIO)
            await ph.request(fph.Permission.VIDEOS)
            await ph.request(fph.Permission.PHOTOS)
            await ph.request(fph.Permission.MANAGE_EXTERNAL_STORAGE)
        except Exception:
            pass

    page.run_task(run_splash_transition)

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)
