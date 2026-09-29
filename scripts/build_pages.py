#!/usr/bin/env python3
"""Generate the governorate + Instagram-stores landing pages from index.html.

The pages are flat files in the repo root (Cloudflare Pages serves them at
/delivery-hawalli etc.) so the relative assets/ URLs in the shared inline
<style> keep working. They reuse index.html's exact <style> block, so the CSP
hash in _headers stays valid. Re-run after editing that block, then refresh the
hash (see README) and sitemap.
"""
import base64, hashlib, html, json, os, re, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://deliverykw.com"
WA = "https://wa.me/96599454818"
TODAY = "2026-09-29"

idx = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
STYLE = re.search(r"<style>.*?</style>", idx, re.S).group(0)
THEME = re.search(r"<script>try\{if\(localStorage.*?</script>", idx, re.S).group(0)
DEFS = re.search(r'<svg class="svg-defs".*?</svg>', idx, re.S).group(0)
LOGO = re.search(r'<a class="brand".*?</a>', idx, re.S).group(0)
MODE_BTN = re.search(r'<button class="mode".*?</button>', idx, re.S).group(0)
DOCK = re.search(r'<a class="fab js-wa".*?</nav>', idx, re.S).group(0)

GOVS = [
    dict(slug="delivery-capital", name="العاصمة", main="مدينة الكويت", title="مندوب توصيل العاصمة ومدينة الكويت",
         areas=["مدينة الكويت", "الشرق", "القبلة", "دسمان", "الصالحية", "المرقاب", "بنيد القار", "الدعية", "الشويخ", "الدسمة", "كيفان", "الشامية", "القادسية", "قرطبة", "السرة", "اليرموك", "الخالدية", "الروضة", "العديلية", "الفيحاء", "النزهة", "المنصورية", "الصليبيخات", "الري", "غرناطة", "النهضة"],
         intro="نوصل طلبات العاصمة من وإلى مدينة الكويت والشرق والقبلة والشويخ والدسمة وكيفان وباقي مناطق المحافظة. سواء عندك أغراض من مكتب أو محل في مدينة الكويت تبي توصلها لحد باب العميل، أو طلب جاي من محافظة ثانية لمنطقة في العاصمة، نرتب لك مندوب توصيل على مدار 24 ساعة.",
         example=("الشويخ", "السالمية")),
    dict(slug="delivery-hawalli", name="حولي", main="السالمية", title="مندوب توصيل حولي والسالمية",
         areas=["حولي", "السالمية", "الجابرية", "الرميثية", "مشرف", "بيان", "سلوى", "الشعب", "الزهراء", "الصديق", "حطين", "السلام", "الشهداء", "ميدان حولي"],
         intro="مندوب توصيل طلبات في حولي والسالمية والجابرية والرميثية ومشرف وبيان وسلوى وباقي مناطق محافظة حولي. المحافظة فيها ازدحام وأسواق ومحلات كثيرة، فنرتب لك استلام وتسليم من الباب للباب بدون ما تحتاج تطلع من مكانك، وعلى مدار 24 ساعة.",
         example=("السالمية", "الجهراء")),
    dict(slug="delivery-farwaniya", name="الفروانية", main="خيطان", title="مندوب توصيل الفروانية وخيطان",
         areas=["الفروانية", "خيطان", "جليب الشيوخ", "العارضية", "الرابية", "الأندلس", "الرقعي", "العمرية", "الفردوس", "صباح الناصر", "الرحاب", "عبدالله المبارك", "اشبيلية", "الضجيج", "العباسية"],
         intro="نوصل طلبات الفروانية من وإلى خيطان وجليب الشيوخ والعارضية والرابية والأندلس والرقعي وباقي مناطق المحافظة. إذا عندك طلب من الفروانية لأي منطقة ثانية في الكويت أو العكس، راسلنا وحدد الاستلام والتسليم ونأكد لك السعر ووقت وصول المندوب.",
         example=("خيطان", "الفحيحيل")),
    dict(slug="delivery-mubarak-al-kabeer", name="مبارك الكبير", main="صباح السالم", title="مندوب توصيل مبارك الكبير وصباح السالم",
         areas=["صباح السالم", "القرين", "العدان", "المسيلة", "أبو فطيرة", "أبو الحصانية", "القصور", "الفنيطيس", "صبحان", "مبارك الكبير", "المسايل", "الوسطى"],
         intro="مندوب توصيل في مبارك الكبير وصباح السالم والقرين والعدان والمسيلة وأبو فطيرة والقصور وباقي مناطق المحافظة. تقدر تطلب توصيل أغراض أو طلبات متجر من أي منطقة بالكويت لحد باب العميل في مبارك الكبير، في أي ساعة من اليوم.",
         example=("صباح السالم", "حولي")),
    dict(slug="delivery-ahmadi", name="الأحمدي", main="الفحيحيل", title="مندوب توصيل الأحمدي والفحيحيل والمنقف",
         areas=["الأحمدي", "الفحيحيل", "المنقف", "المهبولة", "الصباحية", "أبو حليفة", "الفنطاس", "الرقة", "هدية", "العقيلة", "الظهر", "الوفرة", "الزور", "الخيران", "صباح الأحمد السكنية", "الجليعة", "الشعيبة"],
         intro="نوصل طلبات الأحمدي من وإلى الفحيحيل والمنقف والمهبولة والصباحية وأبو حليفة والفنطاس والرقة وباقي مناطق المحافظة الجنوبية. المسافات في الأحمدي أطول، فنأكد لك السعر ووقت الوصول على واتساب قبل ما نستلم الطلب.",
         example=("الفحيحيل", "الجهراء")),
    dict(slug="delivery-jahra", name="الجهراء", main="الجهراء", title="مندوب توصيل الجهراء وسعد العبدالله",
         areas=["الجهراء", "سعد العبدالله", "القصر", "العيون", "النسيم", "النعيم", "تيماء", "الواحة", "الصليبية", "أمغرة", "كبد", "العبدلي", "السالمي"],
         intro="مندوب توصيل طلبات في الجهراء وسعد العبدالله والقصر والعيون والنسيم والنعيم وتيماء والواحة وباقي مناطق المحافظة. نوصل من وإلى الجهراء لأي منطقة بالكويت على مدار 24 ساعة، والسعر حسب المسافة نأكده لك قبل الاستلام.",
         example=("الجهراء", "السالمية")),
]

SERVICES = [
    ("توصيل أغراض شخصية", "ملابس وإكسسوارات وأغراض بين أي منطقتين داخل الكويت."),
    ("توصيل هدايا", "نوصل الهدية لحد الباب في الموعد اللي تحدده."),
    ("توصيل طلبات المطاعم", "اكتب لنا منطقة الاستلام والتسليم ونأكد لك السعر."),
]

STEPS = [
    ("راسلنا على واتساب", "أرسل موقع الاستلام وموقع التسليم ونوع الطلب على الرقم 99454818."),
    ("نأكد السعر والوقت", "نرد عليك بسعر التوصيل ووقت وصول المندوب قبل ما نستلم أي شي."),
    ("نستلم ونسلّم", "المندوب يستلم من الباب ويسلّم للباب، والدفع كاش أو أونلاين."),
]


def esc(s):
    return html.escape(s, quote=True)


def wa_link(text):
    return WA + "?text=" + urllib.parse.quote(text)


def page(slug, title, desc, h1, lead, body, faqs, breadcrumb, extra_ld=None, wa_text="السلام عليكم، أبي أطلب توصيل مع Delivery.KW"):
    url = f"{SITE}/{slug}"
    wa = wa_link(wa_text)
    dock = DOCK.replace(' js-wa"', '"').replace('href="https://wa.me/96599454818"', f'href="{wa}"')
    ld = [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": u}
            for i, (n, u) in enumerate(breadcrumb)]},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]},
        {"@type": "WebPage", "@id": url + "#page", "url": url, "name": title, "inLanguage": "ar-KW",
         "isPartOf": {"@id": SITE + "/#website"}, "about": {"@id": SITE + "/#business"}},
    ]
    if extra_ld:
        ld.append(extra_ld)
    ldjson = json.dumps({"@context": "https://schema.org", "@graph": ld}, ensure_ascii=False, indent=1)
    faq_html = "".join(f"        <details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>\n" for q, a in faqs)
    crumbs = " › ".join(f'<a href="{u}">{esc(n)}</a>' if i < len(breadcrumb) - 1 else esc(n)
                        for i, (n, u) in enumerate(breadcrumb))
    return f"""<!doctype html>
<html lang="ar-KW" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="ar-kw" href="{url}">
<link rel="alternate" hreflang="x-default" href="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="ar_KW">
<meta property="og:site_name" content="Delivery.KW">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE}/assets/door-to-door.jpg">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{ldjson}
</script>
<meta name="theme-color" content="#0A1733">
{THEME}
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" href="/assets/favicon-48.png" sizes="48x48">
<link rel="icon" type="image/png" href="/assets/favicon-32.png" sizes="32x32">
<link rel="icon" type="image/png" href="/assets/icon-192.png" sizes="192x192">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/readex-pro-arabic.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/reem-kufi-arabic.woff2" as="font" type="font/woff2" crossorigin>
{STYLE}
</head>
<body>
{DEFS}
<header class="bar">
  <div class="wrap">
    {LOGO.replace('href="#top"', 'href="/"')}
    <nav aria-label="أقسام الموقع">
      <a href="/">الرئيسية</a>
      <a href="/#order">اطلب الحين</a>
      <a href="/#areas">مناطق التوصيل</a>
      <a href="/instagram-stores-delivery">للمتاجر</a>
    </nav>
    <div class="end">
      {MODE_BTN}
      <a class="btn btn-wa btn-sm" href="{wa}" target="_blank" rel="noopener noreferrer"><svg aria-hidden="true"><use href="#i-wa"/></svg>واتساب</a>
    </div>
  </div>
</header>
<main>
  <section class="phero">
    <div class="wrap">
      <p class="crumbs">{crumbs}</p>
      <h1>{esc(h1)}</h1>
      <p class="lead">{esc(lead)}</p>
      <div class="cta-row">
        <a class="btn btn-wa" href="{wa}" target="_blank" rel="noopener noreferrer"><svg aria-hidden="true"><use href="#i-wa"/></svg>اطلب عبر واتساب</a>
        <a class="btn btn-ig" href="https://www.instagram.com/td.delivery1/" target="_blank" rel="noopener noreferrer"><svg aria-hidden="true"><use href="#i-ig"/></svg>تابعنا على انستجرام</a>
      </div>
    </div>
  </section>
{body}
  <section class="block flush" id="faq">
    <div class="wrap">
      <div class="head">
        <p class="eyebrow">أسئلة متكررة</p>
        <h2>قبل ما تطلب</h2>
      </div>
      <div class="faq">
{faq_html}      </div>
    </div>
  </section>
  <section class="block flush">
    <div class="wrap">
      <div class="head"><h2>مناطق أخرى نوصل لها</h2></div>
      <div class="plinks">
{"".join(f'        <a href="/{g["slug"]}">{esc(g["name"])}</a>' + chr(10) for g in GOVS if g["slug"] != slug)}        <a href="/instagram-stores-delivery">متاجر انستجرام والمشاريع</a>
        <a href="/delivery-guide-kuwait">دليل اختيار مندوب توصيل</a>
        <a href="/">كل مناطق الكويت</a>
      </div>
    </div>
  </section>
</main>
<footer>
  <div class="wrap">
    <span>© 2026 Delivery.KW (deliverykw.com) · توصيل طلبات الكويت · مندوب توصيل 24 ساعة</span>
    <span>واتساب <span class="num">+965 99454818</span></span>
    <p class="sign">تصميم وتطوير <a href="https://kimoo193.github.io/portfolio/" target="_blank" rel="noopener">كريم مرسي</a> · Designed &amp; developed by <a href="https://kimoo193.github.io/portfolio/" target="_blank" rel="noopener">Kareem Moursy</a></p>
  </div>
</footer>

{dock}
<script src="/assets/site.js?v=1" defer></script>
</body>
</html>
"""


def section(eyebrow, h2, inner, lead=""):
    p = f"\n        <p>{esc(lead)}</p>" if lead else ""
    return f"""  <section class="block flush">
    <div class="wrap">
      <div class="head">
        <p class="eyebrow">{esc(eyebrow)}</p>
        <h2>{esc(h2)}</h2>{p}
      </div>
{inner}
    </div>
  </section>"""


def services_html():
    return '      <div class="services">\n' + "".join(
        f'        <article class="service"><h3>{esc(t)}</h3><p>{esc(d)}</p></article>\n' for t, d in SERVICES) + "      </div>"


def steps_html():
    return '      <div class="steps">\n' + "".join(
        f'        <div class="step"><h3>{esc(t)}</h3><p>{esc(d)}</p></div>\n' for t, d in STEPS) + "      </div>"


pages = {}

for g in GOVS:
    n, others = g["name"], [x for x in GOVS if x is not g]
    a = g["areas"]
    ex_from, ex_to = g["example"]
    routes = [f"من {a[0]} إلى {others[0]['areas'][0]}", f"من {others[1]['areas'][0]} إلى {a[1] if len(a) > 1 else a[0]}",
              f"من {a[2] if len(a) > 2 else a[0]} إلى {others[2]['areas'][0]}", f"من {others[3]['areas'][0]} إلى {a[3] if len(a) > 3 else a[0]}"]
    body = "\n".join([
        section("مناطق التغطية", f"مناطق {n} اللي نوصل لها",
                '      <ul class="chips-list">\n' + "".join(f'        <li><a href="{wa_link("السلام عليكم، أبي مندوب توصيل في " + x)}" target="_blank" rel="noopener noreferrer">{esc(x)}</a></li>\n' for x in a) + "      </ul>",
                f"هذي أبرز {len(a)} منطقة نغطيها في محافظة {n}. إذا منطقتك مو مكتوبة راسلنا على واتساب ونأكد لك التغطية."),
        section("مسارات نوصلها", f"توصيل من وإلى {n}",
                '      <ul class="chips-list">\n' + "".join(f'        <li><a href="{wa_link("السلام عليكم، أبي توصيل " + x)}" target="_blank" rel="noopener noreferrer">{esc(x)}</a></li>\n' for x in routes) + "      </ul>",
                f"أمثلة على طلبات نوصلها بين {n} وباقي المحافظات، والسعر حسب المسافة ونأكده لك قبل الاستلام."),
        section("خدماتنا", f"شنو نوصل في {n}؟", services_html()),
        section("طريقة الطلب", "ثلاث خطوات ويوصل طلبك", steps_html()),
    ])
    faqs = [
        (f"تشتغلون توصيل في {n} على مدار 24 ساعة؟", f"إيه، خدمتنا 24 ساعة طول الأسبوع. راسلنا على واتساب 99454818 في أي وقت ونرتب لك مندوب توصيل في {n} أو من {n} لأي منطقة ثانية."),
        (f"شنو أرسل لكم عشان أطلب مندوب توصيل في {n}؟", f"أرسل منطقة الاستلام ومنطقة التسليم ونوع الطلب، مثال: من {ex_from} إلى {ex_to}. نرد عليك بالسعر ووقت وصول المندوب قبل ما نستلم."),
        (f"شنو رقم مندوب توصيل {n}؟", f"رقم Delivery.KW للطلب والاتصال هو 99454818 (واتساب واتصال)، ونرتب لك مندوب توصيل في {n} على مدار 24 ساعة."),
        (f"كم سعر التوصيل من وإلى {n}؟", "أسعار التوصيل تبدأ من دينارين (2 د.ك) وتزيد حسب المسافة بين منطقة الاستلام ومنطقة التسليم، ونأكد لك السعر النهائي على واتساب قبل الاستلام. الدفع كاش أو أونلاين."),
    ]
    ld = {"@type": "Service", "serviceType": "مندوب توصيل طلبات وأغراض", "name": g["title"] + " 24 ساعة",
          "provider": {"@id": SITE + "/#business"},
          "areaServed": [{"@type": "AdministrativeArea", "name": f"محافظة {n}"}] + [{"@type": "City", "name": x} for x in a],
          "availableChannel": {"@type": "ServiceChannel", "serviceUrl": WA, "servicePhone": "+96599454818"}}
    pages[g["slug"]] = page(
        g["slug"], f"{g['title']} 24 ساعة | Delivery.KW",
        f"{g['title']} على مدار 24 ساعة. توصيل أغراض وهدايا وطلبات متاجر من الباب للباب في {n}: " + "، ".join(a[:5]) + ". اطلب عبر واتساب 99454818.",
        f"{g['title']} 24 ساعة", g["intro"], body, faqs,
        [("الرئيسية", SITE + "/"), (f"توصيل {n}", f"{SITE}/{g['slug']}")], ld,
        wa_text=f"السلام عليكم، أبي مندوب توصيل في {n}")

# Instagram stores / small business page
store_faqs = [
    ("هل توصلون طلبات متاجر انستجرام؟", "إيه، نوصل طلبات عملاء متاجر انستجرام والمشاريع المنزلية يوميًا أو حسب الطلب، في جميع محافظات الكويت الست."),
    ("في أسعار خاصة للمشاريع الصغيرة والمتوسطة؟", "إيه، عندنا أسعار خاصة لأصحاب المشاريع. راسلنا على واتساب وقول لنا كم طلب تتوقع بالأسبوع ونعطيك سعر مناسب."),
    ("شنو أجهّز لكم مع كل طلب؟", "رقم العميل، موقعه أو وصف واضح لعنوانه، منطقة الاستلام من عندك، ونوع الطلب. كل ما كانت المعلومات أوضح كان التسليم أسرع."),
    ("شلون أدفع لكم؟", "كاش أو أونلاين، اللي يناسبك، ونتفق عليه قبل الاستلام."),
    ("أقدر أتواصل مع المندوب مباشرة؟", "إيه، يكون عندك تواصل مباشر مع المندوب عشان تتابع طلباتك."),
]
store_body = "\n".join([
    section("لأصحاب المتاجر", "ليش تختار Delivery.KW لمتجرك؟",
            '      <div class="services">\n'
            + "".join(f'        <article class="service"><h3>{esc(t)}</h3><p>{esc(d)}</p></article>\n' for t, d in [
                ("توصيل يومي أو حسب الطلب", "ترسل لنا الطلبات اللي جاهزة ونوصلها لعملائك في نفس اليوم حسب المتفق عليه."),
                ("سعر واضح قبل الاستلام", "نأكد لك السعر على واتساب قبل ما نستلم أي طلب، وعندنا أسعار خاصة للمشاريع."),
                ("مندوب تعرفه", "تواصل مباشر مع المندوب عشان تتابع طلباتك وتطمن على عملائك."),
            ]) + "      </div>",
            "متجر انستجرام أو مشروع من البيت؟ ركّز على البيع وخلّنا نتولى توصيل الطلبات لباب العميل."),
    section("جهّز طلبك", "شنو تجهز مع كل طلب؟",
            '      <ul class="chips-list">\n' + "".join(f"        <li>{esc(x)}</li>\n" for x in [
                "اسم ورقم العميل", "موقع التسليم أو وصف واضح للعنوان", "منطقة الاستلام", "نوع الطلب وحجمه", "طريقة الدفع", "وقت التسليم المناسب"]) + "      </ul>",
            "معلومات واضحة تعني توصيل أسرع وأقل اتصالات بينك وبين العميل."),
    section("مناطق التغطية", "نوصل لعملائك في كل المحافظات",
            '      <div class="plinks">\n' + "".join(f'        <a href="/{g["slug"]}">{esc(g["name"])}</a>\n' for g in GOVS) + "      </div>"),
    section("طريقة الطلب", "ثلاث خطوات ويوصل طلبك", steps_html()),
])
pages["instagram-stores-delivery"] = page(
    "instagram-stores-delivery", "توصيل طلبات متاجر انستجرام والمشاريع المنزلية في الكويت | Delivery.KW",
    "مندوب توصيل لطلبات متاجر انستجرام والمشاريع المنزلية في الكويت، يوميًا أو حسب الطلب، بأسعار خاصة للمشاريع وسعر واضح قبل الاستلام. اطلب عبر واتساب 99454818.",
    "توصيل طلبات متاجر انستجرام والمشاريع في الكويت",
    "خدمة توصيل يومية أو حسب الطلب لعملاء متاجر انستجرام والمشاريع المنزلية في جميع مناطق الكويت، بأسعار خاصة وتواصل مباشر مع المندوب.",
    store_body, store_faqs,
    [("الرئيسية", SITE + "/"), ("توصيل متاجر انستجرام", SITE + "/instagram-stores-delivery")],
    {"@type": "Service", "serviceType": "توصيل طلبات المتاجر والمشاريع", "name": "توصيل طلبات متاجر انستجرام والمشاريع المنزلية",
     "provider": {"@id": SITE + "/#business"}, "areaServed": {"@type": "Country", "name": "الكويت"}},
    wa_text="السلام عليكم، عندي متجر وأبي أسأل عن توصيل الطلبات")


# Guide page
guide_tips = [
    ("حدد منطقتي الاستلام والتسليم بوضوح", "اكتب اسم المنطقة والقطعة أو الشارع ومعلمًا قريبًا. السعر ووقت الوصول يعتمدان على المسافة بين المنطقتين، وكل ما كان العنوان أوضح كان التسليم أسرع."),
    ("اطلب تأكيد السعر قبل الاستلام", "اتفق على سعر التوصيل قبل ما يستلم المندوب الطلب، عشان ما تصير مفاجآت بعدين. نحن نأكد السعر ووقت الوصول على واتساب قبل الاستلام."),
    ("جهّز الغرض بشكل سليم", "غلّف الغرض كويس، واكتب على الأغراض القابلة للكسر أو الحساسة، وتأكد من كتابة اسم المستلم ورقمه على الطلب."),
    ("حدد طريقة الدفع من البداية", "اتفق هل الدفع كاش أو أونلاين، وتأكد أن كل الأطراف تعرف المبلغ المطلوب قبل التسليم."),
    ("اذكر الوقت المناسب للمستلم", "قول للمندوب الوقت اللي يكون فيه المستلم موجود. خدمتنا 24 ساعة، فتقدر ترتب التسليم ليلًا أو صباحًا حسب راحة المستلم."),
    ("خلك على تواصل مع المندوب", "احتفظ برقم المندوب أو رقم الخدمة عشان تتابع الطلب. أفضل خدمات التوصيل تخليك تتواصل معها مباشرة بدل الانتظار بدون معلومات."),
]
guide_faqs = [
    ("كم يستغرق مندوب التوصيل في الكويت؟", "الوقت يعتمد على المسافة بين منطقة الاستلام ومنطقة التسليم وعلى ضغط الطلبات وقت الطلب. نقول لك وقت الوصول المتوقع على واتساب أول ما نأكد الطلب."),
    ("شنو الفرق بين مندوب التوصيل وشركة الشحن؟", "مندوب التوصيل يستلم الغرض ويسلّمه من الباب للباب داخل الكويت. شركات الشحن الدولية تتعامل غالبًا مع الشحنات بين الدول ولها مدد وإجراءات مختلفة."),
    ("شنو الأغراض اللي يقدر يوصلها المندوب؟", "عندنا نوصل الأغراض الشخصية والهدايا والملابس والإكسسوارات وطلبات المطاعم وطلبات المتاجر والمشاريع. للطلبات الخاصة أو الكبيرة راسلنا على واتساب ونأكد لك."),
    ("شلون أعرف إن السعر مناسب؟", "قارن سعر التوصيل بالمسافة بين المنطقتين، واطلب تأكيد السعر قبل الاستلام. عندنا أسعار خاصة للمشاريع الصغيرة والمتوسطة."),
]
guide_body = "\n".join([
    section("نصائح عملية", "ست خطوات تسهّل توصيل طلبك",
            '      <div class="services">\n' + "".join(f'        <article class="service"><h3>{esc(t)}</h3><p>{esc(d)}</p></article>\n' for t, d in guide_tips) + "      </div>",
            "سواء تستخدم خدمة ديليفري أو مندوب توصيل لأول مرة، هذي الخطوات تساعدك توصّل طلبك بأمان وبدون تأخير."),
    section("مناطق التغطية", "نوصل في كل محافظات الكويت",
            '      <div class="plinks">\n' + "".join(f'        <a href="/{g["slug"]}">{esc(g["name"])}</a>\n' for g in GOVS) + "      </div>"),
    section("طريقة الطلب", "ثلاث خطوات ويوصل طلبك", steps_html()),
])
pages["delivery-guide-kuwait"] = page(
    "delivery-guide-kuwait", "كيف تختار مندوب توصيل في الكويت؟ دليل توصيل الطلبات والأغراض | Delivery.KW",
    "دليل عملي لاختيار مندوب توصيل داخل الكويت: كيف تحدد العنوان، تتفق على السعر، تجهّز الغرض وتتابع الطلب. مع إجابات عن الديليفري والشحن. Delivery.KW خدمة 24 ساعة.",
    "كيف تختار مندوب توصيل في الكويت؟",
    "دليل بسيط لأي شخص يبي يوصّل طلب أو غرض داخل الكويت: نصائح عملية للعنوان والسعر والتغليف والدفع، وإجابات عن أكثر الأسئلة شيوعًا.",
    guide_body, guide_faqs,
    [("الرئيسية", SITE + "/"), ("دليل التوصيل", SITE + "/delivery-guide-kuwait")],
    {"@type": "Article", "headline": "كيف تختار مندوب توصيل في الكويت؟", "inLanguage": "ar-KW",
     "author": {"@id": SITE + "/#business"}, "publisher": {"@id": SITE + "/#business"},
     "datePublished": TODAY, "dateModified": TODAY, "mainEntityOfPage": SITE + "/delivery-guide-kuwait"})

# ---------- Articles ----------
ARTICLES = [
 dict(slug="article-how-to-order-delivery-kuwait", card="كيف تطلب مندوب توصيل في الكويت خطوة بخطوة",
  title="كيف تطلب مندوب توصيل في الكويت خطوة بخطوة | Delivery.KW",
  desc="خطوات واضحة لطلب مندوب توصيل داخل الكويت: ما تجهزه قبل الطلب، نموذج رسالة واتساب جاهز، تأكيد السعر والوقت وما بعد الاستلام.",
  h1="كيف تطلب مندوب توصيل في الكويت خطوة بخطوة",
  lead="طلب مندوب توصيل ما يحتاج تعقيد. هذي الخطوات تخليك توصّل طلبك بسرعة وبأقل رسائل، مع نموذج رسالة جاهز ترسله على واتساب.",
  secs=[
   ("قبل ما تراسل المندوب: جهّز هذي المعلومات", [("ul",["منطقة الاستلام ومنطقة التسليم، ويفضل معلم قريب أو موقع على الخريطة.","نوع الطلب وحجمه: ملابس، هدية، طلب مطعم، أو غرض آخر.","اسم المستلم ورقم هاتفه.","الوقت المناسب للاستلام والتسليم.","طريقة الدفع: كاش أو أونلاين."])]),
   ("نموذج رسالة جاهز على واتساب", ["انسخ الرسالة التالية وعدّل عليها، وأرسلها على واتساب 99454818:",("quote","السلام عليكم، أبي أطلب توصيل مع Delivery.KW. الاستلام من: [المنطقة]. التسليم إلى: [المنطقة]. نوع الطلب: [ملابس / هدايا / أخرى]. الدفع: [كاش / أونلاين]. ملاحظات: [الوقت المناسب / رقم المستلم]."),"كل ما كانت الرسالة أوضح، كان رد المندوب بالسعر ووقت الوصول أسرع."]),
   ("تأكيد السعر والوقت قبل الاستلام", ["اطلب من المندوب السعر النهائي ووقت الوصول المتوقع قبل ما يستلم الطلب. أسعار التوصيل عندنا تبدأ من دينارين وتزيد حسب المسافة بين المنطقتين، ونأكد لك الرقم على واتساب قبل الاستلام."]),
   ("بعد الاستلام", ["احتفظ برقم المندوب أو رقم الخدمة عشان تتابع الطلب، واطلب من المستلم يتأكد من الغرض لحظة التسليم. للتفاصيل العامة عن اختيار الخدمة المناسبة اقرأ ",("a","دليل اختيار مندوب توصيل في الكويت","/delivery-guide-kuwait"),"."]),
  ],
  faqs=[("هل أقدر أطلب مندوب في أي وقت؟","إيه، خدمتنا 24 ساعة طول الأسبوع، راسلنا على واتساب في أي وقت."),
        ("هل أقدر أرتب الاستلام من شخص ثاني أو من متجر؟","إيه، اكتب لنا منطقة الاستلام واسم المكان أو الشخص، واتفق مع المندوب على التفاصيل عبر واتساب."),
        ("شلون أدفع؟","الدفع كاش أو أونلاين، ونتفق عليه قبل الاستلام.")]),
 dict(slug="article-instagram-store-delivery", card="كيف تنظم توصيل طلبات متجر انستجرام لعملائك",
  title="كيف تنظم توصيل طلبات متجر انستجرام لعملائك في الكويت | Delivery.KW",
  desc="نصائح عملية لأصحاب متاجر انستجرام والمشاريع المنزلية في الكويت: تجهيز الطلبات، تنظيم يوم التوصيل، والاتفاق على السعر والدفع مع مندوب توصيل.",
  h1="كيف تنظم توصيل طلبات متجر انستجرام لعملائك",
  lead="لو عندك متجر على انستجرام أو مشروع من البيت، التوصيل المنظم يفرق في رضا العملاء وتكرار الطلب. هذي طريقة بسيطة ترتب فيها طلباتك.",
  secs=[
   ("ليش التوصيل مهم لمتجرك؟",["العميل يحكم على متجرك من تجربة الطلب كلها، مو بس من المنتج. توصيل في وقت واضح وبتغليف مرتب يخلي العميل يرجع ويطلب مرة ثانية ويوصي غيره."]),
   ("جهّز كل طلب قبل استلام المندوب",[("ul",["غلّف الطلب بشكل سليم واكتب عليه اسم العميل.","تأكد من رقم العميل وموقع التسليم أو وصف واضح للعنوان.","اكتب ملاحظات مهمة على الطلب مثل قابل للكسر أو يحتاج تسليم باليد.","حدد إذا الدفع تم مسبقًا أو كاش عند التسليم."])]),
   ("نظّم يوم التوصيل",[("ul",["اجمع الطلبات حسب المنطقة عشان تنظم التسليم.","أرسل للمندوب قائمة الطلبات مع مناطق التسليم قبل موعد الاستلام.","خبّر العملاء بالوقت المتوقع للتوصيل."]),"وإذا كان عندك طلبات يومية، اسأل عن الأسعار الخاصة للمشاريع الصغيرة والمتوسطة."]),
   ("السعر والدفع",["أسعار التوصيل تبدأ من دينارين وتزيد حسب المسافة، وعندنا أسعار خاصة لأصحاب المشاريع. الدفع كاش أو أونلاين، ونتفق على التفاصيل قبل البدء. شوف صفحة ",("a","توصيل طلبات متاجر انستجرام والمشاريع","/instagram-stores-delivery"),"."]),
  ],
  faqs=[("هل توصلون طلبات متاجر انستجرام يوميًا؟","إيه، نوصل يوميًا أو حسب الطلب في جميع محافظات الكويت الست."),
        ("في أسعار خاصة للمشاريع؟","إيه، راسلنا على واتساب وقول لنا كم طلب تتوقع بالأسبوع."),
        ("أقدر أتواصل مع المندوب مباشرة؟","إيه، يكون عندك تواصل مباشر مع المندوب عشان تتابع طلباتك.")]),
 dict(slug="article-gift-delivery-kuwait", card="توصيل الهدايا في الكويت: تغليف وتوقيت وتسليم",
  title="توصيل الهدايا في الكويت: تغليف وتوقيت وتسليم | Delivery.KW",
  desc="كيف توصّل هدية بأمان داخل الكويت: اختيار الوقت المناسب، تغليف الهدية، بيانات المستلم، وتنسيق التسليم مع مندوب توصيل على مدار 24 ساعة.",
  h1="توصيل الهدايا في الكويت: تغليف وتوقيت وتسليم",
  lead="الهدية اللي توصل في وقتها وبشكل مرتب تكمّل فرحة المناسبة. هذي نقاط تساعدك توصّل هديتك بدون قلق.",
  secs=[
   ("اختر الوقت المناسب للتسليم",["حدد وقت يكون فيه المستلم موجود، وخصوصًا إذا الهدية مفاجأة. خدمتنا 24 ساعة، فتقدر ترتب التسليم صباحًا أو مساءً حسب المناسبة."]),
   ("غلّف الهدية بشكل يحميها",[("ul",["استخدم علبة مناسبة للحجم وثبّت الهدية داخلها.","الأغراض القابلة للكسر تحتاج حماية إضافية واكتب عليها بوضوح.","ضع بطاقة أو رسالة داخل العلبة بدل ما تنكتب على الغلاف من الخارج."])]),
   ("بيانات المستلم",["أرسل اسم المستلم ورقمه وموقع التسليم. إذا كانت مفاجأة، اتفق مع المندوب على طريقة التواصل عشان ما ينكشف السر."]),
   ("الطلب في المناسبات",["في أيام المناسبات يزيد الضغط على التوصيل، فالأفضل تراسل مبكرًا وتحدد الوقت. أسعارنا تبدأ من دينارين وتزيد حسب المسافة، ونأكدها قبل الاستلام. المناطق المغطاة: ",("a","حولي","/delivery-hawalli"),"، ",("a","العاصمة","/delivery-capital"),"، ",("a","الفروانية","/delivery-farwaniya"),"، ",("a","مبارك الكبير","/delivery-mubarak-al-kabeer"),"، ",("a","الأحمدي","/delivery-ahmadi")," و",("a","الجهراء","/delivery-jahra"),"."]),
  ],
  faqs=[("هل توصلون هدايا داخل الكويت كلها؟","إيه، نوصل هدايا في جميع محافظات الكويت الست."),
        ("أقدر أطلب توصيل هدية مفاجأة؟","إيه، اكتب لنا التفاصيل على واتساب ونتفق على وقت وطريقة تناسب المفاجأة."),
        ("كم سعر توصيل الهدية؟","تبدأ الأسعار من دينارين وتزيد حسب المسافة، ونأكد السعر قبل الاستلام.")]),
 dict(slug="article-delivery-price-kuwait", card="كم يكلف مندوب التوصيل في الكويت؟",
  title="كم يكلف مندوب التوصيل في الكويت؟ العوامل التي تحدد السعر | Delivery.KW",
  desc="ما الذي يحدد سعر مندوب التوصيل في الكويت؟ أسعار Delivery.KW تبدأ من دينارين وتزيد حسب المسافة. تعرف على العوامل وكيف تقلل تكلفة التوصيل.",
  h1="كم يكلف مندوب التوصيل في الكويت؟",
  lead="سعر التوصيل ما يكون رقم ثابت لكل الطلبات. هذي أهم العوامل اللي تحدده، وكيف تعرف السعر قبل ما يستلم المندوب طلبك.",
  secs=[
   ("من كم تبدأ الأسعار؟",["في Delivery.KW أسعار التوصيل تبدأ من دينارين (2 د.ك) وتزيد حسب المسافة بين منطقة الاستلام ومنطقة التسليم. السعر النهائي نأكده لك على واتساب قبل الاستلام."]),
   ("ما الذي يحدد سعر التوصيل؟",[("ul",["المسافة بين منطقة الاستلام ومنطقة التسليم.","حجم الطلب ووزنه.","وقت الطلب وضغط الطلبات وقتها."])]),
   ("كيف تقلل تكلفة التوصيل؟",[("ul",["جمّع أكثر من طلب في نفس المنطقة أو نفس المسار.","حدد العناوين بوضوح عشان ما يضيع وقت المندوب.","إذا عندك متجر أو مشروع، اسأل عن الأسعار الخاصة للمشاريع."])]),
   ("اطلب السعر قبل الاستلام دائمًا",["أي خدمة توصيل محترمة توضح السعر قبل ما تبدأ. راسلنا بمنطقة الاستلام والتسليم ونرد عليك بالسعر ووقت الوصول. تعرف أكثر من ",("a","دليل اختيار مندوب توصيل","/delivery-guide-kuwait"),"."]),
  ],
  faqs=[("كم أقل سعر للتوصيل؟","تبدأ الأسعار من دينارين وتزيد حسب المسافة."),
        ("هل السعر يتغير حسب المنطقة؟","إيه، السعر يعتمد على المسافة بين منطقة الاستلام ومنطقة التسليم."),
        ("هل في أسعار للمشاريع؟","إيه، عندنا أسعار خاصة للمشاريع الصغيرة والمتوسطة، راسلنا على واتساب.")]),
 dict(slug="article-clothes-accessories-delivery", card="توصيل الملابس والإكسسوارات: تغليف وتسليم بدون مشاكل",
  title="توصيل الملابس والإكسسوارات في الكويت: تغليف وتسليم | Delivery.KW",
  desc="نصائح لتوصيل الملابس والإكسسوارات داخل الكويت بدون تلف أو تأخير: التغليف، حماية الأغراض الصغيرة، وتنسيق التسليم مع مندوب توصيل 24 ساعة.",
  h1="توصيل الملابس والإكسسوارات: تغليف وتسليم بدون مشاكل",
  lead="الملابس والإكسسوارات من أكثر الطلبات اللي تنتقل بين المتاجر والعملاء. شوية اهتمام بالتغليف والتفاصيل يضمن توصل بحالة ممتازة.",
  secs=[
   ("تغليف الملابس",[("ul",["استخدم كيس محكم يحمي الملابس من الغبار والرطوبة.","رتّب القطعة بدون ما تنكمش بشكل زايد.","اكتب اسم العميل على الطلب وأي ملاحظة مهمة."])]),
   ("الإكسسوارات والأغراض الصغيرة",["القطع الصغيرة تنضاع أو تنكسر بسهولة، فاحفظها داخل علبة أو كيس مبطّن وثبّتها عشان ما تتحرك أثناء التوصيل، وأغلق العلبة بشكل جيد."]),
   ("تنسيق التسليم مع العميل",["أرسل رقم العميل وموقعه للمندوب مسبقًا، وخبّر العميل بوقت التوصيل المتوقع. لو تحتاج ترتيب استلام مرتجع أو استبدال، اسأل المندوب على واتساب قبل الطلب."]),
   ("السعر والتغطية",["تبدأ أسعارنا من دينارين وتزيد حسب المسافة، ونوصل جميع محافظات الكويت الست على مدار 24 ساعة. لأصحاب المتاجر شوف ",("a","توصيل طلبات المتاجر والمشاريع","/instagram-stores-delivery"),"."]),
  ],
  faqs=[("هل توصلون الملابس والإكسسوارات؟","إيه، نوصل الملابس والإكسسوارات والأغراض الشخصية من الباب للباب."),
        ("أقدر أطلب ترتيب استلام مرتجع؟","اسأل عن ذلك على واتساب قبل الطلب ونتفق على التفاصيل."),
        ("توصلون لأي منطقة؟","نوصل جميع مناطق الكويت في المحافظات الست.")]),
 dict(slug="article-delivery-driver-vs-shipping", card="الفرق بين مندوب التوصيل وشركات الشحن",
  title="الفرق بين مندوب التوصيل وشركات الشحن في الكويت | Delivery.KW",
  desc="ما الفرق بين مندوب التوصيل وشركات الشحن؟ متى تختار مندوب توصيل داخل الكويت ومتى تحتاج شحن دولي؟ مقارنة مبسطة تساعدك تختار.",
  h1="الفرق بين مندوب التوصيل وشركات الشحن",
  lead="الكلمتان يتداخلون عند كثير من الناس، لكن كل خدمة لها استخدام مختلف. هذي مقارنة بسيطة تساعدك تختار الأنسب لطلبك.",
  secs=[
   ("مندوب التوصيل",["مندوب التوصيل يستلم الغرض من مكانك ويسلّمه من الباب للباب داخل الكويت، وغالبًا تتفق معه مباشرة على الوقت والتفاصيل عبر واتساب. مناسب للطلبات اليومية والهدايا وطلبات المتاجر."]),
   ("شركات الشحن",["شركات الشحن الدولية تتعامل غالبًا مع الشحنات بين الدول، وتمر بإجراءات وأوقات مختلفة عن التوصيل المحلي، وقد تتطلب بيانات إضافية ورسوم حسب الوجهة."]),
   ("متى تختار مندوب توصيل؟",[("ul",["الطلب داخل الكويت وتبيه يوصل بشكل مباشر.","تحتاج مرونة في الوقت، حتى ليلًا.","عندك متجر أو مشروع ولك طلبات يومية أو متكررة."])]),
   ("متى تحتاج شحن؟",["إذا كان الغرض ينتقل بين دولتين، فالشحن الدولي هو الأنسب. وللتوصيل داخل الكويت راسلنا على واتساب 99454818 وحدد المنطقتين، أو اقرأ ",("a","دليل اختيار مندوب توصيل","/delivery-guide-kuwait"),"."]),
  ],
  faqs=[("هل توصلون خارج الكويت؟","خدمتنا حاليًا لتوصيل الطلبات داخل الكويت في المحافظات الست."),
        ("هل المندوب أسرع من الشحن؟","للتوصيل داخل الكويت غالبًا تكون العملية مباشرة أكثر، والوقت يعتمد على المسافة وضغط الطلبات."),
        ("شلون أطلب مندوب؟","راسلنا على واتساب 99454818 بمنطقة الاستلام والتسليم ونوع الطلب.")]),
]

def render_block(b):
    if isinstance(b, str):
        return f"      <p>{esc(b)}</p>\n"
    kind = b[0]
    if kind == "ul":
        return "      <ul>\n" + "".join(f"        <li>{esc(x)}</li>\n" for x in b[1]) + "      </ul>\n"
    if kind == "quote":
        return f"      <blockquote>{esc(b[1])}</blockquote>\n"
    raise ValueError(kind)

def render_paragraph(parts):
    # paragraph made of strings and ("a", text, href) links
    out = ""
    for x in parts:
        out += f'<a href="{x[2]}">{esc(x[1])}</a>' if isinstance(x, tuple) else esc(x)
    return f"      <p>{out}</p>\n"

def prose_section(h2, blocks):
    # a block list that mixes str and ("a",...) tuples => single linked paragraph
    if any(isinstance(b, tuple) and b[0] == "a" for b in blocks):
        buf, out, para = [], "", []
        for b in blocks:
            if isinstance(b, tuple) and b[0] in ("ul", "quote"):
                if para: out += render_paragraph(para); para = []
                out += render_block(b)
            else:
                para.append(b)
        if para: out += render_paragraph(para)
    else:
        out = "".join(render_block(b) for b in blocks)
    return f'  <section class="block flush">\n    <div class="wrap prose">\n      <h2>{esc(h2)}</h2>\n{out}    </div>\n  </section>'

for art in ARTICLES:
    secs = "\n".join(prose_section(h2, blocks) for h2, blocks in art["secs"])
    related = "".join(f'        <a href="/{o["slug"]}">{esc(o["card"])}</a>\n' for o in ARTICLES if o is not art)
    tail = f"""  <section class="block flush">
    <div class="wrap">
      <div class="head"><h2>مقالات ذات صلة</h2></div>
      <div class="plinks">
{related}        <a href="/delivery-guide-kuwait">دليل اختيار مندوب توصيل</a>
      </div>
    </div>
  </section>"""
    art_html = page(
        art["slug"], art["title"], art["desc"], art["h1"], art["lead"], secs + "\n" + tail, art["faqs"],
        [("الرئيسية", SITE + "/"), ("مقالات", SITE + "/#articles"), (art["card"], f"{SITE}/{art['slug']}")],
        {"@type": "Article", "headline": art["h1"], "inLanguage": "ar-KW", "description": art["desc"],
         "author": {"@id": SITE + "/#business"}, "publisher": {"@id": SITE + "/#business"},
         "datePublished": TODAY, "dateModified": TODAY, "mainEntityOfPage": f"{SITE}/{art['slug']}"})
    pages[art["slug"]] = art_html.replace('<p class="lead">', f'<p class="crumbs">آخر تحديث: <time datetime="{TODAY}">{TODAY}</time> · Delivery.KW</p>\n      <p class="lead">', 1)

for slug, content in pages.items():
    with open(os.path.join(ROOT, slug + ".html"), "w", encoding="utf-8") as f:
        f.write(content)

# 404 page (not in sitemap; noindex, no canonical)
nf_body = section("روابط مفيدة", "جرّب واحدة من هذي الصفحات",
    '      <div class="plinks">\n' + "".join(f'        <a href="/{g["slug"]}">{esc(g["name"])}</a>\n' for g in GOVS)
    + "".join(f'        <a href="/{a["slug"]}">{esc(a["card"])}</a>\n' for a in ARTICLES) + "      </div>")
nf = page("404", "الصفحة غير موجودة | Delivery.KW", "الصفحة المطلوبة غير موجودة على Delivery.KW.",
    "الصفحة غير موجودة", "الرابط اللي فتحته غير موجود أو تم تغييره. ارجع للصفحة الرئيسية أو راسلنا على واتساب ونرتب لك مندوب توصيل.",
    nf_body, [("شلون أطلب مندوب توصيل؟", "راسلنا على واتساب 99454818 بمنطقة الاستلام والتسليم ونوع الطلب.")],
    [("الرئيسية", SITE + "/"), ("الصفحة غير موجودة", SITE + "/404")])
nf = re.sub(r'<link rel="(canonical|alternate)"[^>]*>\n', "", nf)
nf = re.sub(r'<meta property="og:url"[^>]*>\n', "", nf)
nf = re.sub(r'<meta name="robots" content="[^"]*">', '<meta name="robots" content="noindex, follow">', nf)
nf = re.sub(r'<script type="application/ld\+json">.*?</script>\n', "", nf, flags=re.S)
open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8").write(nf)

# Admin (review moderation) page: not in sitemap, noindex
adm = page("admin", "إدارة الآراء | Delivery.KW", "إدارة آراء العملاء.", "إدارة آراء العملاء",
    "الآراء الجديدة تظهر هنا. اضغط موافقة ونشر عشان تظهر في الموقع، أو حذف.",
    '  <section class="block flush">\n    <div class="wrap">\n      <p class="note" id="adminMsg" role="status"></p>\n      <div id="adminList"></div>\n    </div>\n  </section>',
    [], [("الرئيسية", SITE + "/"), ("إدارة الآراء", SITE + "/admin")])
adm = re.sub(r'<link rel="(canonical|alternate)"[^>]*>\n', "", adm)
adm = re.sub(r'<meta (property="og:[^"]*"|name="twitter:[^"]*")[^>]*>\n', "", adm)
adm = re.sub(r'<meta name="robots" content="[^"]*">', '<meta name="robots" content="noindex, nofollow">', adm)
adm = re.sub(r'<script type="application/ld\+json">.*?</script>\n', "", adm, flags=re.S)
adm = re.sub(r'  <section class="block flush" id="faq">.*?</section>\n', "", adm, flags=re.S)
adm = re.sub(r'<a class="fab".*?</nav>\n', "", adm, flags=re.S)
adm = adm.replace("</body>", '<script src="/assets/admin.js?v=1" defer></script>\n</body>')
open(os.path.join(ROOT, "admin.html"), "w", encoding="utf-8").write(adm)

# sitemap
urls = [("/", "1.0")] + [(f"/{s}", "0.8") for s in pages]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
    f"  <url>\n    <loc>{SITE}{p}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>{pr}</priority>\n  </url>\n"
    for p, pr in urls) + "</urlset>\n"
open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(sm)
print("built", list(pages))
