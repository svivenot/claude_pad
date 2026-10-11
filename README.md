# Claude Pad 🎮

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Platform: macOS | Linux | Windows | WSL2](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows%20%7C%20WSL2-brightgreen.svg)]()
[![Hardware: EezBotFun v1.3](https://img.shields.io/badge/hardware-EezBotFun%20v1.3%20(ESP32--S2)-orange.svg)]()

> **Contrôleur physique pour [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) sur Macropad USB (EezBotFun v1.3 avec écran LCD 480×320 et 8 touches mécaniques RGB).**

---

## ✨ Fonctionnalités

- **🔴 Questions ouvertes & Demandes d'attention** :
  - Clignotement d'alerte des 8 LEDs en **rouge** (3 flashs), puis maintien en rouge fixe.
  - Cadre rouge sur l'écran LCD avec la question posée par Claude Code.
  - Reste allumé jusqu'à votre réponse.

- **🟢 Tâche terminée** :
  - Allumage des 8 touches en **vert vif**.
  - Cadre vert sur l'écran LCD avec un résumé de complétion `{ok} CLAUDE CODE - TERMINÉ`.
  - Maintien pendant 3,5 secondes puis retour automatique à l'écran d'accueil du Macropad.

- **🔵 Choix multiples interactifs** :
  - Détection automatique des listes à choix multiples (`1. ...`, `2. ...`, `3. ...`).
  - Cadre Cyan sur l'écran LCD listant chaque option numérotée `[1]`, `[2]`, `[3]`.
  - **Rétroéclairage LED dynamique** : seules les touches correspondant aux choix valides s'allument (Cyan vif `#00D4FF`). Les autres touches restent éteintes.
  - **Sélection directe** : pressez la touche physique **1** à **6** sur le Macropad pour valider instantanément le choix dans le terminal !

- **✅ Demandes de confirmation Oui / Non & Autorisations d'outils** :
  - Détection des questions binaires et des demandes de permissions d'outils (Bash, Edit, MCP).
  - Cadre vert/ambre sur l'écran avec `[1] OUI (Valider)` et `[2] NON (Refuser)`.
  - **Touche 1** s'allume en **Vert** (`#00FF88`).
  - **Touche 2** s'allume en **Rouge** (`#FF2222`).
  - Validation ou refus d'un seul clic !

- **🔄 Reset automatique** :
  - Dès que vous tapez une commande ou envoyez un prompt dans Claude Code (`UserPromptSubmit`), l'alerte s'efface immédiatement et le Macropad revient à son affichage standard.

---

## ⌨️ Disposition des profils physiques

Le Macropad dispose d'un commutateur de profil pour basculer facilement :

### 📄 Profil 1 (Page 1) : Choix multiples & Actions rapides

| Touche | Label | Action envoyée | Description |
| :---: | :---: | :---: | :--- |
| **1** | `Choix 1` | `1{enter}` | Sélectionner Option 1 |
| **2** | `Choix 2` | `2{enter}` | Sélectionner Option 2 |
| **3** | `Choix 3` | `3{enter}` | Sélectionner Option 3 |
| **4** | `Choix 4` | `4{enter}` | Sélectionner Option 4 |
| **5** | `Choix 5` | `5{enter}` | Sélectionner Option 5 |
| **6** | `Choix 6` | `6{enter}` | Sélectionner Option 6 |
| **7** | `Valider` | `y{enter}` | Valider / Yes / Confirmer (✓) |
| **8** | `Annuler` | `n{enter}` | Refuser / No / Annuler (✕) |

### 📄 Profil 2 (Page 2) : Dédié Oui / Non

| Touche | Label | Action envoyée | Description |
| :---: | :---: | :---: | :--- |
| **1** | `OUI` | `y{enter}` | Badge vert **OUI** |
| **2** | `NON` | `n{enter}` | Badge rouge **NON** |
| **3** | `Entrée` | `{enter}` | Badge bleu **OK** (Validation) |
| **4** | `Échap` | `{escape}` | Badge ambre **ESC** (Échappement) |
| **5** | `oui (Fr)` | `oui{enter}` | Mot complet français "oui" |
| **6** | `non (Fr)` | `non{enter}` | Mot complet français "non" |
| **7** | `Valider` | `y{enter}` | Coche verte (✓) |
| **8** | `Annuler` | `n{enter}` | Croix rouge (✕) |

---

## 🚀 Installation rapide

### Sur macOS ou Linux natif

1. Branchez votre Macropad en USB.
2. Clonez le dépôt et lancez l'installateur :

```bash
git clone https://github.com/svivenot/claude_pad.git
cd claude_pad
./install.sh
```

Le script configure l'environnement virtuel, installe les dépendances, programme les profils sur le Macropad et met à jour `~/.claude/settings.json`.

---

### Sur Windows avec Claude Code dans WSL2

Si vous utilisez Claude Code à l'intérieur de **WSL2** (Ubuntu/Debian sous Windows) avec le Macropad branché sur le PC Windows :

Consultez le guide complet pas à pas : 👉 **[wsl_setup.md](wsl_setup.md)**

En résumé :
1. Dans PowerShell Windows (Admin) :
   ```powershell
   winget install --exact dorssel.usbipd-win
   usbipd bind --hardware-id 303a:1001
   usbipd attach --wsl --hardware-id 303a:1001 --auto-attach
   ```
2. Dans votre terminal WSL2 :
   ```bash
   sudo usermod -aG dialout $USER
   git clone https://github.com/svivenot/claude_pad.git
   cd claude_pad
   ./install.sh
   ```

---

### Sur Windows natif (PowerShell)

Dans un terminal PowerShell :

```powershell
git clone https://github.com/svivenot/claude_pad.git
cd claude_pad
.\install.ps1
```

---

## 🧪 Commandes de test (CLI)

Vous pouvez tester immédiatement chaque état de l'affichage sans lancer Claude :

```bash
# Simuler une question à choix multiples
./claude_hook.py --choices

# Simuler une invite Oui / Non
./claude_hook.py --yes-no "Voulez-vous lancer la suite de tests ?"

# Simuler une demande d'autorisation d'outil
./claude_hook.py --permission "Bash: git push origin main"

# Simuler une question ouverte classique (cadre rouge + LEDs rouges)
./claude_hook.py --question "Quelle architecture préférez-vous ?"

# Simuler une tâche terminée (vert 3.5s puis retour au normal)
./claude_hook.py --done "Tous les tests ont réussi !"

# Réinitialiser l'écran
./claude_hook.py --reset
```

---

## 🎨 Régénération des icônes

Le dossier `icons/` contient déjà les PNG 64×64 anti-aliasés. Pour régénérer de nouvelles icônes ou modifier les couleurs :

```bash
./generate_icons.py
```

Le script détecte automatiquement le volume MSC `/Volumes/EEZBOTFUN` si le Macropad est branché et y copie les icônes dans `app_icons/`.

---

## 🛠️ Structure du projet

```
claude_pad/
├── claude_hook.py       # Hook principal appelé par Claude Code (stdin JSON)
├── macropad.py          # Contrôleur matériel série USB CDC (protocoles cus & ebf)
├── cli.py               # Utilitaire en ligne de commande pour le Macropad
├── generate_icons.py    # Générateur d'icônes haute définition (Pillow)
├── install.sh           # Script d'installation automatique macOS / Linux / WSL2
├── install.ps1          # Script d'installation automatique Windows (PowerShell)
├── wsl_setup.md         # Guide détaillé pour Windows + WSL2
├── requirements.txt     # Dépendances Python (pyserial, pillow)
├── icons/               # Icônes PNG 64x64 pour les touches (Profil 1 et Profil 2)
└── README.md            # Documentation du projet
```

---

## 📄 Licence

Projet distribué sous licence MIT. Voir [LICENSE](LICENSE) pour plus de détails.
