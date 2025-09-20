# Flask-DevKit: مجموعة أدوات API القابلة للتوسعة لـ Flask

`Flask-DevKit` هي مجموعة أدوات قوية وغير منحازة، مصممة لتسريع تطوير واجهات برمجة تطبيقات (APIs) آمنة وقابلة للتطوير وسهلة الصيانة باستخدام Flask. توفر المكتبة أساسًا معماريًا متينًا يعتمد على أنماط تصميم مثبتة مثل نمط المستودع (Repository) ووحدة العمل (Unit of Work)، مع توفير مرونة كاملة لتخصيص أو استبدال أو تمديد أي جزء من النظام.

على عكس الأطر الجامدة، فإن DevKit عبارة عن مجموعة من الأدوات التي يمكنك تبنيها بشكل تدريجي أو استخدامها كنقطة انطلاق كاملة. تأتي مع وحدة مصادقة وتحكم في الوصول (RBAC) افتراضية وكاملة الميزات يمكن استخدامها مباشرة، أو تفعيلها بشكل انتقائي، أو استبدالها بالكامل بمنطقك الخاص.

---

## الفلسفة: القابلية للتوسعة أولاً

-   **أنت المتحكم:** لا تضع المكتبة أي افتراضات حول احتياجات تطبيقك. يمكن تجاوز أو تمديد كل مكون رئيسي - الخدمات، المستودعات، المسارات.
-   **الاصطلاح فوق التكوين، ولكن التكوين عند الحاجة:** تسمح الإعدادات الافتراضية المنطقية بالتطوير السريع، لكن مجموعة غنية من دوال التسجيل توفر نقاطًا لإدخال منطقك المخصص أينما احتجت إليه.
-   **هيكلية متينة:** من خلال توفير تجريدات نظيفة لطبقة الخدمة، ونمط المستودع، ووحدة العمل، تساعدك DevKit على بناء تطبيقات قوية يسهل اختبارها وصيانتها.

## المكونات الأساسية

في جوهرها، تتكون Flask-DevKit من عدة مكونات رئيسية تعمل معًا.

### 1. كلاس `DevKit`

هذا هو نقطة الدخول الرئيسية للمكتبة. يعمل كسجل مركزي لخدماتك وتكويناتك.

-   `devkit.init_app(app, bp)`: يقوم بتهيئة المكتبة وتسجيل مكوناتها.
-   `devkit.register_service(name, service_instance)`: يسجل خدمة مخصصة أو افتراضية (مثل `UserService`).
-   `devkit.register_repository(service_name, CustomRepoClass)`: يتجاوز `BaseRepository` الافتراضي لخدمة معينة.
-   `devkit.register_routes_config(service_name, config_dict)`: يتجاوز إعدادات المسار الافتراضية (مثل متطلبات المصادقة) لنقاط نهاية CRUD الخاصة بالخدمة.

### 2. `BaseService`

كلاس عام لتغليف منطق الأعمال. يجب أن ترث خدماتك الخاصة منه.

-   **إدارة المستودع:** كل نسخة من الخدمة تحتوي على نسخة من المستودع (`self.repo`) للوصول إلى قاعدة البيانات.
-   **هوكات دورة الحياة:** توفر مجموعة غنية من الهوكات لإدخال منطق مخصص قبل أو بعد العمليات:
    -   `pre_create_hook`, `pre_update_hook`, `pre_delete_hook`
    -   `pre_get_hook`, `post_get_hook`, `pre_list_hook`, `post_list_hook`

### 3. `BaseRepository`

تنفيذ عام لنمط المستودع لنماذج SQLAlchemy.

-   **تغليف منطق قاعدة البيانات:** يوفر دوال قياسية مثل `create`, `get_by_id`, `paginate`, `delete`، إلخ.
-   **قابل للتمديد:** قم بإنشاء كلاس مستودع خاص بك يرث من `BaseRepository` لإضافة استعلامات مخصصة (مثل `find_by_email`).
-   **معالجة الأخطاء:** يعالج أخطاء SQLAlchemy الشائعة تلقائيًا ويغلفها في استثناءات تطبيق مخصصة.

### 4. مساعدو المسارات (Route Helpers)

تقلل هذه الدوال الموجودة في `flask_devkit.helpers.routing` بشكل كبير من الكود المتكرر عند إنشاء نقاط نهاية الـ API.

-   `register_crud_routes(...)`: يقوم تلقائيًا بإنشاء مجموعة كاملة من نقاط نهاية CRUD لخدمة معينة.
-   `register_custom_route(...)`: مصنع لإنشاء نقاط نهاية مخصصة (غير CRUD) مع تطبيق الديكورات الخاصة بالمصادقة والصلاحيات والتحقق من الصحة وإدارة المعاملات بشكل متسق.

### 5. وحدة العمل (Unit of Work)

يقوم الديكور `@unit_of_work` بتجريد إدارة جلسة قاعدة البيانات. يقوم تلقائيًا بتنفيذ `commit` للجلسة عند النجاح و `rollback` عند حدوث أي استثناء، مما يضمن أن كل طلب هو وحدة ذرية.

---

## دليل البدء: دليل عملي

فيما يلي سيناريوهات شائعة لاستخدام `flask-devkit`.

### السيناريو 1: بداية سريعة مع المصادقة الافتراضية

إذا كنت بحاجة إلى نظام مصادقة و RBAC كامل على الفور، فما عليك سوى تهيئة `DevKit` دون تسجيل أي خدمات. سيقوم تلقائيًا بتحميل وحدات `user` و `role` و `permission` الافتراضية.

```python
# في مصنع التطبيق الخاص بك
from flask_devkit import DevKit

devkit = DevKit()
# سيقوم هذا بتحميل الخدمات الافتراضية وتسجيل مساراتها على api_v1_bp
devkit.init_app(app, bp=api_v1_bp)
```

### السيناريو 2: تجاوز مستودع المستخدم

لإضافة استعلام مخصص إلى نموذج `User`، يمكنك توفير مستودع خاص بك.

```python
# 1. قم بتعريف المستودع المخصص الخاص بك
class CustomUserRepository(BaseRepository):
    def find_all_active_users(self):
        return self._query().filter_by(is_active=True).all()

# 2. قم بتسجيله مع DevKit
devkit = DevKit()
devkit.register_repository("user", CustomUserRepository)
devkit.init_app(app, bp=api_v1_bp)

# 3. يمكنك الوصول إليه من تطبيقك
with app.app_context():
    user_service = devkit.get_service("user")
    # user_service.repo هو الآن نسخة من CustomUserRepository!
    active_users = user_service.repo.find_all_active_users()
```

### السيناريو 3: جعل ملفات تعريف المستخدمين عامة

بشكل افتراضي، تتطلب نقاط نهاية المستخدم المصادقة. يمكنك تغيير هذا باستخدام `register_routes_config`.

```python
devkit = DevKit()

public_user_routes = {
    "list": {"auth_required": False},  # جعل قائمة المستخدمين عامة
    "get": {"auth_required": False},   # جعل تفاصيل المستخدم عامة
}
devkit.register_routes_config("user", public_user_routes)

devkit.init_app(app, bp=api_v1_bp)
```

### السيناريو 4: إضافة خدمة ومسارات مخصصة

هذا هو السيناريو الأكثر شيوعًا: استخدام أدوات DevKit لإدارة نماذج التطبيق الخاصة بك.

```python
# 1. قم بتعريف النموذج، المخططات، الخدمة، والبلوبرنت
class Post(db.Model, ...): ...

post_schemas = create_crud_schemas(Post, ...)

class PostService(BaseService[Post]):
    # اختياري: أضف منطقًا مخصصًا باستخدام الهوكات
    def pre_create_hook(self, data):
        data["author_id"] = get_jwt_identity()
        return data

posts_bp = APIBlueprint("posts", __name__, url_prefix="/posts")
post_service = PostService(model=Post, db_session=db.session)

# 2. قم بتسجيل مسارات CRUD لخدمتك
register_crud_routes(
    bp=posts_bp,
    service=post_service,
    schemas=post_schemas,
    entity_name="post"
)

# 3. قم بتسجيل البلوبرنت الخاص بك مع التطبيق
app.register_blueprint(posts_bp)
```
