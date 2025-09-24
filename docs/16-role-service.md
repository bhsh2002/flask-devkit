# 16. خدمة الأدوار: `RoleService`

`RoleService` هي طبقة منطق الأعمال المسؤولة عن إدارة الأدوار (Roles) والعلاقات التي تربطها بالمستخدمين والصلاحيات.

## المسؤوليات الرئيسية

### 1. إدارة CRUD للأدوار

نظرًا لأن `RoleService` ترث من `BaseService`، فإنها تحصل تلقائيًا على جميع وظائف CRUD القياسية لإدارة الأدوار:
- `create(data)`: لإنشاء دور جديد.
- `update(id, data)`: لتحديث دور موجود.
- `delete(id)`: لحذف دور.
- `get_by_id(id)`: لجلب دور معين.
- `paginate(...)`: لجلب قائمة بالأدوار مع تقسيم الصفحات والفلترة.

### 2. حماية أدوار النظام

تحتوي الخدمة على منطق مدمج لحماية الأدوار الهامة. أي دور يتم تمييزه بـ `is_system_role=True` (مثل دور "admin" الافتراضي) لا يمكن حذفه أو إعادة تسميته عبر الخدمة. هذا يمنع الأخطاء العرضية التي قد تعطل النظام.

- **`pre_delete_hook`**: يتم استدعاؤه قبل الحذف ويطلق استثناء `BusinessLogicError` إذا كان الدور هو دور نظام.
- **`pre_update_hook`**: يتم استدعاؤه قبل التحديث ويمنع تغيير حقل `name` لدور النظام.

### 3. إدارة علاقات المستخدمين بالأدوار

هذه هي الوظيفة الأساسية لـ `RoleService`. توفر توابع واضحة لإدارة الأدوار المعينة للمستخدمين.

- **`assign_role(user: User, role: Role, assigned_by_user_id: int)`**
  - **الوصف:** يقوم بتعيين دور معين لمستخدم معين. يقوم بإنشاء سجل في جدول الربط `user_roles`.
  - **ملاحظة:** التابع آمن للتكرار؛ إذا كان الدور معينًا بالفعل للمستخدم، فلن يحدث أي تغيير.

- **`revoke_role(user: User, role: Role)`**
  - **الوصف:** يقوم بإلغاء تعيين دور من مستخدم. يقوم بحذف السجل من جدول الربط `user_roles`.

- **`get_roles_for_user(user: User) -> List[Role]`**
  - **الوصف:** يجلب قائمة بجميع كائنات `Role` المعينة لمستخدم معين.

## الاستخدام البرمجي

بينما يتم استدعاء هذه التوابع عادةً تلقائيًا بواسطة نقاط نهاية API المدمجة، يمكنك أيضًا استخدامها برمجيًا في نصوصك المخصصة أو أوامر CLI.

```python
# افترض أن لديك وصولاً إلى الخدمات
user_service = devkit.get_service("user")
role_service = devkit.get_service("role")

# 1. جلب المستخدم والدور المطلوبين
user_to_promote = user_service.find_one_by({"username": "test_user"})
editor_role = role_service.find_one_by({"name": "editor"})

# 2. جلب المستخدم المسؤول عن العملية (من JWT على سبيل المثال)
admin_user_id = 1

# 3. تعيين الدور
if user_to_promote and editor_role:
    role_service.assign_role(
        user=user_to_promote,
        role=editor_role,
        assigned_by_user_id=admin_user_id
    )
    db.session.commit() # لا تنس الـ commit إذا لم تكن تستخدم @unit_of_work
    print(f"Role '{editor_role.name}' assigned to '{user_to_promote.username}'.")

# 4. التحقق من أدوار المستخدم
user_roles = role_service.get_roles_for_user(user=user_to_promote)
print(f"Current roles: {[role.name for role in user_roles]}")
# Output: Current roles: ['editor']
```
