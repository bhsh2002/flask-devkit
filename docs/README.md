# توثيق Flask-DevKit

هذا هو التوثيق الكامل لمكتبة `Flask-DevKit`. يتكون من عدة ملفات، كل منها يغطي جانبًا معينًا من المكتبة.

## الفهرس

### البدء والمفاهيم الأساسية
1.  [الإعداد والتهيئة](./01-setup.md)
2.  [الفئة الرئيسية: `DevKit`](./02-devkit-class.md)
3.  [دالة التهيئة: `init_app`](./03-init-app.md)
4.  [المفاهيم المعمارية الأساسية](./06-core-concepts.md)
5.  [طبقة المستودع: `BaseRepository`](./07-base-repository.md)
6.  [طبقة الخدمة: `BaseService`](./08-base-service.md)
7.  [ضمان سلامة البيانات: `@unit_of_work`](./09-unit-of-work.md)
8.  [الـ Mixins للنماذج](./10-model-mixins.md)

### التخصيص والتوسيع
9.  [تخصيص منطق الأعمال: `register_service`](./04-register-service.md)
10. [تخصيص الوصول للبيانات: `register_repository`](./05-register-repository.md)

### التوليد التلقائي لواجهات API
11. [التوليد التلقائي للمسارات: `register_crud_routes`](./11-register-crud-routes.md)
12. [التوليد التلقائي للـ Schemas: `create_crud_schemas`](./12-create-crud-schemas.md)
13. [بناء نقاط نهاية مخصصة: `register_custom_route`](./27-custom-routes.md)

### الميزات المدمجة

#### وحدة المستخدمين والتحكم في الوصول (RBAC)
14. [نظرة عامة على وحدة المستخدمين](./13-users-module-overview.md)
15. [نماذج قاعدة البيانات: `User`, `Role`, `Permission`](./14-user-models.md)
16. [خدمة المستخدمين: `UserService`](./15-user-service.md)
17. [خدمة الأدوار: `RoleService`](./16-role-service.md)
18. [خدمة الصلاحيات: `PermissionService`](./17-permission-service.md)
19. [مرجع واجهة برمجة التطبيقات (API Reference)](./18-api-reference.md)
20. [حماية نقاط النهاية: `@permission_required`](./19-permission-required.md)

#### التدقيق والأرشفة
21. [نظام التدقيق التلقائي](./20-auditing-system.md)
22. [نموذج سجل التدقيق: `AuditLog`](./21-auditlog-model.md)
23. [استراتيجيات الحذف: ناعم ودائم](./33-deletion-strategies.md)
24. [نموذج السجلات المؤرشفة: `ArchivedRecord`](./34-archived-record-model.md)

### الأدوات المساعدة
25. [معالجة الأخطاء الموحدة](./22-error-handling.md)
26. [أوامر واجهة سطر الأوامر (CLI)](./23-cli-commands.md)
27. [الـ Schemas الأساسية](./30-base-schemas.md)
28. [هيكلة استجابات القوائم](./29-pagination-schema.md)
29. [كائن `PaginationResult`](./37-pagination-result.md)
30. [تسجيل الأحداث (Logging)](./31-logging.md)
31. [الفلترة المتقدمة للاستعلامات](./32-advanced-filtering.md)
32. [تتبع التنفيذ: `@log_activity`](./35-log-activity-decorator.md)
33. [تحديد معدل الطلبات (Rate Limiting)](./36-rate-limiting.md)
34. [كائن قاعدة البيانات: `db`](./38-db-object.md)
