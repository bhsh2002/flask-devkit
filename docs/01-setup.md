# 1. الإعداد والتهيئة (Setup and Initialization)

`Flask-DevKit` مصممة لتكون سهلة التكامل مع أي مشروع Flask. يوضح هذا الدليل كيفية تثبيت المكتبة وتهيئتها بشكل أساسي.

## التثبيت

لتثبيت المكتبة في مشروعك باستخدام `Poetry`، قم بتنفيذ الأمر التالي:

```bash
poetry add flask-devkit
```

## التهيئة الأساسية

تتم التهيئة عبر إنشاء نسخة من فئة `DevKit` ثم ربطها بتطبيق `APIFlask` الخاص بك.

إليك مثال بسيط لملف `app.py`:

```python
from apiflask import APIFlask
from flask_devkit import DevKit

# 1. قم بإنشاء تطبيق APIFlask
app = APIFlask(__name__)

# 2. قم بتعيين إعدادات قاعدة البيانات
#    استخدم متغيرات البيئة في تطبيق حقيقي
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SECRET_KEY"] = "a-secure-secret-key-for-jwt" # استبدله بمفتاح آمن

# 3. قم بإنشاء نسخة من DevKit
devkit = DevKit()

# 4. قم بتهيئة DevKit مع تطبيقك
#    سيؤدي هذا إلى تسجيل جميع المكونات الافتراضية (المصادقة، المستخدمين، إلخ)
devkit.init_app(app)

# يمكنك الآن تشغيل تطبيقك
# flask run
```

### شرح الخطوات:

1.  **`app = APIFlask(__name__)`**: نستخدم `APIFlask` بدلاً من `Flask` للاستفادة من الميزات المدمجة لتوليد وثائق OpenAPI.
2.  **`app.config[...]`**: يجب توفير `SQLALCHEMY_DATABASE_URI` لكي تعمل مكونات قاعدة البيانات. كما أن `SECRET_KEY` ضروري لتوقيع رموز JWT.
3.  **`devkit = DevKit()`**: يتم إنشاء كائن `DevKit` الذي سيعمل كنقطة مركزية لإدارة مكونات المكتبة.
4.  **`devkit.init_app(app)`**: هذه هي الخطوة الأهم. عند استدعاء هذا التابع، تقوم `DevKit` بالآتي:
    *   تهيئة امتداد `SQLAlchemy`.
    *   تهيئة `JWTManager` للمصادقة.
    *   تسجيل خدمات `UserService`, `RoleService`, `PermissionService` الافتراضية.
    *   تسجيل جميع مسارات (routes) واجهات برمجة التطبيقات (APIs) المتعلقة بالمستخدمين والصلاحيات تحت البادئة `/api/v1`.
    *   تسجيل أوامر CLI المساعدة (مثل `flask devkit-seed`).

بعد هذه الخطوات، يصبح تطبيقك جاهزًا مع نظام مصادقة وصلاحيات كامل.
