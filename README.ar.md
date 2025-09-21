# Flask-DevKit: مجموعة أدوات API القابلة للتوسعة لـ Flask

`Flask-DevKit` هي مجموعة أدوات قوية وغير منحازة، مصممة لتسريع تطوير واجهات برمجة تطبيقات (APIs) آمنة وقابلة للتطوير وسهلة الصيانة باستخدام Flask. تم اختبارها بشكل شامل مع **تغطية كود تزيد عن 90%**، وهي توفر أساسًا معماريًا متينًا يعتمد على أنماط تصميم مثبتة مثل نمط المستودع (Repository) ووحدة العمل (Unit of Work)، مع توفير مرونة كاملة لتخصيص أو استبدال أو تمديد أي جزء من النظام.

على عكس الأطر الجامدة، فإن DevKit عبارة عن مجموعة من الأدوات التي يمكنك تبنيها بشكل تدريجي أو استخدامها كنقطة انطلاق كاملة. تأتي مع وحدة مصادقة وتحكم في الوصول (RBAC) افتراضية وكاملة الميزات يمكن استخدامها مباشرة، أو تفعيلها بشكل انتقائي، أو استبدالها بالكامل بمنطقك الخاص.

---

## المفاهيم الأساسية

-   **أنت المتحكم:** لا تضع المكتبة أي افتراضات حول احتياجات تطبيقك. يمكن تجاوز أو تمديد كل مكون رئيسي - الخدمات، المستودعات، المسارات.
-   **الاصطلاح فوق التكوين، ولكن التكوين عند الحاجة:** تسمح الإعدادات الافتراضية المنطقية بالتطوير السريع، لكن مجموعة غنية من دوال التسجيل توفر نقاطًا لإدخال منطقك المخصص أينما احتجت إليه.
-   **هيكلية متينة:** من خلال توفير تجريدات نظيفة لطبقة الخدمة، ونمط المستودع، ووحدة العمل، تساعدك DevKit على بناء تطبيقات قوية يسهل اختبارها وصيانتها.

---

## دليل الاستخدام

يغطي هذا الدليل حالات الاستخدام الشائعة، من البداية السريعة إلى التخصيص المتقدم.

### السيناريو 1: بداية سريعة مع المصادقة الافتراضية

إذا كنت بحاجة إلى نظام مصادقة و RBAC كامل على الفور، فما عليك سوى تهيئة `DevKit` دون تسجيل أي من خدماتك الخاصة. سيقوم تلقائيًا بتحميل وحدات `user` و `role` و `permission` الافتراضية.

```python
# في مصنع التطبيق (e.g., create_app)
from flask import Flask
from apiflask import APIBlueprint
from flask_devkit import DevKit
from .database import db

def create_app():
    app = Flask(__name__)
    # ... إعدادات التطبيق ...
    db.init_app(app)

    # 1. إنشاء مخطط رئيسي لإصدار API الخاص بك
    api_v1_bp = APIBlueprint("api_v1", __name__, url_prefix="/api/v1")

    # 2. إنشاء نسخة من DevKit
    devkit = DevKit()

    # 3. تهيئة. سيقوم DevKit بتحميل الخدمات الافتراضية وتسجيل
    #    مساراتها (المصادقة، المستخدمون، الأدوار، إلخ) على المخطط.
    devkit.init_app(app, bp=api_v1_bp)

    return app
```
سيعطيك هذا على الفور نقاط نهاية مثل `/api/v1/auth/login`, `/api/v1/users`, `/api/v1/roles`, إلخ.

### السيناريو 2: إضافة خدمة تطبيق خاصة بك

هذه هي حالة الاستخدام الأكثر شيوعًا. هنا، نضيف نموذج `Post` والخدمة والمخططات والمسارات المتعلقة به. نظرًا لأننا نسجل خدمة يدويًا، **لن** يقوم DevKit بتحميل خدمات المصادقة الافتراضية.

```python
# في مصنع التطبيق (e.g., create_app)

# 1. استيراد الخدمة والمخطط المخصصين
from .services.post import post_service
from .routes.post import posts_bp

# 2. إنشاء نسخة من DevKit وتسجيل خدمتك
devkit = DevKit()
devkit.register_service("post", post_service)

# 3. تهيئة التطبيق و DevKit
# ...
devkit.init_app(app) # لا حاجة للمخطط إذا لم تكن تستخدم المسارات الافتراضية

# 4. تسجيل مخطط تطبيقك
app.register_blueprint(posts_bp, url_prefix="/api/v1/posts")
```

### ملاحظة هامة حول الاستخدام المستقل

بمجرد تسجيل خدمة واحدة فقط يدويًا عبر `devkit.register_service()`، يتم **تعطيل** التحميل التلقائي للوحدات الافتراضية (User, Role, Permission). هذا مقصود ويسمح لك باستخدام الميزات الأساسية لـ `flask-devkit` (مثل `BaseService`، `register_crud_routes`، إلخ) لنماذجك الخاصة دون التقيد بنظام المصادقة المدمج.

إذا كنت ترغب في استخدام خدماتك الخاصة **و** نظام المصادقة الافتراضي، فيجب عليك تسجيل الخدمات الافتراضية يدويًا بنفسك قبل استدعاء `init_app`.

```python
from flask_devkit.users.services import UserService, RoleService, PermissionService

devkit = DevKit()
devkit.register_service("user", UserService(...))
devkit.register_service("role", RoleService(...))
devkit.register_service("permission", PermissionService(...))
# ... تسجيل خدماتك الخاصة
devkit.init_app(app, bp=api_v1_bp)
```

---

## الأدوات المساعدة والديكورات الأساسية

تتضمن DevKit العديد من الديكورات والدوال المساعدة لتقليل الكود المتكرر.

### `@unit_of_work`

هذا الديكور، الموجود في `flask_devkit.core.unit_of_work`، يغلف دالة في معاملة قاعدة بيانات. يتعامل تلقائيًا مع دورة حياة الجلسة نيابة عنك:

-   **عند النجاح:** يقوم بتنفيذ `commit` لـ `db.session`.
-   **عند حدوث استثناء:** يقوم بتنفيذ `rollback` لـ `db.session`.

يجب تطبيقه على أي دالة عرض تقوم بعمليات كتابة في قاعدة البيانات (إنشاء، تحديث، حذف).

```python
from flask_devkit.core.unit_of_work import unit_of_work

@bp.post("/")
@unit_of_work
def create_item(json_data):
    # ... منطق خدمتك الذي يكتب في قاعدة البيانات ...
    return new_item
```

### `@log_activity`

يوفر هذا الديكور من `flask_devkit.helpers.decorators` تسجيلًا أساسيًا لاستدعاءات الدوال. يسجل اسم الدالة، الوسائط، والنجاح أو الفشل. للأمان، يقوم تلقائيًا بحجب أي وسيطة كلمة رئيسية تحتوي على السلاسل الفرعية التالية: `password`, `token`, `secret`, `key`, `authorization`, `bearer`.

### `setup_rate_limiting`

تقوم هذه الدالة المساعدة في `flask_devkit.helpers.decorators` بتهيئة [Flask-Limiter](https://flask-limiter.readthedocs.io/) لتطبيقك بمعدل افتراضي معقول.

```python
# في مصنع التطبيق
from flask_devkit.helpers.decorators import setup_rate_limiting

def create_app():
    app = Flask(__name__)
    # ...
    setup_rate_limiting(app, default_rate="60/minute")
    return app
```

### معالجة الأخطاء التلقائية

يقوم المساعدان `register_crud_routes` و `register_custom_route` تلقائيًا بتسجيل مجموعة من معالجات الأخطاء على المخطط الخاص بك. تلتقط هذه المعالجات الاستثناءات الشائعة وتعيد استجابات خطأ JSON منظمة مع رموز حالة HTTP الصحيحة:

-   `NotFoundError` -> `404 Not Found`
-   `BusinessLogicError` / `PermissionDeniedError` -> `400 Bad Request` / `403 Forbidden`
-   `ValidationError` (من Marshmallow) -> `422 Unprocessable Entity`
-   `NoAuthorizationError` (من Flask-JWT-Extended) -> `401 Unauthorized`

### الـ Mixins الأساسية للنماذج

لتقليل الكود المكرر في نماذج SQLAlchemy الخاصة بك، توفر DevKit العديد من الـ mixins القابلة لإعادة الاستخدام من `flask_devkit.core.mixins`.

-   `Timestamped`: يضيف تلقائيًا عمودي `created_at` و `updated_at` إلى النموذج الخاص بك، والتي تتم إدارتها بواسطة قاعدة البيانات.

```python
# في ملف models.py الخاص بتطبيقك
from flask_devkit.core.mixins import Timestamped
from .database import db

class MyModel(db.Model, Timestamped):
    id = db.Column(db.Integer, primary_key=True)
    # الآن حقلي created_at و updated_at متاحان في هذا النموذج
```

---

## سير عمل المطور وواجهة سطر الأوامر (CLI)

بالإضافة إلى التجريدات على مستوى الكود، توفر DevKit مجموعة من الأدوات لتبسيط دورة حياة التطوير بأكملها.

### ترحيل قاعدة البيانات (Alembic)

تأتي المكتبة مُهيأة مسبقًا مع [Alembic](https://alembic.sqlalchemy.org/) لإدارة مخطط قاعدة البيانات الخاصة بك. بعد تغيير نماذج SQLAlchemy، يمكنك إنشاء وتطبيق عمليات الترحيل باستخدام أوامر Alembic القياسية.

```bash
# 1. إنشاء سكربت ترحيل جديد
poetry run alembic revision --autogenerate -m "Add post model"

# 2. تطبيق الترحيل على قاعدة البيانات الخاصة بك
poetry run alembic upgrade head
```

### واجهة سطر الأوامر (CLI)

تتضمن DevKit واجهة سطر أوامر قوية للمهام الإدارية الشائعة، مبنية على واجهة سطر الأوامر الأصلية لـ Flask. يتم كشفها عبر `flask_devkit.users.cli`.

-   **إنشاء مستخدمين:** `poetry run flask users create-user <email> --password <password> --is-superuser`
-   **إدارة الأدوار:** `poetry run flask users create-role <name>`
-   **منح الصلاحيات:** `poetry run flask users grant-permission <role_name> <permission_name>`

يتيح لك هذا إدارة تطبيقك من الطرفية (terminal) دون الحاجة إلى واجهة مستخدم أو الوصول المباشر إلى قاعدة البيانات.

### التهيئة الأولية للبيانات (Bootstrapping)

يمكن استخدام الوحدة `flask_devkit.users.bootstrap` لملء قاعدة البيانات الخاصة بك بالبيانات الأولية الأساسية، مثل الأدوار الافتراضية ("admin", "editor") أو حساب مستخدم خارق (superuser). هذا أمر بالغ الأهمية لإعداد بيئات تطوير أو إنتاج جديدة بسرعة.

```python
# في سكربت بدء تشغيل تطبيقك
from flask_devkit.users.bootstrap import bootstrap_roles

with app.app_context():
    bootstrap_roles()
```

---

## الاستخدام المتقدم

### إضافة علاقات إلى النماذج الافتراضية

ماذا لو كنت ترغب في ربط نموذجك الخاص بنموذج DevKit افتراضي؟ على سبيل المثال، لديك نموذج `Post` وتريد الوصول إلى `user.posts`.

نظرًا لأن وحدات Python هي singletons، يمكنك استيراد نموذج `User` من المكتبة وإرفاق `relationship` من SQLAlchemy به *قبل* تشغيل تطبيقك. هذه طريقة نظيفة لتوسيع النماذج الافتراضية دون تعديل الكود المصدري للمكتبة.

المشروع النموذجي `example-project` يفعل هذا بالضبط:

```python
# في your_app/models/post.py

from sqlalchemy.orm import relationship
from flask_devkit.database import db

class Post(db.Model, ...):
    # ... أعمدتك
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author = relationship("User", back_populates="posts")

# --- السحر --- #
# استيراد نموذج User من المكتبة
from flask_devkit.users.models import User

# إرفاق العلاقة الجديدة بكلاس User
User.posts = relationship("Post", back_populates="author", lazy="dynamic")
```

### إضافة حقول إلى النماذج الافتراضية (نمط Profile)

لا يوصى بتعديل جداول النماذج الافتراضية مباشرة (مثل إضافة عمود إلى جدول `users`)، حيث يمكن أن يؤدي ذلك إلى تعارضات مع تحديثات المكتبة المستقبلية. النهج الموصى به هو إنشاء نموذج `Profile` منفصل بعلاقة واحد لواحد (one-to-one) مع نموذج `User`.

هذا النمط مرن للغاية ويحافظ على بيانات المستخدم الخاصة بتطبيقك منفصلة عن بيانات المصادقة الأساسية.

```python
# في your_app/models/user_profile.py

from sqlalchemy.orm import relationship
from flask_devkit.database import db
from flask_devkit.users.models import User

class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # حقولك المخصصة
    full_name = Column(String(100))
    bio = Column(String(255))

    # إنشاء علاقة واحد لواحد
    user = relationship("User", backref=backref("profile", uselist=False))

# يمكنك بعد ذلك الوصول إلى الملف الشخصي عبر `user.profile`
```

### السيناريو 3: تخصيص الخدمات الافتراضية

يمكنك استخدام خدمات المصادقة الافتراضية ولكن مع تجاوز أجزاء من سلوكها.

#### 3.1. تجاوز المستودع (Repository)

إضافة دالة استعلام مخصصة إلى مستودع `User`.

```python
# 1. تعريف المستودع المخصص
from flask_devkit.core.repository import BaseRepository

class CustomUserRepository(BaseRepository):
    def find_all_active_users(self):
        return self._query().filter_by(is_active=True).all()

# 2. تسجيله مع DevKit قبل init_app
devkit = DevKit()
devkit.register_repository("user", CustomUserRepository)
devkit.init_app(app, bp=api_v1_bp) # لا يزال التهيئة مع الخدمات الافتراضية

# 3. الوصول إليه من تطبيقك
with app.app_context():
    user_service = devkit.get_service("user")
    active_users = user_service.repo.find_all_active_users()
```

#### 3.2. تجاوز إعدادات المسار

جعل قائمة المستخدمين عامة وتغيير الصلاحية المطلوبة لحذف مستخدم.

```python
# 1. تعريف إعدادات المسار المخصصة
public_user_routes = {
    "list": {"auth_required": False},
    "get": {"auth_required": False},
    "delete": {"permission": "delete:user_override"}, # الافتراضي هو delete:user
}

# 2. تسجيله مع DevKit قبل init_app
devkit = DevKit()
devkit.register_routes_config("user", public_user_routes)
devkit.init_app(app, bp=api_v1_bp)
```

### السيناريو 4: منطق خدمة متقدم مع الـ Hooks

استخدم الـ Hooks في خدمتك لحقن منطق أعمال دون إعادة كتابة دوال CRUD.

```python
# في services/post.py
from flask_devkit.core.service import BaseService
from flask_devkit.core.exceptions import BusinessLogicError
from flask_jwt_extended import get_jwt_identity

class PostService(BaseService[Post]):
    # استخدم hook لحقن معرف المؤلف قبل إنشاء منشور
    def pre_create_hook(self, data: dict) -> dict:
        data["author_id"] = get_jwt_identity()
        return data

    # استخدم hook لمنع حذف منشور تم نشره
    def pre_delete_hook(self, instance: Post) -> None:
        if instance.is_published:
            raise BusinessLogicError("Cannot delete a post that is already published.")
```

### السيناريو 5: إنشاء مسار مخصص غير CRUD

إنشاء نقطة نهاية مخصصة إلى `/posts/{id}/publish` تغير حالة المنشور.

```python
# في routes/post.py
from apiflask import APIBlueprint
from flask_devkit.helpers.routing import register_custom_route
from ..services.post import post_service
from ..schemas.post import post_schema

posts_bp = APIBlueprint("posts", __name__)

# ستحتوي هذه الدالة على المنطق الأساسي لنقطة النهاية
def publish_post_logic(post_id: int):
    post_service.publish(post_id) # افترض أنك أنشأت دالة `publish`
    return {"message": "Post published successfully."}

# تقوم الدالة المساعدة بربط المسار والديكورات والمنطق
register_custom_route(
    bp=posts_bp,
    view_func=publish_post_logic,
    rule="/<int:post_id>/publish",
    methods=["POST"],
    permission="publish:post",
    output_schema=MessageSchema,
)
```

### السيناريو 6: الفلترة المتقدمة

يدعم `BaseRepository` الفلترة القوية مباشرة. يمكنك تمرير الفلاتر في سلسلة الاستعلام لأي نقطة نهاية `list`.

**URL:** `/api/v1/posts?username=eq__john&likes=gte__10&status=in__draft|review`

يترجم هذا الـ URL إلى:
-   المنشورات حيث `username` يساوي `john`
-   **و** `likes` أكبر من أو تساوي `10`
-   **و** `status` موجود في القائمة `["draft", "review"]`

**المعاملات المدعومة:**
-   `eq`: يساوي
-   `ne`: لا يساوي
-   `lt`: أقل من
-   `lte`: أقل من أو يساوي
-   `gt`: أكبر من
-   `gte`: أكبر من أو يساوي
-   `in`: في قائمة مفصولة بـ `|`
-   `like`: `like` حساس لحالة الأحرف (`%value%`)
-   `ilike`: `like` غير حساس لحالة الأحرف (`%value%`)

### السيناريو 7: توسيع JWT مع Claims مخصصة

يمكنك إضافة بياناتك الخاصة إلى توكنات الوصول JWT.

```python
# 1. تعريف دالة تحميل تأخذ كائن User وتعيد قاموسًا
def add_custom_claims(user: User) -> dict:
    return {"tenant_id": str(user.tenant_id)}

# 2. تمريرها إلى مُنشئ DevKit
devkit = DevKit(additional_claims_loader=add_custom_claims)
devkit.init_app(app, bp=api_v1_bp)

# ستحتوي حمولة JWT الناتجة الآن على claim المخصص الخاص بك:
# { ..., "roles": ["admin"], "tenant_id": "some-uuid", ... }

### السيناريو 8: الحذف الناعم والاستعادة

للتطبيقات التي تتطلب أن تكون البيانات قابلة للاسترداد، توفر DevKit آلية حذف ناعم قوية ومدمجة.

#### 1. تفعيل الحذف الناعم على النموذج

لجعل النموذج "قابلاً للحذف الناعم"، ما عليك سوى إضافة `SoftDeleteMixin` من `flask_devkit.core.mixins`. يضيف هذا عمود `deleted_at` من نوع timestamp قابل للقيم الفارغة.

```python
from flask_devkit.core.mixins import SoftDeleteMixin, Timestamped
from .database import db

class MyAuditableModel(db.Model, Timestamped, SoftDeleteMixin):
    id = db.Column(db.Integer, primary_key=True)
    # ... أعمدة أخرى
```

#### 2. كيف يعمل

بمجرد أن يستخدم النموذج `SoftDeleteMixin`، يغير `BaseService` و `BaseRepository` سلوكهما تلقائيًا:

-   **`service.delete(id)`**: بدلاً من عبارة `DELETE`، يقوم هذا الآن بتنفيذ `UPDATE`، وتعيين الطابع الزمني لـ `deleted_at`. يعتبر العنصر الآن "محذوفًا ناعمًا".
-   **عمليات القراءة**: ستستبعد جميع عمليات القراءة (`get_by_id`، `list`، إلخ) **تلقائيًا** العناصر المحذوفة ناعمًا من نتائجها.

#### 3. الاستعلام عن العناصر المحذوفة ناعمًا

لاسترداد قائمة بالعناصر التي تتضمن العناصر المحذوفة ناعمًا، استخدم معامل الاستعلام `include_soft_deleted` في أي نقطة نهاية قائمة.

**URL:** `/api/v1/my-auditable-models?include_soft_deleted=true`

#### 4. استعادة عنصر

يمكنك استعادة عنصر محذوف ناعمًا باستخدام طبقة الخدمة، والتي تعيد حقل `deleted_at` الخاص به إلى `NULL`.

```python
# في كود التطبيق الخاص بك
from ..services import my_auditable_model_service

my_auditable_model_service.restore(item_id)
```

يمكنك أيضًا تمكين نقطة نهاية `/restore` عبر مساعدي التوجيه. هذه الميزة **معطلة بشكل افتراضي**.

```python
# في ملف المسارات الخاص بك
from flask_devkit.helpers.routing import register_crud_routes

crud_config = {
    "restore": {"enabled": True, "permission": "restore:my_model"},
}

register_crud_routes(
    bp=my_bp,
    service=my_service,
    schemas=my_schemas,
    crud_config=crud_config,
)
```
سيؤدي هذا إلى إنشاء نقطة نهاية `POST /my-auditable-models/<id>/restore`.

#### 5. الحذف الدائم

إذا كنت بحاجة إلى حذف سجل بشكل دائم، متجاوزًا آلية الحذف الناعم، فاستخدم دالة `force_delete`.

```python
# في كود التطبيق الخاص بك
my_auditable_model_service.force_delete(item_id)
```

```