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
- **កាលវិភាគបញ្ចេញ Signal និងកម្រិតកំណត់ (Signal Operating Hours & Daily Limit):**
  - ម៉ោងដំណើរការ Signal: **ចាប់ពីម៉ោង ៧:០០ ព្រឹក ដល់ម៉ោង ១១:០០ យប់** (Strict 07:00 AM – 11:00 PM Cambodia Time / UTC+7)។ ក្រៅពីម៉ោងនេះ (១១:០០ យប់ ដល់ ៧:០០ ព្រឹក) ហាមបញ្ចេញ Signal ថ្មីជាដាច់ខាត ដើម្បីការពារពី Spread រីកធំ និងទីផ្សារគ្មាន Volume។
  - កម្រិត Signal ប្រចាំថ្ងៃ: **មិនឱ្យលើសពី ៥ Signal ក្នុងមួយថ្ងៃជាដាច់ខាត (Strictly Maximum 5 Signals Per Day, NEVER exceed 5)** ដើម្បីការពារទុន និងទប់ស្កាត់ Overtrading។
- Action button waiting text must strictly remain concise: `រង់ចាំ Signal ថ្មី` (no verbose calculations or cluttered descriptions).
- Channel broadcast: Only dispatch the unified single-bubble package (Interactive Poll + Mini App CTA Button) into the Telegram channel. Raw signal levels are never exposed in plain text on the channel, ensuring users engage via the Mini App.

### 5. ♾️ ប្រើប្រាស់បានយូរ មិនរាំងស្ទះ (Long-Term Stability & Zero Bottlenecks)
- Self-healing multi-stream architecture (Binance WebSocket, Gold-API, Swissquote, CoinGecko).
- Automatic reconnects, memory safety, isolated error handlers.
- Built for 24/7 uninterrupted high-reliability operation.

### 6. 📌 អាទិភាពការងារបច្ចុប្បន្ន (Current Development Priority Directive)
- **Mini App Update Concluded & Stable (បញ្ចប់ការ Update ផ្ទាំង Mini App ជាស្ថាពរ)**: ផ្ទាំង Telegram Mini App (`index.html`) ត្រូវបានចាក់សោរ និងដំណើរការយ៉ាងរលូន ១០០% លើ GitHub Pages (ប៊ូតុង `🔒 CLOSED`, ក្រឡា ២x២, ឈ្មោះពេញ Full Names, និង TP3 គណនាត្រឹមត្រូវ)។ ផ្អាកការកែសម្រួល Mini App ជាបណ្តោះអាសន្ន។
- **Bot & Channel Development Active (អាទិភាពចម្បងផ្តោតលើ Bot Channel ទាំងស្រុង)**: បង្វែរការយកចិត្តទុកដាក់ និងការងារទាំងអស់មកផ្តោតលើ Bot Engine (`main.py`) សម្រាប់ការផ្សាយព័ត៌មានទាន់ហេតុការណ៍ (៧ វិស័យស្នូល), ហាងឆេងមាស ៧ ព្រឹក, ការបញ្ជូន Poll និងសារចូល Channel ឱ្យដើរស្វ័យប្រវត្តិកម្រិតកំពូល ២៤/៧។


### 7. 🥇 ស្តង់ដារផ្សាយហាងឆេងមាសប្រចាំថ្ងៃ (Daily Gold Price Broadcast Standard)
- **កាលវិភាគម៉ោង ៧:០០ ព្រឹក (Strict 07:00 AM, Once Per Day)**:
  - ត្រូវផ្សាយចូល Telegram Group/Channel ត្រឹមតែ **១ ដងគត់ក្នុងមួយថ្ងៃនៅវេលាម៉ោង ៧:០០ ព្រឹក** (ម៉ោងនៅកម្ពុជា UTC+7)។ មិនត្រូវផ្សាយខុសម៉ោង ឬច្រឡំផ្សាយពេលរសៀលនៅពេល Bot restart ឡើយ។
- **ទម្រង់ផ្ទាំងរូបភាពកាតមាស Ultra-HD (Graphic Card Standard — បញ្ជាផ្ទាល់)**:
  - ផ្សាយជាផ្ទាំងរូបភាព Graphic Card កម្រិតច្បាស់ Ultra-HD (1080x1080) មាន background ដុំមាសប្រណីត (គ្មានគំនូរទៀន Candlestick កំប៉ិកកំប៉ុកតាមគែមឡើយ)។
  - ចំណងជើងលើ៖ អក្សរ 3D មាសចែងចាំង `ហាងឆេងមាស` (គ្មានពាក្យលើ តម្លៃមាសថ្ងៃនេះ និងគ្មាន Watermark jmsela.com ឡើយ)។
  - ជួរកាលបរិច្ឆេទ និងម៉ោងស្ថិតនៅ **ក្រោមចំណងជើង ហាងឆេងមាស ផ្ទាល់**៖ `ថ្ងៃ {DD/MM/YYYY}   ម៉ោង 07:00 ព្រឹក`។
  - ប្រអប់កាតពណ៌សចំនួន ៣ (White Rounded Pill Cards) នៅចំកណ្តាល បង្ហាញតម្លៃច្បាស់ៗ (គ្មានសញ្ញាចុចពីរ `:` និងមានលេខ `1` នៅខាងមុខ)៖
    1. `1 តម្លឹង`    `$X,XXX`
    2. `1 ជី`        `$XXX`
    3. `1 អោន`      `$X,XXX`
  - គ្មានប៊ូតុង Inline Buttons រញ៉េរញ៉ៃឡើយ។

### 8. 🚫 បិទការផ្សាយព័ត៌មានទាន់ហេតុការណ៍ RSS Breaking News ជាអចិន្ត្រៃយ៍ (Breaking News RSS Alerts Permanently Disabled)
- **បញ្ជាផ្ទាល់ដាច់ខាតពីអ្នកប្រើប្រាស់ (Direct Absolute User Directive — Zero Channel Spam)**:
  - មុខងារ `check_breaking_news` និងការទាញយក RSS Breaking News ទាំងអស់ត្រូវ **បិទចោលទាំងស្រុងជាអចិន្ត្រៃយ៍ (Permanently Disabled)**។
  - ហាមដាច់ខាតមិនឱ្យប្រព័ន្ធស្កេន RSS ឬផ្សាយព័ត៌មានទាន់ហេតុការណ៍ចូលទៅកាន់ Telegram Channel ទៀតជាដាច់ខាត ដើម្បីការពារកុំឱ្យមានការផ្ញើសារជាន់គ្នាក្នុង Channel។
  - Channel ត្រូវរក្សាទុកសម្រាប់តែ៖ ហាងឆេងមាស ៧ ព្រឹក (`check_daily_gold_price`), ដំណឹងបើកផ្សារ London/NY (`check_session_open_alerts`), សេចក្តីថ្លែងការណ៍សំខាន់របស់ Fed/Powell/Warsh (`fomc_interpreter`), និងការវិភាគម៉ាក្រូផ្លូវការប៉ុណ្ណោះ។

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

### 18. 🔒 ស្តង់ដារការពារសុវត្ថិភាពទប់ស្កាត់ការលួចចម្លង Signal (Channel Membership Gate & Anti-Theft Security Standard)
- **ការពារមិនឱ្យអ្នកក្រៅលួចយក Signal ទៅធ្វើអាជីវកម្ម ឬទីផ្សារ (Anti-Theft Protection)**:
  - អ្នកប្រើប្រាស់ដែលមិនទាន់បាន Join Channel ផ្លូវការ (`@GoldMarketKH8888`) មិនអាចមើល Signal ឬប្រើប្រាស់ Telegram Mini App (SMC AI Terminal) បានឡើយ។
  - នៅពេលមានអ្នកចុច Mini App, ប៊ូតុង SMC ឬផ្ញើសារមកកាន់ Bot ដោយមិនទាន់បានចូលរួម Channel ប្រព័ន្ធត្រូវ **Alert និងចាក់សោរបង្ហាញផ្ទាំង Gate Lock ភ្លាមៗ (Instant Gatekeeper)** ព្រមទាំងបង្ហាញប៊ូតុងឱ្យ Join Telegram Channel ជាមុនសិន។
- **ការផ្ទៀងផ្ទាត់ស្វ័យប្រវត្តិតាម Telegram Bot API (`getChatMember`)**:
  - Bot ត្រួតពិនិត្យឋានៈអ្នកប្រើប្រាស់ក្នុង Channel (`is_user_member_of_channel`)៖ ប្រសិនបើឋានៈជា `member`, `administrator`, ឬ `creator` ទើបដោះសោរបើកដំណើរការ Signal Live ជូន។

### 19. ⌨️ ស្តង់ដារ Keyboard ខាងក្រោម Bot (Strict 2-Button Persistent Reply Keyboard Standard)
- **រក្សាត្រឹមតែ ២ ប៊ូតុងគត់ (Strict 2 Buttons Only: `[ Price ]` និង `[ SMC ]`)**:
  - ក្ដារចុចខាងក្រោម (`ReplyKeyboardMarkup`) ត្រូវកំណត់ត្រឹមតែ ២ ប៊ូតុងគត់គឺ `[ Price ]` និង `[ SMC ]` (ភ្ជាប់ WebApp Link ទៅកាន់ Mini App)។
  - **ហាមដាច់ខាតមិនឱ្យមានប៊ូតុង `[ 🧮 គិត Lot ]` លើ Reply Keyboard ឡើយ** (មុខងារគិត Lot ត្រូវស្ថិតក្នុង Mini App ឬតាម Command `/lot` វិញ)។
- **ការកំណត់ប៉ារ៉ាម៉ែត្រ Telegram API ត្រឹមត្រូវ**:
  - ត្រូវប្រើ `"is_persistent": True` (មិនមែន `"persistent": True`) និង `"resize_keyboard": True` ជានិច្ច ដើម្បីឱ្យ Telegram រក្សារូបរាងប៊ូតុងសមមាត្រ និងជាប់រហូត។
- **ការដោះស្រាយ Client-Side Cache របស់ Telegram**:
  - កម្មវិធី Telegram លើទូរស័ព្ទដៃចងចាំ Reply Keyboard តាម Local Cache។ នៅពេលមានការផ្លាស់ប្តូររូបរាង Keyboard ត្រូវផ្ញើសារថ្មីមួយដែលមាន Markup ថ្មីទៅកាន់ Chat (ឬឱ្យអ្នកប្រើប្រាស់វាយ `/start` ឬ `Price`) ដើម្បីឱ្យ Telegram Client ជម្រះប៊ូតុងចាស់ចេញភ្លាមៗ។

### 20. 🎯 ស្តង់ដារប៊ូតុង Signal Action Button, ក្រឡា ២x២ និង TAKE PROFIT 3 (Mini App Signal Card & Action Button Standards)
- **ប៊ូតុង Action Button ក្នុងស្ថានភាព Waiting / Closed (Strict Prominent `🔒 CLOSED` Button)**:
  - ក្នុងអំឡុងពេលរង់ចាំ Signal ថ្មី ពេលហួសម៉ោង (ក្រៅពី 7:00 ព្រឹក - 11:00 យប់) ឬនៅពេល Safety Index មិនទាន់គ្រប់ ៧០% ប៊ូតុងត្រូវបង្ហាញត្រឹមតែ **`🔒 CLOSED`** តែមួយគត់ យ៉ាងសាមញ្ញ ស្រស់ស្អាត ចំកណ្តាលប៊ូតុង ជាមួយពុម្ពអក្សរ Orbitron Bold ពណ៌មាស Gold (letter-spacing: 2px)។
  - **ហាមដាច់ខាតកុំប្រើអក្សរវែងអន្លាយ** ដូចជា `មិនអាចប្រើប្រាស់ SIGNAL នេះបានទេ (រង់ចាំ SIGNAL ថ្មី)` ដែលនាំឱ្យធ្លាក់ជា ២ ជួរ ឬមាន Icon សោរជាន់គ្នាពីរ `🔒 🔒` ឬមាន tag តូចៗនៅកៀនប៊ូតុងនាំឱ្យចង្អៀត។
  - នៅពេល AI ផ្ទៀងផ្ទាត់គ្រប់លក្ខខណ្ឌត្រឹមត្រូវ (Safety Index >= 70% ដល់តំបន់ OTE) ទើបប៊ូតុងប្រែជាពណ៌បៃតង **`🟢 អាចប្រើប្រាស់ SIGNAL នេះបាន`** (Ready/Active)។
- **ការរៀបចំក្រឡាប្រអប់ការពារ និងប្រាក់ចំណេញ ២x២ (2x2 Balanced Grid Layout & Full Names)**:
  - ប្រអប់ទាំង ៤ ត្រូវរៀបជាក្រឡា ២x២ ស្មើគ្នាឥតខ្ចោះ:
    - ជួរលើ: `STOP LOSS` ជាប់គ្នាជាមួយ `TAKE PROFIT 1`
    - ជួរក្រោម: `TAKE PROFIT 2` ជាប់គ្នាជាមួយ `TAKE PROFIT 3`
  - ត្រូវប្រើឈ្មោះពេញលេញ (Full Names) ទាំងអស់: `STOP LOSS`, `TAKE PROFIT 1`, `TAKE PROFIT 2`, `TAKE PROFIT 3` (ហាមប្រើពាក្យកាត់ដូចជា SL ឬ TP1 ឡើយ)។
- **ភាពត្រឹមត្រូវដាច់ខាតនៃតម្លៃ TAKE PROFIT 3 និង STOP LOSS (Strict Directional Sanitization)**:
  - សម្រាប់ **SELL**:
    - `SL` ត្រូវតែនៅ **លើ Entry ($8 - $10, max $12)** ជានិច្ច (`SL = EntryHigh + 8~10 pts`, max 12 pts)។
    - `TP1 < EntryLow`, `TP2 < TP1`, `TP3 < TP2` ជានិច្ច (`TP3 = EntryLow - 37.0` ឬ 1:3.8R)។ ហាមដាច់ខាតមិនឱ្យ TP3 ធំជាង Entry ឬធំជាង TP2 ឡើយ។
  - សម្រាប់ **BUY**:
    - `SL` ត្រូវតែនៅ **ក្រោម Entry ($8 - $10, max $12)** ជានិច្ច (`SL = EntryLow - 8~10 pts`, max 12 pts)។
    - `TP1 > EntryHigh`, `TP2 > TP1`, `TP3 > TP2` ជានិច្ច (`TP3 = EntryHigh + 37.0` ឬ 1:3.8R)។ ហាមដាច់ខាតមិនឱ្យ TP3 តូចជាង Entry ឬតូចជាង TP2 ឡើយ។
- **ការកែប្រែកូដដោយសុវត្ថិភាពខ្ពស់ ជៀសវាង Blank Screen (Zero Corrupted Script Replacement Policy)**:
  - នៅពេលធ្វើការកែសម្រួល `index.html` ត្រូវប្រើប្រាស់ Exact String Replacement ដោយប្រុងប្រយ័ត្នបំផុត ហាមប្រើ Regex ធំៗ `[\s\S]*?` ដែលអាចស៊ីរំលោភកាត់បាត់ JavaScript នាំឱ្យ Mini App គាំងចេញផ្ទាំងខ្មៅ (Blank Grid Screen) ជាដាច់ខាត។
  - ត្រូវផ្ទៀងផ្ទាត់ និង Compile មុនពេល Push ទៅ GitHub ជានិច្ច។











### 21. 🧹 ស្តង់ដារសម្អាត Database & ឯកសារបណ្តោះអាសន្ន (Strict 1–2 Days Auto-Purge Policy)
- **រយៈពេលរក្សាទុកទិន្នន័យចាស់ៗ (Database Retention: Strict 1–2 Days / 48 Hours)**:
  - កំណត់ត្រាប្រវត្តិព័ត៌មាន (Sent News), ព្រឹត្តិការណ៍សេដ្ឋកិច្ច (Sent Events) និងប្រវត្តិហាងឆេងមាសក្នុង `data.db` ត្រូវកំណត់ឱ្យសម្អាតចោល (Purge) រៀងរាល់ **១ ទៅ ២ ថ្ងៃម្តង (Strict 2-Day Retention / 48 Hours)** រួមជាមួយប្រតិបត្តិការ `VACUUM` ដើម្បីធានាថា Database ស្រាល និងដំណើរការលឿនដូចផ្លេកបន្ទោរ (ក្រោម 100 KB) ជានិច្ច។
- **ការសម្អាតឯកសារបណ្តោះអាសន្ន (Automatic Scratch Files Purge)**:
  - ឯកសារតេស្ត ឬឯកសារ scratch បណ្តោះអាសន្នទាំងអស់ក្នុងថត `scratch/` ត្រូវតែសម្អាត និងលុបចោលស្វ័យប្រវត្តិឱ្យតែហួសរយៈពេល **១ ទៅ ២ ថ្ងៃ** ដោយមិនឱ្យរក្សាទុកកាកសំណល់ចាស់ៗ ឬធ្ងន់ម៉ាស៊ីនឡើយ។