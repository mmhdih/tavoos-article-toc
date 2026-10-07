<div dir="rtl">

# انتشار دستی در مخزن وردپرس

این راهنما برای مالک افزونه است. هنوز چیزی به WordPress.org ارسال یا منتشر نشده و نامک پیشنهادی رزرو نشده است.

## قبل از ارسال

۱. با حساب شخصی خودتان در [WordPress.org](https://wordpress.org/) وارد شوید. نام نمایشی نویسنده در فایل اصلی فعلاً **Mahdi Habibi / Tavoos Web** است؛ آن را تأیید کنید. اگر می‌خواهید بخش Contributors داشته باشید، فقط نام کاربری واقعی WordPress.org را در `readme.txt` وارد کنید؛ نام کاربری GitHub الزاماً همان نیست.

۲. [دستورالعمل‌های رسمی افزونه‌ها](https://developer.wordpress.org/plugins/wordpress-org/detailed-plugin-guidelines/) را بخوانید. نامک `tavoos-article-toc` پیشنهادی است و تصمیم نهایی نام و پذیرش با تیم بررسی وردپرس است.

۳. افزونه را با **Plugin Check** روی یک وردپرس آزمایشی اجرا کنید. نتایج را بررسی کنید؛ عبور از تست‌های این مخزن جای بررسی رسمی را نمی‌گیرد. [Plugin Check](https://wordpress.org/plugins/plugin-check/) در این محیط اجرا نشده است.

۴. روی آخرین نسخه پایدار وردپرس و حداقل نسخه‌های اعلام‌شده هم تست کنید. اعتبارسنجی محلی این مخزن روی وردپرس ۶٫۸٫۳ و PHP ۸٫۴ انجام شده؛ مقدار «Requires» ادعای تست روی حداقل نسخه‌ها نیست. `Tested up to` را فقط پس از تست واقعی تغییر دهید. چندسایتی و همه قالب‌ها نیز هنوز پوشش داده نشده‌اند.

۵. [اعتبارسنج رسمی readme](https://wordpress.org/plugins/developers/readme-validator/) را اجرا کنید. نسخه در هدر PHP، ثابت نسخه، Stable tag، changelog و Upgrade Notice باید با هم هماهنگ باشند. مجوز GPL همراه بسته است.

## ساخت فایل ارسالی

در ریشه مخزن اجرا کنید:

```sh
python3 tools/build-release.py
```

فایل `dist/tavoos-article-toc-1.0.0.zip` فقط فایل‌های اجرای افزونه، ترجمه‌ها، مجوز و `readme.txt` را دارد. لوگوها، راهنما، تست‌ها و فایل‌های Git داخل ZIP نصب نمی‌آیند.

روی یک نصب آزمایشی تمیز، ZIP را از صفحه بارگذاری افزونه نصب کنید، فعال کنید، تنظیمات را ذخیره کنید و یک نوشته با سه H2 باز کنید. نصب پوشه از سورس و نصب ZIP دو بررسی متفاوت‌اند.

## ارسال برای بررسی

در [صفحه ارسال افزونه](https://wordpress.org/plugins/developers/add/) با حساب خودتان فایل ZIP را ارسال کنید. ایمیل‌های تیم بررسی را پیگیری کنید و اصلاحات لازم را انجام دهید. زمان بررسی و نامک نهایی از قبل تضمین نمی‌شود. کلید، رمز یا اطلاعات حساب را داخل مخزن قرار ندهید.

## پس از تأیید: انتشار با SVN

WordPress.org یک نشانی SVN برای نامک تأییدشده می‌دهد. ساختار نمونه:

```text
approved-slug/
├── assets/                 # تصاویر صفحه افزونه، خارج از کد نصب
│   ├── icon-128x128.png
│   ├── icon-256x256.png
│   ├── banner-772x250.png
│   ├── banner-1544x500.png
│   ├── screenshot-1.png
│   └── screenshot-2.png
├── trunk/                  # محتوای پوشه tavoos-article-toc در ZIP
└── tags/
    └── 1.0.0/              # نسخه ثابت کد منتشرشده
```

فایل‌های `wordpress-org/` این مخزن برای ریشه `assets/` SVN آماده‌اند. شماره تصاویر با بخش Screenshots در `readme.txt` هماهنگ است. پوشه `assets/` داخل ZIP افزونه فقط CSS و JavaScript اجرا را دارد؛ این دو محل را اشتباه نگیرید.

طبق [راهنمای رسمی SVN](https://developer.wordpress.org/plugins/wordpress-org/how-to-use-subversion/)، کد را در `trunk` قرار دهید، نسخه را در `tags/1.0.0` کپی کنید و پیش از commit تفاوت‌ها را بررسی کنید. این مرحله انتشار عمومی است و شما با حساب خودتان انجام می‌دهید. دستور زیر صرفاً نمونه است؛ نامک تأییدشده را جایگزین کنید:

```sh
svn checkout https://plugins.svn.wordpress.org/APPROVED-SLUG/ wporg-release
# کد استخراج‌شده ZIP را در trunk و تصاویر wordpress-org را در assets کپی کنید.
svn add wporg-release/trunk/* wporg-release/assets/*
svn copy wporg-release/trunk wporg-release/tags/1.0.0
svn status wporg-release
svn diff wporg-release
# پس از بررسی، commit را با حساب خودتان انجام دهید.
```

برای نسخه بعدی، شماره نسخه و changelog را افزایش دهید، بسته و تست‌ها را تکرار کنید و tag جدید بسازید؛ tag منتشرشده را بازنویسی نکنید.

</div>
