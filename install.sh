#!/usr/bin/env bash
# ==============================================================================
# Claude Pad - Script d'installation automatique pour macOS, Linux et WSL2
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================"
echo "  Claude Pad - Installateur Macropad EezBotFun v1.3   "
echo "======================================================"

# 1. Vérification de Python 3
if ! command -v python3 &>/dev/null; then
    echo "[!] Erreur : python3 n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi
echo "[+] Python 3 détecté : $(python3 --version)"

# 2. Détection de l'environnement (macOS, Linux, WSL2)
OS="$(uname -s)"
IS_WSL=false
if [ -f /proc/version ] && grep -qi "microsoft\|wsl" /proc/version; then
    IS_WSL=true
    echo "[+] Environnement détecté : Windows Subsystem for Linux 2 (WSL2)"
elif [ "$OS" = "Darwin" ]; then
    echo "[+] Environnement détecté : macOS"
else
    echo "[+] Environnement détecté : Linux ($OS)"
fi

# 3. Création de l'environnement virtuel .venv
if [ ! -d ".venv" ]; then
    echo "[*] Création de l'environnement virtuel Python (.venv)..."
    python3 -m venv .venv
else
    echo "[+] Environnement virtuel existant (.venv)."
fi

# 4. Installation des dépendances
echo "[*] Installation des dépendances (pyserial, pillow)..."
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
echo "[+] Dépendances installées avec succès."

# 5. Rendre les scripts exécutables
chmod +x claude_hook.py cli.py generate_icons.py

# 6. Configuration des hooks dans ~/.claude/settings.json
CLAUDE_DIR="$HOME/.claude"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
mkdir -p "$CLAUDE_DIR"

echo "[*] Configuration des hooks Claude Code dans $SETTINGS_FILE..."
.venv/bin/python3 - <<EOF
import json, os

settings_path = os.path.expanduser("$SETTINGS_FILE")
venv_py = os.path.join("$SCRIPT_DIR", ".venv", "bin", "python3")
hook_script = os.path.join("$SCRIPT_DIR", "claude_hook.py")
hook_cmd = f"{venv_py} {hook_script}"

data = {}
if os.path.exists(settings_path):
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

if "hooks" not in data:
    data["hooks"] = {}

hooks_config = {
    "Notification": [{"matcher": "*", "hooks": [{"type": "command", "command": hook_cmd}]}],
    "Stop": [{"matcher": "*", "hooks": [{"type": "command", "command": hook_cmd}]}],
    "UserPromptSubmit": [{"matcher": "*", "hooks": [{"type": "command", "command": hook_cmd}]}],
}

for event, cfg in hooks_config.items():
    data["hooks"][event] = cfg

with open(settings_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("[+] ~/.claude/settings.json mis à jour avec succès !")
EOF

# 7. Génération et copie des icônes
echo "[*] Génération des icônes de touches..."
.venv/bin/python3 generate_icons.py || true

# 8. Programmation du Macropad si connecté
echo "[*] Recherche du Macropad USB..."
if .venv/bin/python3 -c "from macropad import EezBotFun; p = EezBotFun(); print(p.port_name)" 2>/dev/null; then
    echo "[+] Macropad détecté ! Programmation des profils..."
    .venv/bin/python3 -c "
from macropad import EezBotFun
try:
    with EezBotFun() as pad:
        print('  - Programmation Profil 1 (Choix 1..6, Valider, Annuler)...')
        pad.configure_claude_profile(profile=1)
        print('  - Programmation Profil 2 (OUI / NON)...')
        pad.configure_oui_non_profile(profile=2)
        print('  - Programmation Profil 3 (Secours)...')
        pad.configure_claude_profile(profile=3)
        pad.stop_custom_display()
    print('[+] Macropad programmé avec succès !')
except Exception as e:
    print(f'[-] Note : {e}')
" || true
else
    echo "[!] Note : Macropad non détecté sur le port série pour le moment."
    if [ "$IS_WSL" = true ]; then
        echo "    Sous WSL2, assurez-vous d'avoir lié le port USB avec usbipd-win :"
        echo "    Dans Windows PowerShell (Admin) : usbipd wsl attach --hardware-id 303a:1001"
        echo "    Voir wsl_setup.md pour les instructions détaillées."
    else
        echo "    Branchez le câble USB et relancez : ./claude_hook.py --setup-keys 1"
    fi
fi

echo ""
echo "======================================================"
echo "  Installation terminée avec succès !                 "
echo "======================================================"
echo "Commandes de test :"
echo "  ./claude_hook.py --choices     # Tester l'affichage choix multiples"
echo "  ./claude_hook.py --yes-no      # Tester l'affichage Oui / Non"
echo "  ./claude_hook.py --permission  # Tester l'alerte d'autorisation"
echo "  ./claude_hook.py --reset       # Réinitialiser l'écran"
echo ""
