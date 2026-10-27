import json
import logging
import requests
from config import GEMINI_KEYS_POOL, GEMINI_MODEL

logger = logging.getLogger("SemanticDeduplicator")

class SemanticEventDeduplicator:
    """
    World-Class AI Semantic Event Deduplication Engine.
    Detects and eliminates news spam where multiple wire agencies report on
    the EXACT SAME underlying event using different headlines or vocabulary.
    """

    _DEDUP_CACHE = {}  # title_hash -> bool (is_duplicate)

    @classmethod
    def is_semantic_duplicate(cls, candidate_title: str, candidate_desc: str, recent_channel_stories: list) -> tuple:
        """
        Checks if candidate news reports on the same core event as any recent channel story.
        Returns (is_duplicate: bool, reason: str).
        """
        if not candidate_title or not recent_channel_stories:
            return (False, "No candidate or no recent stories")

        cache_key = f"{candidate_title[:50]}_{len(recent_channel_stories)}"
        if cache_key in cls._DEDUP_CACHE:
            return cls._DEDUP_CACHE[cache_key]

        if not GEMINI_KEYS_POOL:
            return (False, "No Gemini API key available")

        # Format recent channel stories cleanly (up to 12 recent stories)
        stories_formatted = []
        for i, s in enumerate(recent_channel_stories[:12]):
            s_clean = " ".join(str(s).split())[:200]
            stories_formatted.append(f"[{i+1}] {s_clean}")

        prompt = f"""You are the Chief Editor and Duplication Interception Gatekeeper of a VIP Financial News Channel.
Your mission is to prevent news spam where different news outlets report on the SAME event using different words/headlines.

Candidate News to broadcast:
Title: {candidate_title}
Description: {candidate_desc}

Recent Stories already broadcasted to channel:
""" + "\n".join(stories_formatted) + """

DEDUPLICATION RULES:
1. SAME CORE EVENT: If the candidate covers the SAME news event, development, press release, or speech as any recent post (even if headlines use completely different vocabulary), flag it as a DUPLICATE!
   Example 1: "Iran launches UAV drones at Tel Aviv" vs "IDF intercepts aerial targets from Tehran" -> SAME EVENT (Duplicate).
   Example 2: "Tesla Q3 deliveries miss Wall Street consensus" vs "Elon Musk's EV firm faces delivery slump in third quarter" -> SAME EVENT (Duplicate).
   Example 3: "Powell indicates interest rates to stay restrictive" vs "Fed Chair signals no rush to ease monetary policy" -> SAME EVENT (Duplicate).
2. INCREMENTAL EXCEPTION: Only allow if there is a MASSIVE new quantitative fact (e.g. ceasefire officially signed, war officially declared, rate cut announced).

Return STRICT JSON:
{
  "is_duplicate_event": true or false,
  "matched_post_index": number (or 0 if none),
  "confidence": float (0.0 to 1.0),
  "reason": "Clear explanation in English"
}"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json"
            }
        }

        candidate_models = [GEMINI_MODEL, "gemini-2.5-flash", "gemini-1.5-flash", "gemini-flash-latest"]
        seen_models = set()
        models = [m for m in candidate_models if m and not (m in seen_models or seen_models.add(m))]

        for key in GEMINI_KEYS_POOL:
            for model in models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                try:
                    resp = requests.post(url, json=payload, timeout=10)
                    if resp.status_code == 200:
                        raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                        data = json.loads(raw)
                        is_dup = bool(data.get("is_duplicate_event", False))
                        reason = data.get("reason", "")
                        matched_idx = data.get("matched_post_index", 0)
                        confidence = float(data.get("confidence", 0.0))

                        if is_dup and confidence >= 0.70:
                            logger.info(
                                f"[SEMANTIC DEDUP INTERCEPTED] Candidate '{candidate_title[:45]}...' "
                                f"matches recent story [{matched_idx}]: {reason}"
                            )
                            res_tuple = (True, f"Matched post [{matched_idx}]: {reason}")
                        else:
                            res_tuple = (False, reason)

                        cls._DEDUP_CACHE[cache_key] = res_tuple
                        return res_tuple
                    elif resp.status_code == 429:
                        continue
                except Exception as e:
                    logger.debug(f"[SemanticEventDeduplicator error on {model}] {e}")
                    continue

        return (False, "API check failed, fail-open to not block legitimate news")

    @classmethod
    def find_duplicate_posts_in_channel(cls, posts: list) -> list:
        """
        Audits recent channel posts (list of dicts with 'id' and 'text').
        Detects if any newer post reports on the exact same event as an earlier post
        (even if headlines and wording are completely different).
        Returns list of newer duplicate post IDs that should be automatically purged.
        """
        if not posts or len(posts) < 2 or not GEMINI_KEYS_POOL:
            return []

        recent_posts = posts[-8:]
        posts_formatted = []
        for p in recent_posts:
            pid = p.get("id")
            txt = " ".join(str(p.get("text", "")).split())[:200]
            if txt:
                posts_formatted.append(f"Post #{pid}: {txt}")

        if len(posts_formatted) < 2:
            return []

        prompt = f"""You are the Chief Auditor of a VIP Financial News Channel.
Analyze the following recent channel posts in chronological order (earlier to newest):
""" + "\n".join(posts_formatted) + """

MISSION:
Identify if any NEWER post is an unnecessary duplicate reporting on the EXACT SAME event/story as an EARLIER post, even if the headlines and wording are different!
If a newer post is a duplicate of an earlier post, return its post ID so it can be automatically deleted.

Return STRICT JSON:
{
  "has_duplicate": true or false,
  "duplicate_post_ids": [number, ...],
  "reason": "Clear explanation in English"
}"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json"
            }
        }

        candidate_models = [GEMINI_MODEL, "gemini-2.5-flash", "gemini-1.5-flash", "gemini-flash-latest"]
        seen_models = set()
        models = [m for m in candidate_models if m and not (m in seen_models or seen_models.add(m))]

        for key in GEMINI_KEYS_POOL:
            for model in models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                try:
                    resp = requests.post(url, json=payload, timeout=10)
                    if resp.status_code == 200:
                        raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                        data = json.loads(raw)
                        if data.get("has_duplicate"):
                            dup_ids = data.get("duplicate_post_ids", [])
                            # Ensure we only return IDs of newer posts, not the original/earlier post
                            recent_pids = [p.get("id") for p in recent_posts]
                            valid_ids = [int(i) for i in dup_ids if int(i) in recent_pids[1:]]
                            if valid_ids:
                                logger.info(f"[CHANNEL AUDIT PURGE DETECTED] Duplicate post IDs to delete: {valid_ids} - Reason: {data.get('reason')}")
                                return valid_ids
                        return []
                    elif resp.status_code == 429:
                        continue
                except Exception as e:
                    logger.debug(f"[find_duplicate_posts_in_channel error on {model}] {e}")
                    continue

        return []

