import re
import os

html_path = "ClonAfish/Афиша Краснодара 2025-2026 - куда сходить в Краснодаре - мероприятия и события на сегодня, завтра, выходные _ 😋 KASSIR.RU.html"
css_dest = "web/app/original.css"

try:
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the massive style block. It starts with <style>@font-face
    start_marker = "<style>@font-face"
    end_marker = "</style>"
    start_idx = content.find(start_marker)

    if start_idx != -1:
        # Find the end of THIS style tag
        end_idx = content.find(end_marker, start_idx)
        if end_idx != -1:
            css_content = content[start_idx + len("<style>"):end_idx]
            with open(css_dest, "w", encoding="utf-8") as f:
                f.write(css_content.strip())
            print(f"CSS extracted, size: {len(css_content)} bytes")
        else:
            print("End style tag not found")
    else:
        print("Start style tag not found")
except Exception as e:
    print(f"Error extracting CSS: {e}")

# Check asset dir count
asset_dest = "web/public/original"
try:
    if os.path.exists(asset_dest):
        files = []
        for r, d, f in os.walk(asset_dest):
            for file in f:
                files.append(os.path.join(r, file))
        print(f"Assets in {asset_dest}: {len(files)} files")
    else:
        print("Asset dest not found")
except Exception as e:
    print(f"Error checking assets: {e}")
