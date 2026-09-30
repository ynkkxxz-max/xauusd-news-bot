# 🌟 XAU/USD News Assistant & Telegram Mini App — Core Constitutional Rules

This repository is governed by the 5 Golden Principles established by the system architect:

### 1. ⚡ លឿនរហ័ស (Speed & Sub-Second Latency)
- Spot XAU/USD live price updates with millisecond precision matching MT5 ticks.
- Direct Binance aggregate trades (`@aggTrade`) WebSocket + multi-feed fallback.
- Instant initial UI rendering (Zero Glitch startup).

### 2. 🎯 ត្រឹមត្រូវច្បាស់លាស់ (Absolute Precision & Fixed Structural Levels)
- **តម្លៃ Signal នៅដដែលមិនផ្លាស់ប្ដូរបន្ទាប់ពីចេញ Signal (Strict Post-Issue Signal Freezing):**
  - បន្ទាប់ពី AI បញ្ជាក់ និងចេញ Signal រួច (ប៊ូតុងប្រែជា `អាចប្រើប្រាស់ Signal នេះបាន`) តម្លៃទាំង ៤ ប្រអប់ (`Entry Zone`, `Stop Loss`, `TP1`, `TP2`) ត្រូវតែស្ថិតនៅ **តម្លៃដដែល ១០០% មិនផ្លាស់ប្ដូរ** ដាច់ខាត។
  - ហាមមិនឱ្យរត់តាម Tick ឬ Recalculate តាមរលក Fibonacci ជាដាច់ខាត ដើម្បីកុំឱ្យអ្នកប្រើប្រាស់ច្រឡំ និងអាចដឹងច្បាស់ថាតើពួកគេបានប្រើប្រាស់តម្លៃនេះក្នុងការចូលផ្សារពិតជាបាន TP1, TP2 ឬ SL ពិតប្រាកដឬទេ។
- **ប្ដូរតម្លៃលុះត្រាតែ AI វិភាគត្រឹមត្រូវសិនទើបដាក់ឱ្យប្រើប្រាស់ Signal ថ្មី:**
  - ក្នុងអំឡុងពេលរង់ចាំ `រង់ចាំ Signal ថ្មី` តម្លៃនឹងមិនផ្លាស់ប្តូរផ្តេសផ្តាសឡើយ។
  - លុះត្រាតែ AI វិភាគ (Analyze) ផ្ទៀងផ្ទាត់គ្រប់លក្ខខណ្ឌត្រឹមត្រូវ ១០០% សិន (Safety Index >= 70%, ដល់តំបន់ OTE 0.618-0.786, រចនាសម្ព័ន្ធ M15/H1 ស្របគ្នា) ហើយប៊ូតុងប្រែជា `អាចប្រើប្រាស់ Signal នេះបាន` ទើបធ្វើបច្ចុប្បន្នភាពលេខ Signal ថ្មី។
- **Stop Loss (SL) strictly $8, $10, max $12:**
  - ចម្ងាយ SL ធៀបនឹង Entry ត្រូវតែគោរពតាមគោលការណ៍ចាស់ដដែលគឺ **$8, $10, អតិបរមា $12 ($8 - $10, max $12, NEVER exceed $12)**។
  - សម្រាប់ **SELL**: SL MUST strictly be ABOVE the Entry Zone (`SL = EntryHigh + 8~10 points`, max 12 points). ហាមដាច់ខាតមិនឱ្យ SL នៅក្រោម Entry។
  - សម្រាប់ **BUY**: SL MUST strictly be BELOW the Entry Zone (`SL = EntryLow - 8~10 points`, max 12 points). ហាមដាច់ខាតមិនឱ្យ SL នៅលើ Entry។
- **TP តាមការគិតរបស់ AI & ចំណុច Entry សុវត្ថិភាពបំផុត:**
  - Take Profit (TP1 & TP2) ត្រូវកំណត់តាមការគិត និងការវិភាគបច្ចេកទេសរបស់ AI SMC (TP1: 1.5R BE Secured, TP2: 2.5R+ Max Liquidity Sweep BSL/SSL)។
  - ចំណុច Entry ត្រូវតែជាតំបន់សុវត្ថិភាពបំផុត (SMC OTE Golden Ratio 0.618-0.786 Fibonacci Retracement + Order Block / FVG mitigation)។
- **Real-Time Calibration:** Real-time calibration against Interbank Forex Spot (Gold-API) ensures exact MT5 price alignment.
- **Zero UI Contradiction & Instant Auto-Purge**:
  - Top Hero Bias, M15/H1 Structure, Confluence Matrix, Action Button, and Signal Boxes MUST be 100% harmonized. A SELL header must NEVER coexist with a BUY signal or vice versa.

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

### 6. 📌 អាទិភាពការងារបច្ចុប្បន្ន (Current Development Priority Directive)
- **Mini App Update Active**: បន្តការ Update និងកែលម្អលើ Telegram Mini App (`index.html`) ឡើងវិញតាមការណែនាំរបស់អ្នកប្រើប្រាស់។
- **Bot & Channel Continuous Monitoring**: រក្សាដំណើរការ Bot Engine (`main.py`) ឱ្យដើរស្វ័យប្រវត្តិក្នង Background ដើម្បីបន្តត្រួតពិនិត្យ និងផ្សាយព័ត៌មានលើ Channel ២៤/៧ ដោយរលូន។

### 7. 🥇 ស្តង់ដារផ្សាយហាងឆេងមាសប្រចាំថ្ងៃ (Daily Gold Price Broadcast Standard)
- **កាលវិភាគម៉ោង ៧:០០ ព្រឹក (Strict 07:00 AM, Once Per Day)**:
  - ត្រូវផ្សាយចូល Telegram Group/Channel ត្រឹមតែ **១ ដងគត់ក្នុងមួយថ្ងៃនៅវេលាម៉ោង ៧:០០ ព្រឹក** (ម៉ោងនៅកម្ពុជា UTC+7)។ មិនត្រូវផ្សាយខុសម៉ោង ឬច្រឡំផ្សាយពេលរសៀលនៅពេល Bot restart ឡើយ។
  - ផ្ញើជា Plain/HTML Text ស្អាត គ្មានប៊ូតុង Inline Buttons រញ៉េរញ៉ៃឡើយ។
- **ទម្រង់អក្សរ និងគម្លាតច្បាស់លាស់ (Strict Alignment Template)**:
  - ត្រូវរក្សាទម្រង់ស្អាត ស្មើជួរគម្លាត Space ឥតខ្ចោះដូចខាងក្រោម៖
```text
🥇  <b>DAILY GOLD PRICE — ហាងឆេងមាសប្រចាំថ្ងៃ</b>

📅  <b>កាលបរិច្ឆេទ:</b> {date_str} 


 🌐<b>1 អោន :</b> ${price_oz:,.2f}

🇰🇭 <b>1 តម្លឹង:</b> លក់ ${damlung_sell:,.2f} | ទិញ ${damlung_buy:,.2f}
      
      <b>1 ជី:</b> លក់ ${chi_sell:,.2f} | ទិញ ${chi_buy:,.2f}

 📉   <b>បម្រែបម្រួល:</b> {sign}${change:,.2f} ({sign}{change_pct:.2f}%)
```
  - លុបចោលទាំងស្រុងនូវការបកស្រាយវែងអន្លាយ (Macro correlation, Pivot breakdown, Summary) ដើម្បីរក្សាភាពសាមញ្ញ ស្រួលមើល និងមានសោភ័ណភាពខ្ពស់។

### 8. 🚨 ស្តង់ដារផ្សាយព័ត៌មានទាន់ហេតុការណ៍ (Breaking News Standard)
- **វិស័យស្នូលទាំង ៧ នៃព័ត៌មាន (The 7 Core News Pillars)**:
  1. 🌐 **សេដ្ឋកិច្ច (Economy)**: GDP, CPI, អតិផរណា, NFP, ការងារ, Retail Sales, PMI, កំណើនសេដ្ឋកិច្ច។
  2. ⚔️ **នយោបាយភូមិសាស្ត្រ (Geopolitics)**: សង្គ្រាម, ជម្លោះ, មជ្ឈិមបូព៌ា, អ៊ុយក្រែន, ច្រកសមុទ្រយុទ្ធសាស្ត្រ។
  3. 💻 **បច្ចេកវិទ្យា (Technology)**: AI, Semiconductor, បន្ទះឈីប Chips, Big Tech, សន្តិសុខ Cyber។
  4. 🏦 **គោលនយោបាយរូបិយវត្ថុ និងធនាគារកណ្តាល (Monetary Policy & Central Banks)**: Fed, Powell, FOMC, អត្រាការប្រាក់, ECB, BOJ, PBOC, ទុនបម្រុងមាស។
  5. 🛢️ **បរិស្ថាន និងធនធានធម្មជាតិ (Environment & Natural Resources)**: ប្រេងកាត OPEC, ថាមពល, រ៉ែមាស, ធនធានធម្មជាតិ។
  6. 👥 **កត្តាសង្គម និងប្រជាសាស្ត្រ (Social & Demographic Factors)**: កូដកម្មការងារ, ប្រាក់ឈ្នួល, ចិត្តសាស្ត្រអ្នកប្រើប្រាស់។
  7. ⚖️ **ច្បាប់ បទប្បញ្ញត្តិ និងគោលនយោបាយរដ្ឋាភិបាល (Laws, Regulations & Government Policies)**: ពន្ធគយ Tariffs, ទណ្ឌកម្ម, បំណុលរដ្ឋ, ច្បាប់ហិរញ្ញវត្ថុ/Crypto។
- **គោលការណ៍ផ្សាយចេញមុនគេជាបន្ទាន់ (Zero-Delay & First-to-Publish Mandate — បញ្ជាកំពូល)**:
  - ឱ្យតែ AI វាយតម្លៃថាជាព័ត៌មានថ្មី ធំ សំខាន់ ទាក់ទងនឹងពិភពលោក និងទីផ្សារហិរញ្ញវត្ថុ ស្ថិតក្នុងចំណោមវិស័យស្នូលទាំង ៧ ខាងលើ **ត្រូវតែចេញផ្សាយមុនគេភ្លាមៗជាដាច់ខាត (Must Publish First / Instant Broadcast)** ដោយគ្មានការរារាំង ឬពន្យារពេលឡើយ។ ត្រូវគោរពច្បាប់នេះជាចម្បង។
- **ភាពថ្មីស្រឡាង និងការទប់ស្កាត់ការផ្ញើជាន់គ្នា (Strict Freshness & Anti-Duplicate Rule)**:
  - **ត្រូវតែថ្មី (Fresh Only)**: ហាមផ្ញើសារដដែល ឬព័ត៌មានដែលបានផ្សាយរួចក្នុងរយៈពេល ២៤ ម៉ោងជាដាច់ខាត (Cross-Source Semantic Deduplication 24 Hours)។
  - **បើមិនថ្មី ឬមិនច្បាស់ កុំផ្ញើ**: ប្រសិនបើព័ត៌មាននោះចាស់ ស្រពិចស្រពិល ឬគ្មានឥទ្ធិពលជាក់ស្តែងលើទីផ្សារ ត្រូវទម្លាក់ចោល (`is_clear = false`) មិនត្រូវផ្ញើចូល Channel ឡើយ។
- **ខ្លឹមសាររៀបរាប់ក្បោះក្បាយត្រឹមត្រូវទាន់ហេតុការណ៍ (Accurate & Comprehensive Storytelling)**:
  - ត្រូវរៀបរាប់ដំណើររឿងជាក់ស្តែងឱ្យបានក្បោះក្បាយ ត្រឹមត្រូវតាមសាច់រឿងព័ត៌មាន និងទាន់ហេតុការណ៍ក្រោមចំណងជើង `🔹 ព្រឹត្តិការណ៍សំខាន់:` ដើម្បីឱ្យអ្នកអានយល់ពីប្រភពរឿងដើមហេតុ ហេតុអ្វីបានជាកើតឡើង។
  - **ហាមដាច់ខាតកុំបង្ខំភ្ជាប់រឿងមាស ឬប្រាក់ដុល្លារ ($) បើមិនពាក់ព័ន្ធ (Strict No Forced Gold/USD Rule — បញ្ជាផ្ទាល់)**:
    - ប្រសិនបើព័ត៌មាននោះ **មិនប៉ះពាល់ដល់មាស ឬប្រាក់ដុល្លារ ($) ទេ ហាមនិយាយរឿងមាស ឬប្រាក់ដុល្លារចូលឱ្យសោះ**! គ្រាន់តែរៀបរាប់ និងពន្យល់ពីដំណើររឿងព័ត៌មាននោះឱ្យគេយល់ច្បាស់ និងត្រឹមត្រូវ គឺគ្រប់គ្រាន់ និងត្រឹមត្រូវបំផុតហើយ។
    - លើកលែងតែព័ត៌មាននោះពិតជាមានផលប៉ះពាល់ជាក់ស្តែងលើទីផ្សារមាស ឬដុល្លារ (ដូចជា Fed, CPI, NFP, សង្គ្រាមបិទច្រកប្រេង Hormuz, ពន្ធគយ Tariffs) ទើបមានការវិភាគបន្ថែមពីឥទ្ធិពលលើតម្លៃមាស (XAUUSD) និងប្រាក់ដុល្លារ (USD)។
  - លុបចោលការបែងចែកជាចំណុចកំប៉ិកកំប៉ុកដាច់ៗ (តើមានអ្វីកើតឡើង, ហេតុអ្វីសំខាន់, ផលប៉ះពាល់ USD/Yields)។
- **រូបភាពពិតប្រាកដ ១០០% ពីអត្ថបទ (Genuine Article Image Only — Zero Mismatch)**:
  - រូបភាពដែលត្រូវភ្ជាប់មកជាមួយ ត្រូវតែជារូបភាពពិតប្រាកដដែលទាញចេញផ្ទាល់ពី Article នៃសារព័ត៌មាននោះ (`og:image` / `twitter:image`) តែប៉ុណ្ណោះ។
  - **ហាមដាច់ខាត** ការទាញយករូបភាពពី Link ប្រភេទ Category/Section Pages (ដូចជា `/world`, `/news`, `/politics`, `/markets`) ឬរូប Logo (Google News logo, វេបសាយ icon) ឬរូបភាពដែលមិនត្រូវនឹងសាច់រឿង (ដូចជារូបឡើងភ្នំព្រិលលើរឿង Trump/Iran)។
  - ប្រសិនបើព័ត៌មាននោះគ្មានរូបភាពពិត ឬមិនប្រាកដថាទាក់ទងនឹងសាច់រឿង ១០០% ទេ ត្រូវផ្ញើជា **Plain Text Message ស្អាតជានិច្ច** ជាមួយ Link និង Button អានបន្ថែម ដោយមិនយករូបភាពបន្លំ ឬរូបភាពដែលមិនត្រូវសាច់រឿងមកបង្ហោះឡើយ។

### 9. 🚫 លុបចោលសាររំញ័រតម្លៃមាស (Disable Volatility Spike Alerts Permanently)
- មិនត្រូវផ្ញើសារប្រភេទ `🚨 XAUUSD VOLATILITY ALERT — បម្រែបម្រួលតម្លៃមាសខុសប្រក្រតី` (Bullish Spike / Flash Dump) ចូល Channel/Group ឡើយ។
- មុខងារ `check_price_volatility_spike` ត្រូវបានបិទទាំងស្រុងជាអចិន្ត្រៃយ៍ មិនឱ្យដំណើរការទៀតជាដាច់ខាត។

### 10. 🚫 លុបចោលសេចក្តីសង្ខេបទីផ្សារពេលយប់ (Disable Daily Market Wrap-Up Permanently)
- មិនត្រូវផ្ញើសារប្រភេទ `🌙 DAILY MARKET WRAP-UP — សេចក្តីសង្ខេបទីផ្សារពេលយប់` ចូល Channel/Group ឡើយ។
- មុខងារ `check_night_wrap_up` ត្រូវបានបិទទាំងស្រុងជាអចិន្ត្រៃយ៍ មិនឱ្យដំណើរការទៀតជាដាច់ខាត។

### 11. 🔔 ស្តង់ដារផ្សាយដំណឹងបើកទីផ្សារ London & New York (Session Open Alert Standard)
- **រូបភាព Heatmap Ultra-HD (Zero Broken Glyphs)**:
  - ត្រូវប្រើប្រាស់ Vector Shapes (Circles/Pills) សម្រាប់ Indicator Dots ជៀសវាង Emoji ក្នុង Pillow Canvas ដើម្បីកុំឱ្យធ្លាក់ Font ឬចេញប្រអប់បាក់ `[]`។
  - Label `BSL`, `SSL`, `SPOT` ត្រូវមាន Dark Background Pill ការពារកុំឱ្យចាំងបាំងជាមួយ Bar ពណ៌ទឹកក្រូច/ក្រហម។
- **ខ្លឹមសារពន្យល់ស៊ីជម្រៅ (Institutional SMC Storytelling)**:
  - ត្រូវពន្យល់ពីចលនា **Judas Swing / Fakeout** របស់ធនាគារធំៗក្នុងការ Hunt Stop Loss នៅ Asian High/Low មុនបង្ហាញទិសដៅពិត។
  - ផ្អែកលើ ៣ ដំណាក់កាល៖ រចនាសម្ព័ន្ធ Asian Range ➡️ ចលនាបញ្ឆោត Judas Swing Trap ➡️ ផែនការអនុវត្ត។
- **ទម្រង់អក្សរស្អាត សាមញ្ញ ឥតស្ទួន (Clean & Concise Caption Layout)**:
  - គ្មាន Emoji កណ្តឹង `🔔` នៅខាងមុខ Title។
  - មិនដាក់ជួរ `🕐 ពេលវេលា:` ឡើយ។
  - លុបចោលទាំងស្រុងនូវផ្នែក `តំបន់គន្លឹះយុទ្ធសាស្ត្រ (SMC Key Levels)` និង `ការគ្រប់គ្រងហានិភ័យ` ក្នុង Caption ព្រោះមានបង្ហាញច្បាស់នៅលើផ្ទាំងរូបភាព Heatmap រួចហើយ ដើម្បីរក្សាភាពសាមញ្ញ ស្រួលមើល និងមានសោភ័ណភាពខ្ពស់។
- **ស្តង់ដារពុម្ពអក្សររៀបរាប់រលូន (Smooth Regular Narrative Typography)**:
  - ត្រូវប្រើប្រាស់ទម្រង់ដូចគ្នាបេះបិទនឹងសារ Breaking Event ដោយដាក់តែចំណងជើង `🔹 ការវិភាគទីផ្សារ & យុទ្ធសាស្ត្រស្ថាប័ន (SMC):` រួចសរសេរសាច់រឿងរៀបរាប់ជាអក្សរធម្មតា (Regular Text) ជាប់គ្នា ដោយមិនប្រើចំណុចផ្កាយ `•` ឬដាក់ `<b>` ដិតកំប៉ិកកំប៉ុកនាំឱ្យធ្លាក់រាងពុម្ពអក្សរឡើយ។

### 12. 🚫 លុបចោលសារ Whale Order Book / Iceberg Alerts (Disable Whale Alerts Permanently)
- មិនត្រូវផ្ញើសារប្រភេទ `🛰️ WHALE ORDER BOOK ALERT — រកឃើញ Order ស្ថាប័នលាក់មុខ!` (Whale Iceberg Buy/Sell Wall) ចូល Channel/Group ឡើយ។
- មុខងារ `check_iceberg_orders` ត្រូវបានបិទទាំងស្រុងជាអចិន្ត្រៃយ៍ មិនឱ្យដំណើរការទៀតជាដាច់ខាត។

### 13. 🏛️ ស្តង់ដារផ្សាយ Fed AI Interpreter (Live Speech Interpretation Standard)
- **លុបចោល Emojis រញ៉េរញ៉ៃ (Clean Minimalist Emojis)**:
  - គ្មាន Emoji ផ្លេកបន្ទោរ `⚡` នៅខាងមុខ Header Title (ដាក់ត្រឹម `{icon} <b>LIVE FED AI INTERPRETER...</b>`)។
  - គ្មាន Emoji `🎙️` នៅខាងមុខ `ព្រឹត្តិការណ៍:` (ដាក់ `<b>ព្រឹត្តិការណ៍:</b> {event_title}`)។
  - គ្មាន Emoji `🎭` នៅខាងមុខ `សម្លេង និងអារម្មណ៍ Fed (Tone):` (ដាក់ `<b>សម្លេង និងអារម្មណ៍ Fed (Tone):</b> {tone_clean}`)។
  - លុបចេញនូវ Emojis មុខ Tone ដូចជា `🌓`, `🟢`, `🔴`, `🟡` ដោយទុកតែអក្សរបកស្រាយស្អាត (Regular Text) ដូចជា `Neutral (ប្រុងប្រយ័ត្ន និងរង់ចាំមើលទិន្នន័យ)`។
- **លុបចោលផ្នែកកំប៉ិកកំប៉ុក និងការព្រមានដដែលៗ (Remove Clutter & Repetitive Warnings)**:
  - លុបចោលទាំងស្រុងនូវជួរ `• ទស្សនវិស័យមាស: 🟡 Mixed`។
  - លុបចោលទាំងស្រុងនូវជួរ `🛡️ ការគ្រប់គ្រងហានិភ័យ:...`។
  - លុបចោលទាំងស្រុងនូវជួរ `📊 ពិនិត្យ Chart ផ្ទាល់:...`។
- **សាច់រឿងរៀបរាប់រលូន (Smooth Regular Narrative Typography)**:
  - ផ្នែក `🥇 ផលប៉ះពាល់លើតម្លៃមាស (XAUUSD Impact):` ត្រូវសរសេរជាអក្សរធម្មតា (Regular Text) ជាប់គ្នា ដោយមិនប្រើចំណុចផ្កាយ `•` ឡើយ។
  - ផ្នែក Key Quotes បង្ហាញឈ្មោះ Speaker ជាក់ស្តែង (ឧ. `Kevin Warsh`, `Jerome Powell`, ឬ `Fed`) តាមរយៈ `💬 <b>ចំណុចគន្លឹះសំខាន់ៗដែល {speaker} ថ្លែង (Key Quotes):</b>`។
- **ល្បឿនបន្ទាន់ និងអាទិភាពកំពូលភ្លាមៗ (Zero-Delay & Instant VIP Priority for Kevin Warsh / Fed Chair)**:
  - រាល់ពេលដែលលោក **Kevin Warsh**, Jerome Powell ឬថ្នាក់ដឹកនាំ Fed ថ្លែងសុន្ទរកថា ឬចេញសេចក្តីថ្លែងការណ៍ FOMC ត្រូវតែដំណើរការ និងផ្សាយចេញជាបន្ទាន់ភ្លាមៗ (Instant Zero-Delay) ដោយមិនឱ្យរង់ចាំ ឬច្រានចោលដោយសារ Filter ព័ត៌មានទូទៅឡើយ។
- **ភ្ជាប់សំឡេងបកប្រែជាភាសាខ្មែរជានិច្ច (Mandatory Khmer Voice Note Brief)**:
  - ត្រូវតែបង្កើត និងផ្សាយសំឡេងបកប្រែសង្ខេបជាភាសាខ្មែរ (Natural Khmer Voice Note `.mp3`) អំពីប្រសាសន៍របស់ **Kevin Warsh** ឬ Fed Speaker ភ្លាមៗបន្ទាប់ពីសារ Text ដោយប្រើ Caption: `🎙️ <b>សំឡេងបកប្រែសង្ខេប Fed / {speaker} Speech (Live Voice Brief)</b>`។
- **សម្លេងប្រុសធម្មជាតិដូចមនុស្សពិត ១០០% (100% Natural Human Prosody — Zero Robotic Artifacts)**:
  - ហាមប្រើសំឡេងស្រីជាដាច់ខាតសម្រាប់សុន្ទរកថារបស់លោក **Kevin Warsh** ឬថ្នាក់ដឹកនាំ Fed។
  - ត្រូវប្រើប្រាស់បច្ចេកវិទ្យា Neural Male Voice (`km-KH-PisethNeural`) កម្រិតសូរសព្ទធម្មជាតិរបស់មនុស្សពិត (`pitch='+0Hz'`, `rate='+0%'`, `volume='+30%'`) ដោយគ្មានការបង្ខូចសម្លេងដែលនាំឱ្យចេញសម្លេងម៉ាស៊ីន (Zero metallic synthesizer distortion)។
  - ត្រូវបំប្លែងពាក្យបច្ចេកទេស និងឈ្មោះបរទេសជាសូរសព្ទខ្មែរស្វ័យប្រវត្តិតាមរយៈ `humanize_khmer_text` (ដូចជា `Kevin Warsh` ទៅ `ខេវិន វ៉ាស`, `Fed` ទៅ `ហ្វេត`, `Bullish` ទៅ `ប៊ូលីស`, `Buy` ទៅ `ទិញ បាយ`) ដើម្បីឱ្យការបញ្ចេញសំឡេងមានដង្ហើម និងចង្វាក់រលូនឥតទាក់ ដូចជាពិធីករអានព័ត៌មានទូរទស្សន៍អាជីពផ្ទាល់។
- **ប្រាប់ទិសដៅទីផ្សារមាសនៅចុងបញ្ចប់ជានិច្ច (Mandatory Gold Market Direction Conclusion)**:
  - នៅចុងបញ្ចប់នៃសំឡេងនិយាយ Voice Note ត្រូវតែមានការសន្និដ្ឋាន និងបញ្ជាក់ពីទិសដៅទីផ្សារមាស (Bullish / Bearish / Sideway) និងយុទ្ធសាស្ត្រជួញដូរ (Buy / Sell Priority) ឱ្យបានច្បាស់លាស់ជានិច្ច ដើម្បីឱ្យ Trader ងាយស្រួលសម្រេចចិត្តភ្លាមៗ។

### 14. ✍️ ស្តង់ដារភាសាខ្មែរ-អង់គ្លេសចម្រុះ និងការពារកំហុសអក្ខរាវិរុទ្ធ (Khmer-English Hybrid & Zero-Typo Orthography Standard)
- **លាយភាសាអង់គ្លេសសម្រាប់ឈ្មោះពិបាក (Mandatory English for Foreign Leaders & Places)**:
  - ឈ្មោះមេដឹកនាំពិភពលោក និងបុគ្គលសំខាន់ៗ ត្រូវសរសេរជាអក្សរអង់គ្លេសស្អាត មិនកាឡៃ ឬបំប្លែងសូរសព្ទជាខ្មែរដែលនាំឱ្យបាក់ជើង/បែក Font ឡើយ៖ `លោក Donald Trump`, `លោក Vladimir Putin`, `លោក Volodymyr Zelenskyy`, `លោក Jerome Powell`, `លោក Kevin Warsh`, `លោក Joe Biden`។
  - ទីតាំង និងស្ថាប័នសំខាន់ៗ៖ `ច្រកសមុទ្រ Strait of Hormuz`, `សមុទ្រ Red Sea`, `Yemen`, `Ukraine (អ៊ុយក្រែន)`, `Iran (អ៊ីរ៉ង់)`, `Israel (អ៊ីស្រាអែល)`, `ធនាគារកណ្តាល Fed`, `អង្គការ OPEC`។
  - បច្ចេកទេសទីផ្សារ៖ `Bullish`, `Bearish`, `Sideway`, `Safe-Haven`, `DXY`, `Bond Yields`។
- **ទប់ស្កាត់ការជ្រៀតចូលនៃអក្សរបរទេសចម្លែកជាដាច់ខាត (Zero Foreign Script Contamination)**:
  - ហាមដាច់ខាតកុំឱ្យមានតួអក្សរចម្លែក (អារ៉ាប់ Arabic, Cyrillic, ថៃ Thai, Hebrew, Persian) ជ្រៀតចូលក្នុងអត្ថបទខ្មែរ។
  - ពាក្យរូបិយប័ណ្ណត្រូវសរសេរស្ដង់ដារស្អាត៖ **«ប្រាក់ដុល្លារ (USD)»** ជានិច្ច គ្មានការកាត់តួ ឬខូចទម្រង់។
- **ក្បួនអក្ខរាវិរុទ្ធត្រឹមត្រូវ ១០០% (100% Correct Khmer Orthography)**:
  - សរសេរត្រូវតាមក្បួនវចនានុក្រមផ្លូវការ (ដូចជា `សេដ្ឋកិច្ច` មិនមែន `សេដ្ធកិច្ច`, `អាមេរិក` មិនមែន `អាមេរិច`, `រុស្ស៊ី` មិនមែន `រុស្សី`)។
  - ប្រយោគត្រូវរៀបចំឱ្យរលូន ពិរោះ ស្តាប់បានច្បាស់ គ្មានពាក្យកាត់ខ្វះន័យ។

### 15. 🦆 ស្តង់ដារតុក្កតាកូនទា Mascot (Mascot Duck Interaction & Animation Standard)
- **ចលនាដោះវែនតាប្រព្រិចភ្នែក (Wink & Lowering Sunglasses Animation)**:
  - តុក្កតាកូនទានៅជ្រុងខាងក្រោមស្តាំ ត្រូវតែជាចលនា WebP Animated Sticker ដែលកូនទាលើកដៃដោះវែនតាខ្មៅចុះក្រោមបន្តិច រួចប្រព្រិចភ្នែកម្ខាង (Wink) ព្រមទាំងមានពន្លឺផ្កាយផ្លេកៗ (Sparkle Glint)។
  - រូបភាពត្រូវ Encode ជា Base64 Data URI ក្នុង `index.html` ដើម្បីកុំឱ្យមាន Latency ឬបញ្ហា Cache លើ Telegram Webview។
- **មុខងារ Interactive ពេលចុច (Haptic, Sound & Blessing Toast)**:
  - ពេលអ្នកប្រើប្រាស់ចុច/Tap លើតុក្កតា ត្រូវមាន Bounce Effect, បន្លឺសំឡេង Cyber Sound, រំញ័រ Haptic Feedback (`tg.HapticFeedback`), និងបង្ហាញសារជូនពរលើកទឹកចិត្តជួញដូរ។

### 16. 🌟 ស្តង់ដាររបាររត់ជូនពរខាងក្រោម (Cyber Gold Blessing Marquee Bar Standard)
- **លុបចោលចំណុចអុចទាំងស្រុង (Strict No Dots / No Bullets Rule)**:
  - ហាមមិនឱ្យមានចំណុចអុចមូលខ្មៅនៅខាងឆ្វេង (`cyber-badge-dot`) ឬសញ្ញាអុច `•` នៅចន្លោះអក្សរឡើយ។ ត្រូវប្រើប្រាស់គម្លាត Space ធម្មតា ដើម្បីកុំឱ្យទើសភ្នែក និងរក្សាភាពទាក់ទាញស្អាត។
- **ទំហំអក្សរធំច្បាស់ & កម្ពស់របារសមរម្យ (Large Typography & Safe Height)**:
  - ទំហំ Font ត្រូវរក្សាត្រឹមកម្រិតធំច្បាស់ (អប្បបរមា `16px - 16.5px`, Bold 800+), កម្ពស់របារយ៉ាងតិច `54px` ដើម្បីធានាថាមិនដាច់ ឬទើសជើងអក្សរខ្មែរ (ដូចជាពាក្យ `ជួញដូរ`) នៅលើគ្រប់ទូរស័ព្ទដៃ។
- **រចនាបថទំនើបបែប Cyber Gold Glassmorphism**:
  - ត្រូវមានរាងកោងទន់ភ្លន់ (`16px border-radius`), ពន្លឺភ្លើងឡាស៊ែររត់កាត់រលោង (`cyberSheen`), និង 3D glass highlight។

### 17. 📈 ស្តង់ដារផ្ទៃខាងក្រោយដើរទៀន (Sequential Candlestick Motion Background Standard)
- **រក្សាទម្រង់ដើរទៀនម្ដងមួយៗដូចចាស់ (Strict Sequential Walking Motion)**:
  - ចលនាទៀនផ្ទៃខាងក្រោយ (`#candlestickBgCanvas`) ត្រូវតែជាទម្រង់ **ដើរទៀនម្ដងមួយៗ (Sequential Candle Walking / Growth)** ដោយទៀននីមួយៗដុះកម្ពស់ពី Open ទៅកាន់ Close/High/Low ម្ដងមួយដើមៗតាមលំដាប់លំដោយ មិនមែនជាបន្ទះរត់ផ្ដេកស្មើគ្នា (Ticker stream) ឡើយ។
- **គាំទ្រអេក្រង់កុំព្យូទ័រគ្រប់ទំហំ (Full Screen 100% Width on Large Monitors)**:
  - ត្រូវគណនាចំនួនទៀនស្វ័យប្រវត្តិតាមទទឹងជាក់ស្តែងនៃអេក្រង់ (`Math.ceil(width / candleSpacing) + 4`) ដើម្បីឱ្យទៀនដើរលាតសន្ធឹងពេញផ្ទៃពីឆ្វេងរហូតដល់ផុតគែមស្តាំ មិនថានៅលើទូរស័ព្ទដៃ ឬអេក្រង់កុំព្យូទ័រធំៗ (1080p, 2K, 4K Ultrawide) ឡើយ។
- **ដំណើរការវិលជុំមិនចេះចប់ (Infinite Full-Width Loop)**:
  - ពេលទៀនដើរពេញអេក្រង់ដល់គែមស្តាំ ត្រូវផ្អាក ២ វិនាទី រួចកំណត់ឡើងវិញ (`activeIndex = 0`) ដើម្បីចាប់ផ្តើមដើររៀបក្បួនជាថ្មីជានិច្ច ឥតចេះចប់ឡើយ។










