# 12. التوليد التلقائي للتحقق من الصحة: `create_crud_schemas`

تعمل دالة `create_crud_schemas` جنبًا إلى جنب مع `register_crud_routes` لأتمتة الجزء الأكثر مللاً في بناء واجهات برمجة التطبيقات (APIs): التحقق من صحة المدخلات (Validation) وتنسيق المخرجات (Serialization).

تستخدم هذه الدالة `marshmallow-sqlalchemy` لفحص نموذج `SQLAlchemy` الخاص بك وتوليد مجموعة كاملة من `Schemas` تلقائيًا.

## ماذا تولّد الدالة؟

تقوم الدالة بإرجاع قاموس (dictionary) يحتوي على 5 فئات `Schema` تم إنشاؤها ديناميكيًا، كل واحدة لها غرض محدد:

1.  **`main`**:
    - **الغرض:** التمثيل الكامل للنموذج.
    - **الاستخدام:** لتنسيق المخرجات في نقاط النهاية مثل `GET /<id>` و `POST /` و `PATCH /<id>`.

2.  **`input`**:
    - **الغرض:** التحقق من صحة البيانات عند إنشاء سجل جديد.
    - **الاستخدام:** كـ `input` لنقطة النهاية `POST /`.
    - **السلوك:** تستبعد تلقائيًا الحقول التي يجب ألا يوفرها المستخدم عند الإنشاء (مثل `id`, `uuid`, `created_at`).

3.  **`update`**:
    - **الغرض:** التحقق من صحة البيانات عند تحديث سجل موجود.
    - **الاستخدام:** كـ `input` لنقطة النهاية `PATCH /<id>`.
    - **السلوك:** مثل `input`، ولكن جميع الحقول تكون اختيارية (`partial=True`)، مما يسمح للمستخدم بإرسال الحقول التي يريد تحديثها فقط.

4.  **`query`**:
    - **الغرض:** التحقق من صحة معلمات الاستعلام (query parameters) في `URL`.
    - **الاستخدام:** كـ `input` لنقطة النهاية `GET /`.
    - **السلوك:** تتضمن تلقائيًا حقولًا للترتيب والتقسيم إلى صفحات (`sort_by`, `page`, `per_page`, `deleted_state`)، بالإضافة إلى أي حقول فلترة مخصصة تحددها.

5.  **`pagination_out`**:
    - **الغرض:** هيكلة الاستجابة لنقاط النهاية التي تُرجع قوائم مقسمة إلى صفحات.
    - **الاستخدام:** كـ `output` لنقطة النهاية `GET /`.
    - **السلوك:** تحتوي على حقل `items` (قائمة من `main` schema) وحقل `pagination` (يحتوي على معلومات التقسيم).

## التوقيع وخيارات التخصيص

```python
def create_crud_schemas(model_class: type, **kwargs) -> dict:
```

- **`model_class`**: فئة نموذج `SQLAlchemy` التي تريد إنشاء `Schemas` لها.
- **`**kwargs`**: مجموعة من الخيارات لتخصيص الـ `Schemas` المولدة:
  - **`exclude_from_main`**: قائمة بأسماء الحقول التي سيتم استبعادها من **جميع** الـ `Schemas`.
  - **`exclude_from_input`**: قائمة بالحقول الإضافية التي سيتم استبعادها من `InputSchema` فقط.
  - **`exclude_from_update`**: قائمة بالحقول الإضافية التي سيتم استبعادها من `UpdateSchema` فقط.
  - **`query_schema_fields`**: قائمة بأسماء الحقول التي تريد إضافتها كفلاتر قابلة للاستعلام في `QuerySchema`.
  - **`custom_fields`**: قاموس لإضافة حقول جديدة أو تجاوز حقول موجودة في `MainSchema`.

### مثال عملي: `Schemas` لنموذج منتج

لنفترض أن لدينا نموذج `Product` ونريد إنشاء `Schemas` له مع القواعد التالية:
1.  لا نريد عرض حقل `internal_notes` أبدًا في الـ API.
2.  نريد السماح بالفلترة حسب `name` و `is_active`.
3.  نريد إضافة حقل `url` للقراءة فقط (read-only) إلى الاستجابة.

```python
# models.py
class Product(db.Model, IDMixin, UUIDMixin):
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    internal_notes = Column(Text) # حقل داخلي

# schemas.py
from apiflask.fields import String
from flask_devkit.helpers.schemas import create_crud_schemas
from .models import Product

# 1. إنشاء الـ Schemas مع خيارات التخصيص
product_schemas = create_crud_schemas(
    model_class=Product,
    # 1. استبعاد الحقل الداخلي من كل مكان
    exclude_from_main=["internal_notes"],
    # 2. السماح بالفلترة حسب هذه الحقول
    query_schema_fields=["name", "is_active"],
    # 3. إضافة حقل مخصص للقراءة فقط
    custom_fields={
        "url": String(
            dump_only=True,
            metadata={"description": "The public URL for the product."}
        )
    }
)

# الآن، product_schemas هو قاموس جاهز للاستخدام
# product_schemas["main"]
# product_schemas["input"]
# ...
```

القاموس `product_schemas` الناتج جاهز الآن ليتم تمريره مباشرة إلى دالة `register_crud_routes`، مما يكمل دورة أتمتة واجهة برمجة التطبيقات.
