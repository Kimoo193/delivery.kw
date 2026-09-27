# Delivery.KW

صفحة هبوط لخدمة **Delivery.KW** لتوصيل الطلبات في جميع مناطق الكويت.

- واتساب: [99454818](https://wa.me/96599454818)
- انستجرام: [@td.delivery1](https://www.instagram.com/td.delivery1/)

## التشغيل

الصفحة ملف واحد `index.html` مع مجلد `assets/`. افتحها مباشرة في المتصفح أو انشرها على GitHub Pages:
Settings → Pages → Deploy from a branch → اختر الفرع والمجلد `/ (root)`.

## النشر على Cloudflare Pages

1. من [dash.cloudflare.com](https://dash.cloudflare.com): **Workers & Pages → Create → Pages → Connect to Git**.
2. اختر الريبو `Kimoo193/delivery.kw` والفرع `main`.
3. الإعدادات: **Framework preset: None**، **Build command: فاضي**، **Build output directory: `/`**.
4. اضغط **Save and Deploy**. الموقع يطلع على `https://<اسم-المشروع>.pages.dev` وأي رفع على `main` يتحدث تلقائياً.

ملف `_headers` يضبط التخزين المؤقت للصور على Cloudflare لمدة 30 يوم.

بعد ما تعرف الرابط النهائي، حدّث الرابط في `index.html` (canonical و og:url) وفي `sitemap.xml` و`robots.txt`.

## اختبار عدد الزوار في نفس الوقت

يحتاج Node.js 18 أو أحدث. كل "زائر" يفتح الصفحة وكل الصور مثل المتصفح:

```bash
node scripts/loadtest.mjs https://<اسم-المشروع>.pages.dev 100 30
node scripts/loadtest.mjs https://<اسم-المشروع>.pages.dev 300 30
```

الرقم الثاني = عدد الزوار في نفس اللحظة، والثالث = عدد الثواني. شغّله على موقعك أنت بس، وابدأ بأرقام صغيرة.
