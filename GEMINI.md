# 🌟 XAU/USD News Assistant & Telegram Mini App — Core Constitutional Rules

This repository is governed by the 5 Golden Principles established by the system architect:

### 1. ⚡ លឿនរហ័ស (Speed & Sub-Second Latency)
- Spot XAU/USD live price updates with millisecond precision matching MT5 ticks.
- Direct Binance aggregate trades (`@aggTrade`) WebSocket + multi-feed fallback.
- Instant initial UI rendering (Zero Glitch startup).

### 2. 🎯 ត្រឹមត្រូវច្បាស់លាស់ (Absolute Precision & Fixed Structural Levels)
- Signal boxes (Entry Zone, Stop Loss, TP1, TP2) MUST remain 100% frozen/locked on established structural levels during waiting states. They NEVER float with market price ticks.
- Levels only update to genuine confirmed numbers when AI validates the setup and the action button turns ready.
- Real-time calibration against Interbank Forex Spot (Gold-API) ensures exact MT5 price alignment.

### 3. 🧠 ឆ្លាតខ្លាំង (Deep Intelligence & Institutional Confluence)
- Dual-engine: SMC (BOS, CHoCH, Order Block, FVG, 0.618-0.786 OTE Fibonacci) combined with CVD Whale volume, Depth, Killzones, and Macro DXY analysis.
- Only Grade A+ setups with Institutional Safety Index >= 70% are approved for execution.

### 4. 🛡️ គោរពតាមគោលការណ៍ (Strict Protocol Compliance)
- Daily signal limit: Maximum 3 to 5 signals per day; strict trading cutoff at 10:00 PM Cambodia Time (UTC+7).
- Action button waiting text must strictly remain concise: `រង់ចាំ Signal ថ្មី` (no verbose calculations or cluttered descriptions).
- Channel broadcast: Only dispatch the unified single-bubble package (Interactive Poll + Mini App CTA Button) into the Telegram channel. Raw signal levels are never exposed in plain text on the channel, ensuring users engage via the Mini App.

### 5. ♾️ ប្រើប្រាស់បានយូរ មិនរាំងស្ទះ (Long-Term Stability & Zero Bottlenecks)
- Self-healing multi-stream architecture (Binance WebSocket, Gold-API, Swissquote, CoinGecko).
- Automatic reconnects, memory safety, isolated error handlers.
- Built for 24/7 uninterrupted high-reliability operation.
