# 18. مرجع واجهة برمجة التطبيقات (API Reference)

توفر `Flask-DevKit` مجموعة غنية من نقاط النهاية (Endpoints) الجاهزة لإدارة المستخدمين، الأدوار، الصلاحيات، والمصادقة. البادئة الافتراضية لجميع هذه المسارات هي `/api/v1`.

---

## 1. واجهة المصادقة (Authentication API)
**المسار الأساسي: `/auth`**

### تسجيل الدخول
- **`POST /login`**
  - **الوصف:** لمصادقة المستخدم وإرجاع رموز JWT.
  - **المصادقة:** لا يتطلب.
  - **الطلب (Request Body):**
    ```json
    {
      "username": "admin",
      "password": "your_password"
    }
    ```
  - **الاستجابة (Success 200):**
    ```json
    {
      "access_token": "...",
      "refresh_token": "...",
      "user": {
        "uuid": "...",
        "username": "admin",
        ...
      }
    }
    ```

### تحديث رمز الوصول
- **`POST /refresh`**
  - **الوصف:** لإنشاء `access_token` جديد باستخدام `refresh_token` صالح.
  - **المصادقة:** يتطلب `refresh_token`.
  - **الاستجابة (Success 200):**
    ```json
    {
      "access_token": "..."
    }
    ```

### الحصول على المستخدم الحالي
- **`GET /me`**
  - **الوصف:** للحصول على تفاصيل المستخدم الذي تم توثيقه حاليًا.
  - **المصادقة:** يتطلب `access_token`.
  - **الاستجابة (Success 200):**
    ```json
    {
      "uuid": "...",
      "username": "admin",
      "is_active": true,
      ...
    }
    ```

---

## 2. واجهة المستخدمين (Users API)
**المسار الأساسي: `/users`**

### تغيير كلمة المرور
- **`POST /change-password`**
  - **الوصف:** لتغيير كلمة مرور المستخدم الحالي.
  - **المصادقة:** يتطلب `access_token`.
  - **الطلب (Request Body):**
    ```json
    {
      "current_password": "old_password",
      "new_password": "new_strong_password"
    }
    ```
  - **الاستجابة (Success 200):**
    ```json
    {
      "message": "Password changed successfully"
    }
    ```

### إدارة CRUD للمستخدمين
يتم إنشاء نقاط النهاية التالية تلقائيًا بواسطة `register_crud_routes`.

- `GET /`: قائمة المستخدمين (تتطلب صلاحية `read:user` افتراضيًا).
- `POST /`: إنشاء مستخدم جديد (تتطلب صلاحية `create:user` افتراضيًا).
- `GET /<uuid>`: جلب مستخدم واحد (تتطلب صلاحية `read:user` افتراضيًا).
- `PATCH /<uuid>`: تحديث مستخدم (تتطلب صلاحية `update:user` افتراضيًا).
- `DELETE /<uuid>`: حذف مستخدم (تتطلب صلاحية `delete:user` افتراضيًا).

---

## 3. واجهة الأدوار (Roles API)
**المسار الأساسي: `/roles`**

### إدارة CRUD للأدوار
- `GET /`, `POST /`, `GET /<id>`, `PATCH /<id>`, `DELETE /<id>`
- **الصلاحيات الافتراضية:** `read:role`, `create:role`, `update:role`, `delete:role`.

### إدارة علاقات الأدوار
- **`GET /users/<user_uuid>`**: جلب الأدوار المعينة لمستخدم.
  - **الصلاحية:** `read_roles:user`
- **`POST /users/<user_uuid>`**: تعيين دور لمستخدم.
  - **الصلاحية:** `assign_role:user`
  - **الطلب:** `{"role_id": 123}`
- **`DELETE /users/<user_uuid>`**: إلغاء تعيين دور من مستخدم.
  - **الصلاحية:** `revoke_role:user`
  - **الطلب:** `{"role_id": 123}`
- **`GET /<role_id>/permissions`**: جلب الصلاحيات الممنوحة لدور.
  - **الصلاحية:** `read_permissions:role`
- **`POST /<role_id>/permissions`**: منح صلاحية لدور.
  - **الصلاحية:** `assign_permission:role`
  - **الطلب:** `{"permission_id": 456}`
- **`DELETE /<role_id>/permissions`**: إلغاء منح صلاحية من دور.
  - **الصلاحية:** `revoke_permission:role`
  - **الطلب:** `{"permission_id": 456}`

---

## 4. واجهة الصلاحيات (Permissions API)
**المسار الأساسي: `/permissions`**

### إدارة CRUD للصلاحيات
- `GET /`, `POST /`, `GET /<id>`, `PATCH /<id>`, `DELETE /<id>`
- **الصلاحيات الافتراضية:** `read:permission`, `create:permission`, `update:permission`, `delete:permission`.
- **ملاحظة:** تُستخدم هذه الواجهة عادةً لإضافة صلاحيات مخصصة لتطبيقك (e.g., `create:invoice`, `read:report`).
