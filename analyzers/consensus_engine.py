import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class MultiAIConsensusEngine:
    """
    Hedge Fund-Grade Multi-AI Council Consensus Engine:
    Polls Google Gemini, Claude 3.5 Sonnet, and OpenAI/DeepSeek concurrently.
    Evaluates institutional voting (requires >= 2/3 agreement for BUY or SELL).
    If there is a conflict or insufficient confluence, enforces WAIT / NO TRADE.
    """

    def __init__(self, analyzers: list):
        self.analyzers = analyzers or []

    def get_active_council(self) -> List[Any]:
        """Returns all configured and available AI analyzers."""
        return [a for a in self.analyzers if getattr(a, "is_available", lambda: False)()]

    def generate_consensus_setup(
        self,
        current_price: float,
        key_levels: dict,
        macro_data: dict = None,
        order_book: dict = None,
        timeout: float = 18.0
    ) -> Optional[Dict[str, Any]]:
        """
        Executes parallel calls across active AI models and aggregates their verdicts into a unified Consensus Setup.
        """
        active_ai = self.get_active_council()
        if not active_ai:
            logger.warning("[AIConsensus] No active AI providers available for consensus.")
            return None

        # If only 1 AI is available, fallback to single provider response
        if len(active_ai) == 1:
            analyzer = active_ai[0]
            name = getattr(analyzer, "name", analyzer.__class__.__name__)
            try:
                res = analyzer.generate_smart_smc_setup(current_price, key_levels, macro_data, order_book)
                if res:
                    res["ai_council"] = {
                        "mode": "Single AI (Fallback)",
                        "votes": [{
                            "name": name,
                            "vote": res.get("direction", "WAIT").upper(),
                            "confidence": res.get("confidence", "85%")
                        }],
                        "consensus_reached": True,
                        "ratio": "1/1",
                        "verdict": res.get("direction", "WAIT").upper()
                    }
                return res
            except Exception as e:
                logger.error(f"[AIConsensus] Single AI {name} failed: {e}")
                return None

        ai_votes = []
        raw_results = {}

        def _fetch_from_ai(ai_instance):
            name = getattr(ai_instance, "name", ai_instance.__class__.__name__)
            try:
                setup = ai_instance.generate_smart_smc_setup(current_price, key_levels, macro_data, order_book)
                return name, setup, None
            except Exception as exc:
                return name, None, exc

        # Execute concurrently with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(len(active_ai), 4)) as executor:
            future_to_ai = {executor.submit(_fetch_from_ai, ai): ai for ai in active_ai}
            try:
                for future in as_completed(future_to_ai, timeout=timeout):
                    try:
                        name, setup, err = future.result()
                        if setup and isinstance(setup, dict):
                            direction = str(setup.get("direction", "WAIT")).strip().upper()
                            if "BUY" in direction:
                                clean_dir = "BUY"
                            elif "SELL" in direction:
                                clean_dir = "SELL"
                            else:
                                clean_dir = "WAIT"

                            conf = setup.get("confidence", "85%")
                            ai_votes.append({
                                "name": name,
                                "vote": clean_dir,
                                "confidence": conf
                            })
                            raw_results[name] = setup
                        else:
                            logger.warning(f"[AIConsensus] {name} returned invalid or empty setup. Error: {err}")
                    except Exception as e:
                        logger.warning(f"[AIConsensus] Individual AI thread error: {e}")
            except TimeoutError:
                logger.info(f"[AIConsensus] Timeout {timeout}s reached. Proceeding with responses from {len(ai_votes)} AI models.")
            except Exception as e:
                logger.warning(f"[AIConsensus] AI polling warning: {e}")

        if not ai_votes:
            logger.warning("[AIConsensus] No valid responses received from any AI model.")
            return None

        total_voters = len(ai_votes)
        buy_votes = sum(1 for v in ai_votes if v["vote"] == "BUY")
        sell_votes = sum(1 for v in ai_votes if v["vote"] == "SELL")
        wait_votes = sum(1 for v in ai_votes if v["vote"] == "WAIT")

        # Determine Consensus
        consensus_verdict = "WAIT"
        consensus_reached = False
        primary_setup = None

        # Strict 2/3 majority or unanimous if 2 voters
        if total_voters >= 3:
            if buy_votes >= 2 and buy_votes > sell_votes:
                consensus_verdict = "BUY"
                consensus_reached = True
            elif sell_votes >= 2 and sell_votes > buy_votes:
                consensus_verdict = "SELL"
                consensus_reached = True
        elif total_voters == 2:
            if buy_votes == 2:
                consensus_verdict = "BUY"
                consensus_reached = True
            elif sell_votes == 2:
                consensus_verdict = "SELL"
                consensus_reached = True

        # Select the highest quality setup that matches the verdict
        matching_setups = [
            raw_results[v["name"]] for v in ai_votes if v["vote"] == consensus_verdict and v["name"] in raw_results
        ]

        if matching_setups:
            # Prefer setups with complete SL, TP1, and TP2
            primary_setup = matching_setups[0]
            for s in matching_setups:
                if s.get("sl") and s.get("tp1") and s.get("tp2"):
                    primary_setup = s
                    break
        else:
            # If WAIT or conflict, pick any available result or construct safe WAIT setup
            any_key = next(iter(raw_results))
            primary_setup = raw_results[any_key].copy()
            primary_setup["direction"] = "WAIT"
            primary_setup["setup_title"] = "🟡 ក្រុមប្រឹក្សា AI ណែនាំរង់ចាំ (MULTI-AI CONSENSUS WAIT)"
            primary_setup["entry"] = primary_setup.get("entry") or current_price
            primary_setup["entry_zone"] = primary_setup.get("entry_zone") or f"${current_price:,.2f}"
            primary_setup["sl"] = primary_setup.get("sl") or round(current_price - 10.0, 2)
            primary_setup["tp1"] = primary_setup.get("tp1") or round(current_price + 15.0, 2)
            primary_setup["tp2"] = primary_setup.get("tp2") or round(current_price + 25.0, 2)
            primary_setup["why_this_trade"] = (
                f"• សមាជិកក្រុមប្រឹក្សា AI មានការខ្វែងគំនិតគ្នា (BUY: {buy_votes}, SELL: {sell_votes}, WAIT: {wait_votes})។\n"
                f"• ទីផ្សារកំពុងស្ថិតក្នុងតំបន់ហានិភ័យ ឬ Liquidity Trap គ្មាន Confluence ច្បាស់លាស់ឡើយ។"
            )
            primary_setup["why_not_opposite"] = "• ហាមបើក Position ទាំង BUY និង SELL ព្រោះមិនទាន់មានការឯកភាព 2/3 សំឡេង។"

        # Attach AI Council Breakdown
        primary_setup["direction"] = consensus_verdict
        primary_setup["ai_council"] = {
            "mode": f"Multi-AI Council ({total_voters} Members)",
            "votes": ai_votes,
            "consensus_reached": consensus_reached,
            "ratio": f"{max(buy_votes, sell_votes, wait_votes)}/{total_voters}",
            "verdict": consensus_verdict
        }

        # Boost confidence when high consensus achieved
        if consensus_reached:
            primary_setup["confidence"] = f"{min(95, 85 + (buy_votes if consensus_verdict == 'BUY' else sell_votes) * 4)}%"

        logger.info(
            f"[AIConsensus] Verdict: {consensus_verdict} (BUY:{buy_votes}, SELL:{sell_votes}, WAIT:{wait_votes}) "
            f"Consensus reached: {consensus_reached}"
        )
        return primary_setup
