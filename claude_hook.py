#!/usr/bin/env python3
"""
Hook Claude Code pour Macropad EezBotFun v1.3.

Comportement :
- CHOIX MULTIPLE : Détecte les options (1., 2., 3...) et les affiche sur l'écran LCD.
                   Allume uniquement les LEDs des touches correspondantes (Cyan vif #00D4FF).
                   L'utilisateur sélectionne directement son choix en appuyant sur la touche physique 1 à N !
- PERMISSION     : Propose [1] Autoriser (LED 1 verte) / [2] Refuser (LED 2 rouge).
- ROUGE          : Quand Claude pose une question ouverte sans choix.
                   -> LEDs clignotent en rouge puis restent allumées en rouge fixe.
                   -> L'écran LCD 480x320 affiche la question.
- VERT           : Quand Claude a terminé sa tâche (pas de question en suspens).
                   -> Les 8 LEDs s'allument en vert, affichage de confirmation 3.5s puis retour au normal.
- RESET          : Quand l'utilisateur soumet un prompt (UserPromptSubmit),
                   -> Éteint l'alerte et restaure l'affichage normal du macropad.
"""

import json
import os
import re
import sys
import time
from typing import List, Optional, Tuple

# Assurer l'accès au module local macropad.py
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from macropad import EezBotFun


def clean_markdown(text: str) -> str:
    """Nettoie le balisage markdown pour un affichage propre sur LCD."""
    text = re.sub(r"```[a-zA-Z0-9_-]*\n", "", text)
    text = text.replace("```", "")
    text = re.sub(r"[*_#`]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_last_assistant_message(transcript_path: str) -> str:
    """Extrait le dernier message de l'assistant depuis le fichier transcript JSONL."""
    if not transcript_path or not os.path.exists(transcript_path):
        return ""
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        for line in reversed(lines):
            try:
                data = json.loads(line)
                if data.get("type") == "assistant":
                    msg = data.get("message", {})
                    content = msg.get("content", [])
                    if isinstance(content, list):
                        texts = [
                            c.get("text", "")
                            for c in content
                            if isinstance(c, dict) and c.get("type") == "text"
                        ]
                        res = "\n".join(texts).strip()
                        if res:
                            return res
                    elif isinstance(content, str) and content.strip():
                        return content.strip()
            except Exception:
                continue
    except Exception:
        pass
    return ""


def extract_choices(text: str) -> Tuple[bool, str, List[Tuple[int, str]]]:
    """
    Détecte si le message contient une liste de choix numérotés (1. / 1) / [1]).
    Retourne : (has_choices: bool, question_title: str, [(1, 'Option 1'), (2, 'Option 2'), ...])
    """
    if not text:
        return False, "", []

    clean = clean_markdown(text)
    choice_pattern = re.compile(
        r"^(?:[\s*-]*)(?:\[?(\d+)\]?[.)])\s+(.+)$", re.MULTILINE
    )
    matches = choice_pattern.findall(clean)

    if len(matches) >= 2:
        choices = []
        for num_str, label in matches:
            num = int(num_str)
            clean_label = label.strip()
            # Tronquer chaque choix pour qu'il tienne bien sur une ligne de l'écran
            if len(clean_label) > 42:
                clean_label = clean_label[:40].rstrip() + "..."
            choices.append((num, clean_label))

        first_match = choice_pattern.search(clean)
        header = clean[: first_match.start()].strip() if first_match else ""
        sentences = [s.strip() for s in re.split(r"[\n\r]+", header) if s.strip()]
        q_title = sentences[-1] if sentences else "Choisissez une option :"
        if len(q_title) > 60:
            q_title = q_title[:57].rstrip() + "..."

        return True, q_title, choices

    return False, "", []


def analyze_assistant_message(raw_text: str) -> Tuple[bool, str]:
    """
    Détermine si le message de fin de Claude est une question ouverte
    ou une conclusion de tâche terminée.
    Retourne : (is_question: bool, display_text: str)
    """
    if not raw_text or not raw_text.strip():
        return False, "Tâche terminée avec succès !"

    cleaned = clean_markdown(raw_text)
    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    if not paragraphs:
        return False, "Tâche terminée avec succès !"

    last_para = paragraphs[-1]

    question_markers = [
        r"\?",
        r"\b(?:veux|voulez)-tu\b",
        r"\b(?:voulez|veux)-vous\b",
        r"\b(?:souhaites|souhaitez)-vous\b",
        r"\b(?:souhaites|souhaitez)-tu\b",
        r"\bdois-je\b",
        r"\bqu[\'’]en (?:penses|pensez)-vous\b",
        r"\bqu[\'’]en (?:penses|pensez)-tu\b",
        r"\b(?:dis|dites)-moi\b",
        r"\b(?:confirme|confirmez)(?:-moi|-nous)?\b",
        r"\b(?:préfères|préférez)-vous\b",
        r"\b(?:préfères|préférez)-tu\b",
        r"\b(?:fais|faites)-moi savoir\b",
        r"\b(?:indique|indiquez)-moi\b",
        r"\best-ce que\b",
        r"\bwould you like\b",
        r"\bdo you want\b",
        r"\bshould i\b",
        r"\blet me know\b",
        r"\bplease confirm\b",
        r"\bwhich (?:one|option)\b",
        r"\bwhat do you think\b",
        r"\bhow would you like\b",
    ]

    is_question = any(re.search(pat, last_para, re.IGNORECASE) for pat in question_markers)

    if is_question:
        sentences = re.split(r"(?<=[.?!])\s+", last_para)
        q_sentences = [
            s for s in sentences
            if any(re.search(pat, s, re.IGNORECASE) for pat in question_markers)
        ]
        display_text = " ".join(q_sentences) if q_sentences else last_para
    else:
        display_text = last_para

    if len(display_text) > 175:
        display_text = display_text[:172].rstrip() + "..."

    return is_question, display_text


def show_choices_alert(question_title: str, choices: List[Tuple[int, str]]):
    """
    Affiche une alerte de CHOIX MULTIPLE sur l'écran LCD 480x320 :
    - Question affichée en haut
    - Chaque option numérotée : [1] Option A, [2] Option B...
    - Allume les LEDs Cyan (#00D4FF) pour les touches 1 à N utilisables !
    - Touche 7 (Valider) : Vert (#00FF88)
    - Touche 8 (Annuler) : Rouge (#FF2222)
    """
    cyan_color = "#00D4FF"

    clean_title = clean_markdown(question_title)
    if len(clean_title) > 65:
        clean_title = clean_title[:62].rstrip() + "..."

    # Construction du texte
    lines = [f"{{warning}} CHOIX MULTIPLE", "", clean_title, ""]
    active_keys = set()
    for num, label in choices[:6]:
        clean_label = clean_markdown(label)
        if len(clean_label) > 40:
            clean_label = clean_label[:38].rstrip() + "..."
        lines.append(f" [{num}] {clean_label}")
        active_keys.add(num)

    full_text = "\n".join(lines)

    # Masque de LEDs :
    # Touches 1 à 6 : Cyan si option active
    # Touche 7 : Valider (Vert)
    # Touche 8 : Annuler (Rouge)
    leds = ["#000000"] * 8
    for k in active_keys:
        if 1 <= k <= 6:
            leds[k - 1] = cyan_color
    leds[6] = "#00FF88"  # Touche 7 : Valider
    leds[7] = "#FF2222"  # Touche 8 : Annuler

    try:
        with EezBotFun() as pad:
            pad.display_text(
                text=full_text,
                x=15, y=20, w=450, h=280,
                fg="#FFFFFF", bg="#181825",
                align="LEFT",
                long_mode="WRAP",
                border=3, border_color=cyan_color, border_radius=12,
                clear_canvas=True, fullscreen=True,
                leds=leds
            )

            # 3 flashs rapides sur les touches disponibles pour attirer l'attention
            for _ in range(3):
                pad.set_leds(["#000000"] * 8, on=False)
                time.sleep(0.12)
                pad.set_leds(leds, on=True)
                time.sleep(0.14)

            # Maintien des touches allumées
            pad.set_leds(leds, on=True)
    except Exception as e:
        sys.stderr.write(f"[Macropad Hook] Erreur affichage choix multiples: {e}\n")


def is_yes_no_question(text: str) -> bool:
    """Détermine si une question attend une réponse binaire Oui ou Non."""
    if not text:
        return False
    patterns = [
        r"\(oui\s*/\s*non\)",
        r"\(o\s*/\s*n\)",
        r"\(y\s*/\s*n\)",
        r"\(yes\s*/\s*no\)",
        r"\b(?:oui ou non)\b",
        r"\b(?:confirmez|confirmer)\b",
        r"\b(?:continuer|procéder)\b",
        r"\b(?:voulez|veux)-vous\b",
        r"\b(?:souhaitez|souhaites)-vous\b",
        r"\b(?:dois-je|puis-je)\b",
        r"\b(?:would you like|do you want|should i)\b",
    ]
    return any(re.search(pat, text, re.IGNORECASE) for pat in patterns)


def show_yes_no_alert(question_text: str):
    """
    Affiche une invite de confirmation OUI / NON :
    - Touche [1] : OUI (LED 1 verte #00FF88)
    - Touche [2] : NON (LED 2 rouge #FF2222)
    """
    clean_q = clean_markdown(question_text)
    if len(clean_q) > 130:
        clean_q = clean_q[:127].rstrip() + "..."

    full_text = (
        "{warning} CONFIRMATION (OUI / NON)\n\n"
        f"{clean_q}\n\n"
        " [1] OUI (Valider)\n"
        " [2] NON (Refuser)"
    )

    leds = [
        "#00FF88",  # Touche 1 : Vert
        "#FF2222",  # Touche 2 : Rouge
        "#000000", "#000000",
        "#000000", "#000000", "#000000", "#000000"
    ]

    try:
        with EezBotFun() as pad:
            pad.display_text(
                text=full_text,
                x=15, y=20, w=450, h=280,
                fg="#FFFFFF", bg="#181825",
                align="LEFT",
                long_mode="WRAP",
                border=3, border_color="#00FF88", border_radius=12,
                clear_canvas=True, fullscreen=True,
                leds=leds
            )

            for _ in range(3):
                pad.set_leds(["#000000"] * 8, on=False)
                time.sleep(0.12)
                pad.set_leds(leds, on=True)
                time.sleep(0.14)

            pad.set_leds(leds, on=True)
    except Exception as e:
        sys.stderr.write(f"[Macropad Hook] Erreur affichage oui/non: {e}\n")


def show_permission_alert(message: str):
    """
    Affiche une demande de permission sur l'écran :
    - Touche [1] : Autoriser (LED 1 verte #00FF88)
    - Touche [2] : Refuser   (LED 2 rouge #FF2222)
    """
    clean_msg = clean_markdown(message)
    if len(clean_msg) > 90:
        clean_msg = clean_msg[:87].rstrip() + "..."

    full_text = (
        "{warning} AUTORISATION REQUISE\n\n"
        f"{clean_msg}\n\n"
        " [1] Autoriser (Yes)\n"
        " [2] Refuser   (No)"
    )

    leds = [
        "#00FF88",  # Touche 1 : Vert (Yes)
        "#FF2222",  # Touche 2 : Rouge (No)
        "#000000", "#000000",
        "#000000", "#000000", "#000000", "#000000"
    ]

    try:
        with EezBotFun() as pad:
            pad.display_text(
                text=full_text,
                x=15, y=20, w=450, h=280,
                fg="#FFFFFF", bg="#181825",
                align="LEFT",
                long_mode="WRAP",
                border=3, border_color="#FFA500", border_radius=12,
                clear_canvas=True, fullscreen=True,
                leds=leds
            )

            for _ in range(3):
                pad.set_leds(["#000000"] * 8, on=False)
                time.sleep(0.12)
                pad.set_leds(leds, on=True)
                time.sleep(0.14)

            pad.set_leds(leds, on=True)
    except Exception as e:
        sys.stderr.write(f"[Macropad Hook] Erreur affichage permission: {e}\n")


def show_question_alert(question_text: str, title: str = "{warning} QUESTION DE CLAUDE"):
    """
    Affiche une alerte ROUGE pour une question ouverte :
    - 3 flashs rapides des 8 LEDs en rouge
    - Les LEDs restent allumées en rouge fixe
    - L'écran LCD 480x320 affiche la question avec un cadre rouge
    """
    red_color = "#FF2222"
    full_text = f"{title}\n\n{question_text}"

    try:
        with EezBotFun() as pad:
            pad.display_text(
                text=full_text,
                x=15, y=25, w=450, h=270,
                fg="#FFFFFF", bg="#181825",
                align="CENTER",
                long_mode="WRAP",
                border=3, border_color=red_color, border_radius=12,
                clear_canvas=True, fullscreen=True,
                leds=["#FF0000"] * 8
            )

            for _ in range(3):
                pad.set_leds(["#000000"] * 8, on=False)
                time.sleep(0.14)
                pad.set_leds(["#FF0000"] * 8, on=True)
                time.sleep(0.16)

            pad.set_leds(["#FF0000"] * 8, on=True)
    except Exception as e:
        sys.stderr.write(f"[Macropad Hook] Erreur affichage alerte rouge: {e}\n")


def show_finished_status(summary_text: str = "Tâche terminée avec succès !"):
    """
    Affiche un statut VERT :
    - Les 8 LEDs s'allument en vert
    - L'écran LCD 480x320 affiche un cadre vert avec le résumé
    - Temporisation de 3.5s puis restauration de l'affichage normal du macropad
    """
    green_color = "#00FF88"
    full_text = f"{{ok}} CLAUDE CODE - TERMINÉ\n\n{summary_text}"

    try:
        with EezBotFun() as pad:
            pad.display_text(
                text=full_text,
                x=15, y=25, w=450, h=270,
                fg="#FFFFFF", bg="#181825",
                align="CENTER",
                long_mode="WRAP",
                border=3, border_color=green_color, border_radius=12,
                clear_canvas=True, fullscreen=True,
                leds=[green_color] * 8
            )

            time.sleep(3.5)
            pad.stop_custom_display()
    except Exception as e:
        sys.stderr.write(f"[Macropad Hook] Erreur affichage statut vert: {e}\n")


def reset_display():
    """Restaure l'affichage et les boutons par défaut du macropad."""
    try:
        with EezBotFun() as pad:
            pad.stop_custom_display()
    except Exception:
        pass


def setup_profile_keys(profile: int = 3):
    """Programme les touches 1 à 8 sur le profil spécifié pour Claude Code."""
    print(f"Programmation des touches pour Claude Code sur le profil {profile}...")
    try:
        with EezBotFun() as pad:
            pad.configure_claude_profile(profile=profile)
            print(f"[OK] Profil {profile} configuré avec succès !")
            print("  - Touches 1 à 6 : '1{enter}' à '6{enter}' (sélection de choix)")
            print("  - Touche 7      : 'y{enter}' (Yes / Valider)")
            print("  - Touche 8      : 'n{enter}' (No / Refuser)")
    except Exception as e:
        print(f"Erreur configuration profil : {e}")


def handle_payload(payload: dict):
    """Traite le payload JSON reçu de Claude Code sur stdin."""
    event_name = payload.get("hook_event_name", "")

    # 1. Événement PRE_TOOL_USE (Détection immédiate des questions interactives Claude Code)
    # Permet d'afficher la question à choix multiples AVANT que l'utilisateur ne réponde !
    if event_name == "PreToolUse":
        tool_name = payload.get("tool_name", "")
        tool_input = payload.get("tool_input", {})

        if tool_name in ("AskUserQuestion", "AskFollowupQuestion", "ask_question", "ExitPlanMode"):
            if tool_name == "ExitPlanMode":
                show_yes_no_alert("Quitter le mode plan et exécuter les modifications ?")
                return

            questions = tool_input.get("questions")
            if isinstance(questions, list) and len(questions) > 0:
                q_item = questions[0]
                q_title = q_item.get("question") or q_item.get("header") or "Choix à faire :"
                raw_opts = q_item.get("options", [])
                choices = []
                for idx, opt in enumerate(raw_opts, start=1):
                    if isinstance(opt, dict):
                        label = opt.get("label") or opt.get("description") or f"Option {idx}"
                    else:
                        label = str(opt)
                    choices.append((idx, label))
                if choices:
                    show_choices_alert(q_title, choices)
                    return
            elif "question" in tool_input:
                q_title = tool_input.get("question", "")
                raw_opts = tool_input.get("options", [])
                choices = []
                for idx, opt in enumerate(raw_opts, start=1):
                    label = opt.get("label", str(opt)) if isinstance(opt, dict) else str(opt)
                    choices.append((idx, label))
                if choices:
                    show_choices_alert(q_title, choices)
                    return
        return

    # 2. Événement PERMISSION_REQUEST (Claude demande la validation d'une commande/outil)
    if event_name == "PermissionRequest":
        tool_name = payload.get("tool_name", "Outil")
        tool_input = payload.get("tool_input", {})
        cmd = tool_input.get("command") or tool_input.get("file_path") or tool_input.get("description") or ""
        msg = f"{tool_name}: {cmd}" if cmd else f"Exécution demandée pour l'outil : {tool_name}"
        show_permission_alert(msg)
        return

    # 3. Événement POST_TOOL_USE (L'utilisateur a répondu à la question ou l'outil s'est terminé)
    if event_name == "PostToolUse":
        tool_name = payload.get("tool_name", "")
        if tool_name in ("AskUserQuestion", "AskFollowupQuestion", "ExitPlanMode"):
            # L'utilisateur a répondu, on restaure l'affichage en attendant que Claude finisse
            reset_display()
        return

    # 4. Événement NOTIFICATION (permission demandée, alerte système, etc.)
    if event_name == "Notification":
        notif_type = payload.get("notification_type", "prompt")
        msg = payload.get("message", "")
        transcript_path = payload.get("transcript_path", "")

        if not msg and transcript_path:
            msg = extract_last_assistant_message(transcript_path)

        if not msg:
            if notif_type == "permission_prompt":
                msg = "Autorisation d'outil demandée dans le terminal."
            elif notif_type == "idle_prompt":
                msg = "En attente de vos instructions..."
            else:
                msg = "Votre attention est demandée."

        # Demande de permission
        if notif_type == "permission_prompt":
            show_permission_alert(msg)
            return

        # Vérifier si la notification contient des choix multiples
        has_choices, q_title, choices = extract_choices(msg)
        if has_choices:
            show_choices_alert(q_title, choices)
            return

        clean_msg = clean_markdown(msg)
        if len(clean_msg) > 175:
            clean_msg = clean_msg[:172].rstrip() + "..."
        show_question_alert(clean_msg, title="{warning} ATTENTION REQUISE")
        return

    # 5. Événement STOP (Fin de tour de parole de Claude)
    if event_name == "Stop":
        last_msg = payload.get("last_assistant_message", "")
        transcript_path = payload.get("transcript_path", "")

        if not last_msg and transcript_path:
            last_msg = extract_last_assistant_message(transcript_path)

        # A) Tester si le message se termine par des CHOIX MULTIPLES
        has_choices, q_title, choices = extract_choices(last_msg)
        if has_choices:
            show_choices_alert(q_title, choices)
            return

        # B) Tester si c'est une question binaire Oui / Non
        is_question, display_text = analyze_assistant_message(last_msg)
        if is_question:
            if is_yes_no_question(display_text):
                show_yes_no_alert(display_text)
            else:
                show_question_alert(display_text, title="{warning} QUESTION DE CLAUDE")
        else:
            show_finished_status(display_text)
        return

    # 6. Événement USER_PROMPT_SUBMIT (L'utilisateur a répondu / tapé une commande)
    if event_name == "UserPromptSubmit":
        reset_display()
        return

    # Événement générique / fallback
    msg = payload.get("message") or payload.get("last_assistant_message") or ""
    if msg:
        has_choices, q_title, choices = extract_choices(msg)
        if has_choices:
            show_choices_alert(q_title, choices)
            return
        is_q, text = analyze_assistant_message(msg)
        if is_q:
            show_question_alert(text)
        else:
            show_finished_status(text)
    else:
        reset_display()


def main():
    if "--setup-keys" in sys.argv:
        p = 3
        idx = sys.argv.index("--setup-keys")
        if idx + 1 < len(sys.argv) and sys.argv[idx + 1].isdigit():
            p = int(sys.argv[idx + 1])
        setup_profile_keys(profile=p)
        sys.exit(0)

    if "--choices" in sys.argv:
        show_choices_alert(
            "Quelle option souhaitez-vous choisir ?",
            [
                (1, "Exécuter les tests unitaires"),
                (2, "Compiler le binaire mc-08"),
                (3, "Mettre à jour la documentation"),
            ],
        )
        sys.exit(0)

    if "--yes-no" in sys.argv:
        custom_text = " ".join([a for a in sys.argv[1:] if not a.startswith("--")])
        show_yes_no_alert(custom_text or "Souhaitez-vous appliquer ces modifications ?")
        sys.exit(0)

    if "--permission" in sys.argv:
        show_permission_alert("Bash: npm test -- --coverage")
        sys.exit(0)

    if "--done" in sys.argv:
        custom_text = " ".join([a for a in sys.argv[1:] if not a.startswith("--")])
        show_finished_status(custom_text or "Tâche terminée avec succès !")
        sys.exit(0)

    if "--question" in sys.argv:
        custom_text = " ".join([a for a in sys.argv[1:] if not a.startswith("--")])
        show_question_alert(custom_text or "Souhaitez-vous continuer ?")
        sys.exit(0)

    if "--submit" in sys.argv or "--reset" in sys.argv:
        reset_display()
        sys.exit(0)

    raw_input = ""
    if not sys.stdin.isatty():
        try:
            raw_input = sys.stdin.read()
        except Exception:
            raw_input = ""

    if raw_input.strip():
        try:
            payload = json.loads(raw_input)
            handle_payload(payload)
            sys.exit(0)
        except json.JSONDecodeError:
            has_c, q, c = extract_choices(raw_input)
            if has_c:
                show_choices_alert(q, c)
            else:
                is_q, text = analyze_assistant_message(raw_input)
                if is_q:
                    show_question_alert(text)
                else:
                    show_finished_status(text)
            sys.exit(0)

    print("Usage: claude_hook.py [--choices | --permission | --question | --done | --reset | --setup-keys [profile]]")
    sys.exit(0)


if __name__ == "__main__":
    main()
