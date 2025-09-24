# 17. خدمة الصلاحيات: `PermissionService`

`PermissionService` هي طبقة منطق الأعمال المسؤولة عن إدارة الصلاحيات (Permissions) وربطها بالأدوار (Roles).

## المسؤوليات الرئيسية

### 1. إدارة CRUD للصلاحيات

مثل الخدمات الأخرى، ترث `PermissionService` من `BaseService`، مما يمنحها وظائف CRUD كاملة لنموذج `Permission`. هذا مهم بشكل خاص لأنك ستحتاج إلى إنشاء صلاحيات مخصصة لتطبيقك.

- **`create(data)`**: لإنشاء صلاحية جديدة (e.g., `{"name": "read:report"}`).
- `update(id, data)`: لتحديث صلاحية موجودة.
- `delete(id)`: لحذف صلاحية.
- `get_by_id(id)`: لجلب صلاحية معينة.
- `paginate(...)`: لجلب قائمة بالصلاحيات.

### 2. إدارة علاقات الأدوار بالصلاحيات

توفر الخدمة توابع واضحة لإدارة الصلاحيات الممنوحة لكل دور.

- **`assign_permission_to_role(role_id: int, permission_id: int)`**
  - **الوصف:** يقوم بمنح صلاحية معينة لدور معين.
  - **ملاحظة:** التابع آمن للتكرار؛ إذا كانت الصلاحية ممنوحة بالفعل للدور، فلن يحدث أي تغيير.

- **`revoke_permission_from_role(role_id: int, permission_id: int)`**
  - **الوصف:** يقوم بإلغاء منح صلاحية من دور.

- **`list_role_permissions(role_id: int) -> List[Permission]`**
  - **الوصف:** يجلب قائمة بجميع كائنات `Permission` الممنوحة لدور معين.

## مثال عملي: إعداد دور "محرر" مخصص

يوضح هذا المثال كيف يمكنك استخدام الخدمات الثلاث معًا لإعداد دور مخصص بالكامل مع صلاحياته.

```python
# افترض أن لديك وصولاً إلى الخدمات
role_service = devkit.get_service("role")
permission_service = devkit.get_service("permission")

# 1. إنشاء دور جديد للمحررين
editor_role = role_service.create({
    "name": "editor",
    "display_name": "Content Editor",
    "description": "Can create and manage articles."
})

# 2. إنشاء الصلاحيات المخصصة التي يحتاجها تطبيقك
perm_create = permission_service.create({"name": "create:article"})
perm_update = permission_service.create({"name": "update:article"})
perm_delete = permission_service.create({"name": "delete:article"})

# ارتكاب التغييرات الأولية للحصول على IDs
db.session.commit()

# 3. تعيين الصلاحيات الجديدة لدور المحرر
permission_service.assign_permission_to_role(editor_role.id, perm_create.id)
permission_service.assign_permission_to_role(editor_role.id, perm_update.id)
permission_service.assign_permission_to_role(editor_role.id, perm_delete.id)

db.session.commit()

# 4. التحقق من النتيجة
editor_permissions = permission_service.list_role_permissions(editor_role.id)
print(f"Permissions for role '{editor_role.name}':")
for perm in editor_permissions:
    print(f"- {perm.name}")

# Output:
# Permissions for role 'editor':
# - create:article
# - update:article
# - delete:article
```

بعد تنفيذ هذا الكود، أي مستخدم يتم تعيين دور "editor" له سيرث تلقائيًا هذه الصلاحيات الثلاث، ويمكنك حماية نقاط النهاية الخاصة بالمقالات باستخدام `@permission_required("create:article")` وهكذا.
