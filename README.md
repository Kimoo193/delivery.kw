# Delivery.KW

صفحة هبوط لخدمة **Delivery.KW** لتوصيل الطلبات في جميع مناطق الكويت.

- واتساب: [99454818](https://wa.me/96599454818)
- انستجرام: [@td.delivery1](https://www.instagram.com/td.delivery1/)

## التشغيل

الصفحة ملف واحد `index.html` مع مجلد `assets/`. افتحها مباشرة في المتصفح أو انشرها على GitHub Pages:
Settings → Pages → Deploy from a branch → اختر الفرع والمجلد `/ (root)`.

## النشر على Cloudflare Pages

1. من [dash.cloudflare.com](https://dash.cloudflare.com): **Workers & Pages → Create → Pages → Connect to Git**.
2. اختر الريبو `Kimoo193/delivery.kw` والفرع `claude/kuwait-delivery-page-5h7juu` (هذا هو الفرع الافتراضي في الريبو حالياً — تقدر تتأكد من GitHub → Settings → Branches. إذا رجّعت `main` يكون الفرع الافتراضي بدل كذا، اختره هو).
3. **مهم:** سمّي المشروع `delivery-kw` بالضبط (Project name). كل روابط SEO في الموقع (canonical، og:url، sitemap.xml، robots.txt) مضبوطة مسبقاً على `https://delivery-kw.pages.dev/` — إذا سمّيت المشروع شي ثاني لازم تسوي find-and-replace لنفس الروابط.
4. الإعدادات: **Framework preset: None**، **Build command: فاضي**، **Build output directory: `/`**.
5. اضغط **Save and Deploy**. الموقع يطلع على `https://delivery-kw.pages.dev` وأي رفع على `main` يتحدث تلقائياً.
6. إذا ضفت دومين خاص لاحقاً (مثل delivery.kw): حدّث نفس الروابط (canonical، og:url، JSON-LD، sitemap.xml، robots.txt) للدومين الجديد.

### التحقق بعد النشر

- `curl -I https://delivery-kw.pages.dev/` وتأكد إن `Content-Security-Policy` و`Strict-Transport-Security` موجودين في الرد.
- افتح الموقع وجرّب: تبديل الوضع الداكن/الفاتح، نموذج تجهيز الطلب، وفتح صور المعرض (lightbox) — تأكد ما في أخطاء CSP في Console.
- سجّل الموقع في [Google Search Console](https://search.google.com/search-console) و[Bing Webmaster Tools](https://www.bing.com/webmasters) وقدّم `sitemap.xml`.

## الأمان: CSP بـ hashes

ملف `_headers` يستخدم Content-Security-Policy صارم بدون `'unsafe-inline'` — كل `<script>` و`<style>` داخل `index.html` مسموح له فقط عن طريق SHA-256 hash محدد بالاسم. **إذا عدّلت أي كود داخل `<script>...</script>` أو `<style>...</style>` في `index.html`، لازم تولّد الـ hash الجديد وتحدّثه في `_headers`**، وإلا المتصفح بيمنع الكود المعدّل من الشغل:

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
node scripts/loadtest.mjs https://<اسم-المشروع>.pages.dev 100 30
node scripts/loadtest.mjs https://<اسم-المشروع>.pages.dev 300 30
```

الرقم الثاني = عدد الزوار في نفس اللحظة، والثالث = عدد الثواني. شغّله على موقعك أنت بس، وابدأ بأرقام صغيرة.
