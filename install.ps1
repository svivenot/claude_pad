# ==============================================================================
# Claude Pad - Script d'installation automatique pour Windows (PowerShell)
# ==============================================================================
$ErrorActionPreference = "Stop"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  Claude Pad - Installateur Windows (PowerShell)       " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 1. Vérification de Python
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "[+] Python détecté : $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[!] Erreur : Python n'est pas trouvé dans le PATH." -ForegroundColor Red
    Write-Host "    Veuillez installer Python depuis https://www.python.org et cocher 'Add to PATH'." -ForegroundColor Yellow
    Exit 1
}

# 2. Création de l'environnement virtuel
if (-not (Test-Path ".venv")) {
    Write-Host "[*] Création de l'environnement virtuel (.venv)..." -ForegroundColor Yellow
    & python -m venv .venv
} else {
    Write-Host "[+] Environnement virtuel existant (.venv)." -ForegroundColor Green
}

$venvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"

# 3. Installation des dépendances
Write-Host "[*] Installation des dépendances (pyserial, pillow)..." -ForegroundColor Yellow
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -r requirements.txt
Write-Host "[+] Dépendances installées avec succès." -ForegroundColor Green

# 4. Configuration de ~/.claude/settings.json
$userHome = [System.Environment]::GetFolderPath('UserProfile')
$claudeDir = Join-Path $userHome ".claude"
$settingsFile = Join-Path $claudeDir "settings.json"

if (-not (Test-Path $claudeDir)) {
    New-Item -ItemType Directory -Path $claudeDir -Force | Out-Null
}

$hookPath = (Join-Path $ScriptDir "claude_hook.py") -replace '\\', '/'
$pythonPath = $venvPython -replace '\\', '/'

Write-Host "[*] Configuration des hooks Claude Code dans $settingsFile..." -ForegroundColor Yellow

$settingsObj = @{}
if (Test-Path $settingsFile) {
    try {
        $jsonContent = Get-Content $settingsFile -Raw -Encoding UTF8
        $settingsObj = $jsonContent | ConvertFrom-Json -AsHashtable
    } catch {
        $settingsObj = @{}
    }
}

if (-not $settingsObj.ContainsKey("hooks")) {
    $settingsObj["hooks"] = @{}
}

$hookCommand = "$pythonPath $hookPath"
$settingsObj["hooks"]["PreToolUse"] = @(@{ matcher = "AskUserQuestion,AskFollowupQuestion,ExitPlanMode"; hooks = @(@{ type = "command"; command = $hookCommand }) })
$settingsObj["hooks"]["PermissionRequest"] = @(@{ matcher = "*"; hooks = @(@{ type = "command"; command = $hookCommand }) })
$settingsObj["hooks"]["PostToolUse"] = @(@{ matcher = "AskUserQuestion,AskFollowupQuestion,ExitPlanMode"; hooks = @(@{ type = "command"; command = $hookCommand }) })
$settingsObj["hooks"]["Notification"] = @(@{ matcher = "*"; hooks = @(@{ type = "command"; command = $hookCommand }) })
$settingsObj["hooks"]["Stop"] = @(@{ matcher = "*"; hooks = @(@{ type = "command"; command = $hookCommand }) })
$settingsObj["hooks"]["UserPromptSubmit"] = @(@{ matcher = "*"; hooks = @(@{ type = "command"; command = $hookCommand }) })

$settingsObj | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
Write-Host "[+] Configuration Claude Code enregistrée !" -ForegroundColor Green

# 5. Génération des icônes
Write-Host "[*] Génération des icônes de touches..." -ForegroundColor Yellow
& $venvPython generate_icons.py

# 6. Programmation du Macropad
Write-Host "[*] Recherche et programmation du Macropad..." -ForegroundColor Yellow
& $venvPython -c @"
from macropad import EezBotFun
try:
    with EezBotFun() as pad:
        print('  - Port série détecté :', pad.port_name)
        pad.configure_claude_profile(profile=1)
        pad.configure_oui_non_profile(profile=2)
        pad.stop_custom_display()
    print('[+] Macropad programmé avec succès !')
except Exception as e:
    print(f'[-] Note : {e}')
"@

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "  Installation terminée avec succès !                 " -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host "Commandes de test :"
Write-Host "  & $venvPython claude_hook.py --choices"
Write-Host "  & $venvPython claude_hook.py --yes-no 'Confirmez-vous ?'"
Write-Host "  & $venvPython claude_hook.py --reset"
Write-Host ""
