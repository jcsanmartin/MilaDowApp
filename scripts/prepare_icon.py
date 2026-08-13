import os
import shutil
from PIL import Image

src_png = r"C:\Users\Apocali\.gemini\antigravity-ide\brain\257fcd49-37ec-40ab-adec-ef321e71cc02\media__1785383751472.png"
dst_dir = r"c:\Users\Apocali\.gemini\antigravity-ide\scratch\YtDownloaderApp"

dst_png = os.path.join(dst_dir, "app_icon.png")
dst_ico = os.path.join(dst_dir, "app_icon.ico")

shutil.copy(src_png, dst_png)
print(f"Copiado {src_png} -> {dst_png}")

img = Image.open(dst_png)
img.save(dst_ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(f"Generado {dst_ico} con éxito.")
