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
- **🚫 លុបចោល Signal ជួញដូរមាស SMC ក្នុង Channel ជារៀងរហូត (Permanently Disable Trade Signals — បញ្ជាផ្ទាល់)**:
  - ហាមដាច់ខាតមិនឱ្យផ្ញើ ឬបញ្ចេញ Trade Signals (Buy/Sell, Entry, SL, TP, Trailing) ចូល Telegram Channel ទៀតឡើយ។ មុខងារ Signal ក្នុង Bot (`check_sniper_instant_signals`, `check_candlestick_confirmation`, `check_dynamic_breakeven_trailing`) ត្រូវបានបិទទាំងស្រុងជាស្ថាពរ ១០០% តាមបញ្ជាផ្ទាល់ (ចំណុចទី ៥ ត្រូវបានលុបចេញ)។
- **🚫 លុបចោលការផ្ញើសារ Interactive Poll ជារៀងរហូត (Permanently Disable Polls — បញ្ជាផ្ទាល់)**: ហាមដាច់ខាតមិនឱ្យផ្ញើសារប្រភេទ Interactive Poll (`📊 លទ្ធផល Signal XAUUSD...`) ចូល Telegram Channel ទៀតឡើយ។
- **🚫 លុបចោលសាររំលឹកមុនម៉ោងទិន្នន័យសេដ្ឋកិច្ចចេញ (5-Min & 15-Min Countdowns) ជារៀងរហូត (Permanently Disable Upcoming News Countdowns — បញ្ជាផ្ទាល់)**: ហាមដាច់ខាតមិនឱ្យផ្ញើសារប្រភេទ «🚨 5 នាទីទៀតដល់ម៉ោងចេញទិន្នន័យសំខាន់! (5-MIN COUNTDOWN)», ការរំលឹក ១៥ នាទី ឬ Pre-News Volatility Warning ចូល Telegram Channel ទៀតឡើយ ដើម្បីការពារពីការ Spam និងរក្សាទម្រង់ស្អាតបាតបែប VIP។
- **🚫 លុបចោលសារសំឡេង Voice Note ជារៀងរហូត (Permanently Disable Voice Notes — បញ្ជាផ្ទាល់)**: ហាមដាច់ខាតមិនឱ្យបង្កើត ឬផ្ញើសារជាសំឡេង Voice Note (.mp3) ចូល Telegram Channel ទៀតឡើយ។ មុខងារ `send_voice` ត្រូវបានបិទទាំងស្រុងជាអចិន្ត្រៃយ៍ ដើម្បីឱ្យ Channel មានតែអត្ថបទ និងរូបភាព Ultra-HD ប្រណីត។

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

### 8. 🚨 ស្តង់ដារផ្សាយព័ត៌មានទាន់ហេតុការណ៍ (Breaking News Standard — វិស័យស្នូលទាំង ៧)
- **ប្រព័ន្ធការពារការផ្ញើសារជាន់គ្នា ៣ ជាន់ដាច់ខាត (Triple Anti-Duplicate Shield — Zero Spam Guarantee)**:
  1. **ត្រួតពិនិត្យ Telegram Channel Feed ជាក់ស្តែង (`_is_already_in_telegram_channel`)**: មុននឹងចេញផ្សាយ ត្រូវ Scan មើលសារក្នុង Channel `@GoldMarketKH8888` ជាមុនសិន។ ប្រសិនបើមានព័ត៌មាននេះរួចហើយ ទោះបី Server restart ឬមាន Instance ច្រើនប៉ុនណាក៏ដោយ ក៏ **ហាមដាច់ខាតមិនឱ្យផ្សាយជាន់គ្នាជាលើកទី ២ ឡើយ**។
  2. **In-Memory Process Cache & SQLite Deduplication**: កត់ត្រាចំណងជើង និង ID ក្នុង Memory និង Database SQLite ភ្លាមៗមុនពេលផ្ញើ។
  3. **ល្បឿនផ្សាយទាន់ហេតុការណ៍លឿនរហ័សបំផុត (`BREAKING_ALERT_MIN_GAP = 5s`, VIP Critical = 3s — បញ្ជាផ្ទាល់)**:
     - ផ្សាយព័ត៌មានទាន់ហេតុការណ៍ឱ្យបានលឿនបំផុតចូល Channel ភ្លាមៗនៅពេលមានព័ត៌មានចេញមក ដោយរក្សាគម្លាតសុវត្ថិភាពអប្បបរមាត្រឹមតែ ៥ វិនាទី (VIP Critical ត្រឹមតែ ៣ វិនាទី) ដើម្បីការពារ Telegram Rate Limit ដោយគ្មានការពន្យារពេល ឬកកស្ទះឡើយ។
  4. **របាំងទប់ស្កាត់ប្រធានបទដដែលៗតាមវិស័យ (Macro Cluster Deduplication & Sector Cooldown Shield)**:
     - **Jobs / NFP / ការងារ**: Cooldown ៤ ម៉ោង (បើរាយការណ៍ពី NFP ឬ Jobs Report រួចហើយ ហាមដាច់ខាតមិនឱ្យផ្សាយប្រធានបទការងារដដែលៗពី Feed ផ្សេងទៀតឡើយ)។
     - **Inflation / អតិផរណា (CPI/PPI/PCE)**: Cooldown ៤ ម៉ោង។
     - **Fed / អត្រាការប្រាក់**: Cooldown ២ ម៉ោង។
     - **ថាមពល ប្រេងកាត (Energy/Oil/LNG)**: Cooldown ១ ម៉ោង (មិនឱ្យចេញព័ត៌មានប្រេង ឬ LNG ជាន់គ្នាឡើយ)។
     - **បច្ចេកវិទ្យា & AI**: Cooldown ១ ម៉ោង (មិនឱ្យចេញព័ត៌មាន AI ជាន់គ្នា ២ សារក្នុង ១ នាទីឡើយ)។
     - **Crypto**: Cooldown ១ ម៉ោង។
  5. **ឃ្លាចេញពី Data ភ្លាមៗបន្ទាប់ពីផ្ញើសាររួច (Mandatory Post-Broadcast Data Eviction)**: ភ្លាមៗបន្ទាប់ពីសារមួយត្រូវបានផ្ញើចេញ ឬត្រូវបានច្រានចោល (Drop) ប្រព័ន្ធត្រូវតែហៅ `news_collector.clear_item(...)` ដើម្បីកម្ចាត់ និង Blacklist ចោលភ្លាមៗចេញពី Data Pool, ហៅ `database.clear_news_from_data(...)` ដើម្បីចាក់សោក្នុង SQLite និង `pending.clear()` សម្អាត Queue ចោលភ្លាម ដើម្បីកុំឱ្យមានទិន្នន័យចាស់សេសសល់ក្នុង Loop ឡើយ។
- **វិស័យស្នូលទាំង ៧ នៃព័ត៌មាន (The 7 Core News Pillars)**:
  1. 🌐 **សេដ្ឋកិច្ច (Economy)**: GDP, CPI, អតិផរណា, NFP, ការងារ, Retail Sales, PMI, កំណើនសេដ្ឋកិច្ច។
  2. ⚔️ **នយោបាយភូមិសាស្ត្រ (Geopolitics)**: សង្គ្រាម, ជម្លោះ, មជ្ឈិមបូព៌ា, អ៊ុយក្រែន, ច្រកសមុទ្រយុទ្ធសាស្ត្រ។
  3. 💻 **បច្ចេកវិទ្យា (Technology)**: AI, Semiconductor, បន្ទះឈីប Chips, Big Tech, សន្តិសុខ Cyber។
  4. 🏦 **គោលនយោបាយរូបិយវត្ថុ និងធនាគារកណ្តាល (Monetary Policy & Central Banks)**: Fed, Powell, FOMC, អត្រាការប្រាក់, ECB, BOJ, PBOC, ទុនបម្រុងមាស។
  5. 🛢️ **បរិស្ថាន និងធនធានធម្មជាតិ (Environment & Natural Resources)**: ប្រេងកាត OPEC, ថាមពល, រ៉ែមាស, ធនធានធម្មជាតិ។
  6. 👥 **កត្តាសង្គម និងប្រជាសាស្ត្រ (Social & Demographic Factors)**: កូដកម្មការងារ, ប្រាក់ឈ្នួល, ចិត្តសាស្ត្រអ្នកប្រើប្រាស់។
  7. ⚖️ **ច្បាប់ បទប្បញ្ញត្តិ និងគោលនយោបាយរដ្ឋាភិបាល (Laws, Regulations & Government Policies)**: ពន្ធគយ Tariffs, ទណ្ឌកម្ម, បំណុលរដ្ឋ, ច្បាប់ហិរញ្ញវត្ថុ។
  8. 🪙 **ប្រាក់ឌីជីថល និងទ្រព្យសកម្មគ្រីបតូ (Digital Assets & Cryptocurrency — បញ្ជាផ្ទាល់)**: Bitcoin (BTC), Ethereum (ETH), Stablecoins (USDT/USDC), CBDC, ច្បាប់ SEC, Spot Crypto ETFs, ស្ថាប័នទិញស្តុកទុក (Strategic Crypto Reserves)។ ហាមមិនឱ្យច្រឡំទម្លាក់ព័ត៌មានប្រាក់ឌីជីថលចោលឡើយ។
- **ទម្រង់ និងខ្លឹមសាររៀបរាប់ក្បោះក្បាយត្រឹមត្រូវ (Clean & Professional Standard)**:
  - **Header សាច់រឿងបែបសារព័ត៌មានអាជីព (Story Headline Header — បញ្ជាផ្ទាល់)**៖
    - លុបចោលទាំងស្រុងនូវពាក្យ `🔹 ព្រឹត្តិការណ៍សំខាន់` មិនឱ្យប្រើទៀតឡើយ។
    - ចាប់ផ្ដើមផ្ទាល់ពីទង់ជាតិ និងចំណងជើងសាច់រឿងជាភាសាខ្មែរតែម្ដង៖ `{ទង់ជាតិ} <b>ចំណងជើងសាច់រឿងខ្លីទាន់ហេតុការណ៍ជាភាសាខ្មែរ</b>` (ឧ. `🇹🇼 <b>តៃវ៉ាន់អភិវឌ្ឍបច្ចេកវិទ្យា AI ដើម្បីជួយថែទាំអ្នកជំងឺវង្វេងវង្វាន់</b>`)។
    - **ចំណងជើងពេញលេញ គ្មានសញ្ញាចុចបី (Strict Zero-Ellipsis Headline — បញ្ជាផ្ទាល់)**: ចំណងជើង Header ត្រូវតែជាប្រយោគពេញលេញ ខ្លី ខ្លឹម ហាមដាច់ខាតកុំប្រើសញ្ញាចុចៗ (...) ឬ (…), ហាមកាត់ដាច់ពាក្យពាក់កណ្តាល និងហាមបញ្ចប់ដោយសញ្ញាចុចពីរ (:) ឬ (៖) នៅខាងចុងជាដាច់ខាត។
    - រូបភាពព័ត៌មាន (News Image) ត្រូវបង្ហាញនៅខាងលើគេបង្អស់ បន្ទាប់មកទើបជា Caption អត្ថបទដែលមាន Header ទង់ជាតិ+ចំណងជើងខ្មែរនេះ។
  - សាច់រឿងព័ត៌មានក្បោះក្បាយ ត្រឹមត្រូវតាមដំណើររឿងពិតជាភាសាខ្មែរសុទ្ធសាធ (គ្មានចំណងជើងភាសាអង់គ្លេសនៅខាងមុខឡើយ)។
  - **ឈ្មោះក្រុមហ៊ុន និងឈ្មោះមនុស្ស/មេដឹកនាំ (Original English/Latin Names — បញ្ជាផ្ទាល់)**: ត្រូវរក្សាទុកជាភាសាដើមអង់គ្លេស/ឡាតាំងជានិច្ច ហាមដាច់ខាតកុំបកប្រែ ឬសរសេរកាឡៃជាភាសាខ្មែរឡើយ (ឧ. Apple, Microsoft, NVIDIA, Tesla, Google, Amazon, Tether, BlackRock, TSMC, Boeing, Intel, Elon Musk, Donald Trump, Kevin Warsh, Jerome Powell, Xi Jinping, Scott Bessent, Warren Buffett ជាដើម)។
  - **ការបញ្ជាក់ផលប៉ះពាល់ចំគោលដៅ (Targeted Asset Impact Assessment — ចំណុចគោលទី ៣ & ៦ — បញ្ជាផ្ទាល់)**៖
    - ឈប់ប្រើឃ្លា template ដដែលៗដូចជា «បង្កើនសម្ពាធលើទីផ្សារ» ឬ «ភាពមិនច្បាស់លាស់នៃសេដ្ឋកិច្ច»។ ត្រូវវិភាគផលប៉ះពាល់ឱ្យចំទ្រព្យសកម្មពិតប្រាកដ (ដូចជា លើតម្លៃមាស XAUUSD, ប្រាក់ដុល្លារ USD, អត្រាការប្រាក់/Yields, អតិផរណា, ថ្លៃប្រេងកាត, ឬវិស័យបច្ចេកវិទ្យា/បន្ទះឈីប)។
    - **ត្រូវប្រើប្រាស់ទម្រង់ស្តង់ដារ និងសញ្ញាសម្គាល់**៖
      - `🔹 ផលវិជ្ជមាន៖ {ការពន្យល់ចំទ្រព្យសកម្ម}` (ប្រើសញ្ញា 🔹 សម្រាប់វិជ្ជមាន)
      - `🔸 ផលអវិជ្ជមាន៖ {ការពន្យល់ចំទ្រព្យសកម្ម}` (ប្រើសញ្ញា 🔸 សម្រាប់អវិជ្ជមាន/ហានិភ័យ)
    - **ហាមដាច់ខាតមិនឱ្យប្រើពាក្យ «វា» នៅខាងមុខឡើយ (ហាមប្រើ «វាផលវិជ្ជមាន» ឬ «វាផលអវិជ្ជមាន» — បញ្ជាផ្ទាល់)**។
    - **ហាមដាច់ខាតមិនឱ្យប្រើវង់ក្រចក `()` ក្នុងបន្ទាត់ផលប៉ះពាល់ជាដាច់ខាត (Strict No Parentheses Rule)**។
    - ព័ត៌មានណាដែលជា `ផលអព្យាក្រឹត` ត្រូវទម្លាក់ចោលភ្លាមៗ (Drop/Skip)។
  - **កែសម្រួលការបកប្រែពាក្យបច្ចេកទេសផ្លូវការ (Professional Terminology — ចំណុចគោលទី ៤ — បញ្ជាផ្ទាល់)**:
    - កែពាក្យបកខុសន័យមកជាពាក្យបច្ចេកទេសផ្លូវការ៖
      - «ដាក់ឈ្មោះ» $\rightarrow$ «តែងតាំង» / «តែងតាំងជា» (Appoints / Names)
      - «ប៉ះនឹងប្រេង» $\rightarrow$ «សម្ពាធតម្លៃប្រេង»
      - «គម្លាតសាច់ប្រាក់» $\rightarrow$ «កង្វះខាតសាច់ប្រាក់ងាយស្រួល» (Cash crunch)
      - «ការប្រញាប់ប្រញាល់ផ្តល់មូលនិធិ» $\rightarrow$ «ការសម្រុកបញ្ចេញទុនវិនិយោគ» (Funding rush)
      - «សម្រាប់កាណាដា» $\rightarrow$ «ប្រចាំប្រទេសកាណាដា»
  - **ទប់ស្កាត់ការផ្សាយព័ត៌មានផ្ទាល់ខ្លួន ឬរឿងរ៉ាវឯកជនរបស់បុគ្គល (Strict Personal Affairs & Private Life Filter — បញ្ជាផ្ទាល់)**:
    - ហាមដាច់ខាតមិនឱ្យផ្សាយព័ត៌មានទាក់ទងនឹងរឿងរ៉ាវផ្ទាល់ខ្លួន ឬជីវិតឯកជនរបស់បុគ្គល (រឿងស្នេហា អាពាហ៍ពិពាហ៍ លែងលះ ជម្លោះគ្រួសារ សៀវភៅជីវប្រវត្តិ/អនុស្សាវរីយ៍ Memoir/Biography របៀបរស់នៅ ទ្រព្យសម្បត្តិផ្ទាល់ខ្លួន វិស្សមកាល ការដើរលេង ឬការសារភាពរឿងផ្ទាល់ខ្លួនរបស់ CEO/បុគ្គលល្បី ដែលគ្មានឥទ្ធិពលផ្ទាល់លើសេដ្ឋកិច្ច ឬទីផ្សារហិរញ្ញវត្ថុស្ថាប័នឡើយ)។ ឱ្យតែជួបព័ត៌មានប្រភេទនេះ ប្រព័ន្ធត្រូវ Drop/Skip ចោលភ្លាមៗ (`is_clear = false`) ហាមមិនឱ្យផ្សាយដាច់ខាត។
  - ជួរប្រភពព័ត៌មានខាងក្រោមស្អាត (ហាមដាច់ខាតមិនប្រើសញ្ញា 🌐 — បញ្ជាផ្ទាល់)៖ `ប្រភព | <a href="{link}">{source_name}</a>`។
  - គ្មានប៊ូតុង Inline Buttons ខាងក្រោមឡើយ (`reply_markup=None`)។
  - **ស្តង់ដាររូបភាពពិតប្រាកដ និងកែសម្រួលត្រូវតាមដំណើររឿង (Story-Accurate VIP Image Pipeline — បញ្ជាផ្ទាល់)**:
    - ប្រព័ន្ធបង្កើត និងផ្គូផ្គងរូបភាពឆ្លាតវៃតាមដំណើររឿង ៦ ជាន់ (6-Tier Story-Accurate Image Pipeline)៖
      1. **រូបភាពផ្គួបថ្នាក់ដឹកនាំសងខាង (Dual-Leader Split Image)**: ប្រសិនបើសាច់រឿងនិយាយពីទំនាក់ទំនង ជម្លោះ ឬកិច្ចព្រមព្រៀងរវាងថ្នាក់ដឹកនាំ ២ រូប (ឧ. Meloni និង Trump, Trump និង Putin, Trump និង Xi Jinping, Trump និង Musk, Putin និង Zelenskyy) ប្រព័ន្ធត្រូវកាត់តផ្គួបរូបថតច្បាស់ៗនៃថ្នាក់ដឹកនាំទាំងពីរជា Split Image 50/50 ក្នុង Canvas តែមួយភ្លាមៗ។
      2. **រូបភាពផ្គួបទង់ជាតិប្រទេសសងខាង (Dual-Country Flag Split Image)**: ប្រសិនបើសាច់រឿងជាទំនាក់ទំនង ឬបញ្ហាទ្វេភាគីរវាងប្រទេស ២ (ឧ. ឥណ្ឌា និង កាណាដា, អាមេរិក និង ចិន, អាមេរិក និង តៃវ៉ាន់, អ៊ីស្រាអែល និង អ៊ីរ៉ង់) ប្រព័ន្ធត្រូវបង្កើតផ្ទាំងរូបភាពផ្គួបទង់ជាតិប្រទេសទាំងពីរជា Split Image 50/50 ច្បាស់ត្រដែត។
      3. **រូបថតផ្លូវការមេដឹកនាំទោល (Single Leader Official Portrait)**: ព័ត៌មានដែលនិយាយចំមេដឹកនាំសំខាន់ (Trump, Powell, Warsh, Musk, Meloni, Putin, Xi Jinping, Netanyahu, Zelenskyy, Macron, Starmer, Lagarde, Ueda, Modi) ប្រើប្រាស់រូបថតពិតច្បាស់ផ្លូវការ។
      4. **រូបភាពពិតផ្ទាល់ពីអត្ថបទសារព័ត៌មាន (Direct Verified Article Photo)**: ទាញយករូបភាពពិត Ultra-HD ពីគេហទំព័រផ្ទាល់ (`og:image`, `twitter:image`, `enclosure`) ដែលផ្ទៀងផ្ទាត់មិនមែនជា Logo ឬរូបតូច។
      5. **រូបភាពប្រធានបទសេដ្ឋកិច្ចស្នូល Ultra-HD (Core Topic Photo)**: ផ្គូផ្គងរូបថតពិតតាមប្រធានបទជាក់ស្តែង (Federal Reserve, Gold Bullion ដុំមាស, Crude Oil ប្រេងកាត, Semiconductor Chips បន្ទះឈីប AI, Bitcoin Crypto, Geopolitics កងទ័ពជើងទឹក/ច្រក Hormuz, Wall Street/NYSE)។
      6. **ទង់ជាតិប្រទេសគោល (Single Country Flag Canvas)**: សម្រាប់ព័ត៌មានដែលផ្តោតលើប្រទេសជាក់លាក់មួយហើយគ្មានរូបថតផ្ទាល់ (ឧ. GDP Singapore, Yen Japan) បង្ហាញទង់ជាតិប្រទេសនោះយ៉ាងស្រស់ស្អាត។
    - **ហាមដាច់ខាតរូបភាពមិនត្រូវសាច់រឿង ឬរូបភាព Logo កំប៉ិកកំប៉ុក**: ប្រសិនបើគ្មានរូបភាពពិតដែលត្រូវនឹងសាច់រឿងទេ ត្រូវផ្សាយជា MODE B (អត្ថបទសុទ្ធ Plain Text) ហាមដាច់ខាតមិនយក Logo ស្ថាប័ន, Favicon, ឬរូបភាពផ្តេសផ្តាសមកបង្ហោះឡើយ។
  - **ចន្លោះបន្ទាត់ស្អាតបាត (Clean Blank Line Spacing — បញ្ជាផ្ទាល់)**: ត្រូវចុះបន្ទាត់ទទេ `\n\n` មួយជួរស្អាតនៅចន្លោះ Headline, Summary, Impact, និង Source។
  - **ស្តង់ដារប្រវែងអត្ថបទល្មមស្អាត មិនវែងខ្លាំងពេក ងាយយល់ពីសាច់រឿង (Concise, Clean & Balanced Narrative — ៥០ ដល់ ៨០ ពាក្យ / ២-៣ ប្រយោគច្បាស់ៗ — បញ្ជាផ្ទាល់)**:
    - ហាមដាច់ខាតមិនឱ្យសរសេរអូសបន្លាយវែងអន្លាយ ឬចេញជាជញ្ជាំងអក្សរច្រើនកថាខណ្ឌ (Wall of Text) នាំឱ្យពិបាកអានឡើយ។
    - សាច់រឿងត្រូវសរសេរ **កម្រិតល្មមស្អាត ត្រឹម ២ ទៅ ៣ ប្រយោគខ្លីខ្លឹមច្បាស់ៗ (ប្រមាណ ៥០ ដល់ ៨០ ពាក្យ / ២០០ ដល់ ៣៥០ តួអក្សរ)**៖
      * ប្រយោគទី ១៖ ព្រឹត្តិការណ៍ស្នូលដែលបានកើតឡើង (What happened clearly)
      * ប្រយោគទី ២៖ មូលហេតុ ឬបរិបទជំរុញសំខាន់ (Why it happened / Driving context)
      * ប្រយោគទី ៣ (ប្រសិនបើចាំបាច់)៖ ជំហរស្ថាប័ន ឬការវិវត្តបន្ត (Institutional response or outlook)
    - ធានាឱ្យអ្នកអានចំណាយពេលត្រឹម ១០-១៥ វិនាទីអាចយល់ដំណើររឿងបានគ្រប់ជ្រុងជ្រោយ ១០០%។
  - **MODE A (ភ្ជាប់រូបភាព) & MODE B (អត្ថបទសុទ្ធ)**:
    - `{ទង់ជាតិ} <b>{ចំណងជើងសាច់រឿងខ្លីទាន់ហេតុការណ៍}</b>`
    - `\n\n{ខ្លឹមសារសង្ខេបល្មមស្អាត ២-៣ ប្រយោគច្បាស់ៗ}`
    - `\n\n{🔹 ផលវិជ្ជមាន៖ ... ឬ 🔸 ហានិភ័យទីផ្សារ៖ ...}`
    - `\n\nប្រភព | <a href="{link}">{source_name}</a>`
  - **ស្តង់ដារផ្សាយព័ត៌មានដែលសំខាន់ខ្លាំង (Strict High-Importance / Critical News Only — បញ្ជាផ្ទាល់)**:
    - ផ្សាយតែព័ត៌មានដែលមានសារៈសំខាន់ខ្លាំងចំពោះទីផ្សារហិរញ្ញវត្ថុ សេដ្ឋកិច្ចសកល ឬភូមិសាស្ត្រនយោបាយប៉ុណ្ណោះ៖
      1. សេដ្ឋកិច្ច & ធនាគារកណ្តាលកម្រិតកំពូល៖ អត្រាការប្រាក់ Fed/FOMC, សុន្ទរកថា Jerome Powell/Kevin Warsh, ទិន្នន័យអតិផរណា CPI/PCE, របាយការណ៍ការងារ NFP, GDP។
      2. នយោបាយភូមិសាស្ត្រ & សន្តិសុខ៖ សង្គ្រាម, ការវាយប្រហារមីស៊ីល/ដ្រូន, ច្រកសមុទ្រ Strait of Hormuz, សមុទ្រក្រហម, ទណ្ឌកម្មអន្តរជាតិធំៗ។
      3. ថាមពល & ប្រេងកាត៖ ការកាត់បន្ថយទិន្នផលប្រេង OPEC, វិបត្តិថាមពល, ការទិញមាសរបស់ធនាគារកណ្តាល។
      4. បច្ចេកវិទ្យា & AI យុទ្ធសាស្ត្រ៖ របកគំហើញបន្ទះឈីប/AI ធំៗ, ការរឹតត្បិតការនាំចេញឈីបរបស់ Big Tech (NVIDIA, TSMC, OpenAI, Apple)។
      5. ទ្រព្យឌីជីថលសំខាន់ៗ៖ គោលនយោបាយបម្រុង Bitcoin រដ្ឋាភិបាល, ច្បាប់/ការអនុម័តធំៗរបស់ SEC, ចលនាសាច់ប្រាក់ស្ថាប័នធំៗ។
    - ព័ត៌មានទូទៅតូចតាច, ការព្យាករណ៍តម្លៃប្រចាំថ្ងៃរបស់ Analyst, ព័ត៌មានផ្ទាល់ខ្លួន, ឬព័ត៌មានគ្មានឥទ្ធិពលលើទីផ្សារ ត្រូវច្រានចោលភ្លាមៗ (Drop/Skip)។
### 8.1 🚨 ស្តង់ដារផ្សាយទិន្នន័យសេដ្ឋកិច្ចជាក់ស្តែង (Point 3: Flash Update | Actual Release Standard — គំរូថ្មី VIP)
- **ទម្រង់គំរូថ្មី VIP សុទ្ធសាធ (Strict VIP Actual Release Template — បញ្ជាផ្ទាល់)**:
  - ឈប់ប្រើប្រាស់គំរូចាស់ទាំងស្រុង («ចំនុចទី៣ប្រើគំរូនេះគំរូចាស់មិនយក»)។
  - ត្រូវប្រើប្រាស់ទម្រង់ថ្មីដែលមានបន្ទាត់ខណ្ឌ `━━━━━━━━━━━━━━━━━━━` និងប្លុកព័ត៌មានច្បាស់ៗ៖
```
🚨 FLASH UPDATE | ACTUAL RELEASE {ទង់ជាតិ}

📊 {ឈ្មោះព្រឹត្តិការណ៍ជាភាសាអង់គ្លេស} ({ឈ្មោះជាភាសាខ្មែរ})

⏱ {ម៉ោង} | {កាលបរិច្ឆេទ}

━━━━━━━━━━━━━━━━━━━

📈 ទិន្នន័យជាក់ស្តែង (Actual Data)
• Actual: {តម្លៃ} ⬆️/⬇️ ({ខ្ពស់ជាងរំពឹងទុក / ទាបជាងរំពឹងទុក})
• Forecast: {តម្លៃ}
• Previous: {តម្លៃ}

━━━━━━━━━━━━━━━━━━━

🧠 ការសង្ខេប & ការវិភាគ (Quick Take)
• ស្ថានភាព: {សេចក្តីសង្ខេបស្ថានភាពជាក់ស្តែង}
• ផលជះ: {ផលជះដល់គោលនយោបាយ Fed ឬសេដ្ឋកិច្ច}

━━━━━━━━━━━━━━━━━━━

⚡ ផលប៉ះពាល់ទីផ្សារ (Market Impact)
🔹 USD: {ផលប៉ះពាល់លើប្រាក់ដុល្លារ ដូចជា ឡើងថ្លៃភ្លាមៗ (Bullish)}
🔹 US10Y Yields: {ផលប៉ះពាល់លើប័ណ្ណបំណុល ដូចជា ស្ទុះងើបឡើងខ្ពស់}
🔸 XAUUSD (មាស): {ផលប៉ះពាល់លើតម្លៃមាស ដូចជា ប្រឈមសម្ពាធធ្លាក់ចុះរយៈពេលខ្លី (Bearish Pressure)}

- **លុបចោលបម្រាមហានិភ័យ និងរូបភាព Chart ជារៀងរហូត (Permanently Disable Warning & TradingView Charts — បញ្ជាផ្ទាល់)**:
  - ហាមដាច់ខាតមិនឱ្យដាក់ជួរ `⚠️ បម្រាមហានិភ័យ...` នៅខាងក្រោមឡើយ (លុបចោលជាអចិន្ត្រៃយ៍)។
  - ហាមដាច់ខាតមិនឱ្យចំណាយពេល Render ឬ Upload រូបភាព TradingView Chart ឡើយ (លុបចោលជាអចិន្ត្រៃយ៍)។
  - ត្រូវផ្សាយជា **Instant Text Message** ភ្លាមៗ ដើម្បីឱ្យទិន្នន័យជាក់ស្តែងទៅដល់ Telegram Channel លឿនបំផុតកម្រិត Sub-Second (ក្រោម ១ វិនាទី) ឱ្យទាន់ពេលទីផ្សារប្រែប្រួល!

### 9. 🚫 លុបចោលសាររំញ័រតម្លៃមាស (Disable Volatility Spike Alerts Permanently)
- មិនត្រូវផ្ញើសារប្រភេទ `🚨 XAUUSD VOLATILITY ALERT — បម្រែបម្រួលតម្លៃមាសខុសប្រក្រតី` (Bullish Spike / Flash Dump) ចូល Channel/Group ឡើយ។
- មុខងារ `check_price_volatility_spike` ត្រូវបានបិទទាំងស្រុងជាអចិន្ត្រៃយ៍ មិនឱ្យដំណើរការទៀតជាដាច់ខាត។

### 10. 🚫 លុបចោលសេចក្តីសង្ខេបទីផ្សារពេលយប់ (Disable Daily Market Wrap-Up Permanently)
- មិនត្រូវផ្ញើសារប្រភេទ `🌙 DAILY MARKET WRAP-UP — សេចក្តីសង្ខេបទីផ្សារពេលយប់` ចូល Channel/Group ឡើយ។
- មុខងារ `check_night_wrap_up` ត្រូវបានបិទទាំងស្រុងជាអចិន្ត្រៃយ៍ មិនឱ្យដំណើរការទៀតជាដាច់ខាត។

### 11. 🚫 លុបចោលសារជូនដំណឹងបើកផ្សារ London និង New York (LD / NY Session Open Alerts) ជារៀងរហូត (Permanently Banned — បញ្ជាផ្ទាល់)
- **បិទការផ្ញើសារម៉ោងបើកផ្សារ London & New York ជារៀងរហូត (Permanently Banned — បញ្ជាផ្ទាល់)**:
  - ហាមដាច់ខាតមិនឱ្យផ្ញើសារជូនដំណឹងម៉ោងបើកផ្សារ London Session (LD ម៉ោង ១៤:០០) ឬ New York Session (NY ម៉ោង ១៩:០០) និង Liquidity Heatmap ចូល Telegram Channel ឬ Group ទៀតឡើយ។
  - មុខងារ `check_session_open_alerts()` ត្រូវបានបិទទាំងស្រុងជាអចិន្ត្រៃយ៍។

### 12. 🚫 លុបចោលសារ Whale Order Book / Iceberg Alerts (Disable Whale Alerts Permanently)
- មិនត្រូវផ្ញើសារប្រភេទ `🛰️ WHALE ORDER BOOK ALERT — រកឃើញ Order ស្ថាប័នលាក់មុខ!` (Whale Iceberg Buy/Sell Wall) ចូល Channel/Group ឡើយ។
- មុខងារ `check_iceberg_orders` ត្រូវបានបិទទាំងស្រុងជាអចិន្ត្រៃយ៍ មិនឱ្យដំណើរការទៀតជាដាច់ខាត។

### 13. 🏛️ ស្តង់ដារផ្សាយសុន្ទរកថា Fed / Kevin Warsh (Live Speech Interpretation Standard — គំរូថ្មី VIP)
- **ទម្រង់គំរូថ្មីច្បាស់លាស់ ខ្លី ខ្លឹម (Clean VIP Speech Alert Template — បញ្ជាផ្ទាល់)**:
  - ឈប់ប្រើប្រាស់គំរូចាស់ទាំងស្រុង («ប្រើទម្រង់នេះហើយរូបភាពពិតដែលសាកសមជាងនេះ គំរូចាស់មិនប្រើ»)៖
```
<b>សុន្ទរកថា៖</b> Kevin Warsh (ប្រធាន Federal Reserve)
 <b>ជំហរ៖</b> Hawkish (រឹតបន្តឹងគោលនយោបាយរូបិយវត្ថុ)

💬 <b>សម្រង់សម្តីសំខាន់៖</b>
«Federal Reserve ត្រូវតែប្រុងប្រយ័ត្នខ្ពស់ចំពោះអតិផរណាដែលមិនទាន់ធ្លាក់ដល់គោលដៅ ២% ហើយទីផ្សារមិនគួររំពឹងការបញ្ចុះអត្រាការប្រាក់លឿនពេកឡើយ។»

⚡ <b>ផលប៉ះពាល់ទីផ្សារ៖</b>
🔹 <b>USD & US10Y Yields៖</b> ដុល្លារ និងទិន្នផលប័ណ្ណបំណុលឡើងថ្លៃ (Bullish)
🔸 <b>XAUUSD (មាស)៖</b> ប្រឈមសម្ពាធធ្លាក់ចុះ (Bearish)
```
- **រូបភាពពិតប្រាកដ និងសាកសមបំផុត (Authentic Real Speech / Podium Photo Standard — បញ្ជាផ្ទាល់)**:
  - ហាមដាច់ខាតមិនឱ្យយករូប Portrait ស្នាមញញឹមក្នុង Studio មកប្រើឡើយ។ ត្រូវប្រើរូបថតពិតប្រាកដដែលកំពុងថ្លែងសុន្ទរកថានៅលើវេទិកា (Podium) មានក្បាលមេក្រូ និងទង់ជាតិផ្លូវការ (`assets/speakers/kevin_warsh.jpg`) ជា Photo Caption ដោយផ្ទាល់។
  - ហាមផ្ញើជាអត្ថបទសុទ្ធ ឬរូបភាព Logo ស្ថាប័ននៅពេលមានរូបថតសុន្ទរកថាផ្លូវការ។
- **លុបចោលសារសំឡេង Voice Note ជារៀងរហូត (Permanently Disable Voice Notes — បញ្ជាផ្ទាល់)**:
  - ហាមដាច់ខាតមិនឱ្យបង្កើត ឬផ្ញើសារជាសំឡេង Voice Note (.mp3) ចូល Telegram Channel ទៀតឡើយ។
- **ល្បឿនបន្ទាន់ និងអាទិភាពកំពូលភ្លាមៗ (Zero-Delay & Instant VIP Priority for Kevin Warsh / Fed Chair)**:
  - រាល់ពេលដែលលោក **Kevin Warsh**, Jerome Powell ឬថ្នាក់ដឹកនាំ Fed ថ្លែងសុន្ទរកថា ឬចេញសេចក្តីថ្លែងការណ៍ FOMC ត្រូវតែដំណើរការ និងផ្សាយចេញជាបន្ទាន់ភ្លាមៗ (Instant Zero-Delay) ដោយមិនឱ្យរង់ចាំ ឬច្រានចោលដោយសារ Filter ព័ត៌មានទូទៅឡើយ។

### 14. ✍️ ស្តង់ដារភាសាខ្មែរ-អង់គ្លេសចម្រុះ និងការពារកំហុសអក្ខរាវិរុទ្ធ (Khmer-English Hybrid & Zero-Typo Orthography Standard)
- **លាយភាសាអង់គ្លេសសម្រាប់ឈ្មោះពិបាក (Mandatory English for Foreign Leaders, Companies & Places)**:
  - ឈ្មោះមេដឹកនាំពិភពលោក បុគ្គលសំខាន់ៗ និងឈ្មោះក្រុមហ៊ុន ត្រូវសរសេរជាអក្សរអង់គ្លេសដើមស្អាត មិនកាឡៃ ឬបំប្លែងសូរសព្ទជាខ្មែរឡើយ (ឧ. Apple, Microsoft, NVIDIA, Tesla, Google, Meta, Tether, BlackRock, TSMC, Intel, លោក Donald Trump, លោក Vladimir Putin, លោក Volodymyr Zelenskyy, លោក Jerome Powell, លោក Kevin Warsh, លោក Elon Musk, លោក Joe Biden, លោក Scott Bessent)។
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

### 22. 🛡️ គោលការណ៍ធានាដំណើរការព័ត៌មានទាន់ហេតុការណ៍ ២៤/៧ គ្មានការកកស្ទះ (24/7 Uninterrupted News Pipeline Safeguards)
- **ក្បួនការពារការច្រឡំទម្លាក់ព័ត៌មានចោល (Strict Zero False-Duplicate Dropping)**:
  - ការត្រួតពិនិត្យ Channel Feed (`_is_already_in_telegram_channel`) ហាមដាច់ខាតមិនឱ្យ match លើពាក្យសាមញ្ញ ២ ពាក្យនាំឱ្យច្រឡំថាព័ត៌មានផ្សាយរួច។
  - ត្រូវប្រើ Exact Article Link, URL Slug (ប្រវែង >= 12 តួ), ឬសមាមាត្រពាក្យគន្លឹះដាច់ដោយឡែកយ៉ាងតិច 65% - 100%។
- **ការការពារការកកស្ទះ Network ពេល Startup (Cached Channel HTML 30s TTL)**:
  - ហាមដាច់ខាតមិនឱ្យធ្វើ HTTP request ទៅ Telegram Web រាប់រយដងក្នុង Loop តែមួយពេល Startup។
  - ត្រូវទាញយក Channel HTML តែ ១ ដងគត់ និង Cache ទុក ៣០ វិនាទី ដើម្បីឱ្យការចាប់ផ្ដើម និងការ Scan ព័ត៌មានដើរលឿនក្នុងកម្រិត Sub-Second (< 10 វិនាទី)។
- **ប្រព័ន្ធការពារស្វ័យប្រវត្តិ ២៤/៧ (Supervisor Auto-Healing Loop)**:
  - ក្នុង `render_server.py` ត្រូវដំណើរការក្រោម Supervisor `while True`។ ប្រសិនបើ Bot ជួបប្រទះការដាច់ ឬ Error ណាមួយ វានឹង Restart ខ្លួនឯងស្វ័យប្រវត្តិក្នង ១០ វិនាទី ដោយមិនឱ្យគាំងស្លាប់ឡើយ។
- **ប្រព័ន្ធដាស់ Cloud មិនឱ្យគេង (UptimeRobot 24/7 Heartbeat)**:
  - UptimeRobot Ping រៀងរាល់ ៥ នាទីម្តង ធានាថា Render Web Service មិនចូល Sleeping Mode ជាដាច់ខាត។
- **ប្រព័ន្ធឆ្លាស់ AI ច្រើនជាន់ (Quadruple AI Fallback Hierarchy)**:
  - `Gemini Flash Lite` (Primary) ➡️ `DeepSeek-V4.1-Flash TheHive` (Backup 1) ➡️ `OpenRouter` (Backup 2) ➡️ `Local MacroAnalyzer` (Offline Permanent Safety Net)។ មិនមានករណីណាដែល Bot អត់ AI វិភាគឡើយ។

### 23. 🚫 លុបចោលសារ Weekly Gold Outlook ជារៀងរហូត (Permanently Disable Weekly Gold Outlook — បញ្ជាផ្ទាល់)
- **បិទការផ្សាយ Weekly Gold Outlook ជារៀងរហូត (Permanently Banned)**:
  - មិនត្រូវផ្ញើសារប្រភេទ `🏛️ WEEKLY GOLD OUTLOOK — យុទ្ធសាស្ត្រមាសប្រចាំសប្តាហ៍ថ្មី!` ចូល Telegram Channel ឬ Group ឡើយ។
  - មុខងារ `check_weekly_sunday_outlook` ក្នុង `main.py` ត្រូវបានបិទទាំងស្រុងជាអចិន្ត្រៃយ៍ (`return` ភ្លាមៗ) និងដកចេញពី Background Loop មិនឱ្យដំណើរការទៀតជាដាច់ខាត។

### 24. ☁️ ហេដ្ឋារចនាសម្ព័ន្ធ Cloud ២៤/៧ & UptimeRobot (24/7 Production Hosting & Zero-PC Dependency Standard — បញ្ជាផ្ទាល់)
- **សេវាកម្ម Cloud Render.com & UptimeRobot (Production Verified — កត់ត្រាជាគោលការណ៍ផ្លូវការ)**:
  - Bot ដំណើរការលើ Cloud Host: **Render.com** ភ្ជាប់ជាមួយ Web Service URL ផ្លូវការ: `https://xauusd-news-bot-jcc9.onrender.com`។
  - **UptimeRobot Heartbeat ៥ នាទី (Verified 100% Up)**: ប្រព័ន្ធ UptimeRobot កំពុងតាមដាន និង Ping រៀងរាល់ ៥ នាទីម្តង (`HTTP Up 23h+, 100%`) ការពារកុំឱ្យ Render Web Service ចូល Sleeping Mode ឬផ្អាកដំណើរការជាដាច់ខាត។
  - **ឯករាជ្យភាពពីកុំព្យូទ័រ (Zero Local PC Dependency)**: នៅពេលអ្នកប្រើប្រាស់បិទកុំព្យូទ័រផ្ទាល់ខ្លួន (Shut down PC), បិទ Wi-Fi ឬដកភ្លើង ក៏ Bot នៅតែបន្តដំណើរការ ៤ ចំណុចស្នូលចូល Telegram Channel `@GoldMarketKH8888` បានយ៉ាងទៀងទាត់ និងរលូន ១០០% ដោយគ្មានការរំខានឡើយ។
  - **ស្វ័យប្រវត្តិកម្ម GitHub Auto-Deploy**: រាល់ពេលកូដថ្មីត្រូវបាន Push ទៅកាន់ `ynkkxxz-max/xauusd-news-bot @ main`, Render នឹងទាញយកកូដថ្មី និង Restart Service ដោយស្វ័យប្រវត្តិតាម GitHub Webhook។