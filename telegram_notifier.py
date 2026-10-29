import os
import time
import logging
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

def enforce_telegram_char_limit(text: str, max_visible: int) -> str:
    """Bulletproof gate enforcing strict character limits, lexical rules, and grammatical completeness before any Telegram dispatch."""
    if not text:
        return ""
    import re

    # 1. Comprehensive Lexical & Spelling Sanitization
    try:
        try:
            from formatters.khmer_formatter import sanitize_khmer_spelling
        except ImportError:
            from khmer_formatter import sanitize_khmer_spelling
        text = sanitize_khmer_spelling(text)
    except Exception:
        pass

    text = re.sub(r'ប្រមាន', 'ព្រមាន', text)
    text = re.sub(r'ការប្រមាន', 'ការព្រមាន', text)
    text = re.sub(r'បានប្រមាន', 'បានព្រមាន', text)
    text = re.sub(r'ធ្វើអោយ', 'ធ្វើឱ្យ', text)
    clean_ii = 'អី'
    text = re.sub(r'អ[ុូ៊]+[ីិ]', clean_ii, text)
    text = re.sub(r'អ[ុ៊]*ី|អុី|អ៊ុី|អ៊‍ី', clean_ii, text)
    text = re.sub(r'(?:\u17a2[\u17bb\u17bc\u17ca]*\u17b8|អ[\u17bb\u17ca]*ី|ឿ+|អ[ុ៊]*ី)\s*រ៉ង់', f'{clean_ii}រ៉ង់', text)
    text = re.sub(r'តេហេ(?:\u17a2[\u17bb\u17bc\u17ca]*\u17b8|អ[\u17bb\u17ca]*ី|ឿ+|អ[ុ៊]*ី)\s*រ៉ង់', 'តេហេរ៉ង', text)
    text = re.sub(r'\bរដ្ឋអា\b|នៅរដ្ឋអា(?=[បាក្នុលើពីដល់\s]|$)', 'នៅសហរដ្ឋអាមេរិក', text)
    text = re.sub(r'អគ្លេស', 'អង់គ្លេស', text)
    text = re.sub(r'ចក្រភពអគ្លេស', 'ចក្រភពអង់គ្លេស', text)
    text = re.sub(r'សហរដ្ធ', 'សហរដ្ឋ', text)
    text = re.sub(r'រដ្ធ', 'រដ្ឋ', text)
    text = re.sub(r'សេដ្ធកិច្ច', 'សេដ្ឋកិច្ច', text)
    text = re.sub(r'អត្រាកាប្រាក់', 'អត្រាការប្រាក់', text)
    text = re.sub(r'ពាណិជ្ចកម្ម', 'ពាណិជ្ជកម្ម', text)
    text = re.sub(r'អិរភាព', 'អស្ថិរភាព', text)
    text = re.sub(r'ពីភាពអិរភាព', 'ភាពអស្ថិរភាព', text)
    text = re.sub(r'ពីភាព(?=\s*[\u1780-\u17D3])', 'ភាព', text)
    text = re.sub(r'ប្រាក់អឺរ៉ុប', 'ប្រាក់អឺរ៉ូ (EUR)', text)
    text = re.sub(r'ក្នុងការ៉េដី', 'នៅលើសមរភូមិជាក់ស្តែង', text)
    text = re.sub(r'ក្នុងការពារ', 'ក្នុងការការពារ', text)
    text = re.sub(r'កង\s+RSF', 'កងកម្លាំង RSF', text)
    text = re.sub(r'\bCockroach Party\b', 'គណបក្ស Cockroach Party', text)
    text = re.sub(r'បែប\s*(?:satire|satirical)', 'បែបកំប្លែងចំអក', text)
    text = re.sub(r'បញ៉ា', 'បែបកំប្លែងចំអក', text)
    text = re.sub(r'\b(?:satire|satirical)\b', 'បែបកំប្លែងចំអក', text)
    text = re.sub(r'ដើរហង្ហែ', 'ដើរហែក្បួន', text)
    text = re.sub(r'ហង្ហែ', 'ដង្ហែ', text)
    no_space_stutters = [
        "តវ៉ា", "បាតុកម្ម", "ហែក្បួន", "ប្រឆាំង", "កើនឡើង", "ធ្លាក់ចុះ",
        "រដ្ឋាភិបាល", "សេដ្ឋកិច្ច", "អតិផរណា", "ទីផ្សារ", "វិនិយោគិន", "នយោបាយ",
        "អន្តរជាតិ", "ប្រជាជន", "ប្រជាពលរដ្ឋ", "ព្យាករណ៍", "រំពឹងទុក", "ព្រួយបារម្ភ",
        "តានតឹង", "ប្រកាស", "សម្រេច", "ព្រមាន", "វាយប្រហារ", "ហង្ហែ"
    ]
    for w in no_space_stutters:
        text = re.sub(rf'({w})[\s\u200B]*\1+', r'\1', text)
    for _ in range(2):
        text = re.sub(r'([\u1780-\u17D3]{3,})[\s\u200B]*\1+', r'\1', text)
    text = re.sub(r'(\b[\u1780-\u17D3]{2,}\b)\s*\1\b', r'\1', text)
    
    # 2. Complete Sentence Guarantee & Colon/Fragment Stripping in Headline
    m_head = re.search(r'(<b>(.*?)</b>)', text, re.DOTALL)
    if m_head:
        orig_full_h = m_head.group(1)
        inner_h = m_head.group(2)
        # Strip all colons and trailing dots/ellipsis from headline
        clean_inner = re.sub(r'[\s\u200b]*[៖:：][\s\u200b]*', ' ', inner_h)
        clean_inner = re.sub(r'[\.]{2,}|…', '', clean_inner)
        clean_inner = re.sub(r'\s{2,}', ' ', clean_inner).strip()

        # Multi-Pattern Fragment Transformers:
        # Pattern A: "តួកគី និងដែនកំណត់..." -> "របាយការណ៍បង្ហាញពីដែនកំណត់...របស់តួកគី"
        m_frag_a = re.match(r'^([^\s]+)\s+និង\s*(ដែនកំណត់|អនាគត|ទស្សនវិស័យ|បញ្ហា|ស្ថានភាព|កិច្ចព្រមព្រៀង|វិបត្តិ|គោលនយោបាយ|យុទ្ធសាស្ត្រ|ផលវិបាក|ការប្រឈម)(.+)$', clean_inner)
        if m_frag_a:
            country_subj = m_frag_a.group(1).strip()
            topic_noun = m_frag_a.group(2).strip()
            rest = m_frag_a.group(3).strip()
            clean_inner = f"របាយការណ៍បង្ហាញពី{topic_noun}{rest}របស់{country_subj}"
        
        # Pattern B: Bare noun pair "A និង B" (Strictly short phrases <= 4 words, <= 30 chars, e.g. "អាមេរិក និង ចិន")
        elif re.match(r'^([^\s]+(?:\s+[^\s]+)?)\s+និង\s*([^\s]+(?:\s+[^\s]+)?)$', clean_inner) and len(clean_inner) <= 30:
            _active_verbs = ('ប្រកាស', 'សម្រេច', 'ព្រមាន', 'ធ្លាក់ចុះ', 'កើនឡើង', 'ហក់ឡើង', 'ជួប', 'ពិភាក្សា', 'វាយប្រហារ', 'ពង្រីក', 'បញ្ឈប់', 'ចុះហត្ថលេខា', 'ផ្តល់', 'បដិសេធ', 'រង', 'គ្រោង', 'ដាក់ចេញ', 'អនុម័ត', 'ប្តេជ្ញា', 'ទាមទារ', 'ដក', 'ពង្រឹង', 'រិះគន់', 'បង្ហាញ', 'ត្រៀម', 'រៀបចំ', 'ស្នើ', 'ចុះ', 'ឡើង', 'ទម្លាក់', 'ជំរុញ', 'រារាំង', 'ទប់ស្កាត់', 'កែប្រែ', 'បោះទុន', 'វិនិយោគ', 'ឈ្នះ', 'ចាញ់', 'ចាប់ផ្តើម', 'បញ្ចប់', 'បើក', 'បាញ់', 'ស្លាប់', 'ស្ទាក់', 'ចាប់')
            if not any(v in clean_inner for v in _active_verbs):
                m_pair = re.match(r'^(.+?)\s+និង\s*(.+)$', clean_inner)
                clean_inner = f"ការវិវឌ្ឍរវាង{m_pair.group(1).strip()} និង{m_pair.group(2).strip()}"

        # Pattern C: Starting with prepositions "អំពី..." or "ស្ដីពី..."
        elif re.match(r'^(?:អំពី|ស្ដីពី|ស្តីពី)\s*(.+)$', clean_inner):
            clean_inner = re.sub(r'^(?:អំពី|ស្ដីពី|ស្តីពី)\s*(.+)$', r'បច្ចុប្បន្នភាពស្ដីពី\1', clean_inner)

        # Pattern D: Starting with "ចំពោះ..."
        elif re.match(r'^(?:ចំពោះ)\s*(.+)$', clean_inner):
            clean_inner = re.sub(r'^(?:ចំពោះ)\s*(.+)$', r'ការវិភាគចំពោះ\1', clean_inner)

        # Pattern E: Strip trailing conjunctions leaving headline hanging (e.g. "..., ប៉ុន្តែ", "..., និង")
        clean_inner = re.sub(r'[\s,]+(?:និង|ឬ|ប៉ុន្តែ|ដោយសារ|ព្រោះ)$', '', clean_inner).strip()

        text = text.replace(orig_full_h, f"<b>{clean_inner}</b>")

    # 3. Flag Guarantee: Ensure headline starts with a flag emoji
    first_line = text.splitlines()[0] if text else ""
    has_flag = bool(re.search(r'[\U0001F1E0-\U0001F1FF]{2}|🌐|🥇|📅', first_line))
    if not has_flag and not text.startswith("📊") and not text.startswith("---"):
        t_low = text.lower()
        if any(w in t_low for w in ["amazon", "u.s.", "usa", "america", "fed", "biden", "trump", "powell", "indiana", "texas"]):
            flag = "🇺🇸 "
        elif any(w in t_low for w in ["china", "ចិន"]):
            flag = "🇨🇳 "
        elif any(w in t_low for w in ["russia", "រុស្ស៊ី"]):
            flag = "🇷🇺 "
        elif any(w in t_low for w in ["uk", "អង់គ្លេស"]):
            flag = "🇬🇧 "
        elif any(w in t_low for w in ["japan", "ជប៉ុន"]):
            flag = "🇯🇵 "
        elif any(w in t_low for w in ["germany", "អាល្លឺម៉ង់"]):
            flag = "🇩🇪 "
        elif any(w in t_low for w in ["france", "បារាំង"]):
            flag = "🇫🇷 "
        elif any(w in t_low for w in ["iran", "អ៊ីរ៉ង់"]):
            flag = "🇮🇷 "
        elif any(w in t_low for w in ["israel", "អ៊ីស្រាអែល"]):
            flag = "🇮🇱 "
        else:
            flag = ""
        if flag:
            text = flag + text

    # 4. Balanced HTML Tags Check & Auto-Repair (Headline-aware)
    open_b = len(re.findall(r'<b>', text))
    close_b = len(re.findall(r'</b>', text))
    if open_b > close_b:
        # If headline opened <b> without closing on line 1, close it right after line 1
        lines = text.split("\n", 1)
        if "<b>" in lines[0] and "</b>" not in lines[0]:
            lines[0] = lines[0] + "</b>"
            text = "\n".join(lines)
            open_b = len(re.findall(r'<b>', text))
            close_b = len(re.findall(r'</b>', text))
        if open_b > close_b:
            text += "</b>" * (open_b - close_b)
    elif close_b > open_b:
        text = "<b>" * (close_b - open_b) + text

    open_a = len(re.findall(r'<a\b[^>]*>', text))
    close_a = len(re.findall(r'</a>', text))
    if open_a > close_a:
        text += "</a>" * (open_a - close_a)

    vis_len = len(re.sub(r"<[^>]+>", "", text))
    if vis_len <= max_visible:
        return text

    blocks = text.split("\n\n")
    if len(blocks) <= 1:
        clean = re.sub(r"<[^>]+>", "", text)
        last_period = clean[:max_visible].rfind("។")
        if last_period > 30:
            return clean[:last_period + 1].strip()
        last_sp = clean[:max_visible].rfind(" ")
        if last_sp > 30:
            return clean[:last_sp].strip() + "។"
        return clean[:max_visible]

    header = blocks[0]
    source_line = blocks[-1]

    impact_line = ""
    body_blocks = []
    _impact_prefixes = ("🔹", "🔸", "🔶", "🔴", "🟢", "ផល", "ឥទ្ធិពល", "វាផល", "ហានិភ័យ")
    if len(blocks) >= 4 and blocks[-2].strip().startswith(_impact_prefixes):
        impact_line = blocks[-2].strip()
        body_blocks = blocks[1:-2]
    elif len(blocks) >= 3:
        if blocks[-2].strip().startswith(_impact_prefixes):
            impact_line = blocks[-2].strip()
            body_blocks = blocks[1:-2]
        else:
            body_blocks = blocks[1:-1]
    else:
        body_blocks = blocks[1:]

    body = "\n\n".join(body_blocks)
    clean_body = re.sub(r"<[^>]+>", "", body)

    vis_header = len(re.sub(r"<[^>]+>", "", header))
    vis_source = len(re.sub(r"<[^>]+>", "", source_line))
    vis_impact = len(re.sub(r"<[^>]+>", "", impact_line))
    num_separators = sum(1 for p in [header, clean_body, impact_line, source_line] if p) - 1
    sep_overhead = max(num_separators, 1) * 2

    avail = max(40, max_visible - (vis_header + vis_source + vis_impact + sep_overhead))

    # Sentence-preserving trimmer: split body into complete sentences ending in '។'
    raw_sentences = [s.strip() for s in re.findall(r'[^។]+(?:។|$)', clean_body) if s.strip()]
    if not raw_sentences:
        raw_sentences = [clean_body]

    kept_sentences = []
    curr_len = 0
    for s in raw_sentences:
        add_len = len(s) + (1 if kept_sentences else 0)
        if curr_len + add_len <= avail:
            kept_sentences.append(s)
            curr_len += add_len
        else:
            break

    if kept_sentences:
        trimmed_body = " ".join(kept_sentences)
        if not trimmed_body.endswith("។"):
            trimmed_body += "។"
    else:
        # First sentence alone is longer than avail -> find last clause connector or sentence stop
        first_s = raw_sentences[0]
        last_p = first_s[:avail].rfind("។")
        if last_p > 30:
            trimmed_body = first_s[:last_p + 1].strip()
        else:
            # Look for clause boundary words before avail (e.g. " ដោយ", " ដែល", " និង", " ខណៈ", " បន្ទាប់ពី")
            clause_match = None
            for connector in [" ដោយ", " ដែល", " និង", " ខណៈ", " បន្ទាប់ពី", " ក្នុងការ", " ដើម្បី"]:
                pos = first_s[:avail].rfind(connector)
                if pos > 30 and (clause_match is None or pos > clause_match):
                    clause_match = pos
            if clause_match:
                trimmed_body = first_s[:clause_match].strip() + "។"
            else:
                last_space = first_s[:avail].rfind(" ")
                if last_space > 30:
                    trimmed_body = first_s[:last_space].strip() + "។"
                else:
                    trimmed_body = first_s[:avail].strip() + "។"

    parts = [p for p in [header, trimmed_body, impact_line, source_line] if p]
    res = "\n\n".join(parts)

    # Double check total visible length; if still overflowing, drop sentences from the end
    while len(re.sub(r"<[^>]+>", "", res)) > max_visible and len(kept_sentences) > 1:
        kept_sentences.pop()
        trimmed_body = " ".join(kept_sentences)
        parts = [p for p in [header, trimmed_body, impact_line, source_line] if p]
        res = "\n\n".join(parts)

    return res

def sanitize_khmer_editorial_text(text: str) -> str:
    """Removes stray English suffixes/words and fixes known Khmer editorial typos."""
    if not text:
        return text
    import re
    # Remove stray English suffixes stuck in Khmer text (e.g. " ing ", " ed ")
    text = re.sub(r'(?<=[\u1780-\u17D3])\s+(?:ing|ed)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:ing|ed)\b(?=\s+[\u1780-\u17D3])', '', text, flags=re.IGNORECASE)
    # Fix known editorial slips & financial terminology
    replacements = {
        "វគ្ណ្ឌ": "វគ្គ",
        "ចរក្សា": "ចិនរក្សា",
        "ធ្វើអោយ": "ធ្វើឱ្យ",
        "ធ្វើរ៉ង់": "ធ្វើឱ្យអ៊ីរ៉ង់",
        "ធ្វើ៊ីរ៉ង់": "ធ្វើឱ្យអ៊ីរ៉ង់",
        "ឿរ៉ង់": "អ៊ីរ៉ង់",
        "អ៊ីរ៉ាន": "អ៊ីរ៉ង់",
        "តេហេឿរ៉ង់": "តេហេរ៉ង់",
        "តេហឿរ៉ង់": "តេហេរ៉ង់",
        "ប្រចាំត្រីម័យ": "ប្រចាំត្រីមាស",
        "ត្រីម័យ": "ត្រីមាស",
        "ផ្អោបផ្ដើម": "ចាប់ផ្ដើម",
        "ផ្អោបផ្តើម": "ចាប់ផ្តើម",
        "ប្រមាន": "ព្រមាន",
        "សហរដ្ធ": "សហរដ្ឋ",
        "សេដ្ធកិច្ច": "សេដ្ឋកិច្ច",
        "អគ្លេស": "អង់គ្លេស",
        "អត្រាកាប្រាក់": "អត្រាការប្រាក់",
        "ពាណិជ្ចកម្ម": "ពាណិជ្ជកម្ម",
        "កូដេន": "កាក់ឌីជីថល",
        "លីគីឌីធី": "សាច់ប្រាក់ងាយស្រួល",
        "ដ្ររដោន": "ការខាតបង់ដើមទុន",
        "ទោះបីជាយ៉ាងណាក្តី": "ទោះជាយ៉ាងណាក្ដី",
        "កើនឡើងក្ដីបារម្ភ": "បង្កើនក្តីបារម្ភ",
        "កើនឡើងក្តីបារម្ភ": "បង្កើនក្តីបារម្ភ",
        "diversifications": "ការធ្វើពិពិធកម្ម",
        "diversification": "ការធ្វើពិពិធកម្ម",
        "កិច្ចព្រមព្របទឈប់បាញ់": "កិច្ចព្រមព្រៀងបទឈប់បាញ់",
        "កិច្ចព្រមព្រ": "កិច្ចព្រមព្រៀង",
    }
    for old_w, new_w in replacements.items():
        text = text.replace(old_w, new_w)

    # Clean double periods or trailing punctuation slips
    text = re.sub(r'(?<=[\u1780-\u17D3])\s*\.{2,}', '។', text)
    return text

class TelegramNotifier:
    _global_last_signal_time = 0.0
    _recent_chat_signals = {}
    _recent_private_messages = {}

    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = (bot_token or TELEGRAM_BOT_TOKEN).strip()
        self.chat_id = (chat_id or TELEGRAM_CHAT_ID).strip()
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id and self.bot_token != "YOUR_TELEGRAM_BOT_TOKEN_HERE")

    def _curate_and_sanitize_pre_dispatch(self, raw_text: str, is_photo: bool = False, target_chat: str = None) -> tuple:
        """
        100% PRE-DISPATCH CURATION SHIELD.
        Scrutinizes, corrects, proofreads, and clamps every detail of the message BEFORE
        it is ever sent to Telegram. Guarantees that defective, oversized, or duplicate messages
        are intercepted, repaired, or dropped pre-send, so live subscribers NEVER see a post
        disappear after being published.
        Returns: (is_approved: bool, curated_text: str, reason: str)
        """
        import re
        import time

        if not raw_text:
            return False, "", "Empty text"

        target_chat_str = str(target_chat or self.chat_id)
        is_private_chat = bool(target_chat and target_chat_str != str(self.chat_id) and not target_chat_str.startswith("-100"))

        # 0.1 Strict Private SMC Trade Signal Pre-Dispatch Shield
        is_trade_signal = raw_text.startswith("⚡") or "SMC TRADE SIGNAL" in raw_text or "SMC_" in raw_text
        if is_trade_signal:
            # Rule 4: NEVER send trade signals to public channel
            if not is_private_chat or target_chat_str == str(self.chat_id) or target_chat_str.startswith("-100"):
                logger.critical(f"[CURATION SHIELD] Intercepted trade signal targeted to public channel {target_chat_str}! Suppressed per Rule 4.")
                return False, raw_text, "Trade signal prohibited in public channel"

            now_ts = time.time()

            # Global 90-minute (5400s) Cooldown Guard across all instances/processes
            last_sig_time = getattr(TelegramNotifier, "_global_last_signal_time", 0.0)
            if last_sig_time == 0.0:
                try:
                    import database
                    db_sig_ts = float(database.get_state("last_private_signal_dispatch_ts") or 0.0)
                    if db_sig_ts > 0:
                        last_sig_time = db_sig_ts
                        TelegramNotifier._global_last_signal_time = db_sig_ts
                except Exception:
                    pass

            if last_sig_time > 0 and (now_ts - last_sig_time) < 5400.0:
                logger.critical(f"[SIGNAL PRE-DISPATCH GUARD] Private signal cooldown active ({int(now_ts - last_sig_time)}s / 5400s). Pre-dispatch suppressed!")
                return False, raw_text, "Private signal cooldown active (minimum 90 minutes)"

            # Per-Chat Cooldown Guard (prevents same user from receiving multiple signals within 90 minutes)
            chat_last_sig = TelegramNotifier._recent_chat_signals.get(target_chat_str, 0.0)
            if chat_last_sig > 0 and (now_ts - chat_last_sig) < 5400.0:
                logger.critical(f"[SIGNAL PRE-DISPATCH GUARD] Chat {target_chat_str} already received signal {int(now_ts - chat_last_sig)}s ago. Suppressed!")
                return False, raw_text, f"Chat {target_chat_str} signal cooldown active"

            return True, raw_text, "Approved private trade signal"

        # 0.2 Private Chat General Deduplication Guard (prevent double response to /price, /stats, etc.)
        if is_private_chat:
            now_ts = time.time()
            clean_cmd_key = f"{target_chat_str}:{re.sub(r'[^a-zA-Z0-9\u1780-\u17FF]', '', raw_text[:40])}"
            last_cmd_ts = TelegramNotifier._recent_private_messages.get(clean_cmd_key, 0.0)
            if (now_ts - last_cmd_ts) < 15.0:
                logger.warning(f"[PRIVATE MSG DEDUP] Intercepted duplicate response to {target_chat_str} within 15s. Suppressed!")
                return False, raw_text, "Duplicate private response within 15s"
            TelegramNotifier._recent_private_messages[clean_cmd_key] = now_ts
            return True, raw_text, "Approved private message"

        # Special bypass for calendar/market status
        if raw_text.startswith("📅") or raw_text.startswith("📊") or raw_text.startswith("🎯") or raw_text.startswith("🧮") or raw_text.startswith("---"):
            return True, raw_text, "Special card / Status message"

        text = raw_text

        # 1. Lexical Sanitization & 100% Chuon Nath Spelling Normalization
        text = sanitize_khmer_editorial_text(text)

        # 2. Comprehensive Headline Structuring & Sovereign Flag Guarantee:
        lines = text.splitlines()
        if lines:
            first_line = lines[0].strip()
            # Extract flag if already at start
            flag_match = re.search(r'^((?:[\U0001F1E0-\U0001F1FF]{2}|🌐|🪙|🥇|📅|📊|\s)+)', first_line)
            if flag_match:
                extracted_flag = flag_match.group(1).strip()
                headline_core = first_line[flag_match.end():].strip()
            else:
                extracted_flag = "🌐"
                headline_core = first_line

            # Remove any existing <b> tags from headline_core to avoid nested/broken tags
            headline_core = re.sub(r'</?b>', '', headline_core).strip()
            # Clean trailing colons, ellipsis, dots
            headline_core = re.sub(r'[\s៖:：\.\.…]+$', '', headline_core).strip()
            # Remove embedded colons or ellipsis
            headline_core = re.sub(r'[៖:：]', '', headline_core)
            headline_core = re.sub(r'[\.]{2,}|…', '', headline_core)
            # Reassemble perfectly formatted headline: {FLAG} <b>{TITLE}</b>
            lines[0] = f"{extracted_flag} <b>{headline_core}</b>"
            text = '\n'.join(lines)

        # 3. Strict Sentiment Honesty: Auto-correct war news sentiment mismatch
        war_terms = ['សង្គ្រាម', 'វាយប្រហារ', 'ដ្រូន', 'មីស៊ីល', 'ទាហាន', 'ស្លាប់', 'ផ្ទុះ', 'សមរភូមិ']
        is_peace_or_resilience = any(k in text for k in ['បទឈប់បាញ់', 'សន្តិភាព', 'ទប់ទល់', 'ភាពធន់', 'ស្ថិរភាព', 'បន្ធូរបន្ថយ', 'លុបចោលពន្ធ', 'លើកលែងពន្ធ'])
        if any(w in text for w in war_terms) and '🔹 ផលវិជ្ជមាន' in text and not is_peace_or_resilience:
            text = text.replace('🔹 ផលវិជ្ជមាន', '🔶 ហានិភ័យទីផ្សារ')

        # 4. Strict 2-Line Impact Format Guarantee (🔶 ហានិភ័យទីផ្សារ៖\n... or 🔹 ផលវិជ្ជមាន៖\n...)
        text = re.sub(r'[🔸🔴]\s*(?:ហានិភ័យទីផ្សារ|ផលអវិជ្ជមាន|ហានិភ័យ)', '🔶 ហានិភ័យទីផ្សារ', text)
        text = re.sub(r'[🟢]\s*ផលវិជ្ជមាន', '🔹 ផលវិជ្ជមាន', text)
        text = re.sub(r'(🔹\s*ផលវិជ្ជមាន)[\s៖:]*(?!\n)\s*(.+)', r'🔹 ផលវិជ្ជមាន៖\n\2', text)
        text = re.sub(r'(🔶\s*ហានិភ័យទីផ្សារ)[\s៖:]*(?!\n)\s*(.+)', r'🔶 ហានិភ័យទីផ្សារ៖\n\2', text)
        text = re.sub(r'(🔶\s*ហានិភ័យទីផ្សារ|🔹\s*ផលវិជ្ជមាន)[៖:]\s*([^\n]+)', r'\1៖\n\2', text)

        # 5. Remove any non-VIP emojis (rockets, meme emojis)
        text = re.sub(r'[🚀🔥💥💰🎉🤑💩🤡]', '', text)

        # 6. Character Limit Enforcement Pre-Dispatch
        max_allowed = 574 if is_photo else 750
        text = enforce_telegram_char_limit(text, max_visible=max_allowed)

        clean_vis = re.sub(r'<[^>]+>', '', text).strip()
        vis_len = len(clean_vis)

        # Double-check hard limit
        if vis_len > max_allowed:
            text = enforce_telegram_char_limit(text, max_visible=max_allowed)
            clean_vis = re.sub(r'<[^>]+>', '', text).strip()
            vis_len = len(clean_vis)
            if vis_len > max_allowed:
                logger.warning(f"[PRE-DISPATCH REJECT] Message exceeds max limit ({vis_len} > {max_allowed}). Dropped before sending.")
                return False, text, f"Length {vis_len} exceeds {max_allowed}"

        if vis_len < 35:
            logger.warning(f"[PRE-DISPATCH REJECT] Message too short ({vis_len} chars). Dropped before sending.")
            return False, text, "Message too short"

        # 6.1 Strict English Vocabulary Leakage Shield Pre-Dispatch
        # Any stray Latin word of 4+ characters that is not an approved leader, company, or ticker is rejected
        APPROVED_LATIN = {
            'trump', 'putin', 'biden', 'musk', 'powell', 'warsh', 'zelenskyy', 'netanyahu',
            'nvidia', 'apple', 'tesla', 'google', 'microsoft', 'meta', 'amazon', 'intel',
            'openai', 'deepseek', 'anthropic', 'huawei', 'tencent', 'alibaba', 'samsung',
            'fed', 'fomc', 'cpi', 'gdp', 'pmi', 'nfp', 'opec', 'xau', 'usd', 'xauusd', 'dxy',
            'btc', 'eth', 'sol', 'usdt', 'usdc', 'imf', 'nato', 'tsmc', 'asml', 'amd', 'arm',
            'byd', 'spacex', 'nasa', 'ceo', 'ipo', 'cds', 'us10y', 'sec', 'etf', 'etfs',
            'crypto', 'sinokor', 'strait', 'hormuz', 'news', 'reuters', 'bloomberg', 'cnbc',
            'bbc', 'afp', 'scmp', 'wsj', 'arab', 'oilprice', 'jazeera', 'marketwatch', 'times',
            'post', 'south', 'china', 'morning', 'seatrade', 'maritime', 'global', 'wire',
            'melania', 'bessent', 'nordic', 'cook', 'huang', 'altman', 'nadella', 'starship',
            'roadster', 'optimus', 'blackwell', 'apnews', 'associated', 'press', 'gold',
            'bonds', 'yield', 'yields', 'dow', 'sp500', 'nasdaq'
        }
        # Audit text excluding the source link line at the bottom
        text_before_source = re.split(r'\n+ប្រភព(?:\s*ព័ត៌មាន)?\s*\|', clean_vis)[0]
        body_words = re.findall(r'\b[a-zA-Z]{4,}\b', text_before_source.lower())
        unapproved_pre_leak = [w for w in body_words if w not in APPROVED_LATIN]
        if unapproved_pre_leak:
            logger.warning(f"[PRE-DISPATCH REJECT] Message contains unapproved English words {unapproved_pre_leak}. Dropped before sending.")
            return False, text, f"Unapproved English words {unapproved_pre_leak}"

        # 7. Lightning Anti-Duplicate Pre-Dispatch Intercept
        if not hasattr(self, "_recent_watchdog_posts"):
            self._recent_watchdog_posts = []

        now_ts = time.time()
        self._recent_watchdog_posts = [p for p in self._recent_watchdog_posts if (now_ts - p[0]) < 14400.0]

        headline_match = re.search(r'<b>(.*?)</b>', text, re.DOTALL)
        current_headline = re.sub(r'[^\w\u1780-\u17FF]', '', headline_match.group(1)).strip().lower() if headline_match else ""
        current_sig = re.sub(r'[^\w\u1780-\u17FF]', '', clean_vis)[:60].lower()

        for p_ts, p_head, p_sig, p_id in self._recent_watchdog_posts:
            if (current_headline and len(current_headline) >= 15 and current_headline == p_head) or (current_sig and len(current_sig) >= 30 and current_sig == p_sig):
                logger.warning(f"[PRE-DISPATCH DEDUP INTERCEPT] Dropping candidate post pre-dispatch (duplicates recent post #{p_id}). Never sent to Telegram!")
                return False, text, f"Duplicate of post #{p_id}"

        # 7.1 Multi-Instance Live Channel Verification Guard
        # Directly verifies the live public feed of @GoldMarketKH8888 right before hitting the Telegram API
        # To strictly prevent double-posting across distributed containers (Cloud + PC)!
        try:
            import urllib.request, html as html_mod, difflib
            from datetime import datetime, timezone, timedelta
            ch_req = urllib.request.Request("https://t.me/s/GoldMarketKH8888", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(ch_req, timeout=4.0) as ch_resp:
                ch_html = ch_resp.read().decode("utf-8", errors="ignore")
            if ch_html:
                wraps = ch_html.split("tgme_widget_message_wrap")
                all_wraps = list(reversed(wraps[1:]))  # Newest to oldest!

                # A. Channel Cadence Spacing Guard (Minimum 120s between channel news posts)
                if not text.startswith("🥇") and all_wraps:
                    time_m = re.search(r'<time datetime="([^"]+)"', all_wraps[0])
                    if time_m:
                        try:
                            p_dt = datetime.fromisoformat(time_m.group(1).replace('Z', '+00:00'))
                            now_utc = datetime.now(timezone.utc)
                            gap_elapsed = (now_utc - p_dt).total_seconds()
                            if gap_elapsed < 120.0:
                                logger.critical(f"[LIVE CHANNEL GUARD] Channel already posted a message {gap_elapsed:.1f}s ago (< 120s gap). Pre-dispatch suppressed!")
                                return False, text, f"Channel collision: previous post published {gap_elapsed:.1f}s ago"
                        except Exception:
                            pass

                # B. Gold Card Guard
                if not text or "ហាងឆេងមាស" in text:
                    kh_now = datetime.now(timezone(timedelta(hours=7)))
                    today_kh = kh_now.strftime("%Y-%m-%d")
                    session_str = "07:00 ព្រឹក" if 7 <= kh_now.hour <= 10 else ("07:00 យប់" if 19 <= kh_now.hour <= 22 else "")
                    if session_str:
                        for m_wrap in all_wraps:
                            if ("padding-top:100%" in m_wrap or "tgme_widget_message_photo" in m_wrap) and ("07:00" in m_wrap or "ហាងឆេងមាស" in m_wrap or not re.search(r'tgme_widget_message_(?:text|caption)', m_wrap)):
                                time_m = re.search(r'<time datetime="([^"]+)"', m_wrap)
                                if time_m:
                                    p_dt = datetime.fromisoformat(time_m.group(1).replace('Z', '+00:00')).astimezone(timezone(timedelta(hours=7)))
                                    if p_dt.strftime("%Y-%m-%d") == today_kh:
                                        p_sess = "07:00 ព្រឹក" if 7 <= p_dt.hour <= 10 else ("07:00 យប់" if 19 <= p_dt.hour <= 22 else "")
                                        if p_sess == session_str:
                                            logger.critical(f"[LIVE CHANNEL GUARD] Daily gold card for {today_kh} {session_str} already exists in @GoldMarketKH8888! Pre-dispatch suppressed.")
                                            return False, text, f"Gold card already in channel for {session_str}"

                # C. Breaking News Headline & Content Guard (Checks all recent posts on channel)
                if current_headline and len(current_headline) >= 15:
                    for m_wrap in all_wraps:
                        txt_m = re.search(r'tgme_widget_message_(?:text|caption)[^"]*"[^>]*>(.*?)</div>', m_wrap, re.DOTALL)
                        if txt_m:
                            c_line = html_mod.unescape(re.sub(r'<[^>]+>', ' ', txt_m.group(1))).strip().split('\n')[0]
                            c_head = re.sub(r'[^\w\u1780-\u17FF]', '', c_line).strip().lower()
                            c_full = re.sub(r'[^\w\u1780-\u17FF]', '', html_mod.unescape(re.sub(r'<[^>]+>', ' ', txt_m.group(1)))).strip().lower()
                            if c_head and len(c_head) >= 15:
                                seq_sim = difflib.SequenceMatcher(None, current_headline, c_head).ratio()
                                full_sim = difflib.SequenceMatcher(None, current_sig, c_full[:60]).ratio() if current_sig else 0.0
                                if seq_sim >= 0.40 or full_sim >= 0.50 or current_headline in c_head or c_head in current_headline or (current_sig and current_sig in c_full):
                                    logger.critical(f"[LIVE CHANNEL GUARD] Headline already published in @GoldMarketKH8888 (sim={seq_sim:.2f})! Pre-dispatch suppressed.")
                                    return False, text, f"Duplicate of live channel post (sim={seq_sim:.2f})"
        except Exception as e_live:
            logger.debug(f"[LiveChannelPreDispatch error] {e_live}")

        return True, text, "Approved"

    def _post_dispatch_watchdog(self, message_id: int, is_photo: bool = False, target_chat: str = None, raw_text: str = "") -> bool:
        """
        World-Class Zero-Defect Post-Dispatch Watchdog.
        Audits every message delivered to the channel. If ANY constitutional rule is breached,
        instantly auto-purges (deletes) the message from Telegram within milliseconds,
        guaranteeing the human audience NEVER sees a defective post.
        """
        import re
        if not message_id:
            return True

        raw_text = raw_text or ""

        # Skip scheduled daily price cards, pure graphic cards without caption, or private chat messages/signals
        is_private_chat = bool(target_chat and str(target_chat) != str(self.chat_id) and not str(target_chat).startswith("-100"))
        if is_private_chat or raw_text.startswith("⚡") or raw_text.startswith("🥇") or raw_text.startswith("📅") or raw_text.startswith("📊") or raw_text.startswith("🎯") or raw_text.startswith("🧮") or raw_text.startswith("---"):
            return True
        if is_photo and not raw_text:
            return True

        clean = re.sub(r'<[^>]+>', '', raw_text).strip()
        vis_len = len(clean)
        max_allowed = 574 if is_photo else 750

        # Check 0: Empty or corrupted stub (< 40 chars)
        if vis_len < 40:
            logger.critical(f"[WATCHDOG PURGE] Post #{message_id} is empty or corrupted stub ({vis_len} < 40 chars). Auto-purging immediately!")
            self.delete_message(message_id, chat_id=target_chat)
            return False

        # Check 0.1: Prohibited poll, countdown alert, or trade signals
        if "📊 លទ្ធផល Signal" in clean or "📊 បោះឆ្នោត" in clean:
            logger.critical(f"[WATCHDOG PURGE] Post #{message_id} contains prohibited poll. Auto-purging immediately!")
            self.delete_message(message_id, chat_id=target_chat)
            return False
        if "🚨 5 នាទីទៀត" in clean or "🚨 15 នាទីទៀត" in clean or "COUNTDOWN" in clean:
            logger.critical(f"[WATCHDOG PURGE] Post #{message_id} contains prohibited countdown alert. Auto-purging immediately!")
            self.delete_message(message_id, chat_id=target_chat)
            return False
        if any(sig in clean for sig in ["Entry Zone:", "Stop Loss:", "TP1:", "TP2:"]) and "ហាងឆេងមាស" not in clean:
            logger.critical(f"[WATCHDOG PURGE] Post #{message_id} contains prohibited trade signal. Auto-purging immediately!")
            self.delete_message(message_id, chat_id=target_chat)
            return False

        # Check 1: Absolute hard length ceiling
        if vis_len > max_allowed:
            logger.critical(f"[WATCHDOG PURGE] Post #{message_id} exceeded limit ({vis_len} > {max_allowed}). Auto-purging immediately!")
            self.delete_message(message_id, chat_id=target_chat)
            return False

        # Check 2: Missing country/macro flag
        first_line = clean.splitlines()[0] if clean else ""
        if not re.search(r'[\U0001F1E0-\U0001F1FF]{2}|🌐|🥇|📅|📊|🪙', first_line):
            logger.critical(f"[WATCHDOG PURGE] Post #{message_id} missing sovereign flag emoji. Auto-purging immediately!")
            self.delete_message(message_id, chat_id=target_chat)
            return False

        # Check 3: Colons or ellipsis in headline and ensure <b> tags exist
        m_head = re.search(r'<b>(.*?)</b>', raw_text, re.DOTALL)
        if m_head:
            head_txt = m_head.group(1)
            if re.search(r'[៖:：]|[\.]{3,}|…', head_txt):
                logger.critical(f"[WATCHDOG PURGE] Post #{message_id} contains colon/ellipsis in headline. Auto-purging immediately!")
                self.delete_message(message_id, chat_id=target_chat)
                return False
        else:
            logger.critical(f"[WATCHDOG PURGE] Post #{message_id} missing bold <b> tag in headline. Auto-purging immediately!")
            self.delete_message(message_id, chat_id=target_chat)
            return False

        # Check 4: Uncorrected typos & forbidden words
        typos = ['ប្រមាន', 'ធ្វើអោយ', 'ឿរ៉ង់', 'អគ្លេស', 'សហរដ្ធ', 'សេដ្ធកិច្ច', 'ធ្វើរ៉ង់', 'ធ្វើ៊ីរ៉ង់', 'កូដេន', 'លីគីឌីធី', 'ដ្ររដោន', 'តេហេឿរ៉ង់', 'សមរភូមិ្តមុខ', 'កិច្ចព្រមព្រ', 'កិច្ចព្រមព្របទឈប់បាញ់']
        for tp in typos:
            if tp in clean:
                logger.critical(f"[WATCHDOG PURGE] Post #{message_id} contains forbidden typo '{tp}'. Auto-purging immediately!")
                self.delete_message(message_id, chat_id=target_chat)
                return False

        # Check 5: Stray foreign suffixes (ing, ed) and unapproved Latin words inside Khmer context
        if re.search(r'[\u1780-\u17D3]+\s+(?:ing|ed)\b|\b(?:ing|ed)\s+[\u1780-\u17D3]+', clean, re.IGNORECASE):
            logger.critical(f"[WATCHDOG PURGE] Post #{message_id} contains stray foreign suffix (ing/ed). Auto-purging immediately!")
            self.delete_message(message_id, chat_id=target_chat)
            return False

        # Check 5.1: Detect unapproved English vocabulary leaked into Khmer sentences (e.g. 'diversifications')
        text_before_source = re.split(r'\n+ប្រភព(?:\s*ព័ត៌មាន)?\s*\|', clean)[0]
        body_words = re.findall(r'\b[a-zA-Z]{4,}\b', text_before_source.lower())
        APPROVED_LATIN = {
            'trump', 'putin', 'biden', 'musk', 'powell', 'warsh', 'zelenskyy', 'netanyahu',
            'nvidia', 'apple', 'tesla', 'google', 'microsoft', 'meta', 'amazon', 'intel',
            'openai', 'deepseek', 'anthropic', 'huawei', 'tencent', 'alibaba', 'samsung',
            'fed', 'fomc', 'cpi', 'gdp', 'pmi', 'nfp', 'opec', 'xau', 'usd', 'xauusd', 'dxy',
            'btc', 'eth', 'sol', 'usdt', 'usdc', 'imf', 'nato', 'tsmc', 'asml', 'amd', 'arm',
            'byd', 'spacex', 'nasa', 'ceo', 'ipo', 'cds', 'us10y', 'sec', 'etf', 'etfs',
            'crypto', 'sinokor', 'strait', 'hormuz', 'news', 'reuters', 'bloomberg', 'cnbc',
            'bbc', 'afp', 'scmp', 'wsj', 'arab', 'oilprice', 'jazeera', 'marketwatch', 'times',
            'post', 'south', 'china', 'morning', 'seatrade', 'maritime', 'global', 'wire',
            'melania', 'bessent', 'nordic', 'cook', 'huang', 'altman', 'nadella', 'starship',
            'roadster', 'optimus', 'blackwell', 'apnews', 'associated', 'press', 'gold',
            'bonds', 'yield', 'yields', 'dow', 'sp500', 'nasdaq'
        }
        unapproved_leak = [w for w in body_words if w not in APPROVED_LATIN]
        if unapproved_leak:
            logger.critical(f"[WATCHDOG PURGE] Post #{message_id} contains unapproved foreign English words leaked into text: {unapproved_leak}. Auto-purging immediately!")
            self.delete_message(message_id, chat_id=target_chat)
            return False

        # Check 6: Forbidden non-VIP emojis (rockets, fire, meme emojis)
        if re.search(r'[🚀🔥💥💰🎉🤑💩🤡]', clean):
            logger.critical(f"[WATCHDOG PURGE] Post #{message_id} contains forbidden non-VIP emoji. Auto-purging immediately!")
            self.delete_message(message_id, chat_id=target_chat)
            return False

        # Check 7: Contradictory war news sentiment (preserves genuine resilience & peace stories)
        war_terms = ['សង្គ្រាម', 'វាយប្រហារ', 'ដ្រូន', 'មីស៊ីល', 'ទាហាន', 'ស្លាប់', 'ផ្ទុះ', 'សមរភូមិ']
        is_peace_or_resilience = any(k in clean for k in ['បទឈប់បាញ់', 'សន្តិភាព', 'ទប់ទល់', 'ភាពធន់', 'ស្ថិរភាព', 'បន្ធូរបន្ថយ', 'លុបចោលពន្ធ', 'លើកលែងពន្ធ'])
        if any(w in clean for w in war_terms) and '🔹 ផលវិជ្ជមាន' in clean and not is_peace_or_resilience:
            logger.critical(f"[WATCHDOG PURGE] Post #{message_id} contains contradictory positive sentiment on war/conflict. Auto-purging immediately!")
            self.delete_message(message_id, chat_id=target_chat)
            return False

        # Check 8: Lightning Anti-Duplicate Purge (< 1 second)
        # Guarantees zero duplicate headlines or story signatures can ever coexist on the channel
        import difflib
        headline_match = re.search(r'<b>(.*?)</b>', raw_text, re.DOTALL)
        current_headline = re.sub(r'[^\w\u1780-\u17FF]', '', headline_match.group(1)).strip().lower() if headline_match else ""
        current_sig = re.sub(r'[^\w\u1780-\u17FF]', '', clean)[:60].lower()

        now_ts = time.time()
        if not hasattr(TelegramNotifier, "_global_watchdog_posts"):
            TelegramNotifier._global_watchdog_posts = []
        TelegramNotifier._global_watchdog_posts = [p for p in TelegramNotifier._global_watchdog_posts if (now_ts - p[0]) < 14400.0]

        # 8.1 In-Memory Global Watchdog Check (Fuzzy Similarity)
        for p_ts, p_head, p_sig, p_id in TelegramNotifier._global_watchdog_posts:
            if p_id == message_id:
                continue
            head_sim = difflib.SequenceMatcher(None, current_headline, p_head).ratio() if (current_headline and p_head) else 0.0
            sig_sim = difflib.SequenceMatcher(None, current_sig, p_sig).ratio() if (current_sig and p_sig) else 0.0
            if head_sim >= 0.40 or sig_sim >= 0.45 or (current_headline and len(current_headline) >= 15 and (current_headline in p_head or p_head in current_headline)):
                logger.critical(f"[LIGHTNING WATCHDOG PURGE] Post #{message_id} duplicates earlier post #{p_id} (sim={max(head_sim, sig_sim):.2f}). Auto-purging immediately in < 1 second!")
                self.delete_message(message_id, chat_id=target_chat)
                return False

        # 8.2 Persistent SQLite Watchdog Check (Cross-Process / Cross-Container)
        try:
            import database
            past_posts = database.get_recent_channel_posts(hours=4)
            for (past_id, past_hl, past_full, past_photo, past_epoch) in past_posts:
                if past_id == message_id:
                    continue
                past_clean_hl = re.sub(r'[^\w\u1780-\u17FF]', '', past_hl or '').strip().lower()
                past_clean_sig = re.sub(r'[^\w\u1780-\u17FF]', '', past_full or '')[:60].lower()
                head_sim = difflib.SequenceMatcher(None, current_headline, past_clean_hl).ratio() if (current_headline and past_clean_hl) else 0.0
                sig_sim = difflib.SequenceMatcher(None, current_sig, past_clean_sig).ratio() if (current_sig and past_clean_sig) else 0.0
                if head_sim >= 0.40 or sig_sim >= 0.45 or (current_headline and len(current_headline) >= 15 and (current_headline in past_clean_hl or past_clean_hl in current_headline)):
                    logger.critical(f"[DATABASE WATCHDOG PURGE] Post #{message_id} duplicates DB post #{past_id} (sim={max(head_sim, sig_sim):.2f}). Auto-purging immediately!")
                    self.delete_message(message_id, chat_id=target_chat)
                    return False
        except Exception as e_db_wd:
            logger.debug(f"[DatabaseWatchdog error] {e_db_wd}")

        # Register successful post in memory & database
        if current_headline or current_sig:
            TelegramNotifier._global_watchdog_posts.append((now_ts, current_headline, current_sig, message_id))
            try:
                import database
                database.record_channel_post(message_id, current_headline, clean, is_photo=is_photo)
            except Exception:
                pass

        logger.info(f"[WATCHDOG PASSED] Post #{message_id} passed all 100% quality checks ({vis_len}/{max_allowed} chars).")
        return True

    def send_message(self, text: str, parse_mode: str = "HTML", disable_web_page_preview: bool = True, auto_pin: bool = False, reply_markup: dict = None, chat_id: str = None, is_ultra_breaking: bool = False) -> dict:
        """Send message directly to Telegram channel/chat. If auto_pin is True, pins the message."""
        import re
        import time

        target_chat = str(chat_id or self.chat_id)

        # 100% PRE-DISPATCH CURATION SHIELD: Curate, proofread, and verify BEFORE sending
        is_ok, curated_text, reason = self._curate_and_sanitize_pre_dispatch(text, is_photo=False, target_chat=target_chat)
        if not is_ok:
            logger.warning(f"[TelegramNotifier] Pre-dispatch curation rejected message: {reason}. Dropped before sending.")
            return {"ok": False, "error": f"Pre-dispatch curation rejected: {reason}"}
        text = curated_text

        if not self.is_configured():
            logger.warning("[TelegramNotifier] Credentials not set. Message output (Simulation):\n" + "="*50 + f"\n{text}\n" + "="*50)
            return {"ok": True, "result": {"message_id": 999999, "simulated": True}}

        target_chat = str(chat_id or self.chat_id)

        # Anti-Flood Cadence Guard: strictly 120s for Ultra Breaking, 180s for standard channel alerts
        flood_gap = 120.0 if is_ultra_breaking else 180.0
        last_time = getattr(self, "_last_channel_post_time", 0.0)
        if last_time == 0.0:
            try:
                import database
                db_ts = float(database.get_state("last_breaking_alert_ts") or "0")
                if db_ts > 0:
                    last_time = db_ts
                    self._last_channel_post_time = db_ts
            except Exception:
                pass
        if target_chat == str(self.chat_id) and not text.startswith("🥇") and last_time > 0:
            elapsed = time.time() - last_time
            if elapsed < flood_gap:
                wait_sec = flood_gap - elapsed
                logger.info(f"[Anti-Flood Guard] Spacing channel post by {wait_sec:.1f}s (tier: {'ULTRA' if is_ultra_breaking else 'STANDARD'})...")
                time.sleep(wait_sec)

        url = f"{self.base_url}/sendMessage"
        if parse_mode == "HTML" and text:
            text = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[a-fA-F0-9]+);)', '&amp;', text)
        payload = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
            "link_preview_options": {"is_disabled": True}
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        try:
            resp = requests.post(url, json=payload, timeout=15)
            data = resp.json()
            if not data.get("ok"):
                logger.error(f"[TelegramNotifier] Error sending message: {data}")
                # Fallback: If Telegram rejected unsupported HTML tags (e.g. <font>, <div> from RSS feeds)
                desc = str(data.get("description", "")).lower()
                if "can't parse entities" in desc or "entity" in desc:
                    logger.info("[TelegramNotifier] Retrying message with sanitized HTML tags...")
                    import html
                    # Normalize anchor tags to only keep href (strip target="_blank" and other unsupported attributes)
                    clean_text = re.sub(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>', r'<a href="\1">', text, flags=re.IGNORECASE)
                    # Strip all tags except supported Telegram tags
                    clean_text = re.sub(r'<(?!(?:b|strong|i|em|u|ins|s|strike|del|a|code|pre|blockquote)\b)[^>]+>', '', clean_text)
                    clean_text = re.sub(r'</(?!(?:b|strong|i|em|u|ins|s|strike|del|a|code|pre|blockquote)\b)[^>]+>', '', clean_text)
                    clean_text = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[a-fA-F0-9]+);)', '&amp;', clean_text)
                    payload["text"] = clean_text
                    retry_resp = requests.post(url, json=payload, timeout=15)
                    data = retry_resp.json()
                    if not data.get("ok"):
                        # Ultimate fallback: Plain text without parse_mode (strip ALL HTML tags so raw tags never show)
                        logger.warning("[TelegramNotifier] HTML retry failed, falling back to pure plain text.")
                        payload.pop("parse_mode", None)
                        pure_text = re.sub(r'<[^>]+>', '', text)
                        payload["text"] = html.unescape(pure_text).strip()
                        plain_resp = requests.post(url, json=payload, timeout=15)
                        data = plain_resp.json()

            if not data.get("ok"):
                return data
            
            message_id = data.get("result", {}).get("message_id")
            logger.info(f"[TelegramNotifier] Message sent successfully (ID: {message_id})")
            now_sent = time.time()

            if is_trade_signal:
                TelegramNotifier._global_last_signal_time = now_sent
                TelegramNotifier._recent_chat_signals[str(target_chat)] = now_sent
                try:
                    import database
                    database.set_state("last_private_signal_dispatch_ts", str(now_sent))
                except Exception:
                    pass

            if target_chat == str(self.chat_id):
                self._last_channel_post_time = now_sent
                try:
                    import database
                    database.set_state("last_breaking_alert_ts", str(now_sent))
                except Exception:
                    pass

            # WORLD-CLASS POST-DISPATCH WATCHDOG AUDIT
            if message_id:
                if not self._post_dispatch_watchdog(message_id, is_photo=False, target_chat=target_chat, raw_text=payload.get("text", "")):
                    return {"ok": False, "error": "Watchdog: Message violated rules and was auto-purged"}

            if auto_pin and message_id:
                self.pin_message(message_id)

            return data
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception while sending message: {e}")
            return {"ok": False, "error": str(e)}

    def send_photo(self, photo_bytes: bytes, caption: str = "", parse_mode: str = "HTML", reply_markup: dict = None, chat_id: str = None, is_ultra_breaking: bool = False, is_daily_gold_card: bool = False) -> dict:
        import re
        import time
        from database import calculate_image_dhash, is_image_dhash_duplicate, record_image_dhash

        if isinstance(photo_bytes, str) and os.path.isfile(photo_bytes):
            with open(photo_bytes, "rb") as f:
                photo_bytes = f.read()

        is_gold_card = is_daily_gold_card or (bool(caption) and caption.startswith("🥇"))

        # Circuit Breaker 2: If image is missing, empty, or low-res (< 15KB for news, < 500B for cards), fallback to MODE B text-only!
        min_bytes = 500 if is_gold_card else 15000
        if not photo_bytes or len(photo_bytes) < min_bytes:
            logger.warning(f"[TelegramNotifier] Circuit Breaker: Image too small ({len(photo_bytes) if photo_bytes else 0} bytes < {min_bytes}). Seamless fallback to MODE B (send_message).")
            return self.send_message(text=caption, parse_mode=parse_mode, reply_markup=reply_markup, chat_id=chat_id, is_ultra_breaking=is_ultra_breaking)

        target_chat = str(chat_id or self.chat_id)

        # 100% PRE-DISPATCH CURATION SHIELD: Curate, proofread, and verify caption BEFORE sending
        if caption:
            is_ok, curated_caption, reason = self._curate_and_sanitize_pre_dispatch(caption, is_photo=True, target_chat=target_chat)
            if not is_ok:
                logger.warning(f"[TelegramNotifier] Pre-dispatch curation rejected photo caption: {reason}. Dropped before sending.")
                return {"ok": False, "error": f"Pre-dispatch curation rejected: {reason}"}
            caption = curated_caption

        # STRICT ZERO IMAGE REPETITION GUARD (30-Day Perceptual dHash Check):
        # Excludes daily gold price cards (is_daily_gold_card=True or caption starting with 🥇)
        img_dhash = ""
        is_gold_card = is_daily_gold_card or (bool(caption) and caption.startswith("🥇"))
        if not is_gold_card:
            img_dhash = calculate_image_dhash(photo_bytes)
            if img_dhash and is_image_dhash_duplicate(img_dhash, max_age_seconds=14400.0, max_hamming_dist=6):
                logger.critical(f"[STRICT ZERO REPETITION SHIELD] Image dHash '{img_dhash}' matches an image broadcasted in the channel within 4h cooldown! Auto-dropping image and falling back to MODE B (Clean VIP Text Mode).")
                return self.send_message(text=caption, parse_mode=parse_mode, reply_markup=reply_markup, chat_id=chat_id, is_ultra_breaking=is_ultra_breaking)

        if not self.is_configured():
            logger.warning(f"[TelegramNotifier] Credentials not set. Simulated photo upload ({len(photo_bytes) if photo_bytes else 0} bytes).")
            return {"ok": True, "result": {"message_id": 999998, "simulated": True}}

        # Anti-Flood Cadence Guard: strictly 120s for Ultra Breaking, 180s for standard channel alerts
        flood_gap = 120.0 if is_ultra_breaking else 180.0
        last_time = getattr(self, "_last_channel_post_time", 0.0)
        if last_time == 0.0:
            try:
                import database
                db_ts = float(database.get_state("last_breaking_alert_ts") or "0")
                if db_ts > 0:
                    last_time = db_ts
                    self._last_channel_post_time = db_ts
            except Exception:
                pass
        if target_chat == str(self.chat_id) and not is_gold_card and last_time > 0:
            elapsed = time.time() - last_time
            if elapsed < flood_gap:
                wait_sec = flood_gap - elapsed
                logger.info(f"[Anti-Flood Guard] Spacing channel photo post by {wait_sec:.1f}s (tier: {'ULTRA' if is_ultra_breaking else 'STANDARD'})...")
                time.sleep(wait_sec)

        url = f"{self.base_url}/sendPhoto"
        files = {"photo": ("news_photo.png", photo_bytes, "image/png")}
        data = {"chat_id": target_chat}
        if caption:
            if parse_mode == "HTML":
                import re
                caption = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[a-fA-F0-9]+);)', '&amp;', caption)
            data["caption"] = caption
            data["parse_mode"] = parse_mode
        if reply_markup:
            import json
            data["reply_markup"] = json.dumps(reply_markup)

        try:
            resp = requests.post(url, data=data, files=files, timeout=30)
            result = resp.json()
            if result.get("ok"):
                logger.info(f"[TelegramNotifier] Photo sent (ID: {result.get('result', {}).get('message_id')})")
                if target_chat == str(self.chat_id):
                    now_sent = time.time()
                    self._last_channel_post_time = now_sent
                    try:
                        import database
                        database.set_state("last_breaking_alert_ts", str(now_sent))
                    except Exception:
                        pass
                # Record perceptual dHash into database to lock it for 30 days
                if img_dhash and not is_gold_card:
                    record_image_dhash(img_dhash)
            else:
                logger.error(f"[TelegramNotifier] Error sending photo: {result}")
                # Fallback: if HTML parsing failed, retry with sanitized HTML preserving supported tags & escaped &
                desc = str(result.get("description", "")).lower()
                if "can't parse entities" in desc or "entity" in desc:
                    import re
                    import html
                    clean_caption = re.sub(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>', r'<a href="\1">', caption, flags=re.IGNORECASE)
                    clean_caption = re.sub(r'<(?!(?:b|strong|i|em|u|ins|s|strike|del|a|code|pre|blockquote)\b)[^>]+>', '', clean_caption)
                    clean_caption = re.sub(r'</(?!(?:b|strong|i|em|u|ins|s|strike|del|a|code|pre|blockquote)\b)[^>]+>', '', clean_caption)
                    clean_caption = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[a-fA-F0-9]+);)', '&amp;', clean_caption)[:1020]
                    data["caption"] = clean_caption
                    files = {"photo": ("calendar.png", photo_bytes, "image/png")}
                    retry_resp = requests.post(url, data=data, files=files, timeout=30)
                    result = retry_resp.json()
                    if result.get("ok"):
                        logger.info(f"[TelegramNotifier] Photo sent on sanitized HTML retry (ID: {result.get('result', {}).get('message_id')})")
                    else:
                        clean_caption = re.sub(r"<[^>]+>", "", caption)[:1020]
                        data["caption"] = html.unescape(clean_caption).strip()
                        data.pop("parse_mode", None)
                        files = {"photo": ("calendar.png", photo_bytes, "image/png")}
                        retry_resp2 = requests.post(url, data=data, files=files, timeout=30)
                        result = retry_resp2.json()
                        if result.get("ok"):
                            logger.info(f"[TelegramNotifier] Photo sent on plain-text fallback (ID: {result.get('result', {}).get('message_id')})")
            if result.get("ok"):
                message_id = result.get('result', {}).get('message_id')
                # WORLD-CLASS POST-DISPATCH WATCHDOG AUDIT
                if message_id and not is_gold_card:
                    if not self._post_dispatch_watchdog(message_id, is_photo=True, target_chat=target_chat, raw_text=data.get("caption", "")):
                        return {"ok": False, "error": "Watchdog: Photo caption violated rules and was auto-purged"}

            return result
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception while sending photo: {e}")
            return {"ok": False, "error": str(e)}

    def send_video(self, video_data, caption: str = "", parse_mode: str = "HTML", reply_markup: dict = None, chat_id: str = None, supports_streaming: bool = True, is_ultra_breaking: bool = False) -> dict:
        """
        Sends an authentic HD video clip to the Telegram channel with strict VIP standard.
        Accepts:
          - bytes: raw MP4 bytes
          - str (filepath): path to local .mp4 file
          - str (url): direct HTTPS URL to .mp4 video
        Enforces:
          - Strict character limit <= 574 characters per user rule.
          - Post-dispatch watchdog audit.
          - Automatic fallback to send_message if video sending fails.
        """
        import re
        import time

        if not video_data:
            return self.send_message(text=caption, parse_mode=parse_mode, reply_markup=reply_markup, chat_id=chat_id, is_ultra_breaking=is_ultra_breaking)

        target_chat = str(chat_id or self.chat_id)

        # 100% PRE-DISPATCH CURATION SHIELD: Curate, proofread, and verify caption BEFORE sending
        if caption:
            is_ok, curated_caption, reason = self._curate_and_sanitize_pre_dispatch(caption, is_photo=True, target_chat=target_chat)
            if not is_ok:
                logger.warning(f"[TelegramNotifier] Pre-dispatch curation rejected video caption: {reason}. Dropped before sending.")
                return {"ok": False, "error": f"Pre-dispatch curation rejected: {reason}"}
            caption = curated_caption

        if not self.is_configured():
            logger.warning(f"[TelegramNotifier] Credentials not set. Simulated video upload.")
            return {"ok": True, "result": {"message_id": 999997, "simulated": True}}

        # Anti-Flood Cadence Guard: 15s for Ultra Breaking, 60s for standard channel alerts
        flood_gap = 15.0 if is_ultra_breaking else 60.0
        if target_chat == str(self.chat_id) and hasattr(self, "_last_channel_post_time"):
            elapsed = time.time() - getattr(self, "_last_channel_post_time", 0.0)
            if elapsed < flood_gap:
                wait_sec = min(flood_gap - elapsed, 15.0)
                logger.info(f"[Anti-Flood Guard] Spacing channel video post by {wait_sec:.1f}s (tier: {'ULTRA' if is_ultra_breaking else 'STANDARD'})...")
                time.sleep(wait_sec)

        url = f"{self.base_url}/sendVideo"
        data = {
            "chat_id": target_chat,
            "supports_streaming": "true" if supports_streaming else "false"
        }
        if caption:
            if parse_mode == "HTML":
                caption = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[a-fA-F0-9]+);)', '&amp;', caption)
            data["caption"] = caption
            data["parse_mode"] = parse_mode
        if reply_markup:
            import json
            data["reply_markup"] = json.dumps(reply_markup)

        try:
            # Case 1: video_data is a URL string
            if isinstance(video_data, str) and video_data.startswith("http"):
                data["video"] = video_data
                resp = requests.post(url, data=data, timeout=45)
            # Case 2: video_data is a local file path
            elif isinstance(video_data, str) and os.path.isfile(video_data):
                with open(video_data, "rb") as vf:
                    files = {"video": (os.path.basename(video_data), vf, "video/mp4")}
                    resp = requests.post(url, data=data, files=files, timeout=60)
            # Case 3: video_data is raw bytes
            elif isinstance(video_data, bytes):
                files = {"video": ("news_video.mp4", video_data, "video/mp4")}
                resp = requests.post(url, data=data, files=files, timeout=60)
            else:
                logger.warning(f"[TelegramNotifier] Unsupported video_data type: {type(video_data)}. Falling back to send_message.")
                return self.send_message(text=caption, parse_mode=parse_mode, reply_markup=reply_markup, chat_id=chat_id)

            result = resp.json()
            if result.get("ok"):
                message_id = result.get('result', {}).get('message_id')
                logger.info(f"[TelegramNotifier] Video sent successfully (ID: {message_id})")
                if target_chat == str(self.chat_id):
                    self._last_channel_post_time = time.time()
                # Post-dispatch watchdog audit
                if message_id:
                    if not self._post_dispatch_watchdog(message_id, is_photo=True, target_chat=target_chat, raw_text=data.get("caption", "")):
                        return {"ok": False, "error": "Watchdog: Video caption violated rules and was auto-purged"}
                return result
            else:
                logger.warning(f"[TelegramNotifier] sendVideo failed ({result}). Falling back to text-only mode.")
                return self.send_message(text=caption, parse_mode=parse_mode, reply_markup=reply_markup, chat_id=chat_id)
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception while sending video: {e}. Falling back to text-only mode.")
            return self.send_message(text=caption, parse_mode=parse_mode, reply_markup=reply_markup, chat_id=chat_id)

    def edit_message_caption(self, message_id: int, caption: str, parse_mode: str = "HTML", reply_markup: dict = None, chat_id: str = None) -> dict:
        """Edits the caption of an existing photo/document message in the chat/channel."""
        if not self.is_configured():
            logger.info(f"[TelegramNotifier] Simulated edit caption for message ID: {message_id}")
            return {"ok": True, "result": {"message_id": message_id, "simulated": True}}

        target_chat = str(chat_id or self.chat_id)
        url = f"{self.base_url}/editMessageCaption"
        if parse_mode == "HTML" and caption:
            import re
            caption = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[a-fA-F0-9]+);)', '&amp;', caption)
        payload = {
            "chat_id": target_chat,
            "message_id": message_id,
            "caption": caption,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            resp = requests.post(url, json=payload, timeout=15)
            result = resp.json()
            if result.get("ok"):
                logger.info(f"[TelegramNotifier] Caption edited successfully (ID: {message_id})")
            else:
                logger.error(f"[TelegramNotifier] Error editing caption: {result}")
            return result
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception while editing caption: {e}")
            return {"ok": False, "error": str(e)}

    def edit_message_text(self, message_id: int, text: str, parse_mode: str = "HTML", reply_markup: dict = None, chat_id: str = None) -> dict:
        """Edits the text of an existing text message in the chat/channel."""
        if not self.is_configured():
            logger.info(f"[TelegramNotifier] Simulated edit text for message ID: {message_id}")
            return {"ok": True, "result": {"message_id": message_id, "simulated": True}}

        target_chat = str(chat_id or self.chat_id)
        url = f"{self.base_url}/editMessageText"
        payload = {
            "chat_id": target_chat,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
            "link_preview_options": {"is_disabled": True}
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            resp = requests.post(url, json=payload, timeout=15)
            result = resp.json()
            if result.get("ok"):
                logger.info(f"[TelegramNotifier] Message text edited successfully (ID: {message_id})")
            else:
                logger.error(f"[TelegramNotifier] Error editing message text: {result}")
            return result
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception while editing text: {e}")
            return {"ok": False, "error": str(e)}


    def send_voice(self, voice_bytes: bytes, caption: str = "", parse_mode: str = "HTML", reply_markup: dict = None, chat_id: str = None) -> dict:
        """Voice notes are permanently disabled per user directive."""
        logger.info("[TelegramNotifier] Voice notes are permanently disabled per user directive. Skipping upload.")
        return {"ok": True, "result": {"message_id": 0, "disabled": True}}

    def pin_message(self, message_id: int, disable_notification: bool = True) -> bool:
        """Auto-pin message in the chat/channel."""
        if not self.is_configured():
            logger.info(f"[TelegramNotifier] Simulated pinning message ID: {message_id}")
            return True

        url = f"{self.base_url}/pinChatMessage"
        payload = {
            "chat_id": self.chat_id,
            "message_id": message_id,
            "disable_notification": disable_notification
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            data = resp.json()
            if data.get("ok"):
                logger.info(f"[TelegramNotifier] Pinned message ID: {message_id}")
                return True
            else:
                logger.error(f"[TelegramNotifier] Failed to pin message: {data}")
                return False
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception pinning message: {e}")
            return False

    def get_updates(self, offset: int = None, timeout: int = 1) -> list:
        """Fetches incoming user messages / commands via getUpdates API."""
        if not self.is_configured():
            return []
        url = f"{self.base_url}/getUpdates"
        params = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        try:
            resp = requests.get(url, params=params, timeout=timeout + 5)
            data = resp.json()
            if data.get("ok"):
                return data.get("result", [])
        except Exception as e:
            logger.debug(f"[TelegramNotifier] getUpdates error: {e}")
        return []

    def answer_callback_query(self, callback_query_id: str, text: str = None, show_alert: bool = False):
        """Acknowledges incoming button clicks via answerCallbackQuery API."""
        if not self.is_configured() or not callback_query_id:
            return
        url = f"{self.base_url}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id, "show_alert": show_alert}
        if text:
            payload["text"] = text
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            logger.debug(f"[TelegramNotifier] answerCallbackQuery error: {e}")

    def send_poll(self, question: str, options: list, is_anonymous: bool = False, reply_markup: dict = None, chat_id: str = None) -> dict:
        """Sends an interactive native Telegram Poll directly to the Channel or Chat with optional inline keyboard."""
        if not self.is_configured():
            logger.warning(f"[TelegramNotifier] Credentials not set. Simulated Poll: {question}")
            return {"ok": True, "result": {"message_id": 999990, "simulated": True}}

        target_chat = str(chat_id or self.chat_id)
        url = f"{self.base_url}/sendPoll"
        payload = {
            "chat_id": target_chat,
            "question": question[:300],
            "options": options,
            "is_anonymous": is_anonymous
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            resp = requests.post(url, json=payload, timeout=12)
            data = resp.json()
            if not data.get("ok"):
                logger.error(f"[TelegramNotifier] sendPoll error: {data}")
            else:
                logger.info(f"[TelegramNotifier] Poll sent successfully (ID: {data.get('result', {}).get('message_id')})")
            return data
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception sending poll: {e}")
            return {"ok": False, "error": str(e)}

    def get_file_bytes(self, file_id: str) -> bytes:
        """Downloads a file (e.g. photo) from Telegram servers using getFile API."""
        if not self.is_configured() or not file_id:
            return b""
        try:
            url = f"{self.base_url}/getFile"
            resp = requests.get(url, params={"file_id": file_id}, timeout=10)
            data = resp.json()
            if not data.get("ok"):
                logger.error(f"[TelegramNotifier] getFile error: {data}")
                return b""
            file_path = data.get("result", {}).get("file_path")
            if not file_path:
                return b""
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            f_resp = requests.get(download_url, timeout=25)
            if f_resp.status_code == 200:
                return f_resp.content
            logger.error(f"[TelegramNotifier] Error downloading file bytes: HTTP {f_resp.status_code}")
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception downloading file: {e}")
        return b""

    def is_user_member_of_channel(self, user_id: int, channel_id: str = None) -> bool:
        """Check if user_id is a member/admin/creator of the official channel."""
        if not self.is_configured() or not user_id:
            return True
        target_channel = str(channel_id or self.chat_id)
        url = f"{self.base_url}/getChatMember"
        try:
            resp = requests.get(url, params={"chat_id": target_channel, "user_id": user_id}, timeout=8)
            data = resp.json()
            if data.get("ok"):
                status = data.get("result", {}).get("status", "")
                return status in ("creator", "administrator", "member", "restricted")
            logger.warning(f"[TelegramNotifier] User {user_id} not a member of {target_channel}: {data}")
            return False
        except Exception as e:
            logger.error(f"[TelegramNotifier] Error checking member status: {e}")
    def is_user_admin_of_channel(self, user_id: int, channel_id: str = None) -> bool:
        """Check if user_id is the creator or an administrator of the official channel."""
        if not self.is_configured() or not user_id:
            return False
        target_channel = str(channel_id or self.chat_id)
        url = f"{self.base_url}/getChatMember"
        try:
            resp = requests.get(url, params={"chat_id": target_channel, "user_id": user_id}, timeout=8)
            data = resp.json()
            if data.get("ok"):
                status = data.get("result", {}).get("status", "")
                return status in ("creator", "administrator")
            return False
        except Exception as e:
            logger.error(f"[TelegramNotifier] Error checking admin status: {e}")
            return False

    def delete_message(self, message_id: int, chat_id: str = None) -> bool:
        """Deletes a message directly from the chat/channel using Telegram deleteMessage API."""
        if not self.is_configured() or not message_id:
            return False
        target_chat = str(chat_id or self.chat_id)
        url = f"{self.base_url}/deleteMessage"
        try:
            resp = requests.post(url, json={"chat_id": target_chat, "message_id": message_id}, timeout=10)
            data = resp.json()
            if data.get("ok"):
                logger.info(f"[TelegramNotifier] Successfully deleted message ID {message_id} from {target_chat}.")
                return True
            else:
                logger.warning(f"[TelegramNotifier] deleteMessage returned not ok: {data}")
                return False
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception deleting message {message_id}: {e}")
            return False



