# 22. معالجة الأخطاء الموحدة

توفر `Flask-DevKit` نظامًا مركزيًا لمعالجة الأخطاء يضمن أن جميع استجابات الأخطاء من واجهة برمجة التطبيقات (API) تتبع تنسيق JSON موحدًا وواضحًا. هذا يسهل على مطوري الواجهة الأمامية (Frontend) التعامل مع الأخطاء البرمجية.

## الفكرة الأساسية

تعتمد الفكرة على استخدام فئات استثناء (Exception Classes) مخصصة لتمثيل أنواع مختلفة من الأخطاء (مثل "غير موجود" أو "صلاحية مرفوضة"). تقوم المكتبة بعد ذلك بالتقاط هذه الاستثناءات تلقائيًا وتحويلها إلى استجابات JSON مناسبة مع رموز HTTP الصحيحة.

## `AppBaseException`

هي فئة الاستثناء الأساسية التي ترث منها جميع الاستثناءات المخصصة الأخرى في المكتبة. تحتوي على السمات التالية:
- `message`: رسالة خطأ قابلة للقراءة.
- `status_code`: رمز حالة HTTP الذي سيتم إرساله (e.g., 404, 403).
- `error_code`: رمز نصي فريد للخطأ يمكن استخدامه في الواجهة الأمامية (e.g., "NOT_FOUND").
- `payload`: قاموس اختياري لإرسال بيانات إضافية مع الخطأ.

## الاستثناءات المدمجة

توفر المكتبة مجموعة من الاستثناءات الجاهزة للاستخدام الشائع:

| الاستثناء (Exception) | رمز HTTP | رمز الخطأ (Error Code) | متى يُستخدم |
| :--- | :---: | :--- | :--- |
| `NotFoundError` | 404 | `NOT_FOUND` | عندما لا يتم العثور على سجل (e.g., مستخدم غير موجود). |
| `DuplicateEntryError` | 409 | `DUPLICATE_ENTRY` | عند محاولة إنشاء سجل بقيمة فريدة موجودة بالفعل. |
| `BusinessLogicError` | 400 | `BUSINESS_LOGIC_ERROR` | للأخطاء العامة في منطق العمل (e.g., "رصيد غير كافٍ"). |
| `AuthenticationError` | 401 | `AUTHENTICATION_FAILED` | لبيانات اعتماد تسجيل الدخول غير الصحيحة. |
| `PermissionDeniedError` | 403 | `PERMISSION_DENIED` | عندما يحاول مستخدم مصادق عليه الوصول إلى مورد لا يمتلك صلاحيته. |
| `DatabaseError` | 500 | `DATABASE_ERROR` | للأخطاء غير المتوقعة من قاعدة البيانات. |

## المعالجة التلقائية

تقوم دالة `register_error_handlers` (التي يتم استدعاؤها تلقائيًا بواسطة `register_crud_routes`) بتسجيل معالجات لهذه الاستثناءات. هذا يعني أنك إذا قمت بإطلاق أي من هذه الاستثناءات من أي مكان في طبقة الخدمة أو المسار، فسيتم التقاطه تلقائيًا وإرجاع استجابة JSON منسقة.

### مثال: إطلاق خطأ في منطق العمل

لنفترض أنك تريد منع المستخدمين من حذف الأدوار التي لا تزال معينة لمستخدمين. يمكنك تحقيق ذلك في `RoleService` المخصص لك.

```python
# في CustomRoleService

from flask_devkit.core.exceptions import BusinessLogicError
from flask_devkit.users.services import RoleService

class CustomRoleService(RoleService):
    def pre_delete_hook(self, instance: Role):
        # استدعاء الخطاف الأصلي أولاً لحماية أدوار النظام
        super().pre_delete_hook(instance)

        # إضافة القاعدة المخصصة
        if instance.users: # instance.users هي علاقة SQLAlchemy
            raise BusinessLogicError(
                message=f"Cannot delete role '{instance.name}' because it is still assigned to {len(instance.users)} user(s).",
                error_code="ROLE_IN_USE", # يمكنك تحديد رمز خطأ مخصص
                payload={"user_count": len(instance.users)} # بيانات إضافية
            )
```

**الإجراء:**
يقوم مسؤول بإرسال طلب `DELETE` إلى `/api/v1/roles/3`، وهذا الدور لا يزال معينًا لمستخدمين.

**النتيجة:**
سيطلق الكود أعلاه استثناء `BusinessLogicError`. سيلتقطه معالج الأخطاء ويرسل الاستجابة التالية تلقائيًا:

```json
// HTTP/1.1 400 Bad Request
{
  "message": "Cannot delete role 'editor' because it is still assigned to 5 user(s).",
  "error_code": "ROLE_IN_USE",
  "details": {
    "user_count": 5
  }
}
```
