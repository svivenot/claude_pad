#!/usr/bin/env python3
"""
Générateur d'icônes haute définition pour le Macropad Claude Code (EezBotFun v1.3).
Crée les icônes 64x64 PNG avec anti-aliasing (supersampling 128x128 -> 64x64 LANCZOS).
- Profil 1 : Choix 1 à 6, Valider (✓), Annuler (✕)
- Profil 2 : OUI, NON, OK, ESC, oui, non, Valider (✓), Annuler (✕)
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(SCRIPT_DIR, "icons")
P2_DIR = os.path.join(ICONS_DIR, "profile_2")

# Sélection automatique d'une police grasse selon l'OS
FONT_CANDIDATES = [
    # macOS
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/SFNS.ttf",
    # Linux / WSL2
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    # Windows
    "C:\\Windows\\Fonts\\arialbd.ttf",
    "C:\\Windows\\Fonts\\segoeui.ttf",
]

FONT_PATH = None
for f in FONT_CANDIDATES:
    if os.path.exists(f):
        FONT_PATH = f
        break


def get_font(size: int):
    if FONT_PATH:
        try:
            return ImageFont.truetype(FONT_PATH, size)
        except Exception:
            pass
    return ImageFont.load_default()


def create_badge_base(bg_start, bg_end, border_color):
    """Crée un disque circulaire 128x128 avec dégradé vertical et bordure."""
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r = 58
    cx, cy = 64, 64
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if dist <= r:
                t = (y - (cy - r)) / (2 * r)
                cr = int(bg_start[0] * (1 - t) + bg_end[0] * t)
                cg = int(bg_start[1] * (1 - t) + bg_end[1] * t)
                cb = int(bg_start[2] * (1 - t) + bg_end[2] * t)
                if dist > r - 4:
                    draw.point((x, y), fill=border_color + (255,))
                else:
                    draw.point((x, y), fill=(cr, cg, cb, 255))
    return img, draw


def make_text_icon(text, bg_start, bg_end, border_color, font_size=72):
    img, draw = create_badge_base(bg_start, bg_end, border_color)
    font = get_font(font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    tx = (128 - w) / 2 - bbox[0]
    ty = (128 - h) / 2 - bbox[1] - 2
    draw.text((tx + 2, ty + 2), text, font=font, fill=(0, 0, 0, 90))
    draw.text((tx, ty), text, font=font, fill=(255, 255, 255, 255))
    return img.resize((64, 64), Image.Resampling.LANCZOS)


def make_check_icon():
    img, draw = create_badge_base((34, 197, 94), (22, 163, 74), (134, 239, 172))
    pts_shadow = [(36, 66), (54, 84), (92, 46)]
    draw.line(pts_shadow, fill=(0, 0, 0, 80), width=15, joint="curve")
    pts_main = [(35, 64), (53, 82), (91, 44)]
    draw.line(pts_main, fill=(255, 255, 255, 255), width=15, joint="curve")
    return img.resize((64, 64), Image.Resampling.LANCZOS)


def make_cross_icon():
    img, draw = create_badge_base((239, 68, 68), (220, 38, 38), (252, 165, 165))
    draw.line([(40, 42), (88, 90)], fill=(0, 0, 0, 80), width=15)
    draw.line([(40, 90), (88, 42)], fill=(0, 0, 0, 80), width=15)
    draw.line([(39, 40), (87, 88)], fill=(255, 255, 255, 255), width=15)
    draw.line([(39, 88), (87, 40)], fill=(255, 255, 255, 255), width=15)
    return img.resize((64, 64), Image.Resampling.LANCZOS)


def generate_all_icons(copy_to_device=True):
    os.makedirs(ICONS_DIR, exist_ok=True)
    os.makedirs(P2_DIR, exist_ok=True)

    # 1. Profil 1 (Choix 1..6 + Valider/Annuler)
    p1 = {
        1: make_text_icon("1", (14, 165, 233), (2, 132, 199), (56, 189, 248), 72),
        2: make_text_icon("2", (139, 92, 246), (109, 40, 217), (167, 139, 250), 72),
        3: make_text_icon("3", (245, 158, 11), (217, 119, 6), (252, 211, 77), 72),
        4: make_text_icon("4", (16, 185, 129), (5, 150, 105), (110, 231, 183), 72),
        5: make_text_icon("5", (236, 72, 153), (219, 39, 119), (244, 114, 182), 72),
        6: make_text_icon("6", (99, 102, 241), (79, 70, 229), (129, 140, 248), 72),
        7: make_check_icon(),
        8: make_cross_icon(),
    }

    # 2. Profil 2 (OUI / NON)
    p2 = {
        1: make_text_icon("OUI", (34, 197, 94), (22, 163, 74), (134, 239, 172), 42),
        2: make_text_icon("NON", (239, 68, 68), (220, 38, 38), (252, 165, 165), 42),
        3: make_text_icon("OK", (59, 130, 246), (37, 99, 235), (147, 197, 253), 46),
        4: make_text_icon("ESC", (245, 158, 11), (217, 119, 6), (252, 211, 77), 38),
        5: make_text_icon("oui", (16, 185, 129), (5, 150, 105), (110, 231, 183), 44),
        6: make_text_icon("non", (244, 63, 94), (225, 29, 72), (254, 205, 211), 44),
        7: make_check_icon(),
        8: make_cross_icon(),
    }

    print("[*] Enregistrement local des icônes...")
    for k, img in p1.items():
        img.save(os.path.join(ICONS_DIR, f"key_{k}.png"))
    for k, img in p2.items():
        img.save(os.path.join(P2_DIR, f"key_{k}.png"))

    # Copie sur le Macropad si connecté en lecteur de masse USB
    device_mounts = [
        "/Volumes/EEZBOTFUN",  # macOS
        "/media/EEZBOTFUN",    # Linux
        "/mnt/d", "/mnt/e", "/mnt/f"  # WSL2 Windows mounts
    ]
    if copy_to_device:
        for m in device_mounts:
            app_icons = os.path.join(m, "app_icons")
            if os.path.exists(app_icons):
                print(f"[*] Volume Macropad détecté sur {m}, installation des icônes...")
                for k, img in p1.items():
                    img.save(os.path.join(app_icons, f"profile_1_key_{k}.png"))
                    img.save(os.path.join(app_icons, f"profile_3_key_{k}.png"))
                for k, img in p2.items():
                    img.save(os.path.join(app_icons, f"profile_2_key_{k}.png"))
                print(f"[OK] Icônes synchronisées avec {m}/app_icons !")
                break

    print("[OK] Génération des icônes terminée avec succès !")


if __name__ == "__main__":
    generate_all_icons()
