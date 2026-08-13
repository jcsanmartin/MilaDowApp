import os
import sys
import subprocess

def main():
    print("=== Compilador de MilaDow ===")
    
    # 1. Instalar PyInstaller si no está instalado
    try:
        import PyInstaller
    except ImportError:
        print("[+] Instalando PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # Cerrar procesos MilaDow.exe si están abiertos para evitar error de archivo bloqueado
    try:
        subprocess.run(["taskkill", "/F", "/IM", "MilaDow.exe"], capture_output=True)
    except Exception:
        pass

    # 2. Comando de compilación con PyInstaller
    print("[+] Compilando MilaDow.exe con icono personalizado...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name=MilaDow",
        "--icon=app_icon.ico",
        "--add-data=app_icon.png;.",
        "--add-data=app_icon.ico;.",
        "--collect-all=flet",
        "--collect-all=yt_dlp",
        "--collect-all=imageio_ffmpeg",
        "main.py"
    ]
    
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("[-] Error durante la compilación.")
        return

    print("[+] Compilación completada con éxito.")
    
    # 3. Copiar el ejecutable MilaDow.exe directamente al Escritorio para que sea portátil
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    exe_dist = os.path.abspath(os.path.join("dist", "MilaDow.exe"))
    exe_desktop = os.path.join(desktop, "MilaDow.exe")
    shortcut_lnk = os.path.join(desktop, "MilaDow.lnk")

    # Eliminar el acceso directo viejo .lnk si existe para evitar confusión
    if os.path.exists(shortcut_lnk):
        try:
            os.remove(shortcut_lnk)
        except Exception:
            pass

    if os.path.exists(exe_dist):
        import shutil
        try:
            shutil.copy2(exe_dist, exe_desktop)
            print(f"[+] EXITO! Se ha copiado 'MilaDow.exe' directamente a tu Escritorio:")
            print(f"    -> {exe_desktop}")
            print("\n--- COMO COMPARTIR CON TU AMIGO ---")
            print("1. Copia el archivo 'MilaDow.exe' que ahora esta en tu Escritorio.")
            print("2. Enviaselo a tu amigo (por Google Drive, Telegram, USB, Discord, etc.).")
            print("3. Tu amigo NO necesita tener Python instalado. Solo hace doble clic en 'MilaDow.exe' y listo.")
        except Exception as e:
            print(f"[-] Error al copiar a Escritorio: {e}")

if __name__ == "__main__":
    main()
