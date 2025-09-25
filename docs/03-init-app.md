# 3. تهيئة التطبيق: `devkit.init_app()`

تُعد دالة `init_app` هي المحرك الرئيسي الذي يربط `Flask-DevKit` بتطبيق Flask الخاص بك. هي المسؤولة عن إعداد جميع المكونات وتسجيلها، مما يجعل تطبيقك جاهزًا للعمل ببضع أسطر من الكود.

## التوقيع (Signature)

```python
def init_app(self, app: APIFlask, bp: Optional[APIBlueprint] = None):
    # ...
```

- **`app` (مطلوب):** كائن تطبيق `APIFlask` الذي تريد تهيئة المكتبة عليه.
- **`bp` (اختياري):** كائن `APIBlueprint`. إذا لم يتم توفيره، ستقوم المكتبة بإنشاء `Blueprint` جديد تلقائيًا وتسجيل جميع المسارات (routes) عليه. يمكنك توفير `Blueprint` خاص بك إذا كنت تريد دمج مسارات `DevKit` ضمن `Blueprint` موجود مسبقًا في تطبيقك.

## ماذا تفعل `init_app`؟

عند استدعاء هذه الدالة، تقوم بتنفيذ سلسلة من عمليات الإعداد الهامة بالترتيب:

1.  **إعدادات التطبيق (`_setup_app_config`):**
    *   تضبط قيمًا افتراضية للإعدادات إذا لم تكن موجودة، مثل `DEVKIT_URL_PREFIX` (الافتراضي: `/api/v1`).
    *   تضيف مخطط أمان `bearerAuth` إلى إعدادات `APIFlask` لتوثيق JWT في واجهة Swagger/Redoc.

2.  **تهيئة الامتدادات الأساسية:**
    *   `db.init_app(app)`: تربط كائن `SQLAlchemy` بالتطبيق.
    *   `JWTManager(app)`: تهيئ `Flask-JWT-Extended` لإدارة التوثيق.

3.  **تهيئة وحدات DevKit:**
    *   `audit.init_app(app)`: تفعّل نظام التدقيق التلقائي لتسجيل التغييرات في قاعدة البيانات.
    *   `logging.init_app(app)`: تهيئ نظام تسجيل الأحداث (Logging).

4.  **تسجيل الخدمات الافتراضية (`_register_default_services`):**
    *   إذا لم تقم بتسجيل أي خدمات يدويًا باستخدام `devkit.register_service()‎`، ستقوم المكتبة بتسجيل الخدمات الافتراضية: `UserService`, `RoleService`, و `PermissionService`.

5.  **تسجيل أوامر CLI (`_register_cli`):**
    *   تضيف أوامر `flask devkit-init-db`, `flask devkit-truncate-db`, `flask devkit-drop-db`, و `flask devkit-seed` إلى واجهة سطر الأوامر.

6.  **تسجيل المخططات (Blueprints) والمسارات (`_register_blueprints`):**
    *   تستدعي `register_crud_routes` لإنشاء جميع نقاط نهاية CRUD API للمستخدمين، الأدوار، والصلاحيات.
    *   تُسجل `Blueprint` الخاص بالمصادقة (`/auth`) الذي يحتوي على نقاط نهاية مثل `/login`, `/refresh`, `/me`.
    *   تُسجل معالجات الأخطاء (Error Handlers) القياسية على المخططات لضمان استجابات JSON متسقة للأخطاء.

## مثال على نمط مصنع التطبيق (Application Factory)

من الممارسات الجيدة في Flask استخدام نمط "Application Factory" لتنظيم الكود. `init_app` تعمل بشكل مثالي مع هذا النمط.

```python
# my_project/app.py

from apiflask import APIFlask
from .extensions import devkit # افترض أنك عرفتهم في ملف منفصل

def create_app():
    app = APIFlask(__name__)

    # تحميل الإعدادات من ملف أو متغيرات بيئة
    app.config.from_object("my_project.config.DevelopmentConfig")

    # تهيئة الامتدادات
    devkit.init_app(app)

    return app
```

```python
# my_project/extensions.py

from flask_devkit import DevKit

devkit = DevKit()
```

هذا النمط يفصل بين إنشاء التطبيق وتهيئته، مما يجعل الكود أكثر تنظيمًا وقابلية للاختبار.
