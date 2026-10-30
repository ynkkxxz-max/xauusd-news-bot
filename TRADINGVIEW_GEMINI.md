# TradingView setup reviews

The V11 Pine script adds closed-bar PREP BUY / PREP SELL labels for armed,
unbreached pullback triggers. A PREP label is not an entry. Trend changes,
expiry and entry filters can cancel the setup. All previous trade simulation
rules remain unchanged. Native trade arrows can be hidden in Style → Trades
on chart; updating the script can reset this display preference.

The server accepts V11 `gold-setup-v1` JSON events at:

`POST https://<existing-render-host>/api/tradingview/<private-token>`

Use a server-side `TRADINGVIEW_WEBHOOK_TOKEN` with at least 32 random characters.
If it is not set, the module derives a separate token from `GEMINI_API_KEY`
using HMAC-SHA256. The Google key is never sent to TradingView. Changing that
key changes the derived token. Keep the entire webhook URL private.

Server requirements: existing `GEMINI_API_KEY`, existing `GEMINI_MODEL`, and a
running Render service. No additional Python package is required. Ensure
Render deploys the commit containing `tradingview_gemini_bridge.py` and the
updated `render_server.py`.

In TradingView create a strategy alert using **alert() function calls only**,
enable Webhook URL and enter the private URL above. A paid plan and/or account
configuration may restrict webhooks; the UI must confirm availability. TradingView
requires two-factor authentication for webhooks. Do not select order fills:
those use a different payload. Recreate an existing alert after any script or
input update because TradingView stores a snapshot when an alert is created.

The endpoint acknowledges queued work immediately, before the Gemini request,
to fit TradingView's three-second delivery timeout. It rejects stale/future
candles, invalid OHLC data, unauthenticated requests, conflicting retries and
excess request bursts. Identical retries do not generate extra AI calls. A
failed or malformed Gemini response produces WAIT, never an approval.

Read the latest 30 results privately with GET at the same URL. Reviews include
the original symbol, candle close, event, side, model, Khmer explanation and
missing context. SQLite stores recent reviews on the service filesystem; Render
ephemeral storage can be lost on redeploy, so this is not a permanent trade
journal. Pending jobs survive a process restart only while that file survives.

Gemini can report technical consistency or WAIT. Its answer does not feed back
into Pine, change backtest trades or place orders. No AI score is presented as
a measured win probability. Improving win rate requires separate forward and
out-of-sample testing, including costs, drawdown and profit factor.

Validation: six unit tests cover auth, acknowledgement before AI work, duplicate
delivery, invalid/stale data, failure behavior, structured responses and restart
recovery. A real Google API smoke test also verified Khmer structured output.

References:
- https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/
- https://www.tradingview.com/pine-script-docs/faq/alerts/
- https://ai.google.dev/gemini-api/docs/structured-output
