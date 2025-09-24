# 36. الحماية من الاستخدام المفرط: تحديد معدل الطلبات (Rate Limiting)

تحديد معدل الطلبات هو ممارسة أمان أساسية لحماية واجهات برمجة التطبيقات (APIs) من الاستخدام المفرط، سواء كان ذلك بسبب هجمات القوة الغاشمة (brute-force)، أو هجمات الحرمان من الخدمة (DoS)، أو مجرد عملاء سيئي البرمجة.

توفر `Flask-DevKit` دالة مساعدة بسيطة، `setup_rate_limiting`، لتسهيل دمج مكتبة `Flask-Limiter` القوية في تطبيقك.

**ملاحظة:** على عكس العديد من الميزات الأخرى، **يجب تفعيل هذه الميزة يدويًا**.

## كيفية الاستخدام

يجب استدعاء الدالة في دالة مصنع التطبيق (`create_app`) بعد إنشاء كائن `app`.

```python
from apiflask import APIFlask
from flask_devkit import DevKit
from flask_devkit.helpers.decorators import setup_rate_limiting

def create_app():
    app = APIFlask(__name__)
    # ... إعدادات التطبيق الأخرى

    # قم بتهيئة DevKit أولاً
    devkit = DevKit()
    devkit.init_app(app)

    # قم بتطبيق محدد معدل الطلبات على التطبيق بأكمله
    limiter = setup_rate_limiting(app)

    return app
```

## السلوك الافتراضي

بشكل افتراضي، يقوم استدعاء `setup_rate_limiting(app)` بتطبيق حد شامل (global limit) على **جميع** نقاط النهاية في تطبيقك.

- **الحد:** `100 طلب في الدقيقة` لكل عنوان IP.
- **الاستجابة عند التجاوز:** عندما يتجاوز العميل هذا الحد، سيتلقى تلقائيًا استجابة `429 Too Many Requests`.

## التخصيص

### تغيير الحد الافتراضي
يمكنك بسهولة تغيير الحد الافتراضي عن طريق تمرير سلسلة نصية إلى الدالة.

```python
# حد أقصى 200 طلب في الدقيقة و 50 في الساعة
limiter = setup_rate_limiting(app, default_rate="200/minute, 50/hour")
```

### التكوينات المتقدمة
تعتبر `Flask-Limiter` مكتبة مرنة للغاية وتدعم سيناريوهات معقدة، مثل:
- تطبيق حدود مختلفة على `Blueprints` مختلفة.
- تطبيق حدود على نقاط نهاية معينة.
- تحديد معدل الطلبات بناءً على المستخدم الذي قام بتسجيل الدخول (بدلاً من عنوان IP).

توفر `setup_rate_limiting` نقطة بداية بسيطة. للتكوينات المتقدمة، يوصى بشدة بالرجوع إلى التوثيق الرسمي لمكتبة `Flask-Limiter`.

- **التوثيق الرسمي لـ Flask-Limiter:** [https://flask-limiter.readthedocs.io/](https://flask-limiter.readthedocs.io/)
