"""
EezBotFun v1.3 Macropad Controller
Supporte l'interaction avec l'écran (LCD 480x320) et les 8 LEDs RGB via le port série USB CDC.
Protocole : 'cus' (Customised Display Protocol) et 'ebf' (Configuration).
"""

import json
import os
import struct
import sys
import time
from typing import Dict, List, Optional, Union
import serial
import serial.tools.list_ports


class EezBotFun:
    """Contrôleur pour Macropad EezBotFun v1.3 (ESP32-S3)."""

    DEFAULT_BAUDRATE = 115200
    USB_VENDOR_ID = 0x303A  # Espressif Systems

    def __init__(self, port: Optional[str] = None, baudrate: int = DEFAULT_BAUDRATE, timeout: float = 1.0):
        self.port_name = port or self.find_port()
        if not self.port_name:
            raise ConnectionError(
                "Aucun Macropad EezBotFun détecté. "
                "Vérifiez que le câble USB est bien connecté."
            )
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None

    @classmethod
    def is_wsl(cls) -> bool:
        """Détecte si le script s'exécute dans l'environnement WSL (Windows Subsystem for Linux)."""
        if not sys.platform.startswith("linux"):
            return False
        try:
            with open("/proc/version", "r") as f:
                content = f.read().lower()
                return "microsoft" in content or "wsl" in content
        except Exception:
            return False

    @classmethod
    def find_port(cls) -> Optional[str]:
        """
        Détecte automatiquement le port série du Macropad (macOS, Windows, Linux, WSL2).
        Priorité :
        1. Variable d'environnement MACROPAD_PORT
        2. Détection du Vendor ID Espressif (0x303A)
        3. Nom de périphérique usbmodem (macOS), ttyACM/ttyUSB (Linux/WSL2), COMx (Windows)
        """
        env_port = os.environ.get("MACROPAD_PORT")
        if env_port:
            return env_port

        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            # 1. Correspondance VID Espressif (fonctionne sous macOS, Linux et Windows)
            if p.vid == cls.USB_VENDOR_ID:
                return p.device

            # 2. Correspondance sur le nom ou la description
            desc = (p.description or "").lower()
            dev = (p.device or "").lower()
            if "usbmodem" in dev or "eezbotfun" in desc:
                return p.device
            if "ttyacm" in dev or "ttyusb" in dev:
                return p.device
            if sys.platform == "win32" and "com" in dev and ("espressif" in desc or "usb" in desc):
                return p.device

        # Fallback pour Linux / WSL2 si /dev/ttyACM0 existe
        if sys.platform.startswith("linux"):
            for candidate in ["/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyUSB0"]:
                if os.path.exists(candidate):
                    return candidate

        return None

    def connect(self):
        """Ouvre la connexion série avec retry si le port est brièvement occupé."""
        if self.ser and self.ser.is_open:
            return
        last_err = None
        for attempt in range(4):
            try:
                self.ser = serial.Serial(self.port_name, self.baudrate, timeout=self.timeout)
                time.sleep(0.4)
                return
            except Exception as e:
                last_err = e
                time.sleep(0.2)
        if last_err:
            raise last_err

    def close(self):
        """Ferme la connexion série."""
        if self.ser and self.ser.is_open:
            time.sleep(0.3)
            self.ser.close()
            self.ser = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # =========================================================================
    # PROTOCOLE CUS (ÉCRAN & LEDS)
    # =========================================================================

    def send_cus_frame(self, payload: dict) -> None:
        """
        Envoie une trame de protocole 'cus'.
        Structure :
          - 3 octets : b'cus'
          - 2 octets : longueur N en big-endian (uint16)
          - N octets : payload JSON UTF-8
        """
        if not self.ser or not self.ser.is_open:
            self.connect()

        payload_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        n = len(payload_bytes)
        if n < 1 or n > 2043:
            raise ValueError(f"Taille de payload invalide ({n} octets, max 2043).")

        frame = b"cus" + struct.pack(">H", n) + payload_bytes
        self.ser.write(frame)
        self.ser.flush()
        time.sleep(0.3)

    def start_custom_display(
        self,
        fullscreen: bool = True,
        clear_canvas: bool = True,
        leds: Optional[List[Optional[str]]] = None
    ) -> None:
        """
        Active le mode d'affichage personnalisé sur le Macropad.
        :param fullscreen: True pour plein écran 480x320, False pour 480x200 (garde les boutons affichés).
        :param clear_canvas: Efface le canvas existant.
        :param leds: Liste de jusqu'à 8 couleurs hex (#RRGGBB) pour les touches.
        """
        msg = {
            "cmd": "start",
            "fullscreen": fullscreen,
            "clear_canvas": clear_canvas,
        }
        if leds is not None:
            msg["leds"] = {"on": True, "keys": leds}
        self.send_cus_frame(msg)

    def stop_custom_display(self) -> None:
        """Quitte le mode d'affichage personnalisé et restaure l'affichage et les LEDs normaux."""
        self.send_cus_frame({"cmd": "stop"})

    def display_text(
        self,
        text: str,
        x: int = 0,
        y: int = 0,
        w: int = 480,
        h: int = 200,
        fg: str = "#FFFFFF",
        bg: str = "#000000",
        align: str = "CENTER",
        long_mode: str = "WRAP",
        clear_canvas: bool = False,
        fullscreen: bool = True,
        border: Optional[Union[bool, int]] = None,
        border_color: Optional[str] = None,
        border_radius: Optional[int] = None,
        leds: Optional[List[Optional[str]]] = None,
    ) -> None:
        """
        Affiche un bloc de texte en mode absolu / canvas.
        Prend en charge les symboles LVGL : {ok}, {play}, {pause}, {wifi}, {battery_full}, {warning}, etc.
        """
        msg = {
            "cmd": "start",  # garantit que l'écran bascule en mode custom
            "fullscreen": fullscreen,
            "clear_canvas": clear_canvas,
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "text": text,
            "fg": fg,
            "bg": bg,
            "align": align,
            "long_mode": long_mode,
        }
        if border is not None:
            msg["border"] = border
            if border_color:
                msg["border-color"] = border_color
            if border_radius is not None:
                msg["border-radius"] = border_radius

        if leds is not None:
            msg["leds"] = {"on": True, "keys": leds}

        self.send_cus_frame(msg)

    def set_leds(self, keys: List[Optional[str]], on: bool = True) -> None:
        """
        Définit la couleur des 8 LEDs RGB sous les touches.
        :param keys: Liste de jusqu'à 8 couleurs '#RRGGBB' (ex: ['#FF0000', '#00FF00', ...]).
                     Utilisez None pour conserver la couleur existante, '#000000' pour éteindre.
        :param on: État général des LEDs.
        """
        self.send_cus_frame({
            "cmd": "update",
            "leds": {
                "on": on,
                "keys": keys[:8]
            }
        })

    def setup_grid(
        self,
        cols: List[str],
        rows: List[str],
        widgets: List[dict],
        fullscreen: bool = True,
        gap: int = 4,
        pad: int = 6
    ) -> None:
        """
        Configure un affichage structuré en grille (style WPF/CSS Grid).
        :param cols: Tailles de colonnes (ex: ["*", "*", "*", "*"] ou ["120", "*"])
        :param rows: Tailles de lignes (ex: ["40", "*", "40"])
        :param widgets: Liste des widgets (max 12), chacun avec id, row, col, text, align, etc.
        """
        msg = {
            "cmd": "start",
            "layout": "grid",
            "fullscreen": fullscreen,
            "grid": {
                "cols": cols,
                "rows": rows,
                "gap": gap,
                "pad": pad
            },
            "widgets": widgets
        }
        self.send_cus_frame(msg)

    def update_grid_widget(
        self,
        widget_id: int,
        text: str,
        text_op: str = "replace",
        fg: Optional[str] = None
    ) -> None:
        """
        Met à jour un widget de la grille par son ID (sans redessiner tout l'écran).
        :param widget_id: ID du widget défini lors du setup_grid.
        :param text: Nouveau texte.
        :param text_op: 'replace' pour remplacer, 'append' pour ajouter une ligne au journal.
        :param fg: Couleur optionnelle.
        """
        item = {
            "id": widget_id,
            "text": text,
            "text_op": text_op
        }
        if fg:
            item["fg"] = fg

        msg = {
            "cmd": "update",
            "layout": "grid",
            "set": [item]
        }
        self.send_cus_frame(msg)

    # =========================================================================
    # PROTOCOLE EBF (CONFIGURATION TOUCHES & VERSION)
    # =========================================================================

    def send_ebf_command(self, cmd_bytes: bytes) -> bytes:
        """Envoie une commande ebf au macropad et lit la réponse."""
        if not self.ser or not self.ser.is_open:
            self.connect()

        if len(cmd_bytes) > 255:
            raise ValueError("Commande ebf trop longue (max 255 octets).")

        frame = b"ebf" + bytes([len(cmd_bytes)]) + cmd_bytes
        self.ser.write(frame)
        self.ser.flush()
        time.sleep(0.1)
        return self.ser.read_all()

    def query_version(self) -> str:
        """Interroge la version de firmware du périphérique."""
        resp = self.send_ebf_command(b"5")
        return resp.decode("utf-8", errors="ignore").strip()

    def configure_key(self, profile: int, key: int, text: str, hid_mode: bool = True) -> None:
        """
        Configure une touche physique sur le Macropad via le protocole ebf.
        :param profile: Numéro de profil (1 à 5).
        :param key: Numéro de touche (1 à 8).
        :param text: Texte ou séquence (ex: '1{enter}', 'y{enter}').
        :param hid_mode: Active le mode clavier USB HID pour cette touche.
        """
        raw_text = (
            text.replace("{enter}", "\xa8")
            .replace("{escape}", "\xa9")
            .replace("{bkspace}", "\xaa")
            .replace("{tab}", "\xab")
            .replace("{space}", "\xac")
        )
        cmd_key = f"0{profile}.{key}:0".encode("ascii") + raw_text.encode("latin1")
        self.send_ebf_command(cmd_key)
        if hid_mode:
            cmd_hid = f"a{profile}.{key}".encode("ascii")
            self.send_ebf_command(cmd_hid)

    def set_alias(self, profile: int, key: int, alias: str) -> None:
        """Définit le libellé texte affiché sous la touche sur le Macropad."""
        cmd = f"2{profile}.{key}:{alias}".encode("utf-8")
        self.send_ebf_command(cmd)

    def configure_claude_profile(self, profile: int = 1) -> None:
        """
        Configure un profil complet pour l'interaction avec Claude Code :
        - Touches 1 à 6 : '1{enter}' à '6{enter}' pour la sélection des choix
        - Touche 7 : 'y{enter}' (Valider / Yes)
        - Touche 8 : 'n{enter}' (Refuser / No)
        """
        mapping = {
            1: ("1{enter}", "Choix 1"),
            2: ("2{enter}", "Choix 2"),
            3: ("3{enter}", "Choix 3"),
            4: ("4{enter}", "Choix 4"),
            5: ("5{enter}", "Choix 5"),
            6: ("6{enter}", "Choix 6"),
            7: ("y{enter}", "Valider"),
            8: ("n{enter}", "Annuler"),
        }
        for key, (val, alias) in mapping.items():
            self.configure_key(profile=profile, key=key, text=val, hid_mode=True)
            self.set_alias(profile=profile, key=key, alias=alias)

    def configure_oui_non_profile(self, profile: int = 2) -> None:
        """
        Configure un profil dédié Oui / Non (Page 2) :
        - Touche 1 : 'y{enter}' (OUI)
        - Touche 2 : 'n{enter}' (NON)
        - Touche 3 : '{enter}' (OK)
        - Touche 4 : '{escape}' (ESC)
        - Touche 5 : 'oui{enter}' (oui Fr)
        - Touche 6 : 'non{enter}' (non Fr)
        - Touche 7 : 'y{enter}' (Valider)
        - Touche 8 : 'n{enter}' (Annuler)
        """
        mapping_p2 = {
            1: ("y{enter}", "OUI"),
            2: ("n{enter}", "NON"),
            3: ("{enter}", "Entrée"),
            4: ("{escape}", "Échap"),
            5: ("oui{enter}", "oui (Fr)"),
            6: ("non{enter}", "non (Fr)"),
            7: ("y{enter}", "Valider"),
            8: ("n{enter}", "Annuler"),
        }
        for k, (act, alias) in mapping_p2.items():
            self.configure_key(profile=profile, key=k, text=act, hid_mode=True)
            self.set_alias(profile=profile, key=k, alias=alias)


if __name__ == "__main__":
    print("=== Test du contrôleur EezBotFun ===")
    try:
        pad = EezBotFun()
        print(f"Port détecté : {pad.port_name}")
        with pad:
            v = pad.query_version()
            print(f"Version firmware : {v}")

            # Test des LEDs (arc-en-ciel)
            rainbow = [
                "#FF0000", "#FF7F00", "#FFFF00", "#00FF00",
                "#00F0FF", "#0000FF", "#8A2BE2", "#FF007F"
            ]
            print("Activation de l'écran et des LEDs...")
            pad.display_text(
                text="{ok} Macropad Connecté !\n{wifi} EezBotFun v1.3",
                x=20, y=80, w=440, h=160,
                fg="#00FFCC", bg="#181825",
                align="CENTER",
                border=2, border_color="#00FFCC", border_radius=12,
                clear_canvas=True,
                fullscreen=True,
                leds=rainbow
            )
            print("Affichage réussi !")
    except Exception as e:
        print(f"Erreur : {e}")
