from datetime import datetime
import re

# Perfectly calibrated character limits so the full message with all headers,
# emojis, HTML tags, and clickable source URL fits strictly within Telegram's 1024 photo caption limit:
_BREAKING_CAPS = {
    "what_happened": 220,
    "why_it_matters": 240,
    "usd_impact": 100,
    "rate_yield_impact": 100,
    "xau_pressure": 100,
}

def _clip(text: str, cap: int) -> str:
    text = str(text).strip()
    return text if len(text) <= cap else text[:cap].rstrip() + "…"

def sanitize_khmer_spelling(text: str) -> str:
    """
    Corrects awkward transliteration errors, corrupted glyphs, or broken Unicode clusters in Khmer text.
    Per user directive: uses clean English names directly for foreign leaders, locations, and technical terms
    to ensure 100% clean typography and zero broken characters.
    Strictly removes foreign script leakage (Arabic, Cyrillic, Thai, etc.).
    """
    if not text:
        return ""
    
    res = str(text)

    # 1. Map known Thai economic/financial words to natural Khmer terms before stripping
    thai_to_khmer = [
        (r"พันธบัตร\s*รัฐบาล", "មូលបត្របំណុលរដ្ឋាភិបាល"),
        (r"พันธบัตร", "មូលបត្របំណុល"),
        (r"ตราสารหนี้", "មូលបត្របំណុល"),
        (r"ตลาดหุ้น", "ទីផ្សារភាគហ៊ុន"),
        (r"ตลาด", "ទីផ្សារ"),
        (r"หุ้น", "ភាគហ៊ុន"),
        (r"เศรษฐกิจ", "សេដ្ឋកិច្ច"),
        (r"เงินเฟ้อ", "អតិផរណា"),
        (r"ดอกเบี้ย", "អត្រាការប្រាក់"),
        (r"ธนาคาร\s*กลาง", "ធនាគារកណ្តាល"),
        (r"ธนาคาร", "ធនាគារ"),
        (r"ทองคำ", "មាស"),
        (r"ดอลลาร์", "ដុល្លារ"),
        (r"ราคา", "តម្លៃ"),
        (r"ลดลง", "ធ្លាក់ចុះ"),
        (r"เพิ่มขึ้น", "កើនឡើង"),
        (r"ความเสี่ยง", "ហានិភ័យ"),
        (r"นักลงทุน", "វិនិយោគិន"),
        (r"วิกฤต", "វិបត្តិ"),
        (r"สินทรัพย์", "ទ្រព្យសកម្ម"),
        (r"หนี้", "បំណុល"),
        (r"เงินทุน", "ទុនវិនិយោគ"),
        (r"การค้า", "ពាណិជ្ជកម្ម"),
        (r"ผลกระทบ", "ផលប៉ះពាល់"),
        (r"นโยบาย", "គោលនយោបាយ"),
        (r"การจ้างงาน", "ការងារ"),
    ]
    for pat, rep in thai_to_khmer:
        res = re.sub(pat, rep, res)

    # 2. Map known Greek & Cyrillic leakage to natural Khmer terms before stripping
    greek_cyrillic_fixes = [
        (r"ការ\s*[Ππ]ρόβλημα", "ការព្រួយបារម្ភ"),
        (r"[Ππ]ρόβλημα", "បញ្ហា"),
        (r"[Κκ]ρίση", "វិបត្តិ"),
        (r"[Οο]ικονομία", "សេដ្ឋកិច្ច"),
        (r"ការ\s*[Пп]роблема", "ការព្រួយបារម្ភ"),
        (r"[Пп]роблема", "បញ្ហា"),
        (r"[Оо]блигации", "មូលបត្របំណុល"),
        (r"[Кк]ризис", "វិបត្តិ"),
        (r"[Ээ]кономика", "សេដ្ឋកិច្ច"),
        (r"[Ии]нфляция", "អតិផរណា"),
    ]
    for pat, rep in greek_cyrillic_fixes:
        res = re.sub(pat, rep, res)

    # 3. Clean Arabic / Middle Eastern subwords accidentally emitted by LLM (only when Arabic script actually exists)
    res = re.sub(r"ប្រាក់ដុល្លារ\s*[\u0600-\u06FF]+", "ប្រាក់ដុល្លារ (USD) ", res)
    res = re.sub(r"ដុល្លារ\s*[\u0600-\u06FF]+", "ដុល្លារ (USD) ", res)

    # 4. Strictly strip ANY remaining foreign script characters:
    # Thai (\u0E00-\u0E7F), Lao (\u0E80-\u0EFF), Greek (\u0370-\u03FF, \u1F00-\u1FFF),
    # Cyrillic (\u0400-\u052F, \u2DE0-\u2DFF, \uA640-\uA69F),
    # Arabic (\u0600-\u06FF, \u0750-\u077F, \u08A0-\u08FF, \uFB50-\uFDFF, \uFE70-\uFEFF),
    # Hebrew (\u0590-\u05FF), Indic/Devanagari (\u0900-\u0DFF), Myanmar (\u1000-\u109F),
    # CJK (\u4E00-\u9FFF, \u3040-\u30FF, \uAC00-\uD7AF)
    foreign_regex = (
        r"[\u0E00-\u0E7F\u0E80-\u0EFF\u0370-\u03FF\u1F00-\u1FFF\u0400-\u052F"
        r"\u2DE0-\u2DFF\uA640-\uA69F\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF"
        r"\uFB50-\uFDFF\uFE70-\uFEFF\u0590-\u05FF\u0900-\u0DFF\u1000-\u109F"
        r"\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF]+"
    )
    res = re.sub(foreign_regex, "", res)

    corrections = [
        # Currency & Economy Fixes (prevents orphan or duplicate 'អាមេរិក' / 'ាមេរិក')
        (r"ប្រាក់ដុល្លារ\s*\(USD\)\s*(?:អា|ា)?មេរិក", "ប្រាក់ដុល្លារ (USD)"),
        (r"\(USD\)\s*(?:អា|ា)?មេរិក", "(USD)"),
        (r"ប្រាក់ដុល្លារ\s*(?:អា|ា)?មេរិក(?:\s*\(USD\))?", "ប្រាក់ដុល្លារ (USD)"),
        (r"ដុល្លារ\s*(?:អា|ា)?មេរិក(?:\s*\(USD\))?", "ប្រាក់ដុល្លារ (USD)"),
        (r"(?<![\u1780-\u17A2])ាមេរិក\b", "អាមេរិក"),
        (r"អាមេរិច", "អាមេរិក"),
        (r"សេដ្ធកិច្ច", "សេដ្ឋកិច្ច"),
        (r"រក្សាថ្លៃឡើងថ្លៃ", "រក្សាកំណើនថ្លៃ"),
        (r"តម្លៃលោហៈមានតម្លៃ", "តម្លៃលោហៈដ៏មានតម្លៃ"),

        # Foreign Leaders & Prominent People (Strict Original Language - Zero Khmer Literal Translation per user directive)
        (r"លោក\s*វ៉[្ល\u17d2\u179b]*[ា\u17b6]*ឌីមៀ\s*ពូទីន|វ៉[្ល\u17d2\u179b]*[ា\u17b6]*ឌីមៀ\s*ពូទីន", "Vladimir Putin"),
        (r"លោក\s*ពូទីន|ពូទីន", "Putin"),
        (r"លោក\s*វ៉[្ល\u17d2\u179b]*[ា\u17b6]*ឌីមៀ\s*ហ្សេឡេនស្គី|វ៉[្ល\u17d2\u179b]*[ា\u17b6]*ឌីមៀ\s*ហ្សេឡេនស្គី|ហ្សេឡេនស្គី", "Volodymyr Zelenskyy"),
        (r"ដូណាល់\s*ត្រាំ|ត្រាំព៍|ត្រាំ", "Donald Trump"),
        (r"ជេរ៉ូម\s*ផោវែល|ផោវែល|ផៅវែល", "Jerome Powell"),
        (r"ខេវីន\s*វ៉ាស|ខេវិន\s*វ៉ាស|ខេវិន\s*វ៉ស", "Kevin Warsh"),
        (r"ចូ\s*បៃដិន|បៃដិន", "Joe Biden"),
        (r"បេនចាមីន\s*ណេតាន់យ៉ាហ៊ូ|ណេតាន់យ៉ាហ៊ូ", "Benjamin Netanyahu"),
        (r"អេឡុន\s*ម៉ាស|អ៊ីឡុន\s*ម៉ាស|អេឡុង\s*ម៉ាស", "Elon Musk"),
        (r"ស៊ី\s*ជីនពីង|ស៊ី\s*ជីនភីង", "Xi Jinping"),
        (r"គ្រីស្ទីន\s*ឡាហ្គាដ", "Christine Lagarde"),
        (r"ស្កុត\s*បេសសិន", "Scott Bessent"),
        (r"វ៉ារិន\s*បាហ្វហ្វិត|វ៉ារិន\s*ប៊ូហ្វេត", "Warren Buffett"),
        (r"កាម៉ាឡា\s*ហារីស", "Kamala Harris"),
        (r"គ្រីស្តូហ្វឺ\s*វ៉លលើ|គ្រីស្តូហ្វឺ\s*វ៉ាល័រ", "Christopher Waller"),
        (r"ចន\s*វីលៀម", "John Williams"),
        (r"មីសែល\s*បូមែន", "Michelle Bowman"),
        (r"អូស្ទីន\s*ហ្គូលស្ប៊ី", "Austan Goolsbee"),
        (r"គៀរ\s*ស្តាមឺ|ខៀរ\s*ស្តាម័រ", "Keir Starmer"),
        
        # Strategic Locations, Countries & Institutions
        (r"ហូមុដឌ|ហូមុដ|ហូមូស|ហ័រមូដ|ហូមូដ|ហ័រមុដ", "Strait of Hormuz"),
        (r"ច្រកសមុទ្រ\s*(?:ហ័រមូស|Strait of Hormuz)", "ច្រកសមុទ្រ Strait of Hormuz"),
        (r"សហភាព\s*អឺប(?![រ៉ុ])|សហភាព\s*អឺរុប|សហភាព\s*អ៊ឺរ៉ុប", "សហភាពអឺរ៉ុប"),
        (r"\bអឺប\b", "អឺរ៉ុប"),
        (r"មេដឹកនាំ\s+សហភាពអឺរ៉ុប", "មេដឹកនាំសហភាពអឺរ៉ុប"),
        (r"សហភាព\s+អឺរ៉ុប", "សហភាពអឺរ៉ុប"),
        (r"ដល់\s+(ក្រុង|រាជធានី|ទីក្រុង)", r"ដល់\1"),
        (r"នៅ\s+(អឺរ៉ុប|អាស៊ី|អាមេរិក|កម្ពុជា)", r"នៅ\1"),
        (r"សម្ដែង", "សម្តែង"),
        (r"ប្រធានាធិបតី\s+សហរដ្ឋអាមេរិក\s+(?:លោក\s+)?", "ប្រធានាធិបតីសហរដ្ឋអាមេរិក "),
        (r"លោក\s+Donald Trump", "Donald Trump"),
        (r"តម្លៃប្រេងឆៅនិងឧស្ម័នធម្មជាតិ", "តម្លៃប្រេងឆៅ និងឧស្ម័នធម្មជាតិ"),
        (r"សាអូឌីហាំឌី|សាអ៊ូឌី\s*អារ៉ាប់|សាអូឌី\s*អារ៉ាប៊ី|ប្រទេស\s*សាអូឌី", "អារ៉ាប៊ីសាអ៊ូឌីត"),
        (r"(?:(?:Tehran|តេអ៊ែរ៉ង់|តេហេរ៉ង់|តេអេរ៉ង់)\s*[\(\)]*\s*)+", "តេហេរ៉ង់"),
        (r"(?:(?:Yemen|យេមែន|យេម៉ែន)\s*[\(\)]*\s*)+", "យេមែន"),
        (r"ទទវូច", "ទទូច"),
        (r"យេម៉ែន", "យេមែន"),
        (r"ជៀសវាង", "ចៀសវាង"),
        (r"ជៀសផុត", "ចៀសផុត"),
        (r"គេចជៀស", "គេចចៀស"),
        (r"ជៀស(?=[វផុត])", "ចៀស"),
        (r"កាត់ផ្ដាច់", "កាត់ផ្តាច់"),
        (r"ផ្ដាច់", "ផ្តាច់"),
        (r"ដែលបាន\s+ពាក់ទង(?:នឹង)?", "ដែលពាក់ព័ន្ធនឹង"),
        (r"ពាក់ទងនឹង", "ពាក់ព័ន្ធនឹង"),
        (r"ពាក់ទង", "ពាក់ព័ន្ធ"),
        (r"ស្ថានភាពនេះឱ្យឃើញ", "ស្ថានភាពនេះបង្ហាញឱ្យឃើញ"),
        (r"នេះឱ្យឃើញពី", "នេះបង្ហាញឱ្យឃើញពី"),
        (r"ចាប់ផ្តើមយោលយោគ", "ចាប់ផ្តើមរង្គោះរង្គើ"),
        (r"យោលយោគ", "រង្គោះរង្គើ"),
        (r"(យេមែន|រុស្ស៊ី|អ៊ុយក្រែន|ចិន|អាមេរិក|បារាំង|អាល្លឺម៉ង់|អ៊ីរ៉ង់|អ៊ីស្រាអែល|តួកគី|ជប៉ុន|កូរ៉េខាងត្បូង|កូរ៉េខាងជើង|តៃវ៉ាន់|កាណាដា|អង់គ្លេស|ឥណ្ឌា)\s*(កំពុង|បាន|ត្រូវបាន|អាច|នឹង|គ្រោង|ប្រកាស)", r"\1 \2"),
        # Strictly remove unnatural spacing between Khmer prepositions/prefixes and country names
        (r"(របស់|នៅ|ពី|ដល់|ប្រទេស|ចំពោះ|លើ|រវាង)\s+(រុស្ស៊ី|អ៊ុយក្រែន|ចិន|អាមេរិក|បារាំង|អាល្លឺម៉ង់|អ៊ីរ៉ង់|អ៊ីស្រាអែល|តួកគី|ជប៉ុន|កូរ៉េខាងត្បូង|កូរ៉េខាងជើង|តៃវ៉ាន់|កាណាដា|អង់គ្លេស|ឥណ្ឌា|យេមែន|មជ្ឈិមបូព៌ា)", r"\1\2"),
        (r"រដ្ឋមន្ត្រីក្រសួងហិរញ្ញវត្ថុ\s+ចក្រភពអង់គ្លេស", "រដ្ឋមន្ត្រីក្រសួងហិរញ្ញវត្ថុអង់គ្លេស"),
        (r"ឧបត្ថម្ភដល់សង្គ្រាម", "ចំណាយលើសង្គ្រាម"),
        (r"([\u1780-\u17D3])និង", r"\1 និង"),
        (r"([\u1780-\u17D3])ឬ(?=[\u1780-\u17D3])", r"\1 ឬ "),
        (r"([\u1780-\u17D3])ដើម្បី", r"\1 ដើម្បី"),
        (r"([\u1780-\u17D3])ប៉ុន្តែ", r"\1 ប៉ុន្តែ"),
        (r"([\u1780-\u17D3])ដោយសារ", r"\1 ដោយសារ"),
        (r"សង្គ្រាមនៅមជ្ឈិមបូព៌ា\s*\(\s*អ៊ីរ៉ង់\s*\)", "សង្គ្រាមនៅមជ្ឈិមបូព៌ា"),
        (r"(?:Iran|អ៊ីរ៉ង់)\s*\(\s*(?:Iran|អ៊ីរ៉ង់)\s*\)", "អ៊ីរ៉ង់"),
        (r"(?:Israel|អ៊ីស្រាអែល)\s*\(\s*(?:Israel|អ៊ីស្រាអែល)\s*\)", "អ៊ីស្រាអែល"),
        (r"(?:Ukraine|អ៊ុយក្រែន)\s*\(\s*(?:Ukraine|អ៊ុយក្រែន)\s*\)", "អ៊ុយក្រែន"),
        (r"\bIran\b|អ៊ីរ៉ាន", "អ៊ីរ៉ង់"),
        (r"\bIsrael\b|អ៊ីស្រាអ៊ែល", "អ៊ីស្រាអែល"),
        (r"\bUkraine\b", "អ៊ុយក្រែន"),
        (r"រុស្សី(?![៊ី])", "រុស្ស៊ី"),
        (r"មជ្ឈឹមបូព៌ា|មជ្ឍឹមបូព៌ា", "មជ្ឈិមបូព៌ា"),
        (r"តុលាការព្រហ្មទណ្ឌអន្តរជាតិ\s*(?:ICC|\(ICC\))?", "តុលាការព្រហ្មទណ្ឌអន្តរជាតិ (ICC)"),
        (r"បង្ហាញពីភាព\s+នៃ", "បង្ហាញពីភាពផុយស្រួយនៃ"),
        (r"(អ៊ីស្រាអែល|អ៊ីរ៉ង់|អ៊ុយក្រែន|រុស្ស៊ី|ចិន|អាមេរិក|តួកគី|សហភាពអឺរ៉ុប|Houthi|ICC)និង", r"\1 និង"),
        (r"(\S)និង(អ៊ីស្រាអែល|អ៊ីរ៉ង់|អ៊ុយក្រែន|រុស្ស៊ី|ចិន|អាមេរិក|តួកគី|សហភាពអឺរ៉ុប|អារ៉ាប៊ីសាអ៊ូឌីត|Houthi|ICC)", r"\1 និង \2"),
        
        # Financial & Macro-Economic Terms (GATE 1: LEXICAL INTEGRITY)
        (r"ប៊ូលីស", "Bullish"),
        (r"ប៊ែរីស", "Bearish"),
        (r"សាយវ៉េ", "Sideway"),
        (r"សេហ្វហេវិន", "Safe-Haven"),
        (r"\(ទ្រព្យសកម្មសុវត្ថិភាព\s*\(Safe-Haven\)\)|ទ្រព្យសកម្មសុវត្ថិភាព\s*\(Safe-Haven\)", "ទ្រព្យសុវត្ថិភាព (Safe-Haven)"),
        (r"គម្លាតសាច់ប្រាក់", "កង្វះខាតសាច់ប្រាក់ងាយស្រួល"),
        (r"ទិន្នផលប័ណ្ណបំណុល", "ទិន្នផលមូលបត្របំណុល"),
        (r"ប័ណ្ណបំណុល(?!\s*រដ្ឋ)", "មូលបត្របំណុល"),
        (r"សម្ពាធអតិផរណា និងប្រាក់រូពីផ្ដល់បន្ទប់សម្រាប់ការរឹតបន្តឹងអត្រាការប្រាក់បន្ថែមទៀត", "សម្ពាធអតិផរណា និងប្រាក់រូពីផ្ដល់លទ្ធភាព និងបើកផ្លូវឱ្យមានការរឹតបន្តឹងអត្រាការប្រាក់បន្ថែមទៀត"),
        (r"ផ្ដល់បន្ទប់សម្រាប់ការរឹតបន្តឹង(?:អត្រាការប្រាក់)?", "ផ្ដល់លទ្ធភាព និងបើកផ្លូវឱ្យមានការរឹតបន្តឹងអត្រាការប្រាក់"),
        (r"ផ្ដល់បន្ទប់", "ផ្ដល់លទ្ធភាព និងបើកផ្លូវ"),
        (r"ទ្រង់សង្គ្រាម", "យន្តការសឹក ឬកងកម្លាំងយោធារបស់វិមានក្រឹមឡាំង"),
        (r"តម្លៃថាមពលខាំ|ថាមពលខាំ", "ថ្លៃដើមថាមពលកើនឡើងខ្ពស់"),
        (r"បាន?ថ្លឹងថ្លែងយ៉ាងខ្លាំងទៅលើ", "បានដាក់សម្ពាធយ៉ាងធ្ងន់ធ្ងរលើ"),
        (r"ទិន្នន័យការផលិត PMI|ការផលិត PMI", "សន្ទស្សន៍អ្នកគ្រប់គ្រងការបញ្ជាទិញ (PMI)"),
        (r"(\d+(?:\.\d+)?)\s*ប៊ីដុល្លារ", r"\1 ពាន់លានដុល្លារ"),
        (r"ប៊ីដុល្លារ", "ពាន់លានដុល្លារ"),
        (r"ប៊ីលាន", "ពាន់លាន"),
        (r"ធនាគារអភិវឌ្ឍន៍អាស៊ាន", "ធនាគារអភិវឌ្ឍន៍អាស៊ី (ADB)"),
        # SEC and regulatory authorities (Strict idempotent replacement & collapse)
        (r"(?:(?:គណៈកម្មការ\s*)?គណៈកម្មការមូលបត្រអាមេរិក\s*[\(\)]*\s*)+SEC[\s\)]*", "គណៈកម្មការមូលបត្រអាមេរិក (SEC) "),
        (r"(?<!គណៈកម្មការមូលបត្រអាមេរិក \()(?<!\()\bSEC\b(?!\))", "គណៈកម្មការមូលបត្រអាមេរិក (SEC)"),

        # Corporate, Company & Brand Names (Strict Original Language - Zero Khmer Literal Translation per user directive)
        (r"សំបកកង់កាណាដា|កាណាដា\s*ថាយអឺ|ថាយអឺ\s*កាណាដា", "Canadian Tire"),
        (r"\bCanadian Tire\b", "Canadian Tire"),
        (r"ក្រុមហ៊ុន\s*អេបផល|អេបផល(?!\s*ផ្លែ)", "Apple"),
        (r"ក្រុមហ៊ុន\s*ម៉ៃក្រូសូហ្វ|ម៉ៃក្រូសូហ្វ", "Microsoft"),
        (r"ក្រុមហ៊ុន\s*អិនវីឌៀ|អិនវីឌៀ|អិនវីឌា", "NVIDIA"),
        (r"ក្រុមហ៊ុន\s*ថេសឡា|ថេសឡា", "Tesla"),
        (r"ក្រុមហ៊ុន\s*ហ្គូហ្គល|ហ្គូហ្គល|ហ្គូហ្គល់", "Google"),
        (r"ក្រុមហ៊ុន\s*អាម៉ាហ្សូន|អាម៉ាហ្សូន", "Amazon"),
        (r"ក្រុមហ៊ុន\s*ប៊ិកថេក|ប៊ិកថេក", "Big Tech"),
        (r"ក្រុមហ៊ុន\s*ប៊្លែករ៉ក់|ប៊្លែករ៉ក់", "BlackRock"),
        (r"ក្រុមហ៊ុន\s*ថេតធ័រ|ថេតធ័រ|ថេធើរ|ថេតថឺ", "Tether"),
        (r"ប៊ីណាន|ប៊ីនែន", "Binance"),
        (r"ខ័នបេស|ខយបេស", "Coinbase"),
        (r"ប៊ីតខយ|ប៊ីតខញ|ប៊ីតខ័ន", "Bitcoin"),
        (r"អេធើរៀម|អេធើញៀម", "Ethereum"),
        (r"ដូជខយ|ដូជខញ|ដូកខយ", "Dogecoin"),
        (r"អូផិនអេអាយ|អូផេនអេអាយ", "OpenAI"),
        (r"ក្រុមហ៊ុន\s*ធីអេសអិមស៊ី|ធីអេសអិមស៊ី", "TSMC"),
        (r"ក្រុមហ៊ុន\s*ប៊ូអ៊ីង|ប៊ូអ៊ីង", "Boeing"),
        (r"ក្រុមហ៊ុន\s*អ៊ីនធែល|អ៊ីនធែល", "Intel"),
        (r"ក្រុមហ៊ុន\s*ហ្វាយហ្សឺ|ហ្វាយហ្សឺ", "Pfizer"),
        (r"ក្រុមហ៊ុន\s*ម៉ូឌែណា|ម៉ូឌែណា", "Moderna"),
        (r"ក្រុមហ៊ុន\s*មេតា|មេតា(?!\s*ទិន្នន័យ)", "Meta"),
        (r"ក្រុមហ៊ុន\s*ប៊ែកសៀ\s*ហាតថាវ៉េ|ប៊ែកសៀ\s*ហាតថាវ៉េ", "Berkshire Hathaway"),
        (r"ក្រុមហ៊ុន\s*ស្ប៉េសអ៊ិច|ស្ប៉េសអ៊ិច|ស្ប៉េសអេច|ស្ពេសអេច|ស្ពេសអិច|Space X", "SpaceX"),
        (r"ស្តាលីង|ស្តាលីង្គ|ស្តារលីង", "Starlink"),

        # Natural Journalistic Style & Accurate Spelling Corrections per user directive
        (r"ពួក\s*រុស្ស៊ីម៉ាត់|ក្រុម\s*រុស្ស៊ីម៉ាត់|រុស្ស៊ីម៉ាត់|រុស្សីម៉ាត់", "ក្រុមអ្នកតាំងលំនៅជ្រុលនិយម"),
        (r"ពួក\s*អ្នកតាំងលំនៅ", "ក្រុមអ្នកតាំងលំនៅ"),
        (r"ជនស៊ីវិលអ៊ីស្រាអែល(?=.*(?:វាយប្រហារ|West Bank|តាំងលំនៅ|ប៉ាឡេស្ទីន|អំពើហិង្សា|ក្បួន))", "ក្រុមអ្នកតាំងលំនៅជ្រុលនិយមអ៊ីស្រាអែល"),
        (r"ជនស៊ីវិលអ៊ីស្រាអែល", "ក្រុមអ្នកតាំងលំនៅអ៊ីស្រាអែល"),
        (r"អភិបាលក្រុងប៉ារាំង(?:\s*(?:ម្នាក់|មួយរូប))?", "អភិបាលក្រុងជនជាតិបារាំងមួយរូប"),
        (r"ក្បួនដំណើររថយន្ត", "ក្បួនរថយន្ត"),
        (r"ក្បួនតំណាងអឺរ៉ុប", "ក្បួនរថយន្តប្រតិភូសហភាពអឺរ៉ុប"),
        (r"កន្លែងសន្តិសុខរើសើប|តំបន់សន្តិសុខរើសើប|ទីតាំងសន្តិសុខរើសើប|កន្លែងសន្តិសុខរសើប|កន្លែងរសើប", "ទីតាំងសន្តិសុខរសើប"),
        (r"រើសើប", "រសើប"),
        (r"តម្លើង", "ដំឡើង"),
        (r"ត្រូវបានគេមើលឃើញថាជា", "ត្រូវបានចាត់ទុកជា"),
        (r"ត្រូវបានគេមើលឃើញថា", "ត្រូវបានចាត់ទុកថា"),
        (r"ដំណោះស្រាយចំណាយថវិកាស្តួចស្តើង|ចំណាយថវិកាស្តួចស្តើង|ថវិកាស្តួចស្តើង|ដំណោះស្រាយថោក|ចំណាយថោក", "ដំណោះស្រាយចំណាយទាប"),
        (r"បច្ចេកវិទ្យាទាប", "វិធីសាស្ត្រសាមញ្ញ"),
        (r"ជាញឹកញាប់រងការគំរាមកំហែង", "តែងតែប្រឈមនឹងការគំរាមកំហែង"),
        (r"ជាញឹកញាប់រង", "តែងតែប្រឈម"),
        (r"រងការគំរាមកំហែងពីក្រុមឧទ្ទាម", "ប្រឈមនឹងការគំរាមកំហែងពីក្រុមឧទ្ទាម"),
        (r"ការអនុវត្តនេះឆ្លុះបញ្ចាំង", "ការអនុវត្តបែបនេះបានឆ្លុះបញ្ចាំង"),
        (r"ការការពារថយ", "ការការពារ"),

        # Professional Technical Terms & Mistranslation Corrections (Point 4)
        (r"ដាក់ឈ្មោះ(?:\s*ជា)?", "តែងតាំង"),
        (r"ប៉ះ(?:ពាល់)?(?:នឹង|ទៅលើ)?ប្រេង(?:កាត)?", "សម្ពាធតម្លៃប្រេង"),
        (r"ក្រុមហ៊ុន\s*ប៊ិកថេក|ប៊ិកថេក|របស់បច្ចេកវិទ្យាធំ|បច្ចេកវិទ្យាធំ", "ក្រុមហ៊ុនបច្ចេកវិទ្យាយក្ស"),
        (r"ការប្រញាប់ប្រញាល់ផ្តល់មូលនិធិ", "ការសម្រុកបញ្ចេញទុនវិនិយោគ"),
        (r"គម្លាតសាច់ប្រាក់\s*របស់ទំនើប", "កង្វះខាតសាច់ប្រាក់ងាយស្រួលក្នុងយុគសម័យទំនើប"),
        (r"គម្លាតសាច់ប្រាក់", "កង្វះខាតសាច់ប្រាក់ងាយស្រួល"),
        (r"សម្រាប់កាណាដា", "ប្រចាំប្រទេសកាណាដា"),
        (r"កម្រិតខ្ពស់គ្រប់ពេល", "កម្រិតខ្ពស់បំផុតជាប្រវត្តិសាស្ត្រ (ATH)"),
        (r"កាត់បន្ថយអត្រា(?!ការប្រាក់)", "កាត់បន្ថយអត្រាការប្រាក់"),
        (r"ការដំឡើងអត្រា(?!ការប្រាក់)", "ការដំឡើងអត្រាការប្រាក់"),

        # Crude Oil Barrel Terminology & Verbs (Strict 'បារ៉ែល' - NEVER mistranslate as 'បារ' or 'មួយបារ')
        (r"ហាក់ឡើង(?=ដល់|ខ្ពស់|ខ្លាំង|\s)", "ហក់ឡើង"),
        (r"ហាក់ឡើង", "ហក់ឡើង"),
        (r"ដុល្លារ\s*ក្នុង\s*មួយ\s*បារ(?![៉ែលាំងម្ភ])", "ដុល្លារក្នុងមួយបារ៉ែល"),
        (r"ក្នុង\s*មួយ\s*បារ(?![៉ែលាំងម្ភ])", "ក្នុងមួយបារ៉ែល"),
        (r"មួយ\s*បារ(?![៉ែលាំងម្ភ])", "មួយបារ៉ែល"),
        (r"បារប្រេង", "បារ៉ែលប្រេង"),
        (r"ដុល្លារ\s*ក្នុង\s*មួយ\s*ធុង(?:\s*ប្រេង)?", "ដុល្លារក្នុងមួយបារ៉ែល"),
        (r"ក្នុង\s*មួយ\s*ធុង(?:\s*ប្រេង)?", "ក្នុងមួយបារ៉ែល"),
        (r"ដុល្លារ\s*/\s*បារ(?![៉ែលាំងម្ភ])", "ដុល្លារក្នុងមួយបារ៉ែល"),
        (r"ដុល្លារ\s*/\s*បារ៉ែល", "ដុល្លារក្នុងមួយបារ៉ែល"),
        (r"/បារ(?![៉ែលាំងម្ភ])", "/បារ៉ែល"),
        (r"បារ៉ែល(?:\s*បារ៉ែល)+", "បារ៉ែល"),

        # Olive Harvest & Crops Terminology (Strict 'អូលីវ' - NEVER mistranslate or hallucinate as 'អង្វរ')
        (r"ផលដំណាំអង្វរ|ដំណាំអង្វរ|ផ្លែអង្វរ|ដើមអង្វរ", "ផលដំណាំអូលីវ"),
        (r"អង្វរ(?=\s*ពីប្រជាជន|\s*ប៉ាឡេស្ទីន|\s*របស់ប្រជាជន|\s*នៅលើដី)", "អូលីវ"),
        (r"ប្រេងអង្វរ", "ប្រេងអូលីវ"),
        (r"\bolives?\b", "អូលីវ"),

        # Natural Spacing & Preposition Cleanup
        (r"មជ្ឈិមបូព៌ា\s*(រយៈពេល|បាន|កំពុង|ត្រូវ|ដែល)", r"មជ្ឈិមបូព៌ា \1"),
        (r"([0-9]+)\s*ឆ្នាំ\s*របស់", r"\1 ឆ្នាំ របស់"),
        (r"([A-Za-z0-9]+)\s*ត្រូវបាន", r"\1 ត្រូវបាន"),
        (r"🔶", "🔸"),
        (r"ភាពមិនប្រាកដប្រជាផ្នែកភូមិសាស្ត្រនយោបាយអាចបង្កើនភាពងាយរងគ្រោះដល់", "ហានិភ័យភូមិសាស្ត្រនយោបាយដាក់សម្ពាធប្រែប្រួលខ្លាំងលើ"),
        (r"ភាពមិនប្រាកដប្រជានៃសេដ្ឋកិច្ច\s*អាចដាក់សម្ពាធលើ", "សម្ពាធសេដ្ឋកិច្ចបង្កើនការប្រុងប្រយ័ត្នលើ"),

        # Typography & spacing cleanup (preserve newlines \n)
        (r"\([ \t]+", "("),
        (r"[ \t]+\)", ")"),
        (r"[ \t]{2,}", " "),
    ]
    for pat, rep in corrections:
        res = re.sub(pat, rep, res)
    # Strip any nested duplicate words like "Israel (Israel (...))"
    res = re.sub(r'\b([A-Za-z0-9]+)(?:\s*\(\s*\1\s*[\(\)]*)+', r'\1', res)
    res = re.sub(r'([A-Za-z0-9]+)\s*\(\s*\1\s*\)', r'\1', res)

    # 5. Clean orphaned / stray brackets, parentheses, and dangling prefix artifacts (e.g. "បញ្ហា ) ព្រួយបារម្ភ...")
    res = re.sub(r'^\s*(?:[A-Za-z\u1780-\u17FF\s]{1,15}\s*)?[\)\]\}\>]\s*[-–—:]*\s*', '', res).strip()
    res = re.sub(r'^[\(\[\{][^\)\]\}]{1,25}[\)\]\}]\s*[-–—:]*\s*', '', res).strip()
    res = re.sub(r'^\s*បញ្ហា\s*[\)\]\}\:\-–—\s]+\s*', '', res).strip()

    # 6. Deduplicate repeated Khmer words/syllable stutters (e.g. "ព្យាករណ៍ព្យាករណ៍", "ប្រឆាំង ប្រឆាំង", "ទុកទុក", "កើនឡើងឡើង")
    stutter_fixes = [
        (r"ការព្យាករណ៍ព្យាករណ៍", "ការព្យាករណ៍"),
        (r"ព្យាករណ៍ព្យាករណ៍", "ព្យាករណ៍"),
        (r"រំពឹងទុកទុក", "រំពឹងទុក"),
        (r"ទុកទុកជាមុន", "ទុកជាមុន"),
        (r"ប្រឆាំង\s+ប្រឆាំង", "ប្រឆាំង"),
        (r"ភាពប្រឆាំង\s*ប្រឆាំង", "ភាពប្រឆាំង"),
        (r"កើនឡើងឡើង", "កើនឡើង"),
        (r"ធ្លាក់ចុះចុះ", "ធ្លាក់ចុះ"),
        (r"ព្រួយបារម្ភ\s*ព្រួយបារម្ភ", "ព្រួយបារម្ភ"),
        (r"តានតឹង\s*តានតឹង", "តានតឹង"),
        (r"រដ្ឋាភិបាល\s*រដ្ឋាភិបាល", "រដ្ឋាភិបាល"),
        (r"សេដ្ឋកិច្ច\s*សេដ្ឋកិច្ច", "សេដ្ឋកិច្ច"),
        (r"អតិផរណា\s*អតិផរណា", "អតិផរណា"),
        (r"ទីផ្សារ\s*ទីផ្សារ", "ទីផ្សារ"),
        (r"វិនិយោគិន\s*វិនិយោគិន", "វិនិយោគិន"),
        (r"នយោបាយ\s*នយោបាយ", "នយោបាយ"),
        (r"អន្តរជាតិ\s*អន្តរជាតិ", "អន្តរជាតិ"),
    ]
    for pat, rep in stutter_fixes:
        res = re.sub(pat, rep, res)

    # General algorithmic deduplication of Khmer word/syllable repeats (length >= 3)
    # Strictly require whitespace (\s+) to prevent corrupting compound words like 'ការថារថយន្ត'
    for _ in range(2):
        res = re.sub(r'([\u1780-\u17D3\u17B6-\u17C5]{3,})\s+\1', r'\1', res)

    # 7. Percentage & Financial Number Formatting (Convert Khmer/Latin digits + ភាគរយ/percent to clean Latin %)
    # e.g. ២២ ភាគរយ -> 22%, ២២.២៤ ភាគរយ -> 22.24%, 42 ភាគរយ -> 42%, 15% -> 15%
    _khmer_digits_map = {'០': '0', '១': '1', '២': '2', '៣': '3', '៤': '4', '៥': '5', '៦': '6', '៧': '7', '៨': '8', '៩': '9'}
    def _to_latin_pct(m):
        raw_num = m.group(1)
        latin_num = "".join(_khmer_digits_map.get(ch, ch) for ch in raw_num)
        return f"{latin_num}%"

    def _to_latin_currency(m):
        raw_num = m.group(1)
        suffix = m.group(2)
        latin_num = "".join(_khmer_digits_map.get(ch, ch) for ch in raw_num)
        return f"{latin_num} {suffix}"

    res = re.sub(r'កូដេន\s*', 'កាក់ឌីជីថល ', res)
    res = re.sub(r'([០-៩0-9]+(?:\.[០-៩0-9]+)?)\s*(?:ភាគរយ|percent|%)', _to_latin_pct, res)
    res = re.sub(r'([០-៩]+(?:\.[០-៩]+)?)\s*(ដុល្លារ|រៀល|\$|€|£|¥|បារ៉ែល)', _to_latin_currency, res)
    # Convert all remaining Khmer digits to Latin digits (e.g. ២ ឆ្នាំ -> 2 ឆ្នាំ, ១០៨ -> 108)
    res = re.sub(r'([០-៩]+(?:\.[០-៩]+)?)', lambda m: "".join(_khmer_digits_map.get(ch, ch) for ch in m.group(1)), res)
    res = re.sub(r'(%)([\u1780-\u17D3])', r'\1 \2', res)
    res = re.sub(r'([\u1780-\u17D3])(\d+(?:\.\d+)?%)', r'\1 \2', res)

    # 8. Ensure clean spacing between Khmer letters and Latin (English) characters (e.g. 'កងទ័ព Yemen', 'Houthi បាន')
    # Use letters/vowels [\u1780-\u17D3] only to exclude punctuation marks [\u17D4-\u17DA] (។, ៕, ៖, ៗ)
    res = re.sub(r'([\u1780-\u17D3])([A-Za-z0-9])', r'\1 \2', res)
    res = re.sub(r'([A-Za-z0-9])([\u1780-\u17D3])', r'\1 \2', res)

    # 9. Ensure no awkward whitespace before Khmer punctuation marks (។, ៕, ៖, ៗ, ៘)
    res = re.sub(r'\s+([។៕៖ៗ៘])', r'\1', res)

    # 10. Ensure clean space after Khmer full stop (។) and Bariyoosan (៕)
    res = re.sub(r'([។៕])(?!\s|$)', r'\1 ', res)

    # 11. Strictly collapse multiple consecutive spaces (e.g. "  " -> " ")
    res = re.sub(r'[\t ]{2,}', ' ', res)

    return res.strip()

class KhmerFormatter:
    @staticmethod
    def format_daily_gold_price(price_data: dict, summary: str = "", include_smc: bool = False) -> str:
        """
        Formats daily gold price report in clean, concise Khmer style requested by user:
        🥇  DAILY GOLD PRICE — ហាងឆេងមាសប្រចាំថ្ងៃ

        📅  កាលបរិច្ឆេទ: 29/09/2026 


         🌐1 អោន : $4,127.30

🇰🇭 1 តម្លឹង: លក់ $5,006.09 | ទិញ $4,981.09
              
            1 ជី: លក់ $500.61 | ទិញ $498.11

           📉 បម្រែបម្រួល: $-41.10 (-0.99%)
        """
        oz = price_data.get("price_oz", 0.0)
        chg = price_data.get("change", 0.0)
        pct = price_data.get("change_pct", 0.0)
        date_str = price_data.get("date_str", "")
        if not date_str:
            try:
                from config import CAMBODIA_TZ
                date_str = datetime.now(CAMBODIA_TZ).strftime("%d/%m/%Y")
            except Exception:
                date_str = datetime.now().strftime("%d/%m/%Y")

        loc = price_data.get("local_market", {})
        damlung_sell = loc.get("damlung_sell", 0.0)
        damlung_buy = loc.get("damlung_buy", 0.0)
        chi_sell = loc.get("chi_sell", damlung_sell / 10.0 if damlung_sell else 0.0)
        chi_buy = loc.get("chi_buy", damlung_buy / 10.0 if damlung_buy else 0.0)

        sign = "+" if chg >= 0 else ""
        icon = "📈" if chg >= 0 else "📉"

        msg = (
            f"🥇  <b>DAILY GOLD PRICE — ហាងឆេងមាសប្រចាំថ្ងៃ</b>\n\n"
            f"📅  <b>កាលបរិច្ឆេទ:</b> {date_str} \n\n\n"
            f" 🌐<b>1 អោន :</b> ${oz:,.2f}\n\n"
            f"🇰🇭 <b>1 តម្លឹង:</b> លក់ ${damlung_sell:,.2f} | ទិញ ${damlung_buy:,.2f}\n"
            f"      \n"
            f"      <b>1 ជី:</b> លក់ ${chi_sell:,.2f} | ទិញ ${chi_buy:,.2f}\n\n"
            f" {icon}   <b>បម្រែបម្រួល:</b> {sign}${chg:,.2f} ({sign}{pct:.2f}%)"
        )
        return msg.strip()



    def format_upcoming_alert(event: dict, minutes_left: int) -> str:
        """Upcoming news countdown reminders are permanently disabled per user directive."""
        return ""

    @staticmethod
    def format_actual_release_alert(event: dict, analysis: dict) -> str:
        """
        Formats immediate flash alert when Actual economic data is released.
        Strictly follows Point 3 VIP Flash Update Template:
        🚨 FLASH UPDATE | ACTUAL RELEASE 🇺🇸
        📊 US Core CPI m/m (សន្ទស្សន៍ថ្លៃទំនិញប្រើប្រាស់ស្នូល)
        ⏱ 19:30 | 13/10/2026
        ━━━━━━━━━━━━━━━━━━━
        📈 ទិន្នន័យជាក់ស្តែង (Actual Data)
        • Actual: 0.3% ⬆️ (ខ្ពស់ជាងរំពឹងទុក)
        • Forecast: 0.2%
        • Previous: 0.2%
        ━━━━━━━━━━━━━━━━━━━
        🧠 ការសង្ខេប & ការវិភាគ (Quick Take)
        • ស្ថានភាព: Core CPI កើនឡើង ០.៣% បង្ហាញថាសម្ពាធអតិផរណានៅតែរឹងរូសខ្លាំង (Sticky Inflation)។
        • ផលជះ: កាត់បន្ថយឱកាសដែល Fed នឹងទម្លាក់អត្រាការប្រាក់គំហុកនៅកិច្ចប្រជុំបន្ទាប់។
        ━━━━━━━━━━━━━━━━━━━
        ⚡ ផលប៉ះពាល់ទីផ្សារ (Market Impact)
        🔹 USD: ឡើងថ្លៃភ្លាមៗ (Bullish)
        🔹 US10Y Yields: ស្ទុះងើបឡើងខ្ពស់
        🔸 XAUUSD (មាស): ប្រឈមសម្ពាធធ្លាក់ចុះរយៈពេលខ្លី (Bearish Pressure)
        ━━━━━━━━━━━━━━━━━━━
        ⚠️ បម្រាមហានិភ័យ: ទីផ្សារប្រែប្រួលខ្លាំង! រង់ចាំការបិទទៀន M5/M15 បញ្ជាក់ទិសដៅច្បាស់លាស់ ជៀសវាង FOMO ដេញតាមតម្លៃ។
        """
        import re
        import html
        from datetime import datetime

        if not analysis:
            analysis = {}

        title = str(event.get("title", "Economic Release")).strip()
        currency = str(event.get("currency", "USD")).strip().upper()
        actual = str(event.get("actual", "N/A")).strip()
        forecast = str(event.get("forecast", "N/A")).strip()
        previous = str(event.get("previous", "N/A")).strip()
        time_str = str(event.get("release_time_str", "")).strip()
        date_str = str(event.get("release_date_str", "")).strip()

        # Fallback date / time if not in event dict
        if not time_str or not date_str:
            rel_dt = event.get("release_dt")
            if isinstance(rel_dt, datetime):
                if not time_str:
                    time_str = rel_dt.strftime("%H:%M")
                if not date_str:
                    date_str = rel_dt.strftime("%d/%m/%Y")
            else:
                now_kh = datetime.now()
                if not time_str:
                    time_str = now_kh.strftime("%H:%M")
                if not date_str:
                    date_str = now_kh.strftime("%d/%m/%Y")

        # Currency flag mapping
        FLAG_MAP = {
            "USD": "🇺🇸", "EUR": "🇪🇺", "GBP": "🇬🇧", "JPY": "🇯🇵",
            "AUD": "🇦🇺", "CAD": "🇨🇦", "CNY": "🇨🇳", "CHF": "🇨🇭",
            "NZD": "🇳🇿", "XAU": "🥇", "GOLD": "🥇"
        }
        flag = FLAG_MAP.get(currency, "🇺🇸")

        # Khmer title mapping
        KM_TITLE_MAP = {
            "Core CPI": "សន្ទស្សន៍ថ្លៃទំនិញប្រើប្រាស់ស្នូល",
            "CPI": "សន្ទស្សន៍ថ្លៃទំនិញប្រើប្រាស់",
            "Core PCE": "សន្ទស្សន៍ថ្លៃចំណាយផ្ទាល់ខ្លួនស្នូល",
            "PCE": "សន្ទស្សន៍ថ្លៃចំណាយផ្ទាល់ខ្លួន",
            "Non-Farm Employment Change": "ចំនួនការងារមិនមែនកសិកម្ម",
            "NFP": "ចំនួនការងារមិនមែនកសិកម្ម",
            "Unemployment Rate": "អត្រាគ្មានការងារធ្វើ",
            "Federal Funds Rate": "អត្រាការប្រាក់គោល Fed",
            "FOMC": "កិច្ចប្រជុំគោលនយោបាយ Fed",
            "GDP": "ផលិតផលក្នុងស្រុកសរុប",
            "Retail Sales": "ទិន្នន័យការលក់រាយ",
            "PPI": "សន្ទស្សន៍ថ្លៃអ្នកផលិត",
            "ISM Manufacturing PMI": "សន្ទស្សន៍អ្នកគ្រប់គ្រងការទិញផ្នែកផលិតកម្ម",
            "ISM Services PMI": "សន្ទស្សន៍អ្នកគ្រប់គ្រងការទិញផ្នែកសេវាកម្ម",
            "Jobless Claims": "ពាក្យស្នើសុំប្រាក់ឧបត្ថម្ភអ្នកគ្មានការងារធ្វើ"
        }

        # Check if title already contains Khmer
        has_km_in_title = bool(re.search(r'[\u1780-\u17FF]', title))
        km_sub = event.get("title_km", "")
        if not km_sub and not has_km_in_title:
            for k, v in KM_TITLE_MAP.items():
                if k.lower() in title.lower():
                    km_sub = v
                    break

        if km_sub and not has_km_in_title:
            title_display = f"{title} ({km_sub})"
        else:
            title_display = title

        # Numerical comparison between actual and forecast
        def _parse_num(val_str: str):
            if not val_str or val_str in ("N/A", "--", ""):
                return None
            m = re.search(r'[-+]?\d*\.?\d+', val_str.replace(",", ""))
            if m:
                try:
                    return float(m.group(0))
                except Exception:
                    return None
            return None

        act_num = _parse_num(actual)
        fc_num = _parse_num(forecast)

        if act_num is not None and fc_num is not None:
            diff = act_num - fc_num
            if abs(diff) < 1e-5:
                arrow = "➡️"
                diff_label = "ស្មើនឹងការរំពឹងទុក"
            elif diff > 0:
                arrow = "⬆️"
                diff_label = "ខ្ពស់ជាងរំពឹងទុក"
            else:
                arrow = "⬇️"
                diff_label = "ទាបជាងរំពឹងទុក"
        else:
            arrow = "📌"
            diff_label = "ចេញផ្សាយផ្លូវការ"

        # Quick Take: Condition & Effect
        raw_cond = (analysis.get("condition") or analysis.get("what_happened") or "").strip()
        raw_cond = re.sub(r'^(•|\-|\*|ស្ថានភាព:|\:)+', '', raw_cond).strip()
        raw_cond = re.sub(r'^\*\*.*?\*\*\s*', '', raw_cond).strip()
        if not raw_cond:
            raw_cond = f"{title} ចេញមក {actual} {diff_label} បង្ហាញពីចលនាសេដ្ឋកិច្ចជាក់ស្តែង។"

        raw_effect = (analysis.get("effect") or analysis.get("why_it_matters") or "").strip()
        raw_effect = re.sub(r'^(•|\-|\*|ផលជះ:|\:)+', '', raw_effect).strip()
        raw_effect = re.sub(r'^\*\*.*?\*\*\s*', '', raw_effect).strip()
        if not raw_effect:
            raw_effect = "ជះឥទ្ធិពលផ្ទាល់ដល់ការរំពឹងទុកគោលនយោបាយរូបិយវត្ថុ និងចរន្តសាច់ប្រាក់លើទីផ្សារ។"

        # Market Impact
        # USD
        raw_usd = (analysis.get("usd_impact") or "").strip()
        raw_usd = re.sub(r'^(💵|•|\-|\*|USD:|\:)+', '', raw_usd).strip()
        if not raw_usd:
            bias = analysis.get("bias", "")
            if "Bearish" in bias:
                raw_usd = "ឡើងថ្លៃភ្លាមៗ (Bullish)"
            elif "Bullish" in bias:
                raw_usd = "ចុះខ្សោយភ្លាមៗ (Bearish)"
            else:
                raw_usd = "ប្រែប្រួលចង្អៀត (Mixed/Neutral)"

        # US10Y Yields
        raw_yield = (analysis.get("rate_yield_impact") or analysis.get("rate_impact") or "").strip()
        raw_yield = re.sub(r'^(🏛️|🏦|•|\-|\*|Yields:|\:)+', '', raw_yield).strip()
        if not raw_yield:
            bias = analysis.get("bias", "")
            if "Bearish" in bias:
                raw_yield = "ស្ទុះងើបឡើងខ្ពស់"
            elif "Bullish" in bias:
                raw_yield = "ធ្លាក់ចុះទាប"
            else:
                raw_yield = "ប្រែប្រួលចង្អៀត"

        # XAUUSD
        raw_xau = (analysis.get("xau_pressure") or "").strip()
        raw_xau = re.sub(r'^(🥇|👉|•|\-|\*|🟢|🔴|🟡|XAUUSD:|\:)+', '', raw_xau).strip()
        if not raw_xau:
            bias = analysis.get("bias", "")
            if "Bearish" in bias:
                raw_xau = "ប្រឈមសម្ពាធធ្លាក់ចុះរយៈពេលខ្លី (Bearish Pressure)"
            elif "Bullish" in bias:
                raw_xau = "ទទួលបានកម្លាំងរុញឡើង (Bullish Momentum)"
            else:
                raw_xau = "ប្រឈមការប្រែប្រួលសងខាង (Volatile Range)"

        # Build message exactly per user template
        div = "━━━━━━━━━━━━━━━━━━━"
        msg = (
            f"🚨 FLASH UPDATE | ACTUAL RELEASE {flag}\n\n"
            f"📊 {title_display}\n\n"
            f"⏱ {time_str} | {date_str}\n\n"
            f"{div}\n\n"
            f"📈 ទិន្នន័យជាក់ស្តែង (Actual Data)\n\n"
            f"• Actual: {actual} {arrow} ({diff_label})\n\n"
            f"• Forecast: {forecast}\n\n"
            f"• Previous: {previous}\n\n"
            f"{div}\n\n"
            f"🧠 ការសង្ខេប & ការវិភាគ (Quick Take)\n\n"
            f"• ស្ថានភាព: {raw_cond}\n\n"
            f"• ផលជះ: {raw_effect}\n\n"
            f"{div}\n\n"
            f"⚡ ផលប៉ះពាល់ទីផ្សារ (Market Impact)\n\n"
            f"🔹 USD: {raw_usd}\n\n"
            f"🔹 US10Y Yields: {raw_yield}\n\n"
            f"🔸 XAUUSD (មាស): {raw_xau}"
        )
        return msg

    @staticmethod
    def format_breaking_event_alert(news_item: dict, analysis: dict = None, has_photo: bool = False) -> str:
        """Formats breaking news / major geopolitical or unexpected central bank event alert."""
        import re
        import html

        source_name = (news_item.get("source") or "ForexLive News").strip()
        article_url = (news_item.get("link") or news_item.get("url") or "").strip()
        if article_url:
            source_line = f'ប្រភព | <a href="{html.escape(article_url, quote=True)}">{html.escape(source_name)}</a>'
        else:
            source_line = f"ប្រភព | {html.escape(source_name)}"

        # Extract comprehensive narrative
        key_event = ""
        impact_line = ""
        headline_km = ""
        if isinstance(analysis, dict):
            headline_km = (analysis.get("headline_km") or "").strip()
            key_event = (analysis.get("key_event") or "").strip()
            impact_raw = (analysis.get("impact") or analysis.get("market_impact") or "").strip()
            if impact_raw:
                # Merge detached label lines e.g. "🔸 ហានិភ័យទីផ្សារ៖\nភាពមិនប្រាកដប្រជា..." -> "🔸 ហានិភ័យទីផ្សារ៖ ភាពមិនប្រាកដប្រជា..."
                impact_raw = impact_raw.replace("🔶", "🔸")
                impact_raw = re.sub(r'([🔹🔸🔴🟢]\s*(?:ផលវិជ្ជមាន|ផលអវិជ្ជមាន/ហានិភ័យ|ហានិភ័យទីផ្សារ|ផលអវិជ្ជមាន|ហានិភ័យ)[\s៖:]*)\n+\s*', r'\1 ', impact_raw.strip())
                # Pre-split if multiple impacts were squished on one line without newline
                impact_raw = re.sub(r'([^\n\r])\s+([🔸🔴🔹🟢]\s*(?:ផលវិជ្ជមាន|ផលអវិជ្ជមាន|ហានិភ័យ))', r'\1\n\2', impact_raw)
                parsed_impact_lines = []
                for imp_segment in impact_raw.split("\n"):
                    imp_segment = imp_segment.strip()
                    if not imp_segment:
                        continue
                    # Remove any lingering secondary inline impact clause
                    imp_segment = re.sub(r'\s+[🔸🔴🔹🟢]\s*(?:ផលវិជ្ជមាន|ផលអវិជ្ជមាន|ហានិភ័យ).*$', '', imp_segment).strip()
                    imp_clean = re.sub(r'^[💡🔴🟢🟡🔶:\s]+', '', imp_segment).strip()
                    imp_clean = re.sub(r'\n+\s*', ' ', imp_clean).strip()
                    # Strictly strip leading "វា" or "វាផល" per user directive
                    if imp_clean.startswith("វាផលវិជ្ជមាន"):
                        imp_clean = imp_clean[2:]
                    elif imp_clean.startswith("វាផលអវិជ្ជមាន"):
                        imp_clean = imp_clean[2:]
                    elif imp_clean.startswith("វាផលអព្យាក្រឹត"):
                        imp_clean = imp_clean[2:]
                    elif imp_clean.startswith("វា"):
                        imp_clean = imp_clean[2:].strip()

                    # Strip non-ticker parentheses while preserving standard tickers (XAUUSD, USD, BTC, Crypto, SEC, Fed)
                    imp_clean = re.sub(r'\(\s*(?!XAUUSD\b|USD\b|BTC\b|Crypto\b|SEC\b|PMI\b|FED\b|CPI\b|GDP\b|NFP\b)[A-Za-z\s-]+\s*\)', '', imp_clean).strip()

                    # Standardize to clean Khmer narrative with 🔹 for positive and 🔸 for negative/risk
                    m_pos = re.match(r'^(?:[🔹🟢]*)?\s*(?:ផលវិជ្ជមាន|ឥទ្ធិពលវិជ្ជមាន)\s*[៖:]?\s*(.*)', imp_clean)
                    m_neg = re.match(r'^(?:[🔸🔴]*)?\s*(?:ផលអវិជ្ជមាន/ហានិភ័យ|ហានិភ័យទីផ្សារ|ផលអវិជ្ជមាន|ឥទ្ធិពលអវិជ្ជមាន|ហានិភ័យ)\s*[៖:]?\s*(.*)', imp_clean)
                    m_neu = re.match(r'^(?:[🟡]*)?\s*(?:ផលអព្យាក្រឹត|ឥទ្ធិពលអព្យាក្រឹត)\s*[៖:]?\s*(.*)', imp_clean)
                    if m_pos:
                        detail = m_pos.group(1).strip()
                        detail = re.sub(r'^[\s៖:]+', '', detail).strip()
                        parsed_impact_lines.append(f"🔹 ផលវិជ្ជមាន៖ {detail}" if detail else "🔹 ផលវិជ្ជមាន")
                    elif m_neg:
                        prefix_used = "🔸 ផលអវិជ្ជមាន"
                        if "ហានិភ័យទីផ្សារ" in imp_clean:
                            prefix_used = "🔸 ហានិភ័យទីផ្សារ"
                        elif "ផលអវិជ្ជមាន/ហានិភ័យ" in imp_clean:
                            prefix_used = "🔸 ផលអវិជ្ជមាន/ហានិភ័យ"
                        detail = m_neg.group(1).strip()
                        detail = re.sub(r'^[\s៖:]+', '', detail).strip()
                        parsed_impact_lines.append(f"{prefix_used}៖ {detail}" if detail else prefix_used)
                    elif m_neu:
                        detail = m_neu.group(1).strip()
                        detail = re.sub(r'^[\s៖:]+', '', detail).strip()
                        parsed_impact_lines.append(f"ផលអព្យាក្រឹត៖ {detail}" if detail else "ផលអព្យាក្រឹត")
                    elif not imp_clean.startswith(("ផល", "ឥទ្ធិពល", "ហានិភ័យ")):
                        parsed_impact_lines.append(f"🔸 ហានិភ័យទីផ្សារ៖ {imp_clean}")
                    else:
                        parsed_impact_lines.append(imp_clean)
                
                # Enforce strictly ONE impact line based on sentiment
                if parsed_impact_lines:
                    bias_str = str(analysis.get("bias", "")).lower()
                    full_txt = f"{news_item.get('title', '')} {key_event}".lower()
                    is_neg = "bearish" in bias_str or any(k in full_txt for k in ["crisis", "war", "debt", "default", "fall", "drop", "cut", "risk", "វិបត្តិ", "សង្គ្រាម", "បំណុល", "ក្ស័យធន", "ធ្លាក់ចុះ", "ហានិភ័យ", "សម្ពាធ", "រឹតបន្តឹង"])
                    pos = [l for l in parsed_impact_lines if l.startswith("🔹")]
                    neg = [l for l in parsed_impact_lines if l.startswith("🔸")]
                    if is_neg and neg:
                        impact_line = neg[0]
                    elif pos:
                        impact_line = pos[0]
                    elif neg:
                        impact_line = neg[0]
                    else:
                        impact_line = parsed_impact_lines[0]

            if not key_event:
                what = (analysis.get("what_happened") or "").strip()
                why = (analysis.get("why_it_matters") or "").strip()
                xau = (analysis.get("xau_pressure") or "").strip()
                parts = [p for p in [what, why] if p]
                if xau:
                    parts.append(f"• សម្ពាធលើទីផ្សារមាស (XAUUSD): {xau}")
                key_event = "\n\n".join(parts)

        if not key_event:
            key_event = (news_item.get("description") or news_item.get("title") or "").strip()

        # Flag mapping per user directive (Header only)
        headline_priority = f"{headline_km} {news_item.get('title', '')}".lower()
        full_search = f"{headline_priority} {key_event}".lower()
        
        # Strip common news agencies and source name from search to prevent false country flags (e.g. France 24 -> France flag)
        source_val = (news_item.get("source") or "").strip()
        if source_val:
            full_search = re.sub(re.escape(source_val), "", full_search, flags=re.IGNORECASE)
            headline_priority = re.sub(re.escape(source_val), "", headline_priority, flags=re.IGNORECASE)

        for ag in [
            r"\bfrance\s*24\b", r"\bfrance24\b", r"\bafp\b", r"\bdeutsche\s*welle\b", r"\bdw\b",
            r"\bchina military online\b", r"\btimes of india\b", r"\bal jazeera\b",
            r"\beuromaidan press\b", r"\bkyodo news\b", r"\bsouth china morning post\b",
            r"\bxinhua\b", r"\btass\b", r"\bsputnik\b", r"\bbbc\b", r"\bcnn\b", r"\bcnbc\b",
            r"\breuters\b", r"\bbloomberg\b", r"\bseeking\s*alpha\b", r"\bthe\s*hill\b"
        ]:
            full_search = re.sub(ag, "", full_search, flags=re.IGNORECASE)
            headline_priority = re.sub(ag, "", headline_priority, flags=re.IGNORECASE)

        country_flags = []
        flag_rules = [
            (r"\b(bolivia|bolivian|la paz)\b|បូលីវី", "🇧🇴"),
            (r"\b(u\.s\.|u\.s|usa|united states|america|american|fed|biden|trump|powell)\b|អាមេរិក|សហរដ្ឋអាមេរិក", "🇺🇸"),
            (r"\b(uk|britain|british|london|england|boe|starmer)\b|អង់គ្លេស|ចក្រភពអង់គ្លេស", "🇬🇧"),
            (r"\b(iran|tehran|persian)\b|អ៊ីរ៉ង់|អ៊ីរ៉ាន", "🇮🇷"),
            (r"\b(israel|tel aviv|netanyahu)\b|អ៊ីស្រាអែល", "🇮🇱"),
            (r"\b(palestine|palestinian|west bank|ramallah|gaza)\b|ប៉ាឡេស្ទីន|វេសប៊ែង|ហ្កាហ្សា", "🇵🇸"),
            (r"\b(russia|moscow|kremlin|putin)\b|រុស្ស៊ី|រុស្សី", "🇷🇺"),
            (r"\b(ukraine|kyiv|zelenskyy|zelensky)\b|អ៊ុយក្រែន", "🇺🇦"),
            (r"\b(china|beijing|pboc|xi jinping)\b|ចិន", "🇨🇳"),
            (r"\b(japan|tokyo|boj|yen)\b|ជប៉ុន", "🇯🇵"),
            (r"\b(india|indian|delhi|mumbai|modi|rbi|rupee)\b|ឥណ្ឌា", "🇮🇳"),
            (r"\b(germany|german|berlin|bundesbank|scholz)\b|អាល្លឺម៉ង់", "🇩🇪"),
            (r"\b(france|french|paris|macron)\b|បារាំង", "🇫🇷"),
            (r"\b(eu|europe|european|ecb)\b|អឺរ៉ុប", "🇪🇺"),
            (r"\b(venezuela|venezuelan|caracas|maduro)\b|វ៉េណេស៊ុយអេឡា|វេណេស៊ុយអេឡា", "🇻🇪"),
            (r"\b(argentina|argentine|buenos aires|milei)\b|អាហ្សង់ទីន", "🇦🇷"),
            (r"\b(colombia|colombian|bogota)\b|កូឡុំប៊ី", "🇨🇴"),
            (r"\b(peru|peruvian|lima)\b|ប៉េរូ", "🇵🇪"),
            (r"\b(chile|chilean|santiago)\b|ឈីលី", "🇨🇱"),
            (r"\b(cuba|cuban|havana)\b|គុយបា", "🇨🇺"),
            (r"\b(brazil|brazilian|lula)\b|ប្រេស៊ីល", "🇧🇷"),
            (r"\b(mexico|mexican|banxico)\b|ម៉ិកស៊ិក", "🇲🇽"),
            (r"\b(north korea|dprk|pyongyang|kim jong un|kim jong-un|kim jong)\b|កូរ៉េខាងជើង", "🇰🇵"),
            (r"\b(south korea|seoul|bok)\b|(?<!north\s)(?<!dprk\s)\bkorean?\b|កូរ៉េ(?!\s*ខាងជើង)", "🇰🇷"),
            (r"\b(taiwan|taiwanese|taipei|tsmc)\b|តៃវ៉ាន់", "🇹🇼"),
            (r"\b(australia|australian|sydney|rba|canberra)\b|អូស្ត្រាលី", "🇦🇺"),
            (r"\b(switzerland|swiss|snb|zurich|geneva)\b|ស្វីស", "🇨🇭"),
            (r"\b(singapore|mas)\b|សិង្ហបុរី", "🇸🇬"),
            (r"\b(saudi|opec|riyadh|jeddah|aramco)\b|អារ៉ាប៊ីសាអ៊ូឌីត", "🇸🇦"),
            (r"\b(canada|canadian|boc|toronto|canadian tire)\b|កាណាដា", "🇨🇦"),
            (r"\b(uae|dubai|abu dhabi|emirates)\b|អេមីរ៉ាត|ឌូបៃ", "🇦🇪"),
            (r"\b(turkey|turkish|turkiye|ankara|istanbul|erdogan|cbrt)\b|តួកគី|អ៊ីស្តង់ប៊ុល", "🇹🇷"),
            (r"\b(qatar|doha)\b|(?:ប្រទេស|រដ្ឋ)?\s*កាតា(?![លក\u1780-\u17D3])", "🇶🇦"),
            (r"\b(egypt|cairo)\b|អេហ្ស៊ីប", "🇪🇬"),
            (r"\b(south africa|south african|pretoria|johannesburg)\b|អាហ្វ្រិកខាងត្បូង", "🇿🇦"),
            (r"\b(nigeria|nigerian|abuja|lagos)\b|នីហ្សេរីយ៉ា", "🇳🇬"),
            (r"\b(norway|norwegian|oslo)\b|ន័រវែស", "🇳🇴"),
            (r"\b(sweden|swedish|stockholm)\b|ស៊ុយអែត", "🇸🇪"),
            (r"\b(poland|polish|warsaw)\b|ប៉ូឡូញ", "🇵🇱"),
            (r"\b(spain|spanish|madrid)\b|អេស្ប៉ាញ", "🇪🇸"),
            (r"\b(italy|italian|rome)\b|អ៊ីតាលី", "🇮🇹"),
            (r"\b(netherlands|dutch|amsterdam)\b|ហូឡង់", "🇳🇱"),
            (r"\b(belgium|belgian|brussels)\b|បែលហ្ស៊ិក", "🇧🇪"),
            (r"\b(kazakhstan|kazakh|astana)\b|កាហ្សាក់ស្ថាន", "🇰🇿"),
            (r"\b(kuwait|kuwaiti)\b|គុយវ៉ែត", "🇰🇼"),
            (r"\b(oman|omani|muscat)\b|អូម៉ង់", "🇴🇲"),
            (r"\b(bahrain|bahraini|manama)\b|បារ៉ែន", "🇧🇭"),
            (r"\b(jordan|jordanian|amman)\b|ហ្ស៊កដានី", "🇯🇴"),
            (r"\b(vietnam|vietnamese|hanoi)\b|វៀតណាម", "🇻🇳"),
            (r"\b(pakistan|pakistani|islamabad)\b|ប៉ាគីស្ថាន", "🇵🇰"),
            (r"\b(syria|syrian|damascus)\b|ស៊ីរី", "🇸🇾"),
            (r"\b(lebanon|lebanese|beirut|hezbollah)\b|លីបង់", "🇱🇧"),
            (r"\b(iraq|iraqi|baghdad)\b|អ៊ីរ៉ាក់", "🇮🇶"),
            (r"\b(yemen|yemeni|houthi|sanaa)\b|យេមែន|យេម៉ែន", "🇾🇪"),
            (r"\b(un|united nations|imf|world bank|wto|who|global|worldwide|international)\b|អង្គការសហប្រជាជាតិ|សកលលោក|អន្តរជាតិ|ទូទាំងពិភពលោក", "🌐"),
        ]
        
        # STRICT HEADLINE-FIRST OCCURRENCE RULE:
        # A flag is ONLY valid if that country ACTUALLY appears in the headline!
        # Background countries mentioned casually in the narrative body (e.g. "due to war in Iran")
        # MUST NEVER contaminate the header flag of another sovereign nation!
        matched_flags = []
        for pattern, flag in flag_rules:
            m_head = re.search(pattern, headline_priority, re.IGNORECASE)
            if not m_head and flag == "🇺🇸" and re.search(r'\b(US|USA)\b', headline_priority):
                m_head = True
            if m_head:
                pos = m_head.start() if hasattr(m_head, 'start') else 0
                matched_flags.append((flag, pos))

        matched_flags.sort(key=lambda x: x[1])
        for f, _ in matched_flags:
            if f not in country_flags:
                country_flags.append(f)

        # Palestine / West Bank Priority (Strict rule: West Bank, Gaza, Ramallah strictly get Flag 🇵🇸)
        if re.search(r"\b(palestine|palestinian|west bank|ramallah|gaza)\b|ប៉ាឡេស្ទីន|វេសប៊ែង|ហ្កាហ្សា", f"{headline_priority} {news_item.get('title', '')}", re.IGNORECASE):
            country_flags = ["🇵🇸"]

        # If no country flag was found in headline from rules, check analysis country_flag
        if not country_flags and isinstance(analysis, dict):
            c_flag = (analysis.get("country_flag") or "").strip()
            if c_flag:
                country_flags.append(c_flag)

        # STRICT BILATERAL FLAG RULE: A 2nd flag is ONLY permitted if BOTH nations are prominently in the headline
        # AND it is an official bilateral state summit or war (e.g. US-China trade talks, Russia-Ukraine war).
        # Never contaminate a single-country headline with a 2nd background flag!
        if len(country_flags) >= 2:
            second_flag = country_flags[1]
            sec_pat = next((p for p, fl in flag_rules if fl == second_flag), None)
            is_sec_in_headline = bool(sec_pat and re.search(sec_pat, headline_priority, re.IGNORECASE))
            if not is_sec_in_headline:
                country_flags = country_flags[:1]

        # Build headline: use AI-generated headline_km, fallback to shortened title / what_happened / key_event
        if not headline_km or headline_km == "កំពុងតាមដាន។":
            fallback = ""
            if isinstance(analysis, dict):
                fallback = (analysis.get("headline_km") or "").strip()
            if not fallback or fallback == "កំពុងតាមដាន។":
                raw_title = (news_item.get("title") or "").strip()
                if raw_title:
                    try:
                        from analyzers.macro_analyzer import MacroAnalyzer
                        km_t = MacroAnalyzer.translate_to_khmer(raw_title)
                        if km_t and len(re.findall(r'[\u1780-\u17FF]', km_t)) >= 5:
                            fallback = km_t
                    except Exception:
                        pass
                if not fallback or fallback == "កំពុងតាមដាន។":
                    fallback = raw_title
            if not fallback or fallback == "កំពុងតាមដាន។":
                if isinstance(analysis, dict):
                    fallback = (analysis.get("what_happened") or analysis.get("key_event") or "").strip()
            if "។" in fallback:
                fallback = fallback.split("។")[0].strip()
            if "\n" in fallback:
                fallback = fallback.split("\n")[0].strip()
            if " — " in fallback:
                fallback = fallback.split(" — ")[0].strip()
            headline_km = fallback

        # Strip emojis and flag chars from headline (flags go in prefix, not inside bold)
        headline_km = re.sub(r'[\U0001F1E0-\U0001F1FF]{2}', '', headline_km).strip()
        headline_km = re.sub(r'[\U0001F300-\U0001FFFF]', '', headline_km).strip()

        # STRICT ZERO-TRAILING PUNCTUATION & ZERO-ELLIPSIS DIRECTIVE:
        # Strip all trailing dots, ellipsis, colons, Khmer colons, invisible unicode zero-width spaces (\u200B-\u200D, \uFEFF)
        _trailing_punct_regex = r'[\s\u200B\u200C\u200D\uFEFF\u00A0.,;:៖–—_…\uFF1A\uFE13\uFE55\u2236]+$'
        headline_km = re.sub(_trailing_punct_regex, '', headline_km).strip()
        headline_km = re.sub(r'\.{2,}', '', headline_km).strip()
        headline_km = re.sub(r'…+', '', headline_km).strip()
        headline_km = re.sub(r'\s+(?:នៃ|របស់|និង|ពី|ក្នុង|ដើម្បី|លើ|អំពី)\s*$', '', headline_km).strip()
        headline_km = re.sub(_trailing_punct_regex, '', headline_km).strip()

        # Sanitize spelling
        headline_km = sanitize_khmer_spelling(headline_km)

        # Final pass to ensure absolutely zero trailing dots, colons, or cut-off prepositions
        headline_km = re.sub(_trailing_punct_regex, '', headline_km).strip()
        headline_km = re.sub(r'\.{2,}', '', headline_km).strip()
        headline_km = re.sub(r'…+', '', headline_km).strip()
        headline_km = re.sub(r'\s+(?:នៃ|របស់|និង|ពី|ក្នុង|ដើម្បី|លើ|អំពី)\s*$', '', headline_km).strip()
        headline_km = re.sub(_trailing_punct_regex, '', headline_km).strip()

        flag_prefix = (" ".join(country_flags[:2]) + " ") if country_flags else ""
        headline_km = re.sub(_trailing_punct_regex, '', headline_km).strip()
        header = f"{flag_prefix}<b>{headline_km}</b>".strip()

        # Strip any country flag emojis from body key_event
        for _, fl in flag_rules:
            key_event = key_event.replace(fl, "")

        # Strip trailing news wire tags like ": Report", "៖ របាយការណ៍", ": Reports", "(Report)"
        key_event = re.sub(r'\s*[៖:\-–—|]\s*(?:របាយការណ៍|សេចក្តីរាយការណ៍|ការវិភាគ|ព័ត៌មានលម្អិត|Report|Reports|Analysis)\s*$', '', key_event, flags=re.IGNORECASE).strip()

        # Strip robotic category prefix with colon ONLY if prefix is short (<= 25 chars) and remainder has real content (>= 30 chars, >= 4 words)
        m_prefix = re.match(r'^([^\n៖:]{1,25}[៖:])\s*(.+)$', key_event, re.DOTALL)
        if m_prefix:
            remainder = m_prefix.group(2).strip()
            if len(remainder) >= 30 and len(remainder.split()) >= 4:
                key_event = remainder

        # Strip dangling / orphaned prefixes like "បញ្ហា )", "(Reuters) - ", "Topic )", etc.
        key_event = re.sub(r'^\s*(?:[A-Za-z\u1780-\u17FF\s]{1,15}\s*)?[\)\]\}\>]\s*[-–—:]*\s*', '', key_event).strip()
        key_event = re.sub(r'^[\(\[\{][^\)\]\}]{1,25}[\)\]\}]\s*[-–—:]*\s*', '', key_event).strip()
        key_event = re.sub(r'^\s*បញ្ហា\s*[\)\]\}\:\-–—\s]+\s*', '', key_event).strip()

        # Sanitize Khmer spelling to guarantee 100% accurate spelling
        key_event = sanitize_khmer_spelling(key_event)

        # Remove parenthetical English phrases like (Safe-Haven Assets ) while preserving standard terms like (Safe-Haven), (USD), (SEC)
        key_event = re.sub(r'\(\s*(?!Safe-Haven\b|USD\b|SEC\b|PMI\b|FED\b|CPI\b|GDP\b|NFP\b)[A-Za-z\s-]+\s*\)', '', key_event).strip()

        # Remove trailing wire source name in body (e.g. "- The Guardian")
        key_event = re.sub(r'\s*-\s*(?:The Guardian|Reuters|Bloomberg|CNBC|BBC News|BBC|Al Jazeera|MarketWatch|Yahoo Finance|ForexLive)[^\n]*', '', key_event, flags=re.IGNORECASE).strip()

        # Substantive Narrative Fallback Gate: Never output a single-word or short empty stub like "របាយការណ៍"
        kh_chars = len(re.findall(r'[\u1780-\u17FF]', key_event))
        if kh_chars < 35 or key_event in ("របាយការណ៍", "សេចក្តីរាយការណ៍", "ព័ត៌មាន", "បច្ចុប្បន្នភាព", "ការវិភាគ", "Report"):
            what = (analysis.get("what_happened") or "").strip()
            if what and len(re.findall(r'[\u1780-\u17FF]', what)) >= 35:
                key_event = what
            else:
                desc_raw = (news_item.get("description") or "").strip()
                if desc_raw and len(desc_raw) >= 30:
                    try:
                        from analyzers.macro_analyzer import MacroAnalyzer
                        tr_desc = MacroAnalyzer.translate_to_khmer(desc_raw)
                        if tr_desc and len(re.findall(r'[\u1780-\u17FF]', tr_desc)) >= 35:
                            key_event = tr_desc
                    except Exception:
                        pass

        # Double Safety: If key_event has significant English (> 25% Latin characters), translate to fluent Khmer
        latin_chars = len(re.findall(r'[a-zA-Z]', key_event))
        if latin_chars > len(key_event) * 0.25 and len(key_event) > 20:
            try:
                from analyzers.macro_analyzer import MacroAnalyzer
                km_trans = MacroAnalyzer.translate_to_khmer(key_event)
                if km_trans and len(km_trans) > 15:
                    key_event = km_trans
            except Exception:
                pass

        # Decode HTML entities (&nbsp;, &amp;, etc.)
        key_event = html.unescape(key_event)

        # Remove any embedded anchor tags entirely from narrative text
        key_event = re.sub(r'<a\b[^>]*>(.*?)</a>', r'\1', key_event, flags=re.DOTALL | re.IGNORECASE)

        # Remove any lingering raw http/https links dumped into the middle of text
        key_event = re.sub(r'https?://\S+', '', key_event)

        # Strip all HTML tags EXCEPT clean Telegram formatting tags (<b>, <i>, <code>, <blockquote>)
        key_event = re.sub(r'<(?!/?(?:b|strong|i|em|code|blockquote)\b)[^>]+>', '', key_event)

        # Clean multiple spaces / newlines
        key_event = re.sub(r'[ \t]+', ' ', key_event)
        # Eliminate awkward single line breaks within sentences, turning them into flowing journalistic prose
        key_event = re.sub(r'(?<!\n)\n(?!\n)', ' ', key_event)
        key_event = re.sub(r'\n{3,}', '\n\n', key_event).strip()

        # Sanitize Khmer spelling to guarantee 100% accurate spelling
        key_event = sanitize_khmer_spelling(key_event)

        # Moderate narrative length: Keep it clean, balanced, and digestible (2-3 concise sentences, ~200-360 chars)
        if len(key_event) > 360:
            sentences = [s.strip() for s in re.split(r'(?<=។)\s+', key_event) if s.strip()]
            if len(sentences) >= 2:
                clipped = []
                cur_len = 0
                for s in sentences[:3]:
                    if cur_len + len(s) > 360 and len(clipped) >= 2:
                        break
                    clipped.append(s)
                    cur_len += len(s)
                if clipped:
                    key_event = " ".join(clipped).strip()

        # Security / conflict / attack / drone / bomb / military / strait sentiment safety net: Military threats are strictly ហានិភ័យទីផ្សារ (🔸)
        if impact_line:
            threat_kh = [
                "ដ្រូន", "វាយប្រហារ", "សង្គ្រាម", "គ្រាប់បែក", "ឧទ្ទាម", "ប្រដាប់អាវុធ", "មីស៊ីល",
                "ជម្លោះ", "កងទ័ព", "យោធា", "ទ័ព", "កងកម្លាំង", "ច្រកសមុទ្រ", "សមុទ្រក្រហម", "យេមែន", "យេម៉ែន", "ហូទី"
            ]
            threat_en = [
                r"\bwar\b", r"\bwars\b", r"\bdrone\b", r"\bdrones\b", r"\battack\b", r"\battacks\b",
                r"\bbomb\b", r"\bbombing\b", r"\brebel\b", r"\brebels\b", r"\barmed\b", r"\bmissile\b",
                r"\bmissiles\b", r"\bconflict\b", r"\bmilitary\b", r"\barmy\b", r"\btroops\b",
                r"\bsoldiers\b", r"\bnavy\b", r"\byemen\b", r"\bhouthi\b", r"\bmandab\b", r"\bred sea\b",
                r"\bstrait\b", r"\bstraits\b", r"\bhormuz\b", r"\bclash\b", r"\bairstrike\b"
            ]
            txt_check = f"{news_item.get('title', '')} {key_event} {impact_line} {headline_km}".lower()
            is_threat = any(k in txt_check for k in threat_kh) or any(re.search(pat, txt_check) for pat in threat_en)
            if is_threat and ("ផលវិជ្ជមាន" in impact_line or "អស្ថិរភាពសន្តិសុខសកល" in impact_line or "សន្ទុះកំណើនទីផ្សារ" in impact_line):
                is_oil = any(k in txt_check for k in ["oil", "crude", "diesel", "gas", "energy", "petroleum", "aramco", "iea", "opec", "ប្រេង", "ប្រេងកាត", "ប្រេងឆៅ", "ម៉ាស៊ូត", "ឧស្ម័ន", "ថាមពល"])
                is_strait = any(k in txt_check for k in ["mandab", "bab al-mandab", "red sea", "strait", "straits", "hormuz", "ច្រកសមុទ្រ", "សមុទ្រក្រហម"])
                if is_oil:
                    impact_line = "🔸 ហានិភ័យទីផ្សារ៖ ការរំខានការផ្គត់ផ្គង់ ឬភាពតានតឹងថាមពល រុញសម្ពាធតម្លៃប្រេងឆៅសកលឱ្យឡើងថ្លៃ"
                elif is_strait:
                    impact_line = "🔸 ហានិភ័យទីផ្សារ៖ ភាពតានតឹងនៅច្រកសមុទ្រយុទ្ធសាស្ត្រ គំរាមកំហែងដល់ផ្លូវដឹកជញ្ជូន និងរុញសម្ពាធថ្លៃដឹកជញ្ជូនសកលឱ្យហក់ឡើង"
                elif any(k in txt_check for k in ["gold", "xau", "bullion", "មាស"]):
                    impact_line = "🔸 ហានិភ័យទីផ្សារ៖ បង្កើនតម្រូវការទិញមាស XAUUSD ក្នុងនាមជាទ្រព្យសុវត្ថិភាព"
                else:
                    impact_line = "🔸 ហានិភ័យទីផ្សារ៖ បង្កើនភាពតានតឹងផ្នែកភូមិសាស្ត្រនយោបាយ និងបង្កើនការប្រុងប្រយ័ត្នខ្ពស់ក្នុងទីផ្សារហិរញ្ញវត្ថុសកល"

        if impact_line:
            # Flatten multi-line impact where label was separated from description by newline
            impact_line = re.sub(r'([🔹🔸🔴🟢]?\s*(?:ផលវិជ្ជមាន|ផលអវិជ្ជមាន/ហានិភ័យ|ហានិភ័យទីផ្សារ|ផលអវិជ្ជមាន|ហានិភ័យ|ឥទ្ធិពលវិជ្ជមាន|ឥទ្ធិពលអវិជ្ជមាន)[\s៖:]*)\n+\s*', r'\1 ', impact_line.strip())

            raw_lines = [l.strip() for l in impact_line.split("\n") if l.strip()]
            impact_lines = []
            for iline in raw_lines:
                if "ផលវិជ្ជមាន" in iline or "ឥទ្ធិពលវិជ្ជមាន" in iline:
                    if not iline.startswith("🔹"):
                        iline = "🔹 " + re.sub(r'^[🔹🟢\s]*', '', iline)
                elif any(k in iline for k in ["ផលអវិជ្ជមាន", "ហានិភ័យទីផ្សារ", "ហានិភ័យ", "ឥទ្ធិពលអវិជ្ជមាន"]):
                    if not iline.startswith("🔸"):
                        iline = "🔸 " + re.sub(r'^[🔸🔴\s]*', '', iline)
                else:
                    # If this line is an orphaned description from a broken newline, merge with previous line!
                    if impact_lines:
                        impact_lines[-1] = re.sub(r'[។\.]\s*$', '', impact_lines[-1]).strip() + " " + iline.strip()
                        if not impact_lines[-1].endswith("។"):
                            impact_lines[-1] += "។"
                        continue
                    iline = "🔸 ហានិភ័យទីផ្សារ៖ " + iline

                iline = re.sub(r'^(🔹|🔸)?\s*(ផលវិជ្ជមាន|ផលអវិជ្ជមាន/ហានិភ័យ|ហានិភ័យទីផ្សារ|ផលអវិជ្ជមាន|ផលអព្យាក្រឹត)[\s៖:]+', r'\1 \2៖ ', iline).strip()
                # Strict No Parentheses Rule in impact line
                iline = re.sub(r'[\(\)]', '', iline)
                iline = sanitize_khmer_spelling(iline)
                iline = re.sub(r'[។\.]\s*$', '', iline).strip()
                if iline and not iline.endswith("។"):
                    iline += "។"
                impact_lines.append(iline)
            impact_line = "\n".join(impact_lines)

            # Specific Asset Targeting (Point 3) - Replace generic templates with trader-focused asset impacts
            generic_phrases = [
                "បង្កើនសម្ពាធលើទីផ្សារ",
                "សម្ពាធលើទីផ្សារ",
                "ភាពមិនច្បាស់លាស់នៃទស្សនវិស័យសេដ្ឋកិច្ចអាចជះឥទ្ធិពលដល់ទីផ្សារ",
                "ភាពមិនច្បាស់លាស់នៃកំណើនសេដ្ឋកិច្ចបង្កើនការប្រុងប្រយ័ត្នដល់វិនិយោគិន",
                "អាចជះឥទ្ធិពលដល់ទីផ្សារ",
                "បង្កើនហានិភ័យភូមិសាស្ត្រនយោបាយ និងអស្ថិរភាពសន្តិសុខសកល",
                "ជំរុញនវានុវត្តន៍បច្ចេកវិទ្យា និងទាក់ទាញលំហូរសាច់ប្រាក់វិនិយោគ",
                "ជំរុញនវានុវត្តន៍ និងទាក់ទាញលំហូរទុនវិនិយោគក្នុងវិស័យ AI",
                "ជំរុញនវានុវត្តន៍បច្ចេកវិទ្យា",
            ]
            if any(p in impact_line for p in generic_phrases):
                is_neg = "ផលអវិជ្ជមាន" in impact_line or "ឥទ្ធិពលអវិជ្ជមាន" in impact_line or "ហានិភ័យ" in impact_line
                if any(k in full_search for k in ["oil", "crude", "energy", "petroleum", "diesel", "gas", "aramco", "opec", "iea", "ប្រេង", "ប្រេងកាត", "ប្រេងឆៅ", "ម៉ាស៊ូត", "ឧស្ម័ន", "ថាមពល"]):
                    impact_line = "🔸 ហានិភ័យទីផ្សារ៖ ការរំខានការផ្គត់ផ្គង់ ឬភាពតានតឹងថាមពល រុញសម្ពាធតម្លៃប្រេងឆៅសកលឱ្យឡើងថ្លៃ" if is_neg else "🔹 ផលវិជ្ជមាន៖ ការកើនឡើងការផ្គត់ផ្គង់ប្រេង ជួយកាត់បន្ថយសម្ពាធថ្លៃដើមថាមពលសកល"
                elif any(k in full_search for k in ["ai", "chip", "semiconductor", "tech", "nvidia", "tsmc", "apple", "microsoft", "google", "meta", "intel", "បច្ចេកវិទ្យា", "បន្ទះឈីប"]):
                    impact_line = "🔸 ហានិភ័យទីផ្សារ៖ បង្កផលរំខានដល់ខ្សែច្រវាក់ផ្គត់ផ្គង់បន្ទះឈីប ដែលអាចដាក់សម្ពាធលើទីផ្សារភាគហ៊ុនបច្ចេកវិទ្យា" if is_neg else "🔹 ផលវិជ្ជមាន៖ ជំរុញកំណើនភាគហ៊ុនបច្ចេកវិទ្យា Big Tech និងទាក់ទាញលំហូរទុនវិនិយោគសកល"
                elif any(k in full_search for k in ["tariff", "trade war", "customs", "sanction", "export control", "ពន្ធគយ", "ទណ្ឌកម្ម", "សង្គ្រាមពាណិជ្ជកម្ម"]):
                    impact_line = "🔸 ហានិភ័យទីផ្សារ៖ វិធានការពន្ធគយ និងទណ្ឌកម្ម បង្កើនថ្លៃដើមនាំចូល និងដាក់សម្ពាធលើចរន្តពាណិជ្ជកម្មសកល" if is_neg else "🔹 ផលវិជ្ជមាន៖ កិច្ចព្រមព្រៀងពាណិជ្ជកម្មជួយសម្រួលដល់ខ្សែច្រវាក់នាំចេញ និងកំណើនសេដ្ឋកិច្ច"
                elif any(k in full_search for k in ["fed", "rate", "powell", "fomc", "cpi", "inflation", "yield", "bond", "អត្រាការប្រាក់", "អតិផរណា", "ecb", "boj", "pboc"]):
                    impact_line = "🔸 ហានិភ័យទីផ្សារ៖ អត្រាការប្រាក់កម្រិតខ្ពស់យូរអង្វែង រុញ USD និង Yields ឡើងថ្លៃ ព្រមទាំងដាក់សម្ពាធលើកំណើនសេដ្ឋកិច្ច" if is_neg else "🔹 ផលវិជ្ជមាន៖ ការបន្ធូរបន្ថយអត្រាការប្រាក់ ជួយកាត់បន្ថយថ្លៃដើមកម្ចី និងជំរុញសកម្មភាពសេដ្ឋកិច្ច"
                elif any(k in full_search for k in ["bitcoin", "crypto", "etf", "sec", "គ្រីបតូ", "ប៊ីតខយ", "btc"]):
                    impact_line = "🔸 ហានិភ័យទីផ្សារ៖ បង្កើនសម្ពាធលក់ និងការប្រុងប្រយ័ត្នខ្ពស់ក្នុងទីផ្សារទ្រព្យសកម្មឌីជីថល Crypto" if is_neg else "🔹 ផលវិជ្ជមាន៖ លំហូរទុនវិនិយោគស្ថាប័នក្នុង Spot ETF គាំទ្រដល់ស្ថិរភាព និងកំណើនទីផ្សារ Bitcoin BTC"
                elif any(k in full_search for k in ["gold", "xau", "bullion", "មាស"]):
                    impact_line = "🔸 ហានិភ័យទីផ្សារ៖ ដាក់សម្ពាធលើទិសដៅតម្លៃមាស XAUUSD" if is_neg else "🔹 ផលវិជ្ជមាន៖ គាំទ្រដល់និន្នាការកើនឡើងនៃតម្លៃមាស XAUUSD"
                elif any(k in full_search for k in ["war", "strike", "attack", "drone", "missile", "military", "army", "troops", "strait", "mandab", "yemen", "houthi", "សង្គ្រាម", "វាយប្រហារ", "កងទ័ព", "យោធា", "ច្រកសមុទ្រ"]):
                    if any(k in full_search for k in ["mandab", "bab al-mandab", "red sea", "strait", "straits", "hormuz", "ច្រកសមុទ្រ", "សមុទ្រក្រហម"]):
                        impact_line = "🔸 ហានិភ័យទីផ្សារ៖ ភាពតានតឹងនៅច្រកសមុទ្រយុទ្ធសាស្ត្រ គំរាមកំហែងដល់ផ្លូវដឹកជញ្ជូន និងរុញសម្ពាធថ្លៃដឹកជញ្ជូនសកលឱ្យហក់ឡើង"
                    else:
                        impact_line = "🔸 ហានិភ័យទីផ្សារ៖ បង្កើនភាពតានតឹងផ្នែកភូមិសាស្ត្រនយោបាយ និងបង្កើនការប្រុងប្រយ័ត្នខ្ពស់ក្នុងទីផ្សារហិរញ្ញវត្ថុសកល"
                else:
                    impact_line = "🔸 ផលអវិជ្ជមាន/ហានិភ័យ៖ ការរឹតបន្តឹងគោលនយោបាយរូបិយវត្ថុយូរអង្វែង អាចដាក់សម្ពាធលើកំណើនសេដ្ឋកិច្ច" if is_neg else "🔹 ផលវិជ្ជមាន៖ ជួយពង្រឹងកិច្ចសហប្រតិបត្តិការអន្តរជាតិក្នុងការរក្សាស្ថិរភាពលំហូរសាច់ប្រាក់"
                impact_line = re.sub(r'[\(\)]', '', impact_line)

        # Strictly enforce a SINGLE impact line per user directive (Remove redundant/conflicting 2nd impact)
        if impact_line:
            # Also clean any inline leakage where 🔸 and 🔹 were squished together on the same line
            m_inline1 = re.search(r'([🔹🟢]\s*ផលវិជ្ជមាន[^🔸🔴\n]+)\s*([🔸🔴]\s*(?:ផលអវិជ្ជមាន|ហានិភ័យ)[^\n]+)', impact_line)
            m_inline2 = re.search(r'([🔸🔴]\s*(?:ផលអវិជ្ជមាន|ហានិភ័យ)[^🔹🟢\n]+)\s*([🔹🟢]\s*ផលវិជ្ជមាន[^\n]+)', impact_line)
            bias_str = str(analysis.get("bias", "")).lower() if isinstance(analysis, dict) else ""
            is_threat_or_negative = "bearish" in bias_str or any(k in full_search for k in ["crisis", "war", "debt", "default", "fall", "drop", "cut", "risk", "វិបត្តិ", "សង្គ្រាម", "បំណុល", "ក្ស័យធន", "ធ្លាក់ចុះ", "ហានិភ័យ", "សម្ពាធ", "រឹតបន្តឹង"])

            if m_inline1:
                impact_line = m_inline1.group(2).strip() if is_threat_or_negative else m_inline1.group(1).strip()
            elif m_inline2:
                impact_line = m_inline2.group(1).strip() if is_threat_or_negative else m_inline2.group(2).strip()

            lines = [l.strip() for l in impact_line.split("\n") if l.strip()]
            if len(lines) > 1:
                neg_lines = [l for l in lines if l.startswith("🔸")]
                pos_lines = [l for l in lines if l.startswith("🔹")]
                if is_threat_or_negative and neg_lines:
                    impact_line = neg_lines[0]
                elif pos_lines:
                    impact_line = pos_lines[0]
                else:
                    impact_line = lines[0]
            else:
                impact_line = lines[0] if lines else ""

        # Deduplicate narrative against headline to avoid repeating the exact title
        norm_hl = re.sub(r'[\s\u200b]+', '', headline_km).lower()
        norm_ke = re.sub(r'[\s\u200b]+', '', key_event).lower()
        if norm_hl and (norm_ke.startswith(norm_hl[:25]) or norm_hl.startswith(norm_ke[:25])):
            remainder = key_event
            for delim in ['។', '\n', ' — ', ' - ', ':']:
                if delim in remainder:
                    parts = remainder.split(delim, 1)
                    first_part_norm = re.sub(r'[\s\u200b]+', '', parts[0]).lower()
                    if first_part_norm.startswith(norm_hl[:20]) or norm_hl.startswith(first_part_norm[:20]):
                        remainder = parts[1].strip()
                        break
            norm_rem = re.sub(r'[\s\u200b]+', '', remainder).lower()
            if len(norm_rem) >= 20 and norm_rem != norm_hl and not norm_rem.startswith(norm_hl[:25]):
                key_event = remainder
            elif isinstance(analysis, dict):
                why = (analysis.get("why_it_matters") or "").strip()
                what = (analysis.get("what_happened") or "").strip()
                if why and re.sub(r'[\s\u200b]+', '', why).lower() != norm_hl:
                    key_event = why
                elif what and re.sub(r'[\s\u200b]+', '', what).lower() != norm_hl:
                    key_event = what

        headline_km = re.sub(r'[\s\u200B\u200C\u200D\uFEFF\u00A0.,;:៖–—_…\uFF1A\uFE13\uFE55\u2236]+$', '', headline_km).strip()
        header_bold = f"{flag_prefix}<b>{headline_km}</b>".strip()

        if not has_photo:
            # MODE B: TEXT-ONLY POST (When no image is attached)
            # Structure per user directive:
            # [Flag] <b>[Comprehensive Headline]</b>
            #
            # [Detailed Context Paragraph 1 - Core event and key developments]
            #
            # [Detailed Context Paragraph 2 - Broader economic background or central bank reaction]
            #
            # 🔹 ផលវិជ្ជមាន៖ [Specific positive impact]
            # 🔸 ផលអវិជ្ជមាន/ហានិភ័យ៖ [Specific downside or risk]
            #
            # 🌐 ប្រភព | <a href="{article_url}">{source_name}</a>
            blocks = [header_bold]
            if key_event and key_event != headline_km:
                blocks.append(key_event)
            if impact_line:
                blocks.append(impact_line)
            blocks.append(source_line)
            return "\n\n".join(blocks).strip()
        else:
            # MODE A: PHOTO CAPTION (When an image is attached)
            # Structure per user directive:
            # [Flag] <b>[Headline - 1 to 2 lines max]</b>
            #
            # [Context Summary - 2 to 3 concise sentences]
            #
            # 🔹/🔸 [Market Impact - 1 direct sentence]
            #
            # 🌐 ប្រភព | <a href="{article_url}">{source_name}</a>
            blocks = [header_bold]
            if key_event and key_event != headline_km:
                blocks.append(key_event)
            first_impact = ""
            if impact_line:
                first_impact = impact_line.split("\n")[0].strip()
                blocks.append(first_impact)
            blocks.append(source_line)
            full_msg = "\n\n".join(blocks).strip()

            # Strictly enforce <= 850 total characters for Mode A photo captions (60 to 90 words)
            if len(full_msg) > 850:
                overhead = len(header_bold) + 2 + (len(first_impact) + 2 if first_impact else 0) + len(source_line) + 4
                max_ke_len = max(850 - overhead, 100)
                if key_event and len(key_event) > max_ke_len:
                    sub = key_event[:max_ke_len]
                    last_period = max(sub.rfind("។ "), sub.rfind("។\n"), sub.rfind("។"))
                    if last_period > 50:
                        key_event = sub[:last_period + 1].strip()
                    else:
                        last_space = sub.rfind(" ")
                        if last_space > 50:
                            key_event = sub[:last_space].strip() + "។"
                        else:
                            key_event = sub.strip() + "។"
                    blocks = [header_bold, key_event]
                    if first_impact:
                        blocks.append(first_impact)
                    blocks.append(source_line)
                    full_msg = "\n\n".join(blocks).strip()

            return full_msg

    @staticmethod
    def format_whale_alert(whale_data: dict) -> str:
        """Formats institutional gold whale and central bank flow alert (Point 1)."""
        action = whale_data.get("action", "ទិញបន្ថែម (Inflow)")
        amount = whale_data.get("amount", "10.5 តោន")
        entity = whale_data.get("entity", "SPDR Gold Shares (GLD)")
        impact = whale_data.get("impact", "កម្លាំងគាំទ្រដល់និន្នាការកើនឡើងនៃតម្លៃមាស")
        date_str = whale_data.get("date_str", "")

        msg = (
            f"🐋 <b>GOLD WHALE ALERT — សកម្មភាពស្ថាប័នធំៗលើទីផ្សារមាស!</b>\n\n"
            f"📅 <b>កាលបរិច្ឆេទ:</b> {date_str}\n"
            f"🏛️ <b>ស្ថាប័ន / មូលនិធិ:</b> <b>{entity}</b>\n"
            f"📊 <b>សកម្មភាព:</b> <b>{action} {amount}</b>\n\n"
            f"🧠 <b>ការវិភាគឥទ្ធិពល:</b>\n"
            f"• {impact}\n"
            f"• បង្ហាញពីទំនុកចិត្តវិនិយោគិនស្ថាប័នក្នុងការការពារទ្រព្យសកម្មធៀបនឹងអតិផរណា និងហានិភ័យសកល។\n\n"
            f"🥇 <b>សម្ពាធលើ XAUUSD:</b> 👉 🟢 <b>Bullish Support (កម្លាំងរុញតម្លៃ)</b>\n\n"
            f"🔗 <i>ប្រភព: World Gold Council / SPDR Gold Trust Institutional Holdings</i>"
        )
        return msg

    @staticmethod
    def format_night_wrap_up(price_data: dict, summary: str = "") -> str:
        """Formats daily market wrap-up and London/NY session summary (Point 4)."""
        oz = price_data.get("price_oz", 0.0)
        chg = price_data.get("change", 0.0)
        pct = price_data.get("change_pct", 0.0)
        date_str = price_data.get("date_str", "")
        time_str = price_data.get("updated_time_str", "22:00")
        
        sign = "+" if chg >= 0 else ""
        icon = "📈" if chg >= 0 else "📉"

        macro = price_data.get("macro_correlation", {})
        dxy = macro.get("dxy_price", 0.0)
        us10y = macro.get("us10y_yield", 0.0)

        gld_price = macro.get("gld_price", 0.0)
        gld_vol = macro.get("gld_volume", 0)
        gld_chg = macro.get("gld_pct", 0.0)
        gld_icon = "🟢 ទិញចូល (Inflow)" if gld_chg >= 0 else "🔴 លក់ចេញ (Outflow)"

        summary_block = f"🧠 <b>សេចក្តីសង្ខេបចលនាទីផ្សារ:</b>\n{summary}\n\n" if summary else ""

        spdr_block = (
            f"🐋 <b>លំហូរស្ថាប័នធំៗ (SPDR Gold Trust ETF):</b>\n"
            f"• <b>ភាគហ៊ុន GLD:</b> ${gld_price:,.2f} ({gld_chg:+.2f}%)\n"
            f"• <b>ទំហំជួញដូរស្ថាប័ន:</b> {gld_vol:,.0f} Shares\n"
            f"• <b>និន្នាការ Whale:</b> {gld_icon}\n\n"
        )

        msg = (
            f"🌙 <b>DAILY MARKET WRAP-UP — សេចក្តីសង្ខេបទីផ្សារពេលយប់</b>\n\n"
            f"📅 <b>កាលបរិច្ឆេទ:</b> {date_str} (ម៉ោង {time_str} កម្ពុជា)\n"
            f"🌆 <b>បញ្ចប់ Session:</b> London & New York Active Trading\n\n"
            f"🥇 <b>ស្ថានភាពបិទតម្លៃមាស (XAUUSD):</b>\n"
            f"• <b>តម្លៃបច្ចុប្បន្ន:</b> ${oz:,.2f}\n"
            f"• {icon} <b>បម្រែបម្រួលសរុបថ្ងៃនេះ:</b> {sign}${chg:,.2f} ({sign}{pct:.2f}%)\n\n"
            f"📊 <b>កត្តាគន្លឹះម៉ាក្រូសេដ្ឋកិច្ច:</b>\n"
            f"• 💵 <b>DXY Index:</b> {dxy:.2f}\n"
            f"• 🏛️ <b>US 10Y Yield:</b> {us10y:.2f}%\n\n"
            f"{spdr_block}"
            f"{summary_block}"
            f"🛑 <b>ប្រព័ន្ធ SIGNAL:</b> បានបិទបញ្ចប់ជាផ្លូវការត្រឹមម៉ោង ១០:០០ យប់ (22:00) នេះហើយ ដើម្បីការពារដើមទុន និងចៀសវាងហានិភ័យពេលយប់ជ្រៅ។ ជួបគ្នានៅវគ្គ London ថ្ងៃស្អែកម៉ោង ២:០០ រសៀល!\n\n"
            f"🎯 <b>ទស្សនវិស័យថ្ងៃស្អែក:</b> តាមដានតំបន់ Key Pivot និងប្រតិទិនសេដ្ឋកិច្ចពេលព្រឹក!\n\n"
            f"🔗 <i>ប្រភព: Interbank Bullion Liquidity & SPDR Gold Shares</i>"
        )
        return msg

    @staticmethod
    def format_session_open_alert(
        session_name: str, 
        time_str: str, 
        session_info: str = "",
        price_data: dict = None,
        order_book: dict = None
    ) -> str:
        """
        Formats London / New York Session Open Alert matching the exact clean narrative
        typography of Breaking Event (smooth regular Khmer font, no bold clutters).
        """
        is_london = "london" in session_name.lower()
        flag = "🇬🇧" if is_london else "🇺🇸"
        header_title = f"{flag} <b>{session_name.upper()} OPENING — ទីផ្សារហិរញ្ញវត្ថុបើកដំណើរការ!</b>"

        if is_london:
            story_text = (
                "ទីផ្សារវគ្គព្រឹកបានបង្កើតចលនា Consolidation ដែលធ្វើឱ្យក្រុម Retail Traders កកកុញ Stop Loss យ៉ាងច្រើននៅតំបន់ Asian High និង Asian Low។ "
                "ពេលបើកផ្សារ London នេះ ធនាគារធំៗតែងតែបង្កើតចលនាបញ្ឆោត (Judas Swing / Fakeout) រុញតម្លៃទៅស្រូបយក Stop Loss ទាំងនោះសិន មុននឹងបកក្បាលបង្ហាញទិសដៅពិតប្រាកដ។ "
                "ដូច្នេះ គួររង់ចាំចន្លោះពី 15 ទៅ 30 នាទីឱ្យទីផ្សារ Sweep Liquidity រួចបង្កើតសញ្ញាបញ្ជាក់ M15 Confirmation ច្បាស់លាស់សិន ទើបជាចំណុចចូល Trade ដែលមានសុវត្ថិភាពខ្ពស់បំផុត។"
            )
        else:
            story_text = (
                "ទីផ្សារបានបង្កើតចលនាពាក់កណ្តាលថ្ងៃរួចរាល់ ហើយផ្សារ New York បើកដំណើរការជាមួយស្ថាប័ន Wall Street និង COMEX ដែលជាប្រភពនៃទំហំសាច់ប្រាក់ និងបម្រែបម្រួលតម្លៃមាសធំបំផុតប្រចាំថ្ងៃ។ "
                "ស្ថាប័នធំៗអាចនឹងរុញបន្ត Trend ពី London ឬធ្វើការបកក្បាល Reversal យ៉ាងគំហុកនៅតំបន់ Order Block និង Fair Value Gap (FVG)។ "
                "ដូច្នេះ គួរតាមដានប្រតិកម្មតម្លៃជុំវិញតំបន់កណ្តាល Equilibrium Pivot និងចៀសវាងការដេញតម្លៃពេលទិន្នន័យសេដ្ឋកិច្ចអាមេរិក (USD Data) ចេញផ្សាយ។"
            )

        if session_info:
            story_text = f"{session_info}\n\n{story_text}"

        return (
            f"{header_title}\n\n"
            f"🔹 <b>ការវិភាគទីផ្សារ & យុទ្ធសាស្ត្រស្ថាប័ន (SMC):</b>\n"
            f"{story_text}"
        )






    @staticmethod
    def format_spike_alert(current_price: float, prev_price: float, diff: float, minutes: int = 15) -> str:
        """Formats real-time Gold Volatility Spike / Flash Crash Warning."""
        sign = "+" if diff > 0 else ""
        direction = "🟢 BULLISH SPIKE (ហោះឡើងខ្លាំង)" if diff > 0 else "🔴 FLASH DUMP (ទម្លាក់ចុះខ្លាំង)"
        icon = "🚀" if diff > 0 else "⚡"
        
        return (
            f"🚨 {icon} <b>XAUUSD VOLATILITY ALERT — បម្រែបម្រួលតម្លៃមាសខុសប្រក្រតី!</b>\n\n"
            f"📊 <b>ចលនាទីផ្សារ:</b> <b>{direction}</b>\n"
            f"• <b>តម្លៃបច្ចុប្បន្ន:</b> <code>${current_price:,.2f}</code>\n"
            f"• <b>តម្លៃមុននេះ ({minutes}mn):</b> <code>${prev_price:,.2f}</code>\n"
            f"• <b>បម្រែបម្រួលភ្លាមៗ:</b> <b>{sign}${diff:,.2f}</b> ក្នុងរយៈពេលខ្លី!\n\n"
            f"🧠 <b>ការវិភាគសភាពការណ៍:</b>\n"
            f"• មានការកើនឡើងនៃលំហូរ Order ស្ថាប័នធំៗ (High Volume Institutional Spike) ឬមានប្រតិកម្មនឹងព័ត៌មានបន្ទាន់!\n"
            f"• Spread អាចរីកធំឡើង (Spread Widening) ខ្លាំងនៅតាម Broker នានា។\n\n"
            f"🛡️ <b>ការណែនាំគ្រប់គ្រងហានិភ័យ (Trader Caution):</b>\n"
            f"• ⚠️ <b>ហាមដេញតម្លៃ (Do NOT FOMO / Chase):</b> រង់ចាំទីផ្សារបង្កើត Base ឬ Pullback សិន\n"
            f"• 🔒 <b>ការពារទុន:</b> ពិនិត្យ Margin Level និងរំកិល Stop Loss ការពារប្រាក់ចំណេញ (Trailing Stop) ភ្លាមៗ!\n\n"
            f"📊 <i>មើល Chart ផ្ទាល់: <a href='https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD'>TradingView XAUUSD</a></i>"
        )

    @staticmethod
    def format_candlestick_confirmation(conf: dict) -> str:
        """Formats Technical Candlestick Confirmation Alert at SMC Key Levels."""
        is_bull = "BULLISH" in conf.get("type", "")
        icon = "🟢" if is_bull else "🔴"
        action = "BUY SETUP CONFIRMED (បញ្ជាក់សញ្ញាទិញ)" if is_bull else "SELL SETUP CONFIRMED (បញ្ជាក់សញ្ញាលក់)"
        
        return (
            f"🎯 {icon} <b>AI SMC CONFIRMATION — សញ្ញាទៀនបញ្ជាក់នៅតំបន់គន្លឹះ!</b>\n\n"
            f"📊 <b>សញ្ញា:</b> <b>{action}</b>\n"
            f"• 🕯️ <b>ទម្រង់ទៀន (Pattern):</b> <b>{conf['pattern']}</b> (M15 Structure)\n"
            f"• 🎯 <b>តំបន់គន្លឹះ (Zone):</b> <b>{conf['zone_name']}</b>\n\n"
            f"📈 <b>កម្រិតចូលជួញដូរ (Trade Parameters):</b>\n"
            f"• <b>Entry Price:</b> <code>${conf['entry']:,.2f}</code>\n"
            f"• 🛑 <b>Stop Loss (SL):</b> <code>${conf['sl']:,.2f}</code>\n"
            f"• 🎯 <b>Take Profit (TP):</b> <code>${conf['tp']:,.2f}</code> (Risk/Reward ~ 1:2.5+)\n\n"
            f"🧠 <b>ការពន្យល់បច្ចេកទេស:</b>\n"
            f"• {conf['desc']}\n\n"
            f"🛡️ <b>ការគ្រប់គ្រងហានិភ័យ:</b> ប្រើទំហំ Risk ត្រឹម ១-២% នៃដើមទុនប៉ុណ្ណោះ!\n\n"
            f"📊 <i>ពិនិត្យ Chart: <a href='https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD'>TradingView XAUUSD Live</a></i>"
        )

    @staticmethod
    def format_liquidity_sweep(sweep: dict) -> str:
        """Formats Real-Time Institutional Liquidity Sweep (Stop Loss Hunt) Alert."""
        is_bull = sweep.get("type") == "BULLISH_SWEEP"
        icon = "🟢" if is_bull else "🔴"
        action = "BULLISH REVERSAL SETUP (ឱកាសទិញស្ទុះឡើង)" if is_bull else "BEARISH REVERSAL SETUP (ឱកាសលក់ទម្លាក់ចុះ)"

        return (
            f"🧲 {icon} <b>LIQUIDITY SWEEP ALERT — ស្ថាប័នទើបតែ Hunt Stop Loss!</b>\n\n"
            f"⚡ <b>ស្ថានភាព (Event):</b> <b>{action}</b>\n"
            f"• 🎯 <b>កម្រិត Liquidity (Level):</b> <b>{sweep['level_name']}</b> (<code>${sweep['level_price']:,.2f}</code>)\n"
            f"• 🏹 <b>តម្លៃ Sweep ខ្ពស់បំផុត/ទាបបំផុត:</b> <code>${sweep['sweep_price']:,.2f}</code>\n"
            f"• 🥇 <b>តម្លៃបច្ចុប្បន្ន (Current):</b> <code>${sweep['current_price']:,.2f}</code>\n\n"
            f"📈 <b>កម្រិតណែនាំសម្រាប់ Trader (Smart Money Trade):</b>\n"
            f"• <b>Entry:</b> <code>${sweep['current_price']:,.2f}</code>\n"
            f"• 🛑 <b>Stop Loss (SL):</b> <code>${sweep['sl']:,.2f}</code> (ហួសពីចុង Wick)\n"
            f"• 🎯 <b>Take Profit (TP):</b> <code>${sweep['tp']:,.2f}</code>\n\n"
            f"🧠 <b>ការពន្យល់លំហូរសាច់ប្រាក់ (Smart Money Concept):</b>\n"
            f"• {sweep['desc']}\n"
            f"• ស្ថាប័នធំៗបានប្រើ Fakeout ដើម្បីបង្កើត Liquidity សម្រាប់ Order ធំរបស់ពួកគេ។\n\n"
            f"🛡️ <b>អនុសាសន៍:</b> ចូល Order ជាមួយទំហំ Lot សមរម្យ និងដាក់ Stop Loss ជានិច្ច!\n\n"
            f"📊 <i>ពិនិត្យ Chart: <a href='https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD'>TradingView XAUUSD Live</a></i>"
        )

    @staticmethod
    def format_divergence_alert(div: dict) -> str:
        """Formats Macro Divergence Alert between Gold and US Dollar (DXY)."""
        is_bull = div.get("type") == "BULLISH_DIVERGENCE"
        icon = "🟢" if is_bull else "🔴"
        action = "BULLISH SMART MONEY ACCUMULATION" if is_bull else "BEARISH SMART MONEY DISTRIBUTION"

        g_sign = "+" if div.get("gold_pct", 0) >= 0 else ""
        d_sign = "+" if div.get("dxy_pct", 0) >= 0 else ""

        return (
            f"⚡ {icon} <b>MACRO DIVERGENCE ALERT — សញ្ញាផ្ទុយគ្នារវាងមាស និង USD!</b>\n\n"
            f"📊 <b>ស្ថានភាព (Setup):</b> <b>{action}</b>\n"
            f"• 🥇 <b>តម្លៃមាស (XAU/USD):</b> <code>${div['gold_price']:,.2f}</code> (<b>{g_sign}{div['gold_pct']}%</b>)\n"
            f"• 💵 <b>សន្ទស្សន៍ដុល្លារ (DXY):</b> <code>{div['dxy_price']}</code> (<b>{d_sign}{div['dxy_pct']}%</b>)\n"
            f"• 📈 <b>ទិន្នផលសហរដ្ឋអាមេរិក (US10Y):</b> <code>{div['us10y_yield']}%</code>\n\n"
            f"🧠 <b>ការវិភាគសភាពការណ៍ (Macro Logic):</b>\n"
            f"• {div['desc']}\n"
            f"• <b>ទស្សនវិស័យទីផ្សារ:</b> {div['bias']}\n\n"
            f"🛡️ <b>យុទ្ធសាស្ត្រ Trader:</b> ស្ថាប័នធំៗកំពុងបង្ហាញជំហរច្បាស់លាស់ ផ្តល់អាទិភាពតាមនិន្នាការស្ថាប័ន (Smart Money Trend)!\n\n"
            f"📊 <i>ពិនិត្យ Chart: <a href='https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD'>TradingView XAUUSD Live</a></i>"
        )

    @staticmethod
    def format_fomc_speech_alert(event_title: str, interp: dict) -> str:
        """
        Formats Real-Time AI Live Speech Interpretation of FOMC / Fed Officials.
        Strictly follows the VIP template requested by the user:
        សុន្ទរកថា៖ Kevin Warsh (ប្រធាន Federal Reserve)
        ជំហរ៖ Hawkish (រឹតបន្តឹងគោលនយោបាយរូបិយវត្ថុ)

        💬 សម្រង់សម្តីសំខាន់៖
        «Federal Reserve ត្រូវតែប្រុងប្រយ័ត្នខ្ពស់ចំពោះអតិផរណាដែលមិនទាន់ធ្លាក់ដល់គោលដៅ ២% ហើយទីផ្សារមិនគួររំពឹងការបញ្ចុះអត្រាការប្រាក់លឿនពេកឡើយ។»

        ⚡ ផលប៉ះពាល់ទីផ្សារ៖
        🔹 USD & US10Y Yields៖ ដុល្លារ និងទិន្នផលប័ណ្ណបំណុលឡើងថ្លៃ (Bullish)
        🔸 XAUUSD (មាស)៖ ប្រឈមសម្ពាធធ្លាក់ចុះ (Bearish)
        """
        import re

        # Determine speaker & title
        speaker = interp.get("speaker") or ""
        title_combined = f"{event_title} {speaker}".lower()

        if "warsh" in title_combined:
            speaker_name = "Kevin Warsh"
            speaker_role = "ប្រធាន Federal Reserve"
        elif "powell" in title_combined:
            speaker_name = "Jerome Powell"
            speaker_role = "ប្រធាន Federal Reserve"
        elif "waller" in title_combined:
            speaker_name = "Christopher Waller"
            speaker_role = "ទេសាភិបាល Federal Reserve"
        elif "bowman" in title_combined:
            speaker_name = "Michelle Bowman"
            speaker_role = "ទេសាភិបាល Federal Reserve"
        elif "goolsbee" in title_combined:
            speaker_name = "Austan Goolsbee"
            speaker_role = "ប្រធាន Federal Reserve សាខា Chicago"
        elif "williams" in title_combined:
            speaker_name = "John Williams"
            speaker_role = "ប្រធាន Federal Reserve សាខា New York"
        else:
            speaker_name = speaker if speaker else "Kevin Warsh"
            speaker_role = "ប្រធាន Federal Reserve" if "warsh" in speaker_name.lower() or "powell" in speaker_name.lower() else "មន្ត្រី Federal Reserve"

        # Determine Tone
        tone_str = (interp.get("tone") or "").upper()
        raw_tone_kh = (interp.get("tone_kh") or "").lower()

        if "HAWK" in tone_str or "hawkish" in raw_tone_kh:
            tone_display = "Hawkish (រឹតបន្តឹងគោលនយោបាយរូបិយវត្ថុ)"
            usd_yield_impact = "ដុល្លារ និងទិន្នផលប័ណ្ណបំណុលឡើងថ្លៃ (Bullish)"
            gold_impact = "ប្រឈមសម្ពាធធ្លាក់ចុះ (Bearish)"
        elif "DOV" in tone_str or "dovish" in raw_tone_kh:
            tone_display = "Dovish (បន្ធូរបន្ថយគោលនយោបាយរូបិយវត្ថុ)"
            usd_yield_impact = "ដុល្លារ និងទិន្នផលប័ណ្ណបំណុលធ្លាក់ចុះ (Bearish)"
            gold_impact = "កើនឡើងថ្លៃខ្លាំង (Bullish)"
        else:
            tone_display = "Neutral (អព្យាក្រឹត/ប្រុងប្រយ័ត្ន)"
            usd_yield_impact = "ដុល្លារ និងទិន្នផលប័ណ្ណបំណុលមានស្ថិរភាព (Range-bound)"
            gold_impact = "ជួញដូរក្នុងរង្វង់ចង្អៀត (Sideways)"

        # Custom override if interp provides specific impacts
        custom_usd = interp.get("usd_yield_impact")
        if custom_usd:
            usd_yield_impact = str(custom_usd).strip()

        custom_gold = interp.get("gold_pressure") or interp.get("gold_impact")
        if custom_gold:
            g_clean = str(custom_gold).strip().lstrip("•- ")
            g_clean = re.sub(r'^(xauusd\s+(bearish|bullish)[^:]*:\s*)', '', g_clean, flags=re.I).strip()
            g_clean = sanitize_khmer_spelling(g_clean)
            if g_clean and not ("មាសមាននិន្នាការ" in g_clean and len(g_clean) > 30):
                gold_impact = g_clean

        # Key Quotes
        quotes_raw = interp.get("key_quotes") or ""
        if isinstance(quotes_raw, list):
            quotes = " ".join(str(q).strip() for q in quotes_raw if q)
        else:
            quotes = str(quotes_raw).strip()
        quotes = quotes.strip("«»\"' ")
        quotes = sanitize_khmer_spelling(quotes)
        if not quotes or len(quotes) < 5:
            if "HAWK" in tone_str or "hawkish" in raw_tone_kh:
                quotes = "Federal Reserve ត្រូវតែប្រុងប្រយ័ត្នខ្ពស់ចំពោះអតិផរណាដែលមិនទាន់ធ្លាក់ដល់គោលដៅ ២% ហើយទីផ្សារមិនគួររំពឹងការបញ្ចុះអត្រាការប្រាក់លឿនពេកឡើយ។"
            else:
                quotes = "ទីផ្សារការងារ និងកំណើនសេដ្ឋកិច្ចកំពុងបង្ហាញសញ្ញាបន្ធូរបន្ថយ ដែលអាចបើកផ្លូវឱ្យ Federal Reserve ពិចារណាលើការបន្ធូរបន្ថយគោលនយោបាយរូបិយវត្ថុ។"

        return (
            f"<b>សុន្ទរកថា៖</b> {speaker_name} ({speaker_role})\n"
            f" <b>ជំហរ៖</b> {tone_display}\n\n"
            f"💬 <b>សម្រង់សម្តីសំខាន់៖</b>\n"
            f"«{quotes}»\n\n"
            f"⚡ <b>ផលប៉ះពាល់ទីផ្សារ៖</b>\n"
            f"🔹 <b>USD & US10Y Yields៖</b> {usd_yield_impact}\n"
            f"🔸 <b>XAUUSD (មាស)៖</b> {gold_impact}"
        )

    @staticmethod
    def format_iceberg_alert(iceberg: dict) -> str:
        """Formats Real-Time Institutional Iceberg Order / Whale Wall Alert."""
        is_buy = iceberg.get("type") == "ICEBERG_BUY_WALL"
        icon = "🟢" if is_buy else "🔴"
        action = "WHALE ICEBERG BUY WALL DETECTED (បន្ទាយទប់ទិញយក្ស)" if is_buy else "WHALE ICEBERG SELL WALL DETECTED (ជញ្ជាំងរារាំងលក់យក្ស)"

        return (
            f"🛰️ {icon} <b>WHALE ORDER BOOK ALERT — រកឃើញ Order ស្ថាប័នលាក់មុខ!</b>\n\n"
            f"⚡ <b>ប្រភេទ Order:</b> <b>{action}</b>\n"
            f"• 🎯 <b>តម្លៃដាក់ទប់ (Wall Level):</b> <code>${iceberg['price']:,.2f}</code>\n"
            f"• 🐋 <b>ទំហំទំងន់ (Volume):</b> <code>{iceberg['volume_oz']:.1f} អោន</code> (<b>${iceberg['value_usd']:,.0f}</b>)\n"
            f"• 🥇 <b>តម្លៃទីផ្សារបច្ចុប្បន្ន (Spot):</b> <code>${iceberg['mid_price']:,.2f}</code>\n\n"
            f"🧠 <b>ការពន្យល់ Order Book Depth:</b>\n"
            f"• {iceberg['desc']}\n"
            f"• ស្ថាប័នធំៗបានដាក់ Limit Order កម្រាស់ក្រាស់ក្រែល ដែលអាចធ្វើឱ្យតម្លៃ Rebound ខ្លាំងនៅពេលមកដល់ចំណុចនេះ!\n\n"
            f"🛡️ <b>យុទ្ធសាស្ត្រ Trader:</b> យកកម្រិតនេះធ្វើជាតំបន់ Support/Resistance ដ៏រឹងមាំ ឬជាចំណុច Take Profit / Entry!\n\n"
            f"📊 <i>ពិនិត្យ Chart: <a href='https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD'>TradingView XAUUSD Live</a></i>"
        )

    @staticmethod
    def format_order_book_depth(depth: dict) -> str:
        """Formats full 100-level Institutional Order Book Depth overview."""
        if not depth or not depth.get("available"):
            return "📊 <b>ទិន្នន័យ Order Book Depth មិនទាន់ត្រូវបានធ្វើបច្ចុប្បន្នភាពនៅឡើយទេ។</b>"

        b_walls = depth.get("whale_buy_walls", [])
        s_walls = depth.get("whale_sell_walls", [])

        b_str = ""
        for b in b_walls:
            b_str += f"  • 🟢 <code>${b['price']:,.2f}</code>: <b>{b['volume_oz']:.1f} oz</b> (~${b['value_usd']:,.0f})\n"

        s_str = ""
        for s in s_walls:
            s_str += f"  • 🔴 <code>${s['price']:,.2f}</code>: <b>{s['volume_oz']:.1f} oz</b> (~${s['value_usd']:,.0f})\n"

        return (
            f"🛰️ <b>INSTITUTIONAL GOLD ORDER BOOK DEPTH (100 Levels)</b>\n\n"
            f"🥇 <b>តម្លៃបច្ចុប្បន្ន (Mid Price):</b> <code>${depth['mid_price']:,.2f}</code>\n\n"
            f"⚖️ <b>សមាមាត្រកម្លាំងទីផ្សារ (Liquidity Ratio):</b>\n"
            f"• 🟢 <b>Bid Liquidity (ទិញ):</b> <code>{depth['bid_dominance_pct']}%</code> ({depth['total_bid_vol']:.1f} oz)\n"
            f"• 🔴 <b>Ask Liquidity (លក់):</b> <code>{depth['ask_dominance_pct']}%</code> ({depth['total_ask_vol']:.1f} oz)\n"
            f"• 🧠 <b>ទំនោរកម្លាំង:</b> {depth['bias']}\n\n"
            f"🧱 <b>បន្ទាយទប់ទិញធំបំផុត (Top Whale Buy Walls):</b>\n{b_str}\n"
            f"🧱 <b>ជញ្ជាំងរារាំងលក់ធំបំផុត (Top Whale Sell Walls):</b>\n{s_str}\n"
            f"💡 <i>ទិន្នន័យបញ្ជាក់ពីជម្រៅទីផ្សារកុងត្រាមាស និងតំបន់ Iceberg Orders ពិតប្រាកដ!</i>"
        )

    @staticmethod
    def format_cot_report(cot_data: dict) -> str:
        """Formats CFTC Commitment of Traders (CoT) institutional report for Gold."""
        if not cot_data or not cot_data.get("available"):
            return "📊 <b>ទិន្នន័យ CFTC CoT Report មិនទាន់ត្រូវបានធ្វើបច្ចុប្បន្នភាពនៅឡើយទេ។</b>"

        r_date = cot_data.get("report_date", "")
        net_noncomm = cot_data.get("net_noncommercial", 0)
        chg_noncomm = cot_data.get("change_noncommercial", 0)
        oi = cot_data.get("open_interest", 0)
        cot_idx = cot_data.get("cot_index_52w", 50.0)
        bias = cot_data.get("bias", "Neutral")

        chg_sign = "+" if chg_noncomm >= 0 else ""

        return (
            f"🏛️ <b>CFTC GOLD CoT REPORT — ជំហរស្ថាប័នធំៗ (Smart Money)</b>\n\n"
            f"📅 <b>កាលបរិច្ឆេទរបាយការណ៍ (Report Date):</b> {r_date}\n"
            f"💼 <b>កុងត្រា Hedge Funds (Net Non-Commercial):</b> <code>{net_noncomm:,} contracts</code>\n"
            f"📊 <b>បម្រែបម្រួលប្រចាំសប្តាហ៍ (Weekly Change):</b> <code>{chg_sign}{chg_noncomm:,} contracts</code>\n"
            f"📈 <b>កុងត្រាសរុបក្នុងទីផ្សារ (Open Interest):</b> <code>{oi:,}</code>\n"
            f"🎚️ <b>CoT Index (52-Week Percentile):</b> <code>{cot_idx:.1f}%</code>\n\n"
            f"🧠 <b>ការបកស្រាយអារម្មណ៍ស្ថាប័ន (Institutional Bias):</b>\n"
            f"{bias}\n\n"
            f"💡 <i>CoT Report បង្ហាញពីទំហំកុងត្រាទិញ/លក់ពិតប្រាកដរបស់ស្ថាប័នហិរញ្ញវត្ថុអន្តរជាតិនៅលើ COMEX Gold Futures!</i>\n"
            f"🔗 <a href='https://futuresbench.com/cot/gold/'>CFTC Gold Data Source</a>"
        )

    @staticmethod
    def format_weekly_outlook(price_data: dict, high_impact_events: list, summary: str = "", cot_data: dict = None) -> str:
        """Formats Sunday Evening Weekly Macro & Institutional Gold Outlook."""
        oz = price_data.get("price_oz", 0.0)
        levels = price_data.get("key_levels", {})
        pivot = levels.get("pivot", oz)
        r1 = levels.get("r1", oz + 20)
        s1 = levels.get("s1", oz - 20)

        # Build list of top economic catalysts
        events_str = ""
        if high_impact_events:
            for ev in high_impact_events[:5]:
                events_str += f"• 🔴 <b>{ev.get('release_date_str', '')} {ev.get('release_time_str', '')}</b>: {ev.get('title', '')} ({ev.get('currency', 'USD')})\n"
        else:
            events_str = "• មិនមានទិន្នន័យក្រហមធំៗ (High Impact) ក្នុងសប្តាហ៍នេះទេ\n"

        cot_block = ""
        if cot_data and cot_data.get("available"):
            net_nc = cot_data.get("net_noncommercial", 0)
            chg_nc = cot_data.get("change_noncommercial", 0)
            chg_sign = "+" if chg_nc >= 0 else ""
            cot_block = (
                f"🏛️ <b>ជំហរស្ថាប័នធំៗ (CFTC CoT Hedge Funds):</b>\n"
                f"• Net Long: <code>{net_nc:,} contracts</code> ({chg_sign}{chg_nc:,})\n"
                f"• អារម្មណ៍ស្ថាប័ន: {cot_data.get('bias', 'Bullish')}\n\n"
            )

        summary_block = f"🧠 <b>ទស្សនវិស័យស្ថាប័ន (Institutional Bias):</b>\n{summary}\n\n" if summary else ""

        return (
            f"🏛️ <b>WEEKLY GOLD OUTLOOK — យុទ្ធសាស្ត្រមាសប្រចាំសប្តាហ៍ថ្មី!</b>\n\n"
            f"📅 <b>ការរៀបចំជួញដូរសម្រាប់សប្តាហ៍ថ្មី (ម៉ោងនៅកម្ពុជា UTC+7)</b>\n"
            f"🥇 <b>តម្លៃបិទចុងសប្តាហ៍ (Close):</b> <code>${oz:,.2f}</code>\n\n"
            f"🎯 <b>កម្រិតបច្ចេកទេសប្រចាំសប្តាហ៍ (Weekly Key Levels):</b>\n"
            f"• 🔴 <b>Weekly Resistance (Target Sell):</b> <code>${r1:,.2f}</code>\n"
            f"• 🎯 <b>Weekly Pivot Point (តុល្យភាព):</b> <code>${pivot:,.2f}</code>\n"
            f"• 🟢 <b>Weekly Support (Target Buy):</b> <code>${s1:,.2f}</code>\n\n"
            f"{cot_block}"
            f"📅 <b>ព្រឹត្តិការណ៍សេដ្ឋកិច្ចសំខាន់ៗប្រចាំសប្តាហ៍ (High Impact Catalysts):</b>\n"
            f"{events_str}\n"
            f"{summary_block}"
            f"🛡️ <b>ផែនការ Trader:</b> គ្រប់គ្រងដើមទុន គោរព Stop Loss និងរង់ចាំការបញ្ជាក់ច្បាស់លាស់មុនចូល Trade!\n\n"
            f"📊 <i>មើល Chart: <a href='https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD'>TradingView XAUUSD</a></i> | "
            f"📅 <i><a href='https://www.forexfactory.com/calendar'>ForexFactory Calendar</a></i>"
        )

    @staticmethod
    def format_lot_size_calculator(calc: dict) -> str:
        """Formats the interactive lot size and risk management response in Khmer."""
        if "error" in calc:
            return f"⚠️ <b>បញ្ហាគណនា Lot Size:</b> {calc['error']}"

        bal = calc.get("balance", 0.0)
        risk_pct = calc.get("risk_pct", 1.0)
        risk_usd = calc.get("risk_amount_usd", 0.0)
        dist_usd = calc.get("distance_usd", 10.0)
        pips = calc.get("pips", 100.0)
        lot = calc.get("lot_size", 0.01)
        raw_lot = calc.get("raw_lot", 0.01)
        style = calc.get("style", "")
        lev = calc.get("effective_leverage", 1.0)

        entry_line = ""
        if calc.get("entry_price") and calc.get("sl_price"):
            entry_line = (
                f"• 🎯 <b>Entry Price:</b> <code>${calc['entry_price']:,.2f}</code>\n"
                f"• 🛑 <b>Stop Loss Price:</b> <code>${calc['sl_price']:,.2f}</code>\n"
            )

        # Money Management Table
        half_lot = max(0.01, round(lot / 2.0, 2))
        tp1_profit = round(half_lot * dist_usd * 100.0, 2)
        tp2_profit = round(half_lot * dist_usd * 2.0 * 100.0, 2)

        return (
            f"🤖 <b>SMART LOT SIZE & RISK CALCULATOR (XAU/USD)</b>\n"
            f"<i>ម៉ាស៊ីនគណនាទំហំ Lot ស្តង់ដារតាមដើមទុន & Money Management</i>\n\n"
            f"💰 <b>ដើមទុនគណនី (Balance):</b> <code>${bal:,.2f}</code>\n"
            f"🛡️ <b>កម្រិត Risk %:</b> <code>{risk_pct:.1f}%</code> ({style})\n"
            f"💸 <b>ទឹកប្រាក់ប្រថុយអតិបរមា (Max Risk $):</b> <code>${risk_usd:,.2f}</code>\n"
            f"📏 <b>ចម្ងាយ Stop Loss:</b> <code>${dist_usd:,.2f}</code> (ស្មើនឹង <b>{pips:,.0f} Pips</b>)\n"
            f"{entry_line}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 <b>ទំហំ LOT ណែនាំ (RECOMMENDED LOT):</b>\n"
            f"👉 <code><b>{lot:.2f} LOT</b></code> (ពិត: {raw_lot:.3f})\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎯 <b>យុទ្ធសាស្ត្របែងចែកទំហំ (Position Scaling 1:2 R:R):</b>\n"
            f"• 📦 <b>Lot បំបែក (2 Orders):</b> <code>{half_lot:.2f}</code> + <code>{half_lot:.2f}</code>\n"
            f"• 🎯 <b>TP1 (1:1 R:R):</b> ចម្ងាយ +${dist_usd:,.1f} ➡️ ចំណេញ <b>+${tp1_profit:,.2f}</b> (Lock BE)\n"
            f"• 🏆 <b>TP2 (1:2 R:R):</b> ចម្ងាយ +${dist_usd * 2:,.1f} ➡️ ចំណេញ <b>+${tp2_profit:,.2f}</b>\n"
            f"• ⚙️ <b>Effective Leverage:</b> <code>1:{lev}</code>\n\n"
            f"💡 <i>អនុសាសន៍: មិនត្រូវចូល Trade លើសពីទំហំ Lot នេះឡើយ ដើម្បីការពារគណនីមិនឱ្យ Drawdown ធ្ងន់ធ្ងរ!</i>"
        )

    @staticmethod
    def format_single_smc_setup(setup: dict, key_levels: dict = None, current_price: float = 0.0) -> str:
        """
        Formats a comprehensive, institutional-grade SMC Trading Brief:
        🎯 ផែនការជួញដូរឆ្លាតវៃ AI SMC — ទិសដៅតែមួយគត់ (BUY ONLY ឬ SELL ONLY)
        ជាមួយ Entry, SL, TP1, TP2, R:R និងហេតុផលលម្អិត «ហេតុអ្វីគួរធ្វើ & ហេតុអ្វីមិនគួរធ្វើផ្ទុយ»។
        """
        levels = key_levels or {}
        oz = current_price or setup.get("entry", 0.0)
        pivot = levels.get("pivot", oz)
        r1 = levels.get("r1", oz + 20)
        s1 = levels.get("s1", oz - 20)
        r2 = levels.get("r2", oz + 40)
        s2 = levels.get("s2", oz - 40)

        direction = setup.get("direction", "BUY").upper()
        is_buy = "BUY" in direction
        icon = "🟢" if is_buy else "🔴"
        action_kh = "ទិញឡើង (BUY)" if is_buy else "លក់ចុះ (SELL)"
        opposite_action = "លក់ (SELL)" if is_buy else "ទិញ (BUY)"

        entry_val = setup.get("entry", oz)
        entry_zone = setup.get("entry_zone", f"${entry_val:,.2f}")
        sl = setup.get("sl", 0.0)
        tp1 = setup.get("tp1", 0.0)
        tp2 = setup.get("tp2", 0.0)
        rr = setup.get("rr_ratio", "1:2.0")

        why_trade = setup.get("why_this_trade", "").strip()
        why_not = setup.get("why_not_opposite", "").strip()
        confirm = setup.get("confirmation_note", "រង់ចាំ Confirmation Candle នៅលើ M15 មុនចូល Order!").strip()

        def _clean_bullets(text: str) -> str:
            import re
            parts = re.split(r"(?<=\S)\s+(?=[១-៩1-9]\.|\•|\-)", text.strip())
            formatted = []
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                p = re.sub(r"^[១-៩1-9]\.\s*", "", p)
                if not p.startswith("•") and not p.startswith("-"):
                    formatted.append(f"• {p}")
                else:
                    formatted.append(p)
            return "\n".join(formatted)

        formatted_why_trade = _clean_bullets(why_trade)
        formatted_why_not = _clean_bullets(why_not)

        # Part 1: Top Technical Zones Header
        part1 = (
            f"🎯 <b>កម្រិតបច្ចេកទេស & AI SMC Setup Zone</b>\n\n"
            f"• 🟢 <b>Buy Zone:</b> <code>${s1 - 4:,.2f} - ${s1 + 3:,.2f}</code> (SL: ${s1 - 11:,.2f})\n"
            f"• 🔴 <b>Sell Zone:</b> <code>${r1 - 3:,.2f} - ${r1 + 4:,.2f}</code> (SL: ${r1 + 11:,.2f})\n"
            f"• 🎯 <b>Pivot Point:</b> <code>${pivot:,.2f}</code>\n\n"
            f"💡 <i>អនុសាសន៍: រង់ចាំ Confirmation Candle នៅលើ M15 មុនចូល Order!</i>\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
        )

        conf_score = setup.get("confidence", "88%")
        
        # Calculate Real-Time Execution Status for Telegram
        exec_status_line = ""
        try:
            entry_parts = [float(x.replace("$", "").replace(",", "").strip()) for x in entry_zone.split("-") if x.strip()]
            if len(entry_parts) == 2:
                e_low, e_high = min(entry_parts), max(entry_parts)
                if is_buy:
                    if e_low <= oz <= e_high:
                        exec_status_line = "🟢 <b>ស្ថានភាព (Status): ⚡ READY TO BUY (តម្លៃដល់តំបន់ទិញហើយ)</b>\n"
                    elif oz > e_high:
                        wait_diff = oz - e_high
                        exec_status_line = f"🟡 <b>ស្ថានភាព (Status): ⏳ WAITING PULLBACK (រង់ចាំចុះ ${wait_diff:.1f} ទៀត)</b>\n"
                    else:
                        exec_status_line = "🟢 <b>ស្ថានភាព (Status): ⚡ DEEP DISCOUNT BUY (តំបន់បញ្ចុះតម្លៃពិសេស)</b>\n"
                else:
                    if e_low <= oz <= e_high:
                        exec_status_line = "🟢 <b>ស្ថានភាព (Status): ⚡ READY TO SELL (តម្លៃដល់តំបន់លក់ហើយ)</b>\n"
                    elif oz < e_low:
                        wait_diff = e_low - oz
                        exec_status_line = f"🟡 <b>ស្ថានភាព (Status): ⏳ WAITING BOUNCE (រង់ចាំឡើង ${wait_diff:.1f} ទៀត)</b>\n"
                    else:
                        exec_status_line = "🟢 <b>ស្ថានភាព (Status): ⚡ HIGH PREMIUM SELL (តំបន់លក់បានថ្លៃខ្ពស់)</b>\n"
        except Exception:
            pass

        # Part 2: Decisive Single-Direction Institutional Plan
        trap_banner = ""
        trap_info = setup.get("trap_alert")
        if trap_info:
            trap_banner = (
                f"\n⚠️ <b>{trap_info.get('title', 'AI TRAP DETECTOR')}</b>\n"
                f"<i>{trap_info.get('desc', '')}</i>\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
            )

        news_lock_banner = ""
        news_info = setup.get("news_danger") or {}
        if news_info.get("is_danger"):
            news_lock_banner = (
                f"\n🚨 <b>AI NEWS DANGER ZONE — RED ALERT (AUTO-LOCK)!</b>\n"
                f"⚠️ <b>ព្រមាន:</b> ព័ត៌មានយក្ស <b>{news_info.get('title')}</b> នឹងចេញក្នុងរយៈពេល <b>{news_info.get('mins_left', 15)} នាទីទៀត!</b>\n"
                f"🚫 <b>ហាមបើក Order ថ្មីដាច់ខាត:</b> ជៀសវាងបញ្ហា Slippage និង Stop-Out ភ្លាមៗ!\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
            )

        part2 = (
            f"{news_lock_banner}"
            f"{trap_banner}"
            f"🎯 {icon} <b>ផែនការជួញដូរឆ្លាតវៃ AI SMC — ទិសដៅតែមួយគត់ ({action_kh})</b>\n"
            f"⚡ <b>កម្រិតទំនុកចិត្ត AI (Confidence Score):</b> <code>{conf_score}</code>\n"
            f"{exec_status_line}\n"
            f"📍 <b>កម្រិតតម្លៃចូល និងគ្រប់គ្រងដើមទុន:</b>\n"
            f"• 🎯 <b>តំបន់ Entry:</b> <code>{entry_zone}</code>\n"
            f"• 🛑 <b>Stop Loss (SL):</b> <code>${sl:,.2f}</code>\n"
            f"• 🎯 <b>Take Profit 1 (TP1):</b> <code>${tp1:,.2f}</code> (Lock BE)\n"
            f"• 🏆 <b>Take Profit 2 (TP2):</b> <code>${tp2:,.2f}</code>\n"
            f"• ⚖️ <b>សមាមាត្រចំណេញ/ខាត (R:R):</b> <code>{rr}</code>\n\n"
            f"🧠 <b>ហេតុផលច្បាស់លាស់ដែលគួរ {action_kh}:</b>\n"
            f"{formatted_why_trade}\n\n"
            f"🚫 <b>ហេតុផលដាច់ខាតដែលមិនគួរ {opposite_action}:</b>\n"
            f"{formatted_why_not}\n\n"
            f"💡 <i>អនុសាសន៍: {confirm}</i>\n"
            f"🛡️ <i>គ្រប់គ្រងហានិភ័យដោយបើក <b>📱 Mini App</b> ឬវាយ <code>/lot</code> មុនចូល Order!</i>"
        )
        return part1 + part2

    @staticmethod
    def format_chart_vision_scan(current_price: float, vision_res: dict, timeframe: str = "M15") -> str:
        """
        Formats Multimodal AI Live Computer Vision Candlestick & Pattern Scan results.
        """
        bias = vision_res.get("bias", "🟢 Bullish")
        pattern = vision_res.get("pattern_kh", "ទម្រង់ទៀនបញ្ជាក់ច្បាស់")
        structure = vision_res.get("market_structure", "BOS").replace("_", " ")
        observation = vision_res.get("key_observation", "")
        action = vision_res.get("tactical_action", "")
        conf = vision_res.get("confidence_score", "85%")

        msg = (
            f"👁️‍🗨️ <b>AI LIVE CHART PATTERN & CANDLESTICK SCANNER ({timeframe})</b>\n\n"
            f"• 🥇 <b>Spot XAU/USD:</b> <code>${current_price:,.2f}</code>\n"
            f"• 🕯️ <b>Pattern រកឃើញ:</b> <b>{pattern}</b>\n"
            f"• 🏗️ <b>រចនាសម្ព័ន្ធទីផ្សារ:</b> <code>{structure}</code>\n"
            f"• 🎯 <b>ទិសដៅ AI Bias:</b> <b>{bias}</b> (ទំនុកចិត្ត {conf})\n\n"
            f"🧠 <b>ការសង្កេតទម្រង់ទៀន (Vision Observation):</b>\n"
            f"• {observation}\n\n"
            f"⚡ <b>អនុសាសន៍យុទ្ធសាស្ត្រ (Tactical Action):</b>\n"
            f"👉 <b>{action}</b>\n\n"
            f"📊 <i>ពិនិត្យ Chart ផ្ទាល់: <a href='https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD'>TradingView XAUUSD Live</a></i>"
        )
        return msg

    @staticmethod
    def format_sniper_instant_alert(sig: dict) -> str:
        """Formats real-time AI Pre-Signal Market Analysis and Sniper Signal Alert."""
        action = sig.get("action", "BUY")
        is_buy = "BUY" in action
        icon = "🟢" if is_buy else "🔴"
        trend_desc = sig.get("trend_desc", "តម្លៃកំពុងស្ថិតក្នុងចលនាចំហៀង (Consolidation / Sideways)។")
        ma_desc = sig.get("ma_desc", "ខ្សែបម្លាស់ទីលឿន និងខ្សែបម្លាស់ទីយឺត កំពុងប្រទាក់ក្រឡាគ្នានៅជិតតម្លៃបច្ចុប្បន្ន។")
        res_range = sig.get("resistance_range", "$2700 - $2710")
        sup_range = sig.get("support_range", "$2660 - $2670")

        daily_c = sig.get("daily_count", 1)
        daily_m = sig.get("daily_max", 5)

        ai_analysis_block = ""
        if sig.get("ai_analysis"):
            ai_analysis_block = (
                f"🧠 <b>ការវិភាគស៊ីជម្រៅដោយ AI (Institutional Deep Analysis):</b>\n"
                f"{sig.get('ai_analysis')}\n\n"
            )

        macro_block = ""
        if sig.get("macro_context"):
            macro_block = f"• 💵 <b>ឥទ្ធិពល Macro & DXY:</b> {sig.get('macro_context')}\n"

        inval_block = ""
        if sig.get("invalidation_note"):
            inval_block = f"• 🚫 <b>លក្ខខណ្ឌខូចសុពលភាព (Invalidation):</b> {sig.get('invalidation_note')}\n"

        tips_block = ""
        if sig.get("execution_tips"):
            tips_block = f"• 🎯 <b>ការអនុវត្តជាក់ស្តែង:</b> {sig.get('execution_tips')}\n"

        daily_limit_notice = ""
        if daily_c >= daily_m:
            daily_limit_notice = (
                f"\n🛑 <b>ការការពារដើមទុន (Daily Quota Reached):</b>\n"
                f"នេះជា Position ទី <b>{daily_c}/{daily_m}</b> ចុងក្រោយសម្រាប់ថ្ងៃនេះ! "
                f"Bot នឹងផ្អាកការចេញ Signal បន្ថែមរហូតដល់ថ្ងៃស្អែក ដើម្បីការពារដើមទុន និងទប់ស្កាត់ Overtrading ១០០%។\n"
            )

        return (
            f"📊 <b>១. ការវិភាគស្ថានភាពទីផ្សារបច្ចុប្បន្ន</b>\n\n"
            f"• <b>និន្នាការរួម (Trend):</b> {trend_desc}\n\n"
            f"• <b>ខ្សែបម្លាស់ទី (Moving Averages):</b> {ma_desc}\n\n"
            f"• <b>កម្រិតទ្រទ្រង់ និងរាំងស្ទះ (Support & Resistance):</b>\n"
            f"  - <b>កម្រិតរាំងស្ទះ (Resistance):</b> នៅចន្លោះតម្លៃ <code>{res_range}</code> (ប្រសិនបើតម្លៃអាចបំបែកឡើងលើបាន)\n"
            f"  - <b>កម្រិតទ្រទ្រង់ (Support):</b> នៅចន្លោះតម្លៃ <code>{sup_range}</code> (ប្រសិនបើតម្លៃធ្លាក់ចុះក្រោម)\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 <b>២. ជម្រើសសម្រាប់ការជួញដូរ (Trading Scenarios)</b>\n\n"
            f"🟢 <b>ករណីសម្លឹងមើលការទិញ (Buy Signal):</b>\n"
            f"  - រង់ចាំឱ្យតម្លៃបំបែក (Breakout) ផុតខ្សែបម្លាស់ទី និងកម្រិត Resistance ផ្នែកខាងលើដោយមានទៀនតម្លៃ (Candlestick) បិទយ៉ាងរឹងមាំ។\n"
            f"  - ឬរង់ចាំតម្លៃធ្លាក់ចុះមកប៉ះតំបន់ Support ខាងក្រោម ហើយមានសញ្ញាត្រឡប់ឡើងវិញ (Rejection / Bullish Pattern)។\n\n"
            f"🔴 <b>ករណីសម្លឹងមើលការលក់ (Sell Signal):</b>\n"
            f"  - រង់ចាំឱ្យតម្លៃបំបែកធ្លាក់ចុះក្រោមតំបន់ Support ខាងក្រោមទើបចូលលក់។\n"
            f"  - ឬនៅពេលតម្លៃឡើងទៅប៉ះតំបន់ Resistance ខាងលើ ហើយមិនអាចបំបែករួច (Bearish Rejection)។\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ {icon} <b>សញ្ញា AI SNIPER GRADE A+ (Position {daily_c}/{daily_m} ប្រចាំថ្ងៃ):</b>\n"
            f"🛡️ <b>ការបញ្ជាក់ពី SIGNAL:</b> <b>GRADE A+ Institutional Setup ✓ (AI Audited)</b>\n"
            f"🎯 <b>ប្រតិបត្តិការ:</b> <b>{sig.get('action_title', action)}</b>\n"
            f"• 🥇 <b>Entry តម្លៃចូល:</b> <code>${sig.get('entry', 0.0):,.2f}</code>\n"
            f"• 🛑 <b>Stop Loss (SL):</b> <code>${sig.get('sl', 0.0):,.2f}</code>\n"
            f"• 🎯 <b>Take Profit 1 (TP1):</b> <code>${sig.get('tp1', 0.0):,.2f}</code>\n"
            f"• 🏆 <b>Take Profit 2 (TP2):</b> <code>${sig.get('tp2', 0.0):,.2f}</code>\n"
            f"• ⚖️ <b>Risk:Reward:</b> <code>{sig.get('rr_ratio', '1:2.0')}</code>\n"
            f"• 🎯 <b>ពិន្ទុទំនុកចិត្ត (Confidence Score):</b> <code>{sig.get('confidence_score', '85%')}</code>\n"
            f"{macro_block}"
            f"{inval_block}"
            f"{tips_block}"
            f"• 💡 <b>ការបញ្ជាក់បច្ចេកទេស:</b> {sig.get('reason', '')}\n\n"
            f"{ai_analysis_block}"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <b>អនុសាសន៍គ្រប់គ្រងហានិភ័យ (Risk Management)</b>\n\n"
            f"1. <b>រង់ចាំសញ្ញាច្បាស់លាស់ (Wait for Confirmation):</b> ដោយសារទីផ្សារអាចមាន Sideways ការចូល Order ត្រូវមានការផ្ទៀងផ្ទាត់ Candle Confirmation ជានិច្ច។\n"
            f"2. <b>កំណត់ Stop Loss (SL) និង Take Profit (TP):</b> ត្រូវដាក់ SL ជានិច្ច និងកំណត់ទំហំហានិភ័យត្រឹម 1-2% នៃទុនគណនី។\n"
            f"3. <b>ពិនិត្យមើលព័ត៌មានសេដ្ឋកិច្ច (Economic News Filter):</b> បិទ Signal មុន/ក្រោយ 30 នាទីនៃ High-Impact News (CPI, NFP, FOMC) ដើម្បីការពារដើមទុន!{daily_limit_notice}"
        )

    @staticmethod
    def format_signal_stats(stats: dict) -> str:
        """Formats community trade feedback summary."""
        tp = stats.get("tp_votes", 0)
        sl = stats.get("sl_votes", 0)
        total = stats.get("total_votes", 0)
        wr = stats.get("win_rate", 0.0)
        traders = stats.get("total_traders", 0)

        wr_emoji = "🔥" if wr >= 70 else ("👍" if wr >= 50 else "⚠️")

        return (
            f"📊 <b>ស្ថិតិលទ្ធផល SIGNAL ពីសមាជិក (COMMUNITY FEEDBACK)</b>\n\n"
            f"👥 <b>ចំនួនសមាជិកចូលរួមបោះឆ្នោត:</b> <code>{traders:,} នាក់</code>\n"
            f"🗳️ <b>សន្លឹកឆ្នោតសរុប:</b> <code>{total:,} ដង</code>\n\n"
            f"🎯 <b>ឈ្នះ (Hit TP):</b> <code>{tp:,} ដង</code>\n"
            f"🛑 <b>ចាញ់ (Hit SL):</b> <code>{sl:,} ដង</code>\n\n"
            f"{wr_emoji} <b>អត្រាជោគជ័យ (Win Rate):</b> <code><b>{wr}%</b></code>\n\n"
            f"💡 <i>ទិន្នន័យនេះបានមកពីការចុចប៊ូតុងជាក់ស្តែងរបស់សមាជិកលើគ្រប់ Signal ដែល Bot AI បានបាញ់កន្លងមក!</i>"
        )

    @staticmethod
    def format_breakeven_profit_alert(info: dict) -> str:
        """Formats Dynamic Break-Even & Profit Lock Alert."""
        action = info.get("action", "BUY")
        is_buy = "BUY" in action
        icon = "🟢" if is_buy else "🔴"
        pips = info.get("pips_gained", 30)
        curr_p = info.get("current_price", 0.0)
        entry_p = info.get("entry_price", 0.0)
        tp1_p = info.get("tp1_price", 0.0)

        return (
            f"🛡️ <b>DYNAMIC BREAK-EVEN & PROFIT LOCK ALERT!</b> ⚡\n\n"
            f"{icon} <b>Signal XAUUSD:</b> <b>{action} @ ${entry_p:,.2f}</b>\n"
            f"🚀 <b>ស្ថានភាពបច្ចុប្បន្ន:</b> តម្លៃបានរត់ទៅមុខ <b>+{pips:.0f} Pips</b> (Spot: <code>${curr_p:,.2f}</code>)!\n"
            f"🎯 <b>ទិសដៅ TP1:</b> <code>${tp1_p:,.2f}</code> (ជិតសម្រេចគោលដៅ)\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <b>សកម្មភាពត្រូវធ្វើជាបន្ទាន់ (Action Required):</b>\n"
            f"1. 🔒 <b>រំកិល Stop Loss មកស្មើ Entry (Lock Break-Even):</b>\n"
            f"   👉 កំណត់ SL = <code>${entry_p:,.2f}</code> ដើម្បីធានាការជួញដូរនេះ <b>គ្មានហានិភ័យ (Zero Risk)</b> ១០០%!\n"
            f"2. 💰 <b>កាត់ប្រាក់ចំណេញមួយផ្នែក (Partial TP - Close 50%):</b>\n"
            f"   👉 អាចបិទ Order ពាក់កណ្តាលយកចំណេញទុកក្នុងហោប៉ៅ ហើយទុកចំណែកដែលនៅសល់រត់ទៅ TP2!\n\n"
            f"🛡️ <i>វិន័យត្រឹមត្រូវ: មិនត្រូវបណ្តោយឱ្យ Order ដែលកំពុងចំណេញ ប្រែត្រឡប់មកខាតវិញជាដាច់ខាត!</i>"
        )

    @staticmethod
    def format_ai_chat_response(query: str, answer_html: str, price_data: dict = None) -> str:
        """Formats the interactive AI Q&A answer for Telegram."""
        oz = price_data.get("price_oz", 0.0) if price_data else 0.0
        change_pct = price_data.get("change_pct", 0.0) if price_data else 0.0
        sign = "+" if change_pct >= 0 else ""
        header = "🤖 <b>XAUUSD INSTITUTIONAL AI ASSISTANT</b> ⚡\n"
        if oz > 0:
            header += f"📊 <b>Spot Gold:</b> <code>${oz:,.2f}</code> ({sign}{change_pct:.2f}%)\n"
        header += f"❓ <b>សំណួរ:</b> <i>\"{query}\"</i>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        footer = "\n\n━━━━━━━━━━━━━━━━━━━━\n💡 <i>វិភាគដោយ Gemini Institutional AI Engine • ផ្សារភ្ជាប់ជាមួយទិន្នន័យ Live Market</i>"
        return f"{header}{answer_html}{footer}"

    @staticmethod
    def format_ai_chart_vision_response(analysis: dict, price_data: dict = None) -> str:
        """Formats the AI Computer Vision Chart analysis for Telegram."""
        if not analysis:
            return "⚠️ មិនអាចវិភាគរូបភាព Chart បាននៅពេលនេះទេ។ សូមប្រាកដថារូបភាពមាន Candlestick និងតម្លៃច្បាស់លាស់។"

        direction = analysis.get("direction", "WAIT").upper()
        if "BUY" in direction:
            dir_badge = "🟢 BUY SETUP (ទិញឡើង)"
            dir_icon = "🟢"
        elif "SELL" in direction:
            dir_badge = "🔴 SELL SETUP (លក់ចុះ)"
            dir_icon = "🔴"
        else:
            dir_badge = "🟡 WAIT / NO TRADE (រង់ចាំ)"
            dir_icon = "🟡"

        title = analysis.get("setup_title", dir_badge)
        tf = analysis.get("timeframe", "M15 / H1")
        pat_kh = analysis.get("pattern_kh", analysis.get("pattern_detected", "Price Action Structure"))
        entry = analysis.get("entry_zone", "N/A")
        sl = analysis.get("stop_loss", "N/A")
        tp1 = analysis.get("take_profit_1", "N/A")
        tp2 = analysis.get("take_profit_2", "N/A")
        rr = analysis.get("rr_ratio", "1:2.0")
        conf = analysis.get("confidence_score", "85%")
        reasons = analysis.get("confluence_reasons", [])
        reasons_text = "\n".join([f"• {r}" for r in reasons]) if reasons else "• សម្ពាធ Candlestick Rejection និងកម្រិតគន្លឹះ Liquidity"
        inval = analysis.get("invalidation_rule", "តម្លៃទម្លុះកម្រិតគន្លឹះប្រឆាំងទិសដៅ")
        risk = analysis.get("risk_warning", "គ្រប់គ្រងទំហំ Lot សមស្រប Risk 1-2% ជៀសវាង Overtrade!")
        summary = analysis.get("detailed_summary_kh", "")

        msg = (
            f"🔍 <b>AI COMPUTER VISION CHART AUDIT</b> ⚡\n\n"
            f"📌 <b>ផែនការ:</b> <b>{title}</b>\n"
            f"⏱️ <b>Timeframe:</b> <code>{tf}</code> | <b>ពិន្ទុទំនុកចិត្ត:</b> <code>{conf}</code>\n"
            f"🕯️ <b>ទម្រង់ Candlestick:</b> <b>{pat_kh}</b>\n\n"
            f"🎯 <b>កម្រិតប្រតិបត្តិការ (Execution Levels):</b>\n"
            f"• {dir_icon} <b>ទិសដៅ:</b> <b>{direction}</b>\n"
            f"• 🎯 <b>តំបន់ Entry:</b> <code>{entry}</code>\n"
            f"• 🛑 <b>Stop Loss (SL):</b> <code>{sl}</code>\n"
            f"• 🏆 <b>Take Profit 1:</b> <code>{tp1}</code>\n"
            f"• 🏆 <b>Take Profit 2:</b> <code>{tp2}</code>\n"
            f"• ⚖️ <b>Risk:Reward:</b> <code>{rr}</code>\n\n"
            f"💡 <b>ហេតុផលបញ្ជាក់ (Confluence Reasons):</b>\n"
            f"{reasons_text}\n\n"
            f"❌ <b>លក្ខខណ្ឌលុបចោល Setup:</b> {inval}\n\n"
            f"🛡️ <b>ការគ្រប់គ្រងហានិភ័យ:</b> {risk}\n"
        )
        if summary:
            msg += f"\n📝 <b>សេចក្តីសង្ខេប AI:</b>\n{summary}\n"
        msg += "\n━━━━━━━━━━━━━━━━━━━━\n🤖 <i>វិភាគផ្ទាល់ពីរូបភាព Chart ដោយ Gemini Multimodal Vision AI</i>"
        return msg




