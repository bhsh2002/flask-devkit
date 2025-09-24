# 37. حاوية نتائج التقسيم: `PaginationResult`

`PaginationResult` هو كائن بسيط ومخصص لتخزين البيانات (data container) يُستخدم داخل المكتبة لتمرير نتائج استعلامات التقسيم إلى صفحات بطريقة منظمة.

إنه `typing.NamedTuple`، مما يعني أنه كائن خفيف الوزن وغير قابل للتغيير (immutable) يوفر وصولاً سهلاً إلى حقوله عبر السمات (attributes) ويدعم تلميحات الأنواع (type hints).

## تدفق البيانات (Data Flow)

1.  يقوم تابع `repository.paginate()` بتجميع نتائج الاستعلام من قاعدة البيانات (قائمة العناصر، العدد الإجمالي، إلخ) ويقوم بتغليفها في كائن `PaginationResult`.
2.  يتم إرجاع هذا الكائن إلى تابع `service.paginate()`.
3.  يمكنك التفاعل مع هذا الكائن داخل خطافات الخدمة (service hooks) مثل `post_list_hook` لقراءة البيانات أو إجراء تعديلات على العناصر قبل إرسالها.
4.  أخيرًا، يستقبل `PaginationOutSchema` هذا الكائن ويقوم بتحويله إلى قاموس JSON النهائي الذي يتم إرساله كاستجابة لواجهة برمجة التطبيقات (API).

## حقول الكائن

يحتوي `PaginationResult` على الحقول التالية:

- **`items: List[T]`**
  - **الوصف:** قائمة بكائنات `SQLAlchemy` التي تمثل سجلات الصفحة الحالية.

- **`total: int`**
  - **الوصف:** العدد الإجمالي للسجلات المطابقة للاستعلام عبر جميع الصفحات.

- **`page: int`**
  - **الوصف:** رقم الصفحة الحالية التي تم إرجاعها (تبدأ من 1).

- **`per_page: int`**
  - **الوصف:** الحد الأقصى لعدد السجلات لكل صفحة.

- **`total_pages: int`**
  - **الوصف:** العدد الإجمالي المحسوب للصفحات.

- **`has_next: bool`**
  - **الوصف:** تكون قيمته `True` إذا كانت هناك صفحة تالية متاحة.

- **`has_prev: bool`**
  - **الوصف:** تكون قيمته `True` إذا كانت هناك صفحة سابقة متاحة.

## مثال على الاستخدام

المكان الأكثر شيوعًا للتفاعل مع هذا الكائن هو داخل خطاف `post_list_hook` في خدمة مخصصة.

```python
# في خدمة مخصصة
from flask_devkit.core.repository import PaginationResult
from flask_devkit.core.service import BaseService

class MyCustomService(BaseService):
    # ...

    def post_list_hook(self, result: PaginationResult) -> PaginationResult:
        """
        يتم استدعاؤه بعد جلب قائمة مقسمة إلى صفحات.
        """
        # يمكنك الوصول إلى البيانات الوصفية بسهولة
        print(f"Page {result.page} of {result.total_pages} loaded.")

        # يمكنك أيضًا التفاعل مع العناصر نفسها
        for item in result.items:
            # إضافة حقل محسوب قبل إرسال الاستجابة
            item.extra_info = f"This is item with ID {item.id}"

        # يجب عليك دائمًا إرجاع كائن النتيجة
        return result
```
