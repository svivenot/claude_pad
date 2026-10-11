# Guide d'installation : Windows 11 / 10 avec Claude Code dans WSL2

Ce guide vous explique pas à pas comment utiliser le Macropad **EezBotFun v1.3** avec **Claude Code** s'exécutant dans votre environnement **WSL2** (Ubuntu, Debian, etc.).

---

## 1. Comprendre l'architecture

- **Matériel** : Le Macropad est physiquement branché sur un port USB de votre PC Windows.
- **Clavier physique (HID)** : Windows reconnaît le Macropad comme un clavier standard. Lorsque vous pressez une touche sur le Macropad, la frappe est directement envoyée dans la fenêtre active (par exemple le Terminal Windows où tourne Claude Code dans WSL2).
- **Écran LCD & LEDs (USB Série)** : Le Macropad dispose d'un port série USB CDC (`COMx` sous Windows). Pour que Claude Code (qui tourne dans WSL2) puisse afficher les questions et contrôler les LEDs, il doit pouvoir communiquer avec ce port série.

Deux méthodes sont disponibles :
1. **Méthode 1 (Recommandée & 100% native)** : Partager le périphérique USB directement dans WSL2 avec `usbipd-win`.
2. **Méthode 2 (Sans pilote additionnel)** : Utiliser l'interopérabilité WSL pour exécuter le script côté Windows.

---

## Méthode 1 : Partage USB natif avec `usbipd-win` (Recommandée)

Cette méthode est la solution officielle de Microsoft pour connecter des périphériques USB série à WSL2.

### Étape 1 : Installer `usbipd-win` sous Windows

Ouvrez **PowerShell** en tant qu'**Administrateur** sous Windows et exécutez :

```powershell
winget install --exact dorssel.usbipd-win
```

*(Redémarrez votre terminal ou votre session si demandé).*

### Étape 2 : Autoriser le partage du Macropad (une seule fois)

Branchez votre Macropad en USB, puis toujours dans PowerShell (Admin) :

```powershell
# 1. Lister les périphériques USB
usbipd list

# Vous devriez voir une ligne avec VID:PID 303a:1001 (Espressif Systems)
# 2. Enregistrer le périphérique pour le partage
usbipd bind --hardware-id 303a:1001
```

### Étape 3 : Attacher le Macropad à WSL2

Toujours dans PowerShell (Admin ou normal) :

```powershell
# Attachement persistant automatique
usbipd attach --wsl --hardware-id 303a:1001 --auto-attach
```

> [!TIP]
> Avec l'option `--auto-attach`, le Macropad sera automatiquement réattaché à WSL2 chaque fois que vous le débranchez/rebranchez ou que vous démarrez Windows.

### Étape 4 : Permissions sous WSL2

Basculez dans votre terminal **WSL2** (Ubuntu / Debian) :

```bash
# 1. Vérifier que le périphérique série est bien visible
ls -l /dev/ttyACM*
# Vous devriez voir /dev/ttyACM0

# 2. Ajouter votre utilisateur au groupe dialout pour accéder au port série sans sudo
sudo usermod -aG dialout $USER

# 3. Appliquer le nouveau groupe (ou fermez et rouvrez votre terminal WSL)
newgrp dialout
```

### Étape 5 : Installer Claude Pad dans WSL2

Toujours dans votre terminal **WSL2** :

```bash
cd ~
git clone https://github.com/svivenot/claude_pad.git
cd claude_pad
./install.sh
```

L'installateur va :
- Créer l'environnement virtuel `.venv`
- Configurer automatiquement `~/.claude/settings.json` dans WSL2
- Programmer les touches du Macropad (Profil 1 et Profil 2)
- Tester la connexion série

---

## Méthode 2 : Sans `usbipd` (via Interopérabilité Windows Python)

Si vous ne souhaitez pas installer `usbipd-win`, vous pouvez exploiter la capacité de WSL2 à exécuter des commandes Windows directement.

### Étape 1 : Installer Python et PySerial sous Windows
1. Téléchargez et installez Python pour Windows ([python.org](https://www.python.org/downloads/)).
2. Cochez **"Add Python to PATH"** lors de l'installation.
3. Dans l'invite de commandes Windows :
   ```cmd
   pip install pyserial pillow
   ```

### Étape 2 : Cloner le dépôt sur votre disque Windows
Dans PowerShell sous Windows :
```powershell
cd C:\Users\$env:USERNAME
git clone https://github.com/svivenot/claude_pad.git
```

### Étape 3 : Configurer le hook dans WSL2
Dans WSL2, modifiez `~/.claude/settings.json` pour appeler Python Windows :

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python.exe /mnt/c/Users/<votre_utilisateur>/claude_pad/claude_hook.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python.exe /mnt/c/Users/<votre_utilisateur>/claude_pad/claude_hook.py"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python.exe /mnt/c/Users/<votre_utilisateur>/claude_pad/claude_hook.py"
          }
        ]
      }
    ]
  }
}
```

---

## 3. Vérification du fonctionnement

Dans votre terminal WSL2, lancez les commandes de test :

```bash
# Simuler une question à choix multiples
./claude_hook.py --choices

# Simuler une question Oui / Non
./claude_hook.py --yes-no "Voulez-vous lancer la compilation ?"

# Réinitialiser l'écran
./claude_hook.py --reset
```

Puis démarrez `claude` dans WSL2 :
```bash
claude
```

Dès que Claude Code pose une question, le Macropad réagit instantanément !
