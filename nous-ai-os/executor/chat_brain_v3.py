from __future__ import annotations

import ast
import json
import operator as op
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from executor.natural_chat_orchestrator import natural_chat_answer, is_natural_chat

from executor.document_chat_bridge import document_chat_answer, format_document_answer
from executor.internet_search_engine import answer_from_web
from executor.deep_research_engine import deep_research
from executor.url_reader_engine import summarize_url
from executor.chat_capabilities import capability_text
from executor.conversation_manager import append_turn, conversation_context
from executor.conversation_summary_engine import update_conversation_summary, summary_context
from executor.conversation_search_engine import answer_from_conversations, cross_conversation_context
from executor.conversation_title_engine import generate_conversation_title
from executor.knowledge_memory_engine import answer_from_knowledge_memory, learn_from_chat_result, coding_context
from executor.error_learning_engine import engineering_memory_context

DATA = Path("data")
REPORTS = DATA / "reports"
CHAT_MEMORY = DATA / "chat_memory_v3.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def remember_turn(user: str, answer: str, mode: str) -> None:
    memory = load_json(CHAT_MEMORY, [])
    if not isinstance(memory, list):
        memory = []

    memory.append({
        "time": now_iso(),
        "user": user,
        "answer": answer,
        "mode": mode,
    })

    save_json(CHAT_MEMORY, memory[-80:])


def norm(text: str) -> str:
    return (text or "").strip().lower()


def is_explicit_command(message: str) -> bool:
    m = norm(message)
    return (
        m.startswith("/")
        or m.startswith("plan ")
        or m.startswith("run ")
        or m.startswith("mission ")
        or m.startswith("task ")
        or m.startswith("deploy ")
        or m.startswith("φτιάξε αποστολή")
        or m.startswith("δημιούργησε αποστολή")
        or m.startswith("κανε αποστολη")
        or m.startswith("κάνε αποστολή")
    )




def has_general_knowledge_question(message: str) -> bool:
    """
    Επιστρέφει True ΜΟΝΟ για ερωτήσεις εγκυκλοπαιδικής γνώσης
    που ξεκινούν με συγκεκριμένα patterns.
    ΔΕΝ πυροδοτείται μόνο από "?" — αυτό ήταν πάρα πλατύ.
    """
    m = norm(message)
    if not m:
        return False

    # Ερωτήσεις γνώμης/εκτίμησης → ΟΧΙ web search
    opinion_starters = [
        "πιστεύεις", "νομίζεις", "νομιζεις", "θεωρείς", "θεωρεις",
        "χρειάζεσαι", "χρειαζεσαι", "θέλεις", "θελεις",
        "πώς νιώθεις", "πως νιωθεις",
        "τι πιστεύεις", "τι νομίζεις",
        "αισθάνεσαι", "αισθανεσαι",
        "μπορείς να", "μπορεις να",
        "θα μπορούσες", "θα μπορουσες",
    ]
    if any(m.startswith(x) or x in m for x in opinion_starters):
        return False

    # Ερωτήσεις για τον ΝΟΥΣ/το σύστημα → ΟΧΙ web search
    if any(x in m for x in ["νους", "νουσ", "nous", "σύστημα", "συστημα", "εσύ", "εσυ"]):
        return False

    starters = [
        "τι είναι", "τι ειναι",
        "ποιος είναι", "ποιος ειναι",
        "ποια είναι", "ποια ειναι",
        "πότε έγινε", "ποτε εγινε",
        "πού βρίσκεται", "που βρισκεται",
        "γιατί συμβαίνει", "γιατι συμβαινει",
        "εξήγησε", "εξηγησε",
        "πες μου για",
        "ξέρεις για", "ξερεις για",
        "τι γνωρίζεις", "τι γνωριζεις",
    ]

    return any(m.startswith(x) for x in starters)


def has_document_intent(message: str) -> bool:
    m = norm(message)
    return any(w in m for w in [
        "εγχειρίδιο", "εγχειριδιο", "manual",
        "pdf", "docx", "έγγραφο", "εγγραφο",
        "αρχείο", "αρχειο", "μαθημένο", "μαθημενο",
        "μαθημένα", "μαθημενα", "σύμφωνα με τα έγγραφα",
        "τι λένε τα έγγραφα", "τι λεει το εγχειριδιο",
        "τι λέει το εγχειρίδιο"
    ])






def has_conversation_search_intent(message: str) -> bool:
    m = norm(message)
    return any(x in m for x in [
        "βρες τη συνομιλία",
        "βρες την συνομιλία",
        "ψάξε στις συνομιλίες",
        "ψαξε στις συνομιλιες",
        "παλιά συνομιλία",
        "παλια συνομιλια",
        "παλιές συνομιλίες",
        "παλιες συνομιλιες",
        "σε ποια συνομιλία",
        "σε ποια συνομιλια",
        "conversation search"
    ])


def has_cross_memory_intent(message: str) -> bool:
    m = norm(message)
    return any(x in m for x in [
        "θυμάσαι τι αποφασίσαμε",
        "θυμασαι τι αποφασισαμε",
        "τι είχαμε πει",
        "τι ειχαμε πει",
        "παλιότερα",
        "παλιοτερα",
        "πριν καιρό",
        "πριν καιρο",
        "σε άλλη συνομιλία",
        "σε αλλη συνομιλια",
        "από παλιά συνομιλία",
        "απο παλια συνομιλια"
    ])


def has_deep_research_intent(message: str) -> bool:
    m = norm(message)
    return any(x in m for x in [
        "κάνε βαθιά έρευνα",
        "κανε βαθια ερευνα",
        "deep research",
        "ψάξε βαθιά",
        "ψαξε βαθια",
        "ερεύνησε αναλυτικά",
        "ερευνησε αναλυτικα",
        "άνοιξε πηγές",
        "ανοιξε πηγες"
    ])


def has_internet_intent(message: str) -> bool:
    m = norm(message)
    return any(w in m for w in [
        "ψάξε", "ψαξε", "αναζήτησε", "αναζητησε",
        "internet", "ίντερνετ", "ιντερνετ", "online", "web",
        "τελευταία", "τελευταια", "νέα", "νεα", "ειδήσεις", "ειδησεις",
        "τρέχον", "τρεχον", "σημεριν", "τιμή", "τιμη", "κόστος", "κοστος"
    ])


def has_calc_intent(message: str) -> bool:
    m = norm(message)
    if any(w in m for w in ["υπολόγισε", "υπολογισε", "πόσο κάνει", "ποσο κανει", "calculator"]):
        return True
    return bool(re.fullmatch(r"[0-9\s\+\-\*\/\.\,\(\)%]+", m))


_ALLOWED_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
    ast.Mod: op.mod,
}


def safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](safe_eval(node.left), safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](safe_eval(node.operand))
    raise ValueError("unsafe_expression")


def calculator_answer(message: str) -> str:
    expr = norm(message)
    expr = expr.replace("υπολόγισε", "").replace("υπολογισε", "")
    expr = expr.replace("πόσο κάνει", "").replace("ποσο κανει", "")
    expr = expr.replace(",", ".")
    expr = expr.strip()

    tree = ast.parse(expr, mode="eval")
    result = safe_eval(tree)

    if int(result) == result:
        result = int(result)

    return f"Το αποτέλεσμα είναι: {result}"


def extract_urls(message: str) -> list[str]:
    return re.findall(r"https?://[^\s]+", message or "")


def link_answer(message: str) -> str | None:
    urls = extract_urls(message)
    if not urls:
        return None

    lines = ["Βρήκα τους συνδέσμους που έστειλες:"]
    for i, u in enumerate(urls, 1):
        lines.append(f"{i}. {u}")
    return "\n".join(lines)


def is_about_nous(message: str) -> bool:
    m = norm(message)
    return "νους" in m or "νουσ" in m or "nous" in m


def nous_status_answer() -> str:
    priorities = load_json(DATA / "executive_priorities.json", {})
    summary = load_json(DATA / "executive_state_summary.json", {})

    top = priorities.get("top_action") if isinstance(priorities, dict) else None

    missions = summary.get("missions", {}).get("total", 0) if isinstance(summary, dict) else 0
    reviews = summary.get("pending_reviews", {}).get("total", 0) if isinstance(summary, dict) else 0
    patches = summary.get("patch_proposals", {}).get("total", 0) if isinstance(summary, dict) else 0

    lines = [
        "Για να γίνει ο ΝΟΥΣ πιο κοντά σε πραγματικό AI Agent, οι βασικές βελτιώσεις είναι:",
        "",
        "• Καθαρό chat σαν ChatGPT, χωρίς να δημιουργεί αποστολές μόνος του.",
        "• Καλύτερη σύνθεση απαντήσεων από έγγραφα, μνήμη και internet.",
        "• Upload αρχείων και εικόνων με αυτόματη ανάλυση.",
        "• Web page reader για να διαβάζει ολόκληρες σελίδες και όχι μόνο αποτελέσματα αναζήτησης.",
        "• Conversational memory για συνέχεια στη συζήτηση.",
        "• Πιο αυστηρό mission mode μόνο με ρητή εντολή.",
        "",
        f"Τρέχουσα εικόνα: missions={missions}, pending reviews={reviews}, patch proposals={patches}."
    ]

    if top:
        lines.append("")
        lines.append("Πρώτη προτεραιότητα που βλέπει ο prioritizer:")
        lines.append(f"• {top.get('title', 'Άγνωστο')}")

    return "\n".join(lines)


def casual_answer(message: str) -> str | None:
    m = norm(message)

    if any(x in m for x in ["τι κάνεις", "τι κανεις", "πως είσαι", "πώς είσαι", "πως εισαι"]):
        return (
            "Είμαι εδώ φίλε μου και λειτουργώ κανονικά. "
            "Μπορείς να με ρωτήσεις, να μου δώσεις έγγραφο, να ζητήσεις αναζήτηση internet, "
            "ή να γράψεις /plan για να φτιάξω αποστολή."
        )

    if any(x in m for x in ["γεια", "γειά", "καλημέρα", "καλημερα", "καλησπέρα", "καλησπερα"]):
        return "Γεια σου φίλε μου. Είμαι έτοιμος. Τι θέλεις να δούμε;"

    if is_about_nous(message) and any(x in m for x in [
        "βελτι", "καλυτερ", "πρέπει", "πρεπει", "λείπει", "λειπει",
        "αναβάθμι", "αναβαθμι", "χρειάζεσαι", "χρειαζεσαι",
        "αδυναμ", "αδυνατ", "μπορείς", "μπορεις", "ικανότητ", "ικανοτητ",
    ]):
        return nous_status_answer()

    return None




def looks_corrupted_answer(text: str) -> bool:
    """Conservative check — prefers keeping a borderline answer over
    replacing a valid one with the fallback."""
    t = str(text or "").strip()
    if not t or len(t) < 3:
        return True

    bad_fragments = [
        "επιδελιώστα",
        "κραταγωγή",
        "έπληθιστε",
        "ακριηζον",
        "ηπαγωγή",
    ]
    low = t.lower()
    if any(x in low for x in bad_fragments):
        return True

    # Only flag extreme weird-char ratios (Cyrillic mixed in Greek, etc)
    weird = sum(
        1 for ch in t
        if ord(ch) > 127
        and not ("Ͱ" <= ch <= "Ͽ")
        and not ("ἀ" <= ch <= "῿")
        and not ("̀" <= ch <= "ͯ")
        and ch not in "€–—“”‘’•…°·"
    )
    if weird > max(15, len(t) * 0.15):
        return True

    return False


def safe_llm_fallback() -> str:
    return (
        "Δεν είμαι βέβαιος για την απάντηση που πήγα να δώσω, "
        "οπότε δεν την κρατάω ως αξιόπιστη. Μπορείς να το διατυπώσεις λίγο πιο συγκεκριμένα;"
    )


def document_context_for_llm(message: str) -> str:
    """Search stored documents and return relevant excerpts for LLM context.
    Always runs if documents exist — no keyword trigger needed."""
    try:
        from executor.document_intelligence_engine import answer_from_documents, status as doc_status
        st = doc_status()
        if not st.get("chunks", 0):
            return ""
        result = answer_from_documents(message, limit=4)
        sources = result.get("sources", [])
        if not sources:
            return ""
        parts = []
        for src in sources[:3]:
            excerpt = str(src.get("excerpt", "")).strip()
            doc_name = src.get("document", "")
            if excerpt:
                parts.append(f"[{doc_name}]: {excerpt[:500]}")
        if parts:
            return "Σχετικά αποσπάσματα από ανεβασμένα έγγραφα:\n" + "\n\n".join(parts)
    except Exception:
        pass
    return ""


def build_llm_turns(message: str, conversation_id: str | None = None) -> list[dict]:
    """Build multi-turn messages list from recent chat history."""
    memory = load_json(CHAT_MEMORY, [])
    turns: list[dict] = []

    if isinstance(memory, list):
        clean_items = []
        for item in memory:
            if not isinstance(item, dict):
                continue
            u = str(item.get("user", "")).strip()
            a = str(item.get("answer", "")).strip()
            mode = str(item.get("mode", ""))
            if not u or not a:
                continue
            if mode in {"memory_recall", "system_status", "missions_list", "goals_list"}:
                continue
            clean_items.append((u, a))

        for u, a in clean_items[-6:]:
            if len(a) > 400:
                a = a[:400].rstrip() + "..."
            turns.append({"role": "user", "content": u})
            turns.append({"role": "assistant", "content": a})

    turns.append({"role": "user", "content": message})
    return turns


def try_llm_answer(message: str, conversation_id: str | None = None) -> str | None:
    try:
        from executor.remote_llm import ask_with_turns
    except Exception:
        return None

    code_ctx = coding_context(message)
    eng_ctx = engineering_memory_context(message)
    doc_ctx = document_context_for_llm(message)

    system_extra = ""
    if doc_ctx:
        system_extra += f"\n\n{doc_ctx}"
    if code_ctx:
        system_extra += f"\n\nΠλαίσιο κώδικα:\n{code_ctx}"
    if eng_ctx:
        system_extra += f"\n\nΜνήμη μηχανικής:\n{eng_ctx}"

    system = (
        "Είσαι ο ΝΟΥΣ, έξυπνος AI βοηθός. "
        "Απάντα σε φυσικά ελληνικά, σύντομα και ουσιαστικά. "
        "Μην δημιουργείς αποστολές, μην δίνεις JSON. "
        "Αν κάτι δεν το ξέρεις, πες το ειλικρινά."
        + system_extra
    )

    turns = build_llm_turns(message, conversation_id)

    try:
        result = ask_with_turns(turns, system=system)
    except Exception:
        return None

    if isinstance(result, dict):
        candidate = result.get("response", "")
        if candidate and isinstance(candidate, str) and candidate.strip():
            if looks_corrupted_answer(candidate):
                return safe_llm_fallback()
            return candidate.strip()

    return None






def recent_chat_context(limit: int = 3) -> str:
    memory = load_json(CHAT_MEMORY, [])

    if not isinstance(memory, list) or not memory:
        return ""

    clean_items = []

    for item in memory:
        if not isinstance(item, dict):
            continue

        u = str(item.get("user", "")).strip()
        a = str(item.get("answer", "")).strip()
        mode = str(item.get("mode", "")).strip()

        if not u or not a:
            continue

        ulow = u.lower()

        if any(x in ulow for x in ["θυμάσαι", "θυμασαι", "τι είπα", "τι ειπα"]):
            continue

        if mode in {"memory_recall"}:
            continue

        clean_items.append((u, a))

    recent = clean_items[-limit:]
    lines = []

    for u, a in recent:
        if len(a) > 180:
            a = a[:180].rstrip() + "..."

        lines.append(f"• Εσύ: {u}\n  ΝΟΥΣ: {a}")

    return "\n\n".join(lines)



def memory_question_answer(message: str, conversation_id: str | None = None) -> str | None:
    m = norm(message)

    if not any(x in m for x in [
        "τι είπα",
        "τι ειπα",
        "τι συζητάμε",
        "τι συζηταμε",
        "θυμάσαι",
        "θυμασαι",
        "πριν",
        "προηγουμένως",
        "προηγουμενως",
        "εδώ",
        "εδω"
    ]):
        return None

    active_ctx = conversation_context(conversation_id, 8) if conversation_id else ""

    if active_ctx:
        return "Στην ενεργή συνομιλία θυμάμαι:\n\n" + active_ctx

    ctx = recent_chat_context(3)

    if not ctx:
        return "Δεν έχω ακόμα αρκετό χρήσιμο πρόσφατο ιστορικό συνομιλίας."

    return "Από την πρόσφατη συνομιλία θυμάμαι:\n\n" + ctx


def summarize_search_results(web: dict[str, Any]) -> str:
    results = web.get("results", [])
    if not results:
        return web.get("answer", "Δεν βρήκα καθαρά αποτελέσματα.")

    lines = ["Βρήκα τα εξής βασικά σημεία:"]
    for item in results[:3]:
        title = item.get("title", "Αποτέλεσμα")
        snippet = item.get("snippet", "")
        url = item.get("url", "")
        if len(snippet) > 260:
            snippet = snippet[:260].rstrip() + "..."
        lines.append("")
        lines.append(f"• {title}")
        if snippet:
            lines.append(f"  {snippet}")
        if url:
            lines.append(f"  Πηγή: {url}")

    return "\n".join(lines)




def capability_answer(message: str) -> str | None:
    m = norm(message)
    keys = [
        "τι μπορείς", "τι μπορεις", "δυνατότητες", "δυνατοτητες",
        "διαβάζεις εικόνες", "διαβαζεις εικονες",
        "διαβάζεις αρχεία", "διαβαζεις αρχεια",
        "αρχεία και εικόνες", "αρχεια και εικονες",
        "υποστηρίζεις", "υποστηριζεις",
        "capabilities"
    ]
    if any(k in m for k in keys):
        return capability_text()
    return None




def user_statement_answer(message: str) -> str | None:
    m = norm(message)

    statement_starts = [
        "μιλάμε για", "μιλαμε για",
        "συζητάμε για", "συζηταμε για",
        "θέλω να θυμάσαι", "θελω να θυμασαι",
        "κρατάμε ότι", "κραταμε οτι",
        "σημείωσε", "σημειωσε",
        "να θυμάσαι", "να θυμασαι",
        "θέλω να", "θελω να",
        "επίσης θέλω", "επισης θελω",
        "θέλω επίσης", "θελω επισης"
    ]

    if any(m.startswith(x) for x in statement_starts):
        return (
            "Το κρατάω στην ενεργή συνομιλία. "
            "Όταν συνεχίσουμε από αυτή τη συνομιλία, θα μπορώ να το χρησιμοποιήσω ως πλαίσιο."
        )

    return None




def identity_answer(message: str) -> str | None:
    m = norm(message)

    if any(x in m for x in [
        "με λένε", "με λενε", "το όνομά μου", "το ονομα μου",
        "εμένα με λένε", "εμενα με λενε"
    ]):
        return "Χάρηκα Τραϊανέ. Εμένα μπορείς να με λες ΝΟΥΣ. Είμαι ο προσωπικός σου βοηθός μέσα στο NOUS AI OS."

    if any(x in m for x in [
        "εσένα", "εσενα", "πως σε λένε", "πώς σε λένε",
        "πως σε λενε", "πώς σε λενε", "ποιος είσαι", "ποιος εισαι"
    ]):
        return "Εμένα με λένε ΝΟΥΣ. Είμαι ο προσωπικός σου AI βοηθός και είμαι εδώ για συζήτηση, κώδικα, έρευνα, έγγραφα, μνήμη και αποστολές όταν μου το ζητάς ρητά."

    return None


def should_skip_knowledge_and_web(message: str) -> bool:
    """
    True → μη χρησιμοποιείς knowledge_memory / web search.
    Ισχύει για casual chat, ερωτήσεις γνώμης, ερωτήσεις για τον ίδιο τον ΝΟΥΣ.
    """
    m = norm(message)

    # Casual / identity patterns
    casual_patterns = [
        "τι κάνεις", "τι κανεις",
        "τι μπορείς να κάνεις", "τι μπορεις να κανεις",
        "τι είναι να κάνεις", "τι ειναι να κανεις",
        "και τι μπορείς", "και τι μπορεις",
        "εμένα με λένε", "εμενα με λενε",
        "με λένε", "με λενε",
        "εσένα", "εσενα",
        "ποιος είσαι", "ποιος εισαι",
        "πως σε λένε", "πως σε λενε",
        "πώς σε λένε", "πώς σε λενε",
    ]
    if any(x in m for x in casual_patterns):
        return True

    # Ερωτήσεις γνώμης / εκτίμησης — ο LLM απαντά απευθείας
    opinion_patterns = [
        "πιστεύεις", "νομίζεις", "νομιζεις",
        "θεωρείς", "θεωρεις",
        "πώς νιώθεις", "πως νιωθεις",
        "αισθάνεσαι", "αισθανεσαι",
        "τι πιστεύεις", "τι νομιζεις",
        "τι γνώμη", "τι γνωμη",
        "θα ήθελες", "θα ηθελες",
    ]
    if any(x in m for x in opinion_patterns):
        return True

    # Ερωτήσεις για τον ΝΟΥΣ / το σύστημα / τον εαυτό του
    if any(x in m for x in ["νους", "νουσ", "nous"]):
        nous_self_patterns = [
            "χρειάζεσαι", "χρειαζεσαι",
            "αναβάθμι", "αναβαθμι",
            "βελτίωση", "βελτιωση",
            "βελτιώσεις", "βελτιωσεις",
            "αδυναμίες", "αδυναμιες",
            "δυνατότητες", "δυνατοτητες",
            "μπορείς", "μπορεις",
            "ικανότητες", "ικανοτητες",
            "λειτουργε", "τρέχεις", "τρεχεις",
        ]
        if any(x in m for x in nous_self_patterns):
            return True

    return False


def fallback_answer(message: str) -> str:
    return (
        "Σε ακούω. Μπορώ να απαντήσω σε απλή συζήτηση, να ψάξω στα μαθημένα έγγραφα, "
        "να κάνω internet search όταν μου το ζητήσεις, ή να δημιουργήσω αποστολή μόνο με /plan ή /run."
    )


def answer_chat(message: str, conversation_id: str | None = None) -> dict[str, Any] | None:
    if is_explicit_command(message):
        return None

    natural = natural_chat_answer(message)
    if natural is not None:
        return natural

    mode = "normal_chat"
    answer = None
    sources = []

    if has_document_intent(message):
        doc = document_chat_answer(message)
        if doc.get("used_documents") and doc.get("sources"):
            answer = format_document_answer(message)
            sources = [{"document": s.get("document")} for s in doc.get("sources", [])]
            mode = "document_recall"

    if answer is None:
        answer = capability_answer(message)
        if answer is not None:
            mode = "capabilities"

    if answer is None:
        answer = identity_answer(message)
        if answer is not None:
            mode = "identity"

    if answer is None:
        answer = capability_answer(message)
        if answer is not None:
            mode = "capabilities"

    if answer is None:
        answer = casual_answer(message)
        if answer is not None:
            mode = "normal_chat"

    if answer is None and not should_skip_knowledge_and_web(message):
        km = answer_from_knowledge_memory(message)
        if km.get("found"):
            answer = km.get("answer")
            sources = [{"document": h.get("id")} for h in km.get("hits", [])]
            mode = "knowledge_memory"

    if answer is None and has_conversation_search_intent(message):
        conv_search = answer_from_conversations(message)
        answer = conv_search.get("answer") or "Δεν βρήκα σχετικές συνομιλίες."
        sources = [{"document": h.get("conversation_id")} for h in conv_search.get("hits", [])]
        mode = "conversation_search"

    if answer is None and has_cross_memory_intent(message):
        memory = cross_conversation_context(message, limit=5)
        if memory:
            answer = memory
            mode = "cross_conversation_memory"

    if answer is None and has_deep_research_intent(message):
        research = deep_research(message, max_results=5)
        answer = research.get("answer") or "Δεν μπόρεσα να ολοκληρώσω τη βαθιά έρευνα."
        sources = [{"document": s.get("url")} for s in research.get("sources", [])]
        mode = "deep_research"

    if answer is None and has_internet_intent(message):
        web = answer_from_web(message)
        answer = summarize_search_results(web)
        sources = [{"document": r.get("url")} for r in web.get("results", [])[:3]]
        mode = "internet_search"

    if answer is None and has_calc_intent(message):
        try:
            answer = calculator_answer(message)
            mode = "calculator"
        except Exception:
            answer = "Δεν μπόρεσα να υπολογίσω αυτή την έκφραση."
            mode = "calculator_error"

    if answer is None:
        urls = extract_urls(message)
        if urls:
            url_result = summarize_url(urls[0])
            answer = url_result.get("answer") or link_answer(message)
            sources = [{"document": urls[0]}]
            mode = "url_reader"

    if answer is None:
        answer = memory_question_answer(message, conversation_id=conversation_id)
        if answer is not None:
            mode = "memory_recall"

    if answer is None:
        answer = user_statement_answer(message)
        if answer is not None:
            mode = "conversation_note"

    if answer is None:
        answer = casual_answer(message)

    # Agent loop — LLM αποφασίζει ο ίδιος αν θέλει tools ή απαντά απευθείας.
    # Αντικαθιστά την τυφλή web search για γενικές ερωτήσεις.
    if answer is None:
        try:
            from executor.agent_loop import run_agent
            agent_result = run_agent(message, conversation_id=conversation_id)
            if agent_result.get("ok") and agent_result.get("answer"):
                answer = agent_result["answer"]
                mode = agent_result.get("mode", "agent_loop")
                tool_used = agent_result.get("tool_used")
                if tool_used:
                    sources = [{"document": f"tool:{tool_used}"}]
        except Exception:
            pass

    # Fallback: απλό LLM call αν το agent loop απέτυχε
    if answer is None:
        answer = try_llm_answer(message, conversation_id=conversation_id)
        if answer:
            mode = "llm_chat"

    if answer is None:
        answer = fallback_answer(message)

    if looks_corrupted_answer(answer):
        answer = safe_llm_fallback()
        mode = "llm_guard"

    try:
        learn_from_chat_result(message, answer, mode, sources)
    except Exception:
        pass

    remember_turn(message, answer, mode)
    conv = append_turn(
        user_message=message,
        assistant_answer=answer,
        mode=mode,
        conversation_id=conversation_id,
        title=message,
    )

    try:
        if conv.get("conversation_id") and int(conv.get("messages", 0)) >= 10:
            update_conversation_summary(conv.get("conversation_id"))
            generate_conversation_title(conv.get("conversation_id"))
    except Exception:
        pass

    return {
        "ok": True,
        "executed": False,
        "source": "chat_brain_v3",
        "mode": mode,
        "answer": answer,
        "response": answer,
        "text": answer,
        "human_answer": answer,
        "sources": sources,
        "conversation": conv,
        "conversation_id": conv.get("conversation_id"),
        "timestamp": now_iso(),
    }


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "Τι κάνεις;"
    print(json.dumps(answer_chat(q), indent=2, ensure_ascii=False))
