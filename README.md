# 🥇 XAUUSD NEWS ASSISTANT — TELEGRAM AUTO ALERT BOT

ប្រព័ន្ធស្វ័យប្រវត្តិ 100% សម្រាប់តាមដានព័ត៌មាន XAUUSD (មាស) វិភាគ និងផ្ញើដំណឹងជូនដំណឹងទៅកាន់ Telegram Channel/Group ដោយផ្ទាល់ជាខេមរភាសា ដោយអ្នកប្រើប្រាស់ **មិនបាច់ចុចអ្វីទាំងអស់ (Receive-Only)**។

---

## 🌟 លក្ខណៈពិសេសចម្បង (Core Features)

1. **🌐 Market Information & Validation**:
   - ប្រមូលទិន្នន័យពីប្រភពដែលអាចទុកចិត្តបាន (ForexFactory, Yahoo Finance, Live Feeds)។
   - ត្រួតពិនិត្យ និងផ្ទៀងផ្ទាត់ទិន្នន័យសេដ្ឋកិច្ច (CPI, NFP, Fed Interest Rates, Treasury Yields, China Gold Events)។

2. **🥇 Daily Gold Price (ស្ដង់ដារទម្ងន់មាសខ្មែរ)**:
   - គណនាតម្លៃមាស XAUUSD ទៅតាមឯកតាខ្មែរត្រឹមត្រូវ៖
     - **1 Troy Ounce** = 31.1034768 grams
     - **1 តម្លឹង** = 37.5 grams (1.20565 Troy Ounce)
     - **1 ជី** = 1/10 តម្លឹង = 3.75 grams
     - **1 ហ៊ុន** = 1/10 ជី = 0.375 grams
   - បង្ហាញ Daily Change ($ និង %) + ម៉ោងនៅកម្ពុជា (UTC+7)
   - **Auto-Pin** សារនេះជារៀងរាល់ថ្ងៃ (ម៉ោង 07:00 ព្រឹក) ដោយស្វ័យប្រវត្តិ។

3. **⏱️ Dynamic Monitoring Modes**:
   - 🟢 **Mode 1 (Normal Day)**: ឆែករៀងរាល់ 1 ម៉ោង (បើគ្មានព័ត៌មានថ្មី មិន spam ទេ)។
   - 🟡 **Mode 2 (Upcoming News)**: ផ្ញើការរំលឹក 15 នាទី និង 5 នាទីមុនព័ត៌មាន High-Impact ចេញ។
   - 🔴 **Mode 3 (High-Impact Release)**: ប្តូរទៅឆែករៀងរាល់ 30 វិនាទី ហើយនៅពេល `Actual` ចេញ ផ្ញើ Flash Alert ភ្លាមៗ (Send Immediately)។
   - 🚨 **Mode 4 (Breaking Event)**: ផ្ញើការវិភាគបន្ទាន់ភ្លាមៗពេលមានព្រឹត្តិការណ៍សង្គ្រាម ឬការផ្លាស់ប្តូរនយោបាយរូបិយវត្ថុបន្ទាន់។

4. **🧠 Khmer Macroeconomic Analysis Engine**:
   - រៀបចំសារតាមលំដាប់លំដោយ៖
     1. 🚨 តើមានអ្វីកើតឡើង? (WHAT HAPPENED?)
     2. 📊 ទិន្នន័យជាក់ស្តែង (Actual vs Forecast vs Previous)
     3. 🧠 ហេតុអ្វីវាសំខាន់? (WHY IT MATTERS)
     4. 💵 ផលប៉ះពាល់លើ USD (USD IMPACT)
     5. 🏦 សម្ពាធលើអត្រាការប្រាក់/Yields (RATES & YIELDS)
     6. 🥇 សម្ពាធលើ XAUUSD: 🟢 Possible Bullish / 🔴 Possible Bearish / 🟡 Mixed
     7. ⚠️ ការប្រែប្រួល និង Price Action Confirmation Reminder
     8. 🔗 ប្រភពទិន្នន័យ

5. **🛡️ Anti-Spam & SQLite Persistence**:
   - ចងចាំ Event ID, Actual Data, និង News Hash មិនឱ្យផ្ញើស្ទួនដាច់ខាត។

---

## 🚀 របៀបតម្លើង និងដំណើរការ (Setup & Run)

### 1. បង្កើត Telegram Bot និងយក Chat ID
- ចូលទៅកាន់ Telegram ស្វែងរក `@BotFather` រួចវាយ `/newbot` ដើម្បីយក **BOT TOKEN**។
- បង្កើត Channel ឬ Group រួចទាញ Bot ចូលជា **Administrator**។
- យក **CHAT ID** របស់ Channel (ឧ. `@your_channel` ឬ ID `-100xxxxxxxxx`)។

### 2. កំណត់ `.env`
ចម្លង `.env.example` ទៅជា `.env` រួចបំពេញព័ត៌មាន៖
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=-1001234567890
```

### 3. ដំណើរការតេស្តសាកល្បង (Test Simulation)
```powershell
python test_simulation.py
```

### 4. ដំណើរការ Bot ជាផ្លូវការ (Run Autonomous Bot)
```powershell
python -c "from main import XAUUSDNewsAssistantBot; bot = XAUUSDNewsAssistantBot(); bot.start_loop()"
```

<!-- auto-deploy verification 1790021531 -->
