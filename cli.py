#!/usr/bin/env python3
"""
CLI interactif pour piloter le Macropad EezBotFun v1.3.
Permet de contrôler l'écran (LCD 480x320) et les 8 LEDs RGB par le port série.
"""

import argparse
import datetime
import math
import subprocess
import sys
import time
from macropad import EezBotFun

try:
    import psutil
except ImportError:
    psutil = None


def cmd_text(args):
    with EezBotFun(port=args.port) as pad:
        print(f"Affichage sur {pad.port_name}...")
        led_list = None
        if args.led_color:
            led_list = [args.led_color] * 8

        pad.display_text(
            text=args.message,
            x=args.x,
            y=args.y,
            w=args.w,
            h=args.h,
            fg=args.fg,
            bg=args.bg,
            align=args.align,
            clear_canvas=not args.append,
            fullscreen=args.fullscreen,
            border=args.border,
            border_color=args.border_color,
            border_radius=args.border_radius,
            leds=led_list,
        )
        print("Message envoyé !")


def cmd_leds(args):
    colors = args.colors
    # Si moins de 8 couleurs fournies, on complète avec la dernière ou #000000
    if len(colors) == 1:
        colors = colors * 8
    elif len(colors) < 8:
        colors = colors + ["#000000"] * (8 - len(colors))
    colors = colors[:8]

    with EezBotFun(port=args.port) as pad:
        print(f"Configuration des LEDs : {colors}")
        pad.set_leds(colors, on=not args.off)
        print("LEDs mises à jour !")


def cmd_rainbow(args):
    print("Animation Rainbow démarrée sur les 8 touches (Ctrl+C pour quitter)...")
    colors_base = [
        (255, 0, 0),
        (255, 127, 0),
        (255, 255, 0),
        (0, 255, 0),
        (0, 240, 255),
        (0, 0, 255),
        (138, 43, 226),
        (255, 0, 127),
    ]

    def hsv_to_hex(h, s=1.0, v=1.0):
        # h: 0..360
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        if 0 <= h < 60:
            r, g, b = c, x, 0
        elif 60 <= h < 120:
            r, g, b = x, c, 0
        elif 120 <= h < 180:
            r, g, b = 0, c, x
        elif 180 <= h < 240:
            r, g, b = 0, x, c
        elif 240 <= h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        return f"#{int((r+m)*255):02X}{int((g+m)*255):02X}{int((b+m)*255):02X}"

    with EezBotFun(port=args.port) as pad:
        offset = 0
        try:
            while True:
                keys = [hsv_to_hex((offset + i * 45) % 360) for i in range(8)]
                pad.set_leds(keys)
                offset = (offset + 15) % 360
                time.sleep(0.08)
        except KeyboardInterrupt:
            print("\nAnimation stoppée.")


def cmd_blink(args):
    print(f"Lancement du clignotement des LEDs ({args.cycles} cycles, couleur: {args.color})...")
    with EezBotFun(port=args.port) as pad:
        color = args.color
        for i in range(args.cycles):
            print(f"Cycle {i+1}: ON")
            pad.set_leds([color] * 8, on=True)
            time.sleep(args.speed)
            print(f"Cycle {i+1}: OFF")
            pad.set_leds(["#000000"] * 8, on=False)
            time.sleep(args.speed)
        print("Clignotement terminé !")


def cmd_monitor(args):
    if not psutil:
        print("Erreur: le module 'psutil' est requis pour le moniteur.")
        return

    print("Démarrage du Dashboard Système (Ctrl+C pour quitter)...")
    with EezBotFun(port=args.port) as pad:
        # Configuration de la grille
        # 3 lignes : En-tête (40px), Métriques (220px), Footer (40px)
        # 4 colonnes
        pad.setup_grid(
            cols=["*", "*", "*", "*"],
            rows=["45", "*", "45"],
            gap=6,
            pad=8,
            fullscreen=True,
            widgets=[
                {
                    "id": 0,
                    "type": "text",
                    "row": 0,
                    "col": 0,
                    "col_span": 2,
                    "align": "LEFT",
                    "text": "{settings} Macropad Monitor",
                    "fg": "#89B4FA",
                },
                {
                    "id": 1,
                    "type": "text",
                    "row": 0,
                    "col": 2,
                    "col_span": 2,
                    "align": "RIGHT",
                    "text": "{wifi} Connecté",
                    "fg": "#A6E3A1",
                },
                {
                    "id": 2,
                    "type": "text",
                    "row": 1,
                    "col": 0,
                    "col_span": 2,
                    "align": "CENTER",
                    "text": "CPU: ...%",
                    "fg": "#FAB387",
                    "border": 1,
                    "border_color": "#45475A",
                    "border_radius": 8,
                },
                {
                    "id": 3,
                    "type": "text",
                    "row": 1,
                    "col": 2,
                    "col_span": 2,
                    "align": "CENTER",
                    "text": "RAM: ...%",
                    "fg": "#F38BA8",
                    "border": 1,
                    "border_color": "#45475A",
                    "border_radius": 8,
                },
                {
                    "id": 4,
                    "type": "text",
                    "row": 2,
                    "col": 0,
                    "col_span": 4,
                    "align": "CENTER",
                    "text": "Heure: --:--:--",
                    "fg": "#CDD6F4",
                },
            ],
        )

        try:
            while True:
                cpu = psutil.cpu_percent(interval=1.0)
                ram = psutil.virtual_memory().percent
                now_str = datetime.datetime.now().strftime("%H:%M:%S - %d/%m/%Y")

                pad.update_grid_widget(2, f"CPU\n{cpu:.1f} %", fg="#FAB387")
                pad.update_grid_widget(3, f"RAM\n{ram:.1f} %", fg="#F38BA8")
                pad.update_grid_widget(4, f"{now_str}", fg="#CDD6F4")

                # Jauge LED pour le CPU : nombre de touches allumées selon le % CPU
                # 8 touches -> 12.5% par touche
                active_keys = min(8, max(0, int(round(cpu / 12.5))))
                led_colors = []
                for i in range(8):
                    if i < active_keys:
                        # Vert -> Jaune -> Rouge
                        if i < 4:
                            led_colors.append("#00FF00")
                        elif i < 6:
                            led_colors.append("#FFFF00")
                        else:
                            led_colors.append("#FF0000")
                    else:
                        led_colors.append("#111111")
                pad.set_leds(led_colors)

        except KeyboardInterrupt:
            print("\nArrêt du moniteur...")
            pad.stop_custom_display()
            print("Mode normal restauré.")


def cmd_stop(args):
    with EezBotFun(port=args.port) as pad:
        print("Restauration du mode normal du Macropad...")
        pad.stop_custom_display()
        print("Mode normal restauré !")


def cmd_web(args):
    port = args.web_port
    print(f"Lancement du serveur Web Configurator sur http://localhost:{port}")
    print("Ouvrez Chrome, Edge ou Brave et allez sur http://localhost:" + str(port))
    print("Cliquez ensuite sur 'Connect' pour associer le Macropad.")
    subprocess.run([
        sys.executable, "-m", "http.server", str(port),
        "-d", "8-key-macropad/web-config"
    ])


def main():
    parser = argparse.ArgumentParser(description="CLI de contrôle pour EezBotFun v1.3")
    parser.add_argument("--port", "-p", help="Port série (par défaut détecté automatiquement)")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Commande 'text'
    p_text = subparsers.add_parser("text", help="Afficher du texte sur l'écran LCD")
    p_text.add_argument("message", help="Texte à afficher (supporte {ok}, {wifi}, etc.)")
    p_text.add_argument("--x", type=int, default=10)
    p_text.add_argument("--y", type=int, default=60)
    p_text.add_argument("--w", type=int, default=460)
    p_text.add_argument("--h", type=int, default=180)
    p_text.add_argument("--fg", default="#FFFFFF", help="Couleur texte (#RRGGBB)")
    p_text.add_argument("--bg", default="#1E1E2E", help="Couleur fond (#RRGGBB)")
    p_text.add_argument("--align", default="CENTER", choices=["LEFT", "CENTER", "RIGHT", "AUTO"])
    p_text.add_argument("--border", type=int, default=2)
    p_text.add_argument("--border-color", default="#89B4FA")
    p_text.add_argument("--border-radius", type=int, default=10)
    p_text.add_argument("--fullscreen", action="store_true", default=True)
    p_text.add_argument("--append", action="store_true", help="Ne pas effacer l'écran")
    p_text.add_argument("--led-color", help="Couleur uniforme pour les 8 LEDs")
    p_text.set_defaults(func=cmd_text)

    # Commande 'leds'
    p_leds = subparsers.add_parser("leds", help="Contrôler les 8 LEDs sous les touches")
    p_leds.add_argument("colors", nargs="+", help="1 à 8 couleurs hex (#RRGGBB)")
    p_leds.add_argument("--off", action="store_true", help="Éteindre les LEDs")
    p_leds.set_defaults(func=cmd_leds)

    # Commande 'rainbow'
    p_rainbow = subparsers.add_parser("rainbow", help="Animation arc-en-ciel sur les 8 touches")
    p_rainbow.set_defaults(func=cmd_rainbow)

    # Commande 'blink'
    p_blink = subparsers.add_parser("blink", help="Faire clignoter les 8 LEDs")
    p_blink.add_argument("--cycles", type=int, default=5, help="Nombre de cycles (defaut: 5)")
    p_blink.add_argument("--color", default="#00FF88", help="Couleur du clignotement (defaut: #00FF88)")
    p_blink.add_argument("--speed", type=float, default=0.3, help="Vitesse en secondes (defaut: 0.3)")
    p_blink.set_defaults(func=cmd_blink)

    # Commande 'monitor'
    p_monitor = subparsers.add_parser("monitor", help="Dashboard système en direct (CPU, RAM, Horloge, Jauge LED)")
    p_monitor.set_defaults(func=cmd_monitor)

    # Commande 'stop'
    p_stop = subparsers.add_parser("stop", help="Quitter le mode personnalisé et restaurer l'affichage normal")
    p_stop.set_defaults(func=cmd_stop)

    # Commande 'web'
    p_web = subparsers.add_parser("web", help="Lancer le configurateur visuel officiel dans le navigateur")
    p_web.add_argument("--web-port", type=int, default=8080)
    p_web.set_defaults(func=cmd_web)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
