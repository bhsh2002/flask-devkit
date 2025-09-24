# 28. تسجيل معالجات الأخطاء: `register_error_handlers`

هذه الدالة المساعدة هي التي تربط نظام الاستثناءات المخصص (Custom Exceptions) بـ `Blueprint` معين، مما يضمن أن جميع الأخطاء التي تحدث داخل هذا الـ `Blueprint` يتم تحويلها إلى استجابات JSON موحدة.

## الغرض

تقوم الدالة بتسجيل مجموعة من معالجات الأخطاء (Error Handlers) على `Blueprint` معين. كل معالج مسؤول عن التقاط نوع معين من الاستثناءات وتحويله إلى استجابة HTTP مناسبة.

## ماذا تعالج الدالة؟

تقوم بتسجيل معالجات للاستثناءات التالية:

- **`AppBaseException` (وفئاتها الفرعية):**
  - هذا هو المعالج الرئيسي. عندما يتم إطلاق أي استثناء يرث من `AppBaseException` (مثل `NotFoundError`, `BusinessLogicError`, `PermissionDeniedError`)، يقوم هذا المعالج باستدعاء تابع `.to_dict()` الخاص بالاستثناء لتوليد جسم JSON للخطأ، ويستخدم `.status_code` الخاص به لرمز حالة HTTP.

- **`ValidationError` (من Marshmallow):**
  - يلتقط أخطاء التحقق من الصحة من `Schemas`. يُرجع استجابة `422 Unprocessable Entity` مع قاموس `errors` مفصل يوضح أي الحقول فشلت في التحقق ولماذا.

- **`NoAuthorizationError` (من Flask-JWT-Extended):**
  - يلتقط الحالة التي يتم فيها استدعاء نقطة نهاية تتطلب JWT دون إرسال التوكن. يُرجع استجابة `401 Unauthorized`.

- **`Exception` (المعالج الشامل):**
  - هذا هو صمام الأمان. يلتقط أي استثناء آخر غير متوقع في التطبيق.
  - يقوم بتسجيل الخطأ كـ "critical" في سجلات الخادم.
  - يُرجع استجابة `500 Internal Server Error` عامة لتجنب تسريب أي تفاصيل حساسة عن التنفيذ إلى العميل.

## الاستخدام التلقائي مقابل اليدوي

**عادة، لا تحتاج إلى استدعاء هذه الدالة بنفسك.**

تقوم دالة `register_crud_routes` باستدعائها تلقائيًا على كل `Blueprint` يتم تمريره إليها. هذا يعني أن جميع واجهات برمجة التطبيقات التي تم إنشاؤها تلقائيًا تحصل على معالجة الأخطاء الموحدة هذه مجانًا.

الحالة الوحيدة التي قد تحتاج فيها إلى استدعاء هذه الدالة يدويًا هي إذا قمت بإنشاء `Blueprint` جديد تمامًا من الصفر (دون استخدام `register_crud_routes`) وتريد أن يكون له نفس سلوك معالجة الأخطاء المتسق.

### مثال على الاستخدام اليدوي

```python
from apiflask import APIBlueprint
from flask_devkit.helpers.routing import register_error_handlers
from flask_devkit.core.exceptions import BusinessLogicError

# 1. إنشاء Blueprint مخصص
payments_bp = APIBlueprint('payments', __name__, url_prefix='/payments')

# 2. تطبيق معالجات الأخطاء القياسية عليه
register_error_handlers(payments_bp)

@payments_bp.route('/charge', methods=['POST'])
def charge_customer():
    # ... منطق معالجة الدفع
    if insufficient_funds:
        # بفضل register_error_handlers، سيتم تحويل هذا الاستثناء
        # تلقائيًا إلى استجابة JSON 400 Bad Request.
        raise BusinessLogicError("Insufficient funds.")

    return {"message": "Charge successful"}
```
