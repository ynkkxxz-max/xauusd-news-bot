import requests
import json

key = "AQ.Ab8RN6JtMkYA8Hns4E2Kjg1io_Q3DDVBOPrPtgIU6C-rXphBLQ"
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={key}"

prompt = """
You are an institutional Gold (XAUUSD) & Macroeconomic Analyst writing in Khmer.
Market Data:
- US Core CPI Actual: 0.4% (Forecast: 0.3%, Previous: 0.3%)
- Gold Spot Price: $2,915.20
- US Dollar Index (DXY): 104.85 (+0.42%)
- 10-Year Treasury Yield: 4.45% (+4.2 bps)

Please provide a structured high-conviction analysis in Khmer.
Respond ONLY with a valid JSON object matching this schema:
{
  "headline": "ចំណងជើងសង្ខេបគួរឱ្យចាប់អារម្មណ៍ (Short Impactful Headline)",
  "what_happened": "ព្រឹត្តិការណ៍ជាក់ស្ដែង (What happened with numbers and comparisons)",
  "usd_yields_impact": "ផលប៉ះពាល់លើ USD និង Yields (Why DXY and yields moved)",
  "gold_pressure": "សម្ពាធលើ XAUUSD (បញ្ជាក់ច្បាស់ 🟢 Possible Bullish ឬ 🔴 Possible Bearish រួមទាំងហេតុផលសេដ្ឋកិច្ច)",
  "trader_advice": "ដំបូន្មាននិងចំណុចប្រុងប្រយ័ត្នសម្រាប់ Trader (Confirmation, Volume, Key Levels)"
}
"""

payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {
        "response_mime_type": "application/json",
        "temperature": 0.2
    }
}

resp = requests.post(url, json=payload, timeout=20)
print("Status:", resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    content = data["candidates"][0]["content"]["parts"][0]["text"]
    with open("gemini_khmer_sample.json", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS! Output written to gemini_khmer_sample.json")
else:
    print("Error:", resp.text)
