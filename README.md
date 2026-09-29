# Delivery.KW

صفحة هبوط لخدمة **Delivery.KW** لتوصيل الطلبات في جميع مناطق الكويت.

- واتساب: [99454818](https://wa.me/96599454818)
- انستجرام: [@td.delivery1](https://www.instagram.com/td.delivery1/)

## التشغيل

الموقع صفحات HTML ثابتة مع مجلد `assets/`:

- `index.html`: الصفحة الرئيسية (تُعدّل يدوياً).
- صفحات المحافظات والمقالات والدليل وصفحة `404.html` و`sitemap.xml` تتولّد من `scripts/build_pages.py`، اللي يعيد استخدام كتلة `<style>` من `index.html`. بعد أي تعديل على المحتوى أو على `<style>`:

```bash
python3 scripts/build_pages.py
```

## النشر على Cloudflare Pages

- الدومين: `https://deliverykw.com` (كل روابط SEO: canonical، og:url، JSON-LD، sitemap.xml، robots.txt، llms.txt مضبوطة عليه).
- `www.deliverykw.com` يتحوّل 301 إلى `https://deliverykw.com` (قاعدة Redirect في Cloudflare).
- مشروع Pages اسمه `delivery-kw` ونوعه **Direct Upload**، يعني الرفع على GitHub **ما ينشر تلقائياً**. للنشر: جهّز مجلد فيه ملفات الموقع فقط (بدون `.git` و`scripts` و`.wrangler`) وشغّل:

```bash
npx wrangler pages deploy <المجلد> --project-name delivery-kw --branch main
```

- نسخة `delivery-kw.pages.dev` عليها `X-Robots-Tag: noindex` من `_headers` عشان ما تنافس الدومين في البحث.

### التحقق بعد النشر

- `curl -I https://deliverykw.com/` وتأكد إن `Content-Security-Policy` و`Strict-Transport-Security` موجودين، وما في `X-Robots-Tag`.
- `curl -I https://deliverykw.com/no-such-page` لازم يرجع 404.
- افتح الموقع وجرّب: تبديل الوضع الداكن/الفاتح، نموذج تجهيز الطلب، وفتح صور المعرض (lightbox) — تأكد ما في أخطاء CSP في Console.
- الموقع مسجّل في Google Search Console (خاصية Domain وخاصية URL)، و`sitemap.xml` مقدَّم. للصفحات الجديدة يُرسل IndexNow بالمفتاح الموجود في ملف `<key>.txt` بجذر الموقع.

## الأمان: CSP بـ hashes

ملف `_headers` يستخدم Content-Security-Policy صارم بدون `'unsafe-inline'` — كل `<script>` و`<style>` داخل صفحات الموقع مسموح له فقط عن طريق SHA-256 hash محدد بالاسم. **إذا عدّلت أي كود داخل `<script>...</script>` أو `<style>...</style>` في `index.html`، لازم تولّد الـ hash الجديد وتحدّثه في `_headers`**، وإلا المتصفح بيمنع الكود المعدّل من الشغل:

```bash
python3 -c "
import re, hashlib, base64
html = open('index.html', encoding='utf-8').read()
for tag, attr in [('style', 'style-src'), ('script', 'script-src')]:
    for m in re.finditer(rf'<{tag}(?:\s[^>]*)?>(.*?)</{tag}>', html, re.S):
        body = m.group(1)
        if 'application/ld+json' in m.group(0)[:60] or not body.strip():
            continue
        h = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
        print(f\"{attr}: 'sha256-{h}'\")"
```

انسخ الـ hash الجديد داخل `_headers` مكان القديم لنفس الكتلة.

ملف `_headers` يضبط أيضاً التخزين المؤقت للصور على Cloudflare لمدة 30 يوم، ورؤوس أمان إضافية (HSTS، Permissions-Policy، X-Frame-Options، إلخ).

## الصور

كل صورة موجودة بنسختين: الأصلية (`.jpg`/`.png`) ونسخة `.webp` مضغوطة (توفير ٣٨٪ من الحجم بدون فرق يذكر بالجودة)، مربوطتين بوسم `<picture>` — المتصفح يختار WebP تلقائياً ويرجع للأصلية لو ما يدعمها. إذا ضفت صورة جديدة، حوّلها بنفس الطريقة:

```bash
python3 -c "
from PIL import Image
im = Image.open('assets/NAME.jpg')
im.save('assets/NAME.webp', 'WEBP', quality=80, method=6)"
```

وحطها داخل `<picture><source srcset="assets/NAME.webp" type="image/webp"><img src="assets/NAME.jpg" ...></picture>`.

## الخطوط

الموقع يحمّل خطوط Reem Kufi و Readex Pro محلياً من `assets/fonts/` (بدل Google Fonts مباشرة) — يحسّن الخصوصية (ما نرسل IP الزائر لجوجل) والسرعة، ويسهّل CSP الصارم. إذا احتجت تغيّر الأوزان أو تضيف خط جديد، حمّل ملفات الـ woff2 يدوياً من [Google Fonts](https://fonts.google.com) وحدّث كتلة `@font-face` في `index.html`.

## اختبار عدد الزوار في نفس الوقت

يحتاج Node.js 18 أو أحدث. كل "زائر" يفتح الصفحة وكل الصور مثل المتصفح:

```bash
node scripts/loadtest.mjs https://deliverykw.com 100 30
node scripts/loadtest.mjs https://deliverykw.com 300 30
```

الرقم الثاني = عدد الزوار في نفس اللحظة، والثالث = عدد الثواني. شغّله على موقعك أنت بس، وابدأ بأرقام صغيرة.
