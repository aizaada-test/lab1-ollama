"""Lab 5 guardrails: same rules and 7 models as Lab 3, plus optional SKILLs.
The guardrails run FIRST. A skill only changes HOW a GREEN/ORANGE answer is written.

GREEN  = in scope: Computer Science, Linux, Cybersecurity (defensive / learning)
ORANGE = related to tech, but not the main topic (general IT, math, careers, gadgets)
RED    = dangerous / harmful request, OR not appropriate for this assistant (off topic)

Two layers:
  Layer 1 - RULES: fast keyword and pattern checks (you can read and edit them below).
  Layer 2 - AI CLASSIFIER: if no rule matches, the LLM itself labels the question.
"""
import json
import re
import urllib.request

OLLAMA_URL = "http://localhost:11434"
# The 7 models compared in Lab 3 (smallest to largest).
# Pull each one first with:  ollama pull <name>
MODELS = [
    {"name": "llama3.2:1b",  "label": "Llama 3.2 - 1B",  "size": "1.3 GB"},
    {"name": "gemma3:1b",    "label": "Gemma 3 - 1B",    "size": "0.8 GB"},
    {"name": "qwen2.5:1.5b", "label": "Qwen 2.5 - 1.5B", "size": "1.0 GB"},
    {"name": "llama3.2:3b",  "label": "Llama 3.2 - 3B",  "size": "2.0 GB"},
    {"name": "phi4-mini",    "label": "Phi-4 mini - 3.8B", "size": "2.5 GB"},
    {"name": "gemma3:4b",    "label": "Gemma 3 - 4B",    "size": "3.3 GB"},
    {"name": "llama3.1:8b",  "label": "Llama 3.1 - 8B",  "size": "4.9 GB"},
]
MODEL_NAMES = [m["name"] for m in MODELS]
MODEL = MODELS[0]["name"]   # default model (same as Lab 2)

# ---------------------------------------------------------------- Layer 1: rules
# RED: harmful intent. Each pattern looks for an ACTION + a TARGET, so that
# "what is ransomware?" (learning) is allowed but "write ransomware" is blocked.
RED_PATTERNS = [
    r"\b(write|create|build|make|code|develop|generate)\b.{0,40}\b(malware|ransomware|virus|keylogger|trojan|worm|botnet|spyware|rootkit)\b",
    r"\b(hack|break into|get into|access)\b.{0,40}\b(someone|somebody|my (ex|neighbou?r|friend|boss|teacher)|neighbou?r'?s?|other people'?s?|another person'?s?)\b",
    r"\b(hack|crack|break into)\b.{0,30}\b(instagram|facebook|whatsapp|tiktok|gmail|email|snapchat|bank)\b",
    r"\b(steal|dump|grab|harvest)\b.{0,30}\b(password|credential|credit card|cookie|session|data)s?\b",
    r"\b(ddos|dos attack|flood)\b.{0,30}\b(website|site|server|school|company|ip)\b",
    r"\b(bypass|disable|evade)\b.{0,30}\b(antivirus|edr|detection|school filter|paywall|license)\b",
    r"\b(phishing (page|email|site|kit))\b",
    r"\b(bomb|explosive|weapon|poison|kill|suicide|drugs?)\b",
]

GREEN_KEYWORDS = [
    # Linux
    "linux", "ubuntu", "debian", "bash", "shell", "terminal", "command", "chmod", "chown",
    "sudo", "grep", "systemd", "kernel", "file system", "filesystem", "permission", "cron",
    "ssh", "apt", "process", "directory",
    # Cybersecurity (defensive / learning)
    "firewall", "iptables", "ufw", "encryption", "hashing", "hash", "tls", "ssl", "vpn",
    "malware", "ransomware", "phishing", "vulnerability", "cve", "sql injection", "xss",
    "authentication", "2fa", "mfa", "password policy", "intrusion", "ids", "ips",
    "cybersecurity", "security", "nmap", "port", "secure",
    # Computer Science
    "algorithm", "data structure", "python", "java", "c++", "programming", "code",
    "function", "variable", "loop", "recursion", "big o", "database", "sql", "network",
    "tcp", "udp", "ip address", "dns", "http", "operating system", "compiler", "git",
    "computer science", "binary", "array", "linked list", "stack", "queue",
]

# Checked BEFORE green: career questions are close to the course but not the main topic.
ORANGE_FIRST_KEYWORDS = ["career", "job", "salary", "certification", "resume", "interview"]

ORANGE_KEYWORDS = [
    "laptop", "computer", "phone", "smartphone", "windows", "macbook", "iphone", "android",
    "excel", "word", "printer", "monitor", "keyboard", "gaming", "graphics card", "gpu",
    "math", "statistics",
    "ai", "chatgpt", "internet", "wifi", "router", "cloud", "website",
]


def _contains(text, words):
    for w in words:
        if re.search(r"\b" + re.escape(w) + r"\b", text):
            return w
    return None


def check_rules(question):
    """Layer 1. Returns (color, reason) or (None, None) if no rule matched."""
    q = question.lower()
    for pattern in RED_PATTERNS:
        if re.search(pattern, q):
            return "RED", "Blocked by a safety rule (harmful request)."
    word = _contains(q, ORANGE_FIRST_KEYWORDS)
    if word:
        return "ORANGE", f'Matched related-tech keyword: "{word}".'
    word = _contains(q, GREEN_KEYWORDS)
    if word:
        return "GREEN", f'Matched course keyword: "{word}".'
    word = _contains(q, ORANGE_KEYWORDS)
    if word:
        return "ORANGE", f'Matched related-tech keyword: "{word}".'
    return None, None


# ---------------------------------------------------------- Layer 2: AI classifier
CLASSIFIER_PROMPT = """You are a strict classifier for a university course assistant.
The course topics are: Computer Science, Linux, and Cybersecurity.
Label the user's question with exactly one category:
GREEN  - directly about Computer Science, Linux, or defensive Cybersecurity.
ORANGE - related to technology or IT, but not directly one of the course topics.
RED    - harmful, illegal, unsafe, or not related to technology at all.
Reply ONLY with JSON like {"category": "GREEN", "reason": "short reason"}.

Question: """


def ask_ollama(prompt, model=MODEL, system=None, max_tokens=400, json_mode=False):
    body = {"model": model, "prompt": prompt, "stream": False,
            "options": {"temperature": 0, "num_predict": max_tokens}}
    if system:
        body["system"] = system
    if json_mode:
        body["format"] = "json"
    req = urllib.request.Request(OLLAMA_URL + "/api/generate",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r).get("response", "")


def classify_with_ai(question, model=MODEL):
    """Layer 2. Asks the SELECTED model to label the question."""
    raw = ask_ollama(CLASSIFIER_PROMPT + question, model=model, max_tokens=60, json_mode=True)
    try:
        data = json.loads(raw)
        color = str(data.get("category", "")).upper().strip()
        reason = str(data.get("reason", "")).strip() or "No reason given."
    except json.JSONDecodeError:
        color, reason = "", ""
    if color not in ("GREEN", "ORANGE", "RED"):
        # The small model did not answer clearly -> be careful.
        return "ORANGE", "AI classifier was unsure, so the answer is marked as caution."
    return color, "AI classifier: " + reason


def classify(question, model=MODEL):
    """Returns (color, reason, layer)."""
    color, reason = check_rules(question)
    if color:
        return color, reason, "rules"
    color, reason = classify_with_ai(question, model)
    return color, reason, "ai"


# ------------------------------------------------------------- Answer step
SYSTEM_GREEN = ("You are a helpful teaching assistant for a university course on "
                "Computer Science, Linux and Cybersecurity. Answer clearly in under "
                "150 words. For security topics, explain concepts and how to defend, "
                "never give step-by-step attack instructions.")

SYSTEM_ORANGE = ("You are a teaching assistant for Computer Science, Linux and "
                 "Cybersecurity. This question is only partly related to the course. "
                 "Answer in at most 3 short sentences, then add one sentence connecting "
                 "it to Computer Science, Linux or Cybersecurity.")

RED_MESSAGE = ("I can't help with this question. I am a course assistant for Computer "
               "Science, Linux and Cybersecurity, and this request is unsafe or outside "
               "what I was built for. Try asking about Linux commands, networking, "
               "programming, or how to protect systems.")


def add_skill(system, skill):
    """Put the skill's instructions after the normal system prompt."""
    if not skill:
        return system
    return (system + "\n\nYou must follow this SKILL when you answer.\n"
            f"### SKILL: {skill['name']}\n{skill['text']}")


def answer(question, model=MODEL, skill=None):
    """Full pipeline: classify, then answer according to the color (and the skill)."""
    if model not in MODEL_NAMES:
        raise ValueError(f"Unknown model: {model}")
    color, reason, layer = classify(question, model)
    used = None
    if color == "RED":
        text = RED_MESSAGE                      # blocked: the model and the skill are NOT used
    elif color == "ORANGE":
        text = ask_ollama(question, model=model, system=add_skill(SYSTEM_ORANGE, skill), max_tokens=250)
        used = skill["name"] if skill else None
    else:
        text = ask_ollama(question, model=model, system=add_skill(SYSTEM_GREEN, skill), max_tokens=400)
        used = skill["name"] if skill else None
    return {"color": color, "reason": reason, "layer": layer, "answer": text,
            "model": model, "skill": used}


def installed_models():
    """Names of the models already pulled into Ollama (from /api/tags)."""
    with urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=5) as r:
        tags = json.load(r).get("models", [])
    names = set()
    for t in tags:
        n = t.get("name", "")
        names.add(n)
        if n.endswith(":latest"):
            names.add(n[: -len(":latest")])
    return names
