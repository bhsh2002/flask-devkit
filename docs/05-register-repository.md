# 5. تخصيص الوصول للبيانات: `devkit.register_repository()`

إذا كان منطق الأعمال في الخدمات (Services) الافتراضية يناسبك، ولكنك تحتاج إلى تغيير الطريقة التي يتم بها تنفيذ استعلامات قاعدة البيانات، فإن `register_repository` هي الأداة المناسبة.

المستودع (Repository) هو فئة مسؤولة حصريًا عن عمليات قاعدة البيانات (CRUD) لنموذج معين. `register_repository` تسمح لك باستبدال فئة المستودع الافتراضية بأخرى مخصصة، دون الحاجة إلى استبدال الخدمة بأكملها.

## متى تستخدم `register_repository`؟

- عندما تحتاج إلى كتابة استعلامات `SQLAlchemy` معقدة لا تدعمها `BaseRepository` بشكل مباشر.
- لتحسين أداء الاستعلامات، على سبيل المثال، عن طريق إضافة `joinedload` أو `selectinload` لتحميل العلاقات بكفاءة (Eager Loading).
- للتكامل مع ميزات خاصة بقاعدة بيانات معينة (مثل `JSONB` في PostgreSQL).

## كيفية الاستخدام

يجب استدعاء `devkit.register_repository(service_name, repository_class)` **قبل** استدعاء `devkit.init_app(app)`.

على عكس `register_service`، فإن استخدام `register_repository` **لا** يعطل التسجيل التلقائي للخدمات الافتراضية. بدلاً من ذلك، تقوم `DevKit` بحقن المستودع المخصص الخاص بك في الخدمة الافتراضية المقابلة عند إنشائها.

### مثال: تحسين استعلام جلب المستخدمين

بشكل افتراضي، عند جلب مستخدم، لا يتم جلب أدواره (roles) في نفس الاستعلام. هذا يمكن أن يؤدي إلى مشكلة "N+1 query" إذا احتجت إلى الوصول إلى أدوار عدة مستخدمين في حلقة.

يمكننا حل هذه المشكلة عن طريق إنشاء مستودع مخصص يقوم بالتحميل المسبق (eager load) للأدوار.

1.  **أنشئ المستودع المخصص:**
    قم بإنشاء فئة ترث من `BaseRepository` وقم بتجاوز التوابع التي تريد تغييرها.

    ```python
    # my_project/repositories.py

    from sqlalchemy.orm import joinedload
    from flask_devkit.core.repository import BaseRepository
    from flask_devkit.users.models import User

    class CustomUserRepository(BaseRepository[User]):
        def _query(self):
            # قم دائمًا بتحميل علاقة 'roles' بشكل استباقي
            # لتجنب استعلامات إضافية
            return super()._query().options(joinedload(User.roles))

        def find_active_users_with_logins_after(self, date):
            """مثال على دالة مخصصة لاستعلام معقد."""
            return self._query().filter(
                User.is_active == True,
                User.last_login_at > date
            ).all()
    ```

2.  **قم بتسجيل المستودع المخصص:**
    في ملف تهيئة التطبيق، قم بتسجيل **فئة** المستودع (وليس كائنًا منه).

    ```python
    # my_project/app.py

    from apiflask import APIFlask
    from flask_devkit import DevKit

    # استورد المستودع المخصص
    from .repositories import CustomUserRepository

    def create_app():
        app = APIFlask(__name__)
        app.config.from_object("my_project.config.DevelopmentConfig")

        devkit = DevKit()

        # قم بتسجيل فئة المستودع المخصصة لخدمة 'user'
        # لاحظ أننا نمرر الفئة نفسها، وليس نسخة منها
        devkit.register_repository("user", CustomUserRepository)

        # الآن قم بتهيئة DevKit
        # ستقوم init_app بإنشاء UserService الافتراضي،
        # ولكنها ستمرر CustomUserRepository إليه.
        devkit.init_app(app)

        return app
    ```

الآن، في أي مكان في الكود يتم فيه استخدام `UserService` لجلب مستخدم (على سبيل المثال، في نقطة النهاية `GET /api/v1/users/{uuid}`), سيتم استخدام `CustomUserRepository` تلقائيًا، وسيتم تحميل الأدوار بكفاءة في استعلام واحد.
