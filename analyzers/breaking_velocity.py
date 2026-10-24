import re
import time

class BreakingVelocityEngine:
    """
    Sub-Second Breaking Velocity & Multi-Wire Consensus Engine.
    Detects high-impact geopolitical and macroeconomic flashpoints.
    Calculates multi-wire consensus when >= 2 distinct world agencies report the same event.
    Unlocks instant priority broadcast (< 30 seconds).
    """

    CRISIS_KEYWORDS = [
        # Geopolitical & War flashpoints
        "nuclear", "outbreak of war", "declares war", "declared war", "declaration of war",
        "airstrike", "air strike", "missile strike", "missiles launched", "drone strike",
        "ballistic missile", "martial law", "assassination", "coup", "invasion",
        "ground invasion", "evacuation order", "strait of hormuz closed", "red sea attack",
        "warship attacked", "shot down", "emergency evacuation", "mobilization",
        # Central Bank & Macro Shock flashpoints
        "emergency rate cut", "emergency rate hike", "emergency meeting", "surprise rate cut",
        "bank run", "circuit breaker", "trading halted", "trading suspended",
        "debt default", "liquidity freeze", "bank collapse", "bailout", "flash crash"
    ]

    HIGH_VELOCITY_KEYWORDS = [
        "plunges", "surges", "slashes", "halts", "suspends", "bans", "strikes",
        "collapses", "explodes", "threatens", "emergency", "orders", "warns",
        "retaliates", "seizes", "intercepts", "spikes", "tumbles", "crashes"
    ]

    STOPWORDS = {
        "the", "a", "an", "in", "to", "and", "of", "on", "for", "with", "at", "by", "from",
        "as", "is", "are", "was", "were", "be", "been", "has", "have", "had", "it", "its",
        "after", "says", "said", "new", "amid", "over", "into", "about", "against", "more",
        "than", "will", "would", "could", "should", "out", "up", "down", "ahead", "before"
    }

    @classmethod
    def extract_keywords(cls, title: str) -> set:
        """Extracts significant alphanumeric tokens from a title."""
        if not title:
            return set()
        words = re.findall(r'[a-zA-Z0-9]{3,}', title.lower())
        return {w for w in words if w not in cls.STOPWORDS}

    @classmethod
    def calculate_multi_wire_consensus(cls, items: list) -> list:
        """
        Analyzes a batch of fresh news items across all feeds.
        Detects if multiple distinct news agencies are reporting the same story.
        Attaches 'consensus_sources' and 'consensus_count' to each item.
        """
        if not items:
            return items

        # Pre-extract keywords for each item
        item_kw = []
        for it in items:
            title = (it.get("title") or "").strip()
            kw = cls.extract_keywords(title)
            src = (it.get("source") or "").strip()
            item_kw.append((it, kw, src))

        for i, (it_i, kw_i, src_i) in enumerate(item_kw):
            consensus_sources = {src_i} if src_i else set()

            for j, (it_j, kw_j, src_j) in enumerate(item_kw):
                if i == j:
                    continue
                # Same publisher under different categories doesn't count as multi-wire consensus
                clean_src_i = re.split(r'[\s\-_]', src_i.lower())[0] if src_i else "1"
                clean_src_j = re.split(r'[\s\-_]', src_j.lower())[0] if src_j else "2"
                if clean_src_i == clean_src_j:
                    continue

                # Calculate token intersection
                intersection = kw_i & kw_j
                if not intersection:
                    continue

                # If >= 3 significant keywords match, OR >= 2 rare keywords match with high Jaccard
                union = kw_i | kw_j
                jaccard = len(intersection) / len(union) if union else 0.0

                if len(intersection) >= 3 or (len(intersection) >= 2 and jaccard >= 0.35):
                    consensus_sources.add(src_j)

            it_i["consensus_sources"] = list(consensus_sources)
            it_i["consensus_count"] = len(consensus_sources)

        return items

    @classmethod
    def evaluate_velocity(cls, item: dict) -> dict:
        """
        Evaluates the velocity tier, gap requirements, and urgency score for an item.
        """
        title = (item.get("title") or "").strip()
        desc = (item.get("description") or "").strip()
        full_text = f"{title} {desc}".lower()

        consensus_count = item.get("consensus_count", 1)
        consensus_sources = item.get("consensus_sources", [item.get("source", "")])

        # 1. Tier 3: ULTRA BREAKING
        # Triggered if extreme crisis keywords are present OR multi-wire consensus >= 2 sources!
        has_crisis_kw = any(k in full_text for k in cls.CRISIS_KEYWORDS)
        is_multi_wire = consensus_count >= 2

        is_ultra_breaking = has_crisis_kw or (is_multi_wire and any(k in full_text for k in cls.HIGH_VELOCITY_KEYWORDS))
        if not is_ultra_breaking and is_multi_wire:
            # 2 distinct wires reporting on the same event is at least High Velocity
            is_high_velocity = True
        else:
            is_high_velocity = any(k in full_text for k in cls.HIGH_VELOCITY_KEYWORDS)

        if is_ultra_breaking:
            tier = "ULTRA_BREAKING"
            required_gap = 60.0   # Instant 1-minute gap for major crises and multi-wire flashes
            bypass_cooldown = True
            urgency_score = 1000 + (consensus_count * 200)
            urgency_reason = f"Multi-wire consensus ({consensus_count} sources: {', '.join(consensus_sources[:3])})" if is_multi_wire else "Tier-1 Crisis flashpoint"
        elif is_high_velocity:
            tier = "HIGH_VELOCITY"
            required_gap = 120.0  # High velocity: 2-minute window
            bypass_cooldown = False
            urgency_score = 500 + (consensus_count * 100)
            urgency_reason = f"High velocity market flash ({consensus_count} sources)" if is_multi_wire else "High-velocity market movement"
        else:
            tier = "STANDARD"
            required_gap = 180.0  # Standard 3-minute pacing for responsive channel flow
            bypass_cooldown = False
            urgency_score = 100
            urgency_reason = "Standard macroeconomic wire"

        return {
            "tier": tier,
            "is_ultra_breaking": is_ultra_breaking,
            "is_high_velocity": is_high_velocity,
            "consensus_count": consensus_count,
            "consensus_sources": consensus_sources,
            "required_gap": required_gap,
            "bypass_cooldown": bypass_cooldown,
            "urgency_score": urgency_score,
            "urgency_reason": urgency_reason
        }

    @classmethod
    def prioritize_pending(cls, items: list) -> list:
        """
        Sorts pending candidates by urgency score (highest first), breaking ties by newest timestamp.
        """
        if not items:
            return []

        # Run multi-wire consensus detection across the batch
        items = cls.calculate_multi_wire_consensus(items)

        def sort_key(it):
            eval_res = cls.evaluate_velocity(it)
            it["velocity_eval"] = eval_res
            return eval_res["urgency_score"]

        return sorted(items, key=sort_key, reverse=True)
