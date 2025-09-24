=================================================
خطة التوثيق الشاملة: Flask-DevKit
=================================================
ملخص: لقد قمت بمسح شامل للكود وتم تحديد 38 عنصر قابل للتوثيق.
-------------------------------------------------

ID: 1
  - النوع: الإعداد
  - الوحدة: README.md
  - الاسم: الإعداد والتهيئة
  - الوصف: كيفية تثبيت المكتبة وتهيئة الفئة `DevKit` الرئيسية داخل مشروع Flask.

ID: 2
  - النوع: Class
  - الوحدة: flask_devkit/__init__.py
  - الاسم: DevKit
  - الوصف: الفئة الرئيسية للمكتبة التي تدير الخدمات، المستودعات، والإعدادات.

ID: 3
  - النوع: Function
  - الوحدة: flask_devkit/__init__.py
  - الاسم: DevKit.init_app
  - الوصف: تهيئة المكتبة مع تطبيق Flask، وتسجيل المكونات الافتراضية.

ID: 4
  - النوع: Function
  - الوحدة: flask_devkit/__init__.py
  - الاسم: DevKit.register_service
  - الوصف: كيفية تسجيل خدمة مخصصة (Custom Service) لتجاوز أو إضافة منطق أعمال.

ID: 5
  - النوع: Function
  - الوحدة: flask_devkit/__init__.py
  - الاسم: DevKit.register_repository
  - الوصف: كيفية تسجيل مستودع مخصص (Custom Repository) لتجاوز منطق الوصول للبيانات.

ID: 6
  - النوع: Concept
  - الوحدة: flask_devkit/core/
  - الاسم: المفاهيم الأساسية
  - الوصف: شرح للأنماط المعمارية المستخدمة: Repository, Service, Unit of Work.

ID: 7
  - النوع: Class
  - الوحدة: flask_devkit/core/repository.py
  - الاسم: BaseRepository
  - الوصف: الفئة الأساسية للمستودعات التي توفر عمليات CRUD عامة.

ID: 8
  - النوع: Class
  - الوحدة: flask_devkit/core/service.py
  - الاسم: BaseService
  - الوصف: الفئة الأساسية للخدمات التي تحتوي على منطق الأعمال وتستخدم المستودعات.

ID: 9
  - النوع: Decorator
  - الوحدة: flask_devkit/core/unit_of_work.py
  - الاسم: @unit_of_work
  - الوصف: مُزين (Decorator) لضمان تنفيذ العمليات داخل معاملة قاعدة بيانات (Transaction).

ID: 10
  - النوع: Concept
  - الوحدة: flask_devkit/core/mixins.py
  - الاسم: Model Mixins
  - الوصف: شرح للـ Mixins الجاهزة (`IDMixin`, `UUIDMixin`, `TimestampMixin`, `SoftDeleteMixin`).

ID: 11
  - النوع: Function
  - الوحدة: flask_devkit/helpers/routing.py
  - الاسم: register_crud_routes
  - الوصف: دالة قوية لتوليد مسارات CRUD REST API بشكل تلقائي لنموذج معين.

ID: 12
  - النوع: Function
  - الوحدة: flask_devkit/helpers/schemas.py
  - الاسم: create_crud_schemas
  - الوصف: دالة لإنشاء مجموعة كاملة من Schemas (main, input, update, query) لنموذج SQLAlchemy.

ID: 13
  - النوع: Concept
  - الوحدة: flask_devkit/users/
  - الاسم: وحدة المستخدمين
  - الوصف: نظرة عامة على وحدة إدارة المستخدمين والصلاحيات المدمجة.

ID: 14
  - النوع: Models
  - الوحدة: flask_devkit/users/models.py
  - الاسم: User, Role, Permission
  - الوصف: شرح لنماذج قاعدة البيانات الأساسية لإدارة المستخدمين والصلاحيات.

ID: 15
  - النوع: Service
  - الوحدة: flask_devkit/users/services.py
  - الاسم: UserService
  - الوصف: الخدمة المسؤولة عن منطق المستخدمين، مثل تسجيل الدخول وإنشاء المستخدمين.

ID: 16
  - النوع: Service
  - الوحدة: flask_devkit/users/services.py
  - الاسم: RoleService
  - الوصف: الخدمة المسؤولة عن إدارة الأدوار (Roles) وتعيينها للمستخدمين.

ID: 17
  - النوع: Service
  - الوحدة: flask_devkit/users/services.py
  - الاسم: PermissionService
  - الوصف: الخدمة المسؤولة عن إدارة الصلاحيات (Permissions) وربطها بالأدوار.

ID: 18
  - النوع: Endpoints
  - الوحدة: flask_devkit/users/routes.py
  - الاسم: Auth & Users API
  - الوصف: توثيق نقاط النهاية (Endpoints) الخاصة بالمصادقة وإدارة المستخدمين.

ID: 19
  - النوع: Decorator
  - الوحدة: flask_devkit/auth/decorators.py
  - الاسم: @permission_required
  - الوصف: مُزين للتحقق من أن المستخدم لديه صلاحية معينة للوصول إلى نقطة نهاية.

ID: 20
  - النوع: Concept
  - الوحدة: flask_devkit/audit/
  - الاسم: نظام التدقيق (Auditing)
  - الوصف: شرح لكيفية عمل نظام التدقيق التلقائي الذي يسجل جميع عمليات (CUD).

ID: 21
  - النوع: Model
  - الوحدة: flask_devkit/audit/models.py
  - الاسم: AuditLog
  - الوصف: نموذج قاعدة البيانات الذي يخزن سجلات التدقيق.

ID: 22
  - النوع: Concept
  - الوحدة: flask_devkit/core/exceptions.py
  - الاسم: معالجة الأخطاء
  - الوصف: شرح لنظام الاستثناءات (Exceptions) المخصص وكيفية التعامل معه.

ID: 23
  - النوع: CLI Command
  - الوحدة: flask_devkit/core/cli.py
  - الاسم: devkit-init-db
  - الوصف: أمر لإنشاء جميع جداول قاعدة البيانات.

ID: 24
  - النوع: CLI Command
  - الوحدة: flask_devkit/core/cli.py
  - الاسم: devkit-truncate-db
  - الوصف: أمر لحذف جميع البيانات من الجداول (Truncate).

ID: 25
  - النوع: CLI Command
  - الوحدة: flask_devkit/core/cli.py
  - الاسم: devkit-drop-db
  - الوصف: أمر لحذف قاعدة البيانات بالكامل (للـ SQLite و MySQL).

ID: 26
  - النوع: CLI Command
  - الوحدة: flask_devkit/users/cli.py
  - الاسم: devkit-seed
  - الوصف: أمر لملء قاعدة البيانات بالصلاحيات والأدوار الافتراضية ومستخدم مسؤول.

ID: 27
  - النوع: Function
  - الوحدة: flask_devkit/helpers/routing.py
  - الاسم: register_custom_route
  - الوصف: دالة مساعدة لتسجيل نقاط نهاية مخصصة مع تطبيق معايير المكتبة.

ID: 28
  - النوع: Function
  - الوحدة: flask_devkit/helpers/routing.py
  - الاسم: register_error_handlers
  - الوصف: دالة لتسجيل معالجات الأخطاء القياسية لمخطط (Blueprint).

ID: 29
  - النوع: Function
  - الوحدة: flask_devkit/helpers/schemas.py
  - الاسم: create_pagination_schema
  - الوصف: دالة لإنشاء Schema لإخراج البيانات المقسمة لصفحات (Pagination).

ID: 30
  - النوع: Schemas
  - الوحدة: flask_devkit/helpers/schemas.py
  - الاسم: Schemas أساسية
  - الوصف: شرح للـ Schemas الأساسية مثل `PaginationQuerySchema` و `MessageSchema`.

ID: 31
  - النوع: Function
  - الوحدة: flask_devkit/logging.py
  - الاسم: init_app (logging)
  - الوصف: دالة لتهيئة نظام تسجيل الأحداث (Logging).

ID: 32
  - النوع: Concept
  - الوحدة: flask_devkit/core/repository.py
  - الاسم: مرونة الفلاتر
  - الوصف: كيفية استخدام الفلاتر المتقدمة (`__in`, `__like`, etc) مع `BaseRepository`.

ID: 33
  - النوع: Concept
  - الوحدة: flask_devkit/core/repository.py
  - الاسم: الحذف الناعم والدائم
  - الوصف: شرح للفرق بين الحذف الناعم (Soft Delete) والحذف الدائم (Force Delete).

ID: 34
  - النوع: Model
  - الوحدة: flask_devkit/core/archive.py
  - الاسم: ArchivedRecord
  - الوصف: نموذج قاعدة البيانات الذي يخزن السجلات المحذوفة بشكل دائم.

ID: 35
  - النوع: Decorator
  - الوحدة: flask_devkit/helpers/decorators.py
  - الاسم: @log_activity
  - الوصف: مُزين لتسجيل نشاط استدعاء الدوال (لأغراض التصحيح).

ID: 36
  - النوع: Function
  - الوحدة: flask_devkit/helpers/decorators.py
  - الاسم: setup_rate_limiting
  - الوصف: دالة لإعداد وتطبيق حدود لمعدل الطلبات (Rate Limiting).

ID: 37
  - النوع: Class
  - الوحدة: flask_devkit/core/repository.py
  - الاسم: PaginationResult
  - الوصف: كائن NamedTuple الذي يتم إرجاعه من استعلامات التقسيم لصفحات.

ID: 38
  - النوع: Variable
  - الوحدة: flask_devkit/database.py
  - الاسم: db
  - الوصف: كائن `SQLAlchemy` المستخدم في المكتبة بأكملها.
