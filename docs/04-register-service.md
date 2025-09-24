# 4. تخصيص منطق الأعمال: `devkit.register_service()`

توفر `Flask-DevKit` طريقة قوية لتجاوز (override) أو تمديد (extend) منطق الأعمال الافتراضي عن طريق تسجيل "خدمات" (Services) مخصصة. الخدمة هي فئة بايثون تحتوي على منطق الأعمال لتخصص معين (مثل المستخدمين أو الأدوار).

## متى تستخدم `register_service`؟

- عندما تريد إضافة خطوات تحقق (validation) مخصصة قبل إنشاء أو تحديث كائن.
- عندما تريد تغيير سلوك تسجيل الدخول.
- عندما تريد إرسال بريد إلكتروني أو استدعاء واجهة برمجة تطبيقات أخرى بعد إنشاء مستخدم جديد.
- عندما تريد دمج منطق أعمال خاص بتطبيقك ضمن تدفقات `DevKit`.

## كيفية الاستخدام

لتسجيل خدمة مخصصة، يجب عليك استدعاء `devkit.register_service(name, service_instance)` **قبل** استدعاء `devkit.init_app(app)`.

**نقطة هامة جداً:** بمجرد تسجيلك لخدمة واحدة يدويًا، تقوم `DevKit` بإلغاء تفعيل آلية تسجيل الخدمات الافتراضية بالكامل. هذا يعني أنك **مسؤول عن تسجيل جميع الخدمات** التي يحتاجها تطبيقك، حتى تلك التي لا تنوي تخصيصها.

### مثال: تخصيص خدمة المستخدمين

لنفترض أننا نريد منع إنشاء مستخدمين بأسماء مستخدمين محجوزة مثل "admin" أو "root".

1.  **أنشئ خدمتك المخصصة:**
    قم بإنشاء فئة ترث من `UserService` الافتراضية وقم بتجاوز `pre_create_hook`.

    ```python
    # my_project/services.py

    from flask_devkit.users.services import UserService
    from flask_devkit.core.exceptions import BusinessLogicError

    FORBIDDEN_USERNAMES = ["admin", "root", "superuser"]

    class CustomUserService(UserService):
        def pre_create_hook(self, data: dict) -> dict:
            # قم أولاً باستدعاء المنطق الأصلي في الفئة الأم
            processed_data = super().pre_create_hook(data)

            # أضف منطق التحقق المخصص الخاص بك
            username = processed_data.get("username")
            if username and username.lower() in FORBIDDEN_USERNAMES:
                raise BusinessLogicError(f"Username '{username}' is reserved.")

            print(f"Custom pre-create hook is running for user: {username}")
            return processed_data
    ```

2.  **قم بتسجيل جميع خدماتك:**
    في ملف تهيئة التطبيق، قم بتسجيل خدمتك المخصصة **وجميع الخدمات الافتراضية الأخرى** التي تحتاجها.

    ```python
    # my_project/app.py

    from apiflask import APIFlask
    from flask_devkit import DevKit
    from flask_devkit.database import db
    from flask_devkit.users.models import User, Role, Permission
    from flask_devkit.users.services import RoleService, PermissionService

    # استورد خدمتك المخصصة
    from .services import CustomUserService

    def create_app():
        app = APIFlask(__name__)
        app.config.from_object("my_project.config.DevelopmentConfig")

        devkit = DevKit()
        db.init_app(app) # تهيئة db أولاً

        # --- التسجيل اليدوي للخدمات ---
        # 1. أنشئ نسخة من خدمتك المخصصة
        custom_user_service = CustomUserService(
            model=User, db_session=db.session
        )

        # 2. أنشئ نسخًا من الخدمات الافتراضية الأخرى التي تحتاجها
        role_service = RoleService(model=Role, db_session=db.session)
        permission_service = PermissionService(model=Permission, db_session=db.session)

        # 3. قم بتسجيل جميع الخدمات. يجب استدعاء هذا قبل init_app
        devkit.register_service("user", custom_user_service)
        devkit.register_service("role", role_service)
        devkit.register_service("permission", permission_service)
        # --- نهاية التسجيل اليدوي ---

        # الآن قم بتهيئة DevKit
        # لن تقوم init_app بتسجيل أي خدمات افتراضية لأنك سجلتها يدويًا
        devkit.init_app(app)

        return app
    ```

بهذه الطريقة، عندما يتم استدعاء نقطة النهاية `POST /api/v1/users`، سيتم استخدام `CustomUserService` بدلاً من الخدمة الافتراضية، وسيتم تطبيق منطق التحقق المخصص الخاص بك.
