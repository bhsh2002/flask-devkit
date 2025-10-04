# 8. طبقة منطق الأعمال: `BaseService`

تعتبر `BaseService` هي الفئة الأساسية لطبقة منطق الأعمال (Business Logic Layer). هي بمثابة المنسق الذي يقف بين طبقة المسارات (Routes) وطبقة المستودعات (Repositories).

## الغرض الأساسي

- **تطبيق قواعد العمل:** هذا هو المكان الذي تضع فيه قواعد تطبيقك. على سبيل المثال، "لا يمكن للمستخدم تغيير بريده الإلكتروني إلى عنوان مستخدم بالفعل" أو "يجب أن يكون سعر المنتج أكبر من صفر".
- **تنسيق العمليات:** قد تتطلب عملية واحدة التفاعل مع عدة مستودعات أو خدمات أخرى. الخدمة هي المكان المناسب لتنسيق هذا التفاعل.
- **فصل الاهتمامات:** تفصل منطق الأعمال عن تفاصيل الوصول إلى قاعدة البيانات (المستودع) وتفاصيل بروتوكول HTTP (المسار).

## نظام الخطافات (The Hook System)

الميزة الأقوى في `BaseService` هي نظام "الخطافات" (Hooks). هذه هي توابع فارغة يمكنك تجاوزها (override) في فئات الخدمة المخصصة الخاصة بك لوضع منطقك الخاص في مراحل مختلفة من دورة حياة عملية ما (CRUD).

### خطافات الكتابة (Write Hooks)

- **`pre_create_hook(self, data: Dict) -> Dict`**
  - **متى:** يُستدعى قبل إنشاء سجل جديد، بعد تلقي البيانات من المستخدم.
  - **الاستخدام:** مثالي للتحقق من صحة البيانات (validation)، أو تعديل البيانات قبل حفظها (e.g., `username.lower()‎`), أو تعيين قيم افتراضية. يجب أن يُرجع القاموس `data` بعد التعديل.

- **`post_create_hook(self, instance: TModel) -> TModel`**
  - **متى:** يُستدعى بعد إنشاء السجل وحفظه في قاعدة البيانات.
  - **الاستخدام:** لتنفيذ إجراءات لاحقة مثل إرسال بريد إلكتروني أو تحديث نظام آخر.

- **`pre_update_hook(self, instance: TModel, data: Dict)`**
  - **متى:** يُستدعى قبل تحديث سجل موجود.
  - **الاستخدام:** للتحقق من صحة البيانات في سياق السجل الحالي. على سبيل المثال، التحقق من أن الحالة الجديدة للسجل مسموح بها بناءً على حالته الحالية.

- **`post_update_hook(self, instance: TModel) -> TModel`**
  - **متى:** يُستدعى بعد تحديث السجل.
  - **الاستخدام:** لتنفيذ إجراءات لاحقة بعد التحديث.

- **`pre_delete_hook(self, instance: TModel, data: Optional[Dict] = None)`**
  - **متى:** يُستدعى قبل حذف سجل.
  - **الاستخدام:** للتحقق مما إذا كان يمكن حذف السجل. إذا تم توفير `input_schema` لمسار الحذف، فستكون البيانات المدمجة متاحة في المعلمة `data` (e.g., لتسجيل سبب الحذف).

- **`post_delete_hook(self, instance: TModel) -> None`**
  - **متى:** يُستدعى بعد حذف السجل.
  - **الاستخدام:** لتنفيذ عمليات تنظيف أو تسجيل بعد الحذف.

- **`pre_restore_hook(self, instance: TModel, data: Optional[Dict] = None)`**
  - **متى:** يُستدعى قبل استعادة سجل محذوف حذفًا ناعمًا.
  - **الاستخدام:** يمكن استخدام البيانات الممررة من `input_schema` لتسجيل سبب الاستعادة.

- **`post_restore_hook(self, instance: TModel) -> TModel`**
  - **متى:** يُستدعى بعد استعادة السجل.

### خطافات القراءة (Read Hooks)

- **`post_get_hook(self, entity: Optional[TModel]) -> Optional[TModel]`**
  - **متى:** يُستدعى بعد جلب سجل واحد من قاعدة البيانات.
  - **الاستخدام:** لتعديل السجل قبل إرساله كاستجابة. على سبيل المثال، إضافة حقل محسوب (calculated field).

- **`post_list_hook(self, result: PaginationResult) -> PaginationResult`**
  - **متى:** يُستدعى بعد جلب قائمة من السجلات (من `paginate`).
  - **الاستخدام:** لتعديل قائمة السجلات أو بيانات التقسيم إلى صفحات (pagination) قبل إرسالها.

## مثال عملي: خدمة منتجات مخصصة

لنفترض أن لدينا نموذج `Product` ونريد إنشاء خدمة له مع القواعد التالية:
1. لا يمكن إنشاء منتج بسعر سالب.
2. عند جلب منتج، أضف حقلاً `price_with_tax` (السعر مع الضريبة).

```python
# models.py
class Product(db.Model, IDMixin):
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)

# services.py
from flask_devkit.core.service import BaseService
from flask_devkit.core.exceptions import BusinessLogicError

TAX_RATE = 0.15

class ProductService(BaseService[Product]):

    def pre_create_hook(self, data: dict) -> dict:
        """
        التحقق من السعر قبل إنشاء المنتج.
        """
        if data.get("price", 0) < 0:
            raise BusinessLogicError("Price cannot be negative.")
        return data

    def post_get_hook(self, entity: Product | None) -> Product | None:
        """
        إضافة حقل محسوب إلى المنتج بعد جلبه.
        """
        if entity:
            entity.price_with_tax = entity.price * (1 + TAX_RATE)
        return entity

    def post_list_hook(self, result: PaginationResult) -> PaginationResult:
        """
        إضافة الحقل المحسوب لكل منتج في القائمة.
        """
        for item in result.items:
            item.price_with_tax = item.price * (1 + TAX_RATE)
        return result

# app.py
# ...
# devkit.register_service(
#     "product",
#     ProductService(model=Product, db_session=db.session)
# )
# devkit.init_app(app)
```

بهذه الطريقة، يمكنك بسهولة حقن منطق عملك في التدفق القياسي للمكتبة دون الحاجة إلى إعادة كتابة منطق CRUD الأساسي.