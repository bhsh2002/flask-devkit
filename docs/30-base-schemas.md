# 30. الـ Schemas الأساسية والقابلة لإعادة الاستخدام

بالإضافة إلى دوال المصانع (factories) التي تولد `Schemas` تلقائيًا، توفر `Flask-DevKit` مجموعة من فئات `Schema` الأساسية التي يمكنك استخدامها مباشرة أو الوراثة منها لبناء منطق تحقق من الصحة مخصص.

## 1. Schemas معلمات الاستعلام (Query Parameter Schemas)

توفر المكتبة سلسلة من `Schemas` المخصصة للتحقق من صحة معلمات الاستعلام في عنوان URL (e.g., `?page=2&sort_by=-name`). هذه الـ `Schemas` مبنية على الوراثة.

### `PaginationQuerySchema`
- **الوصف:** أبسط `Schema` للاستعلام، يوفر فقط معلمات التقسيم إلى صفحات.
- **الحقول:**
  - `page` (Integer, default: 1)
  - `per_page` (Integer, default: 10)

### `BaseListQuerySchema`
- **الوصف:** يرث من `PaginationQuerySchema` ويضيف معلمات للترتيب والتحكم في الحذف الناعم.
- **الحقول الإضافية:**
  - `sort_by` (String): للترتيب التصاعدي (`name`) أو التنازلي (`-created_at`).
  - `deleted_state` (String, default: 'active'): للتحكم في عرض السجلات المحذوفة (`active`, `all`, `deleted_only`).

### `BaseFilterQuerySchema`
- **الوصف:** يرث من `BaseListQuerySchema` ويضيف حقول فلترة شائعة تعتمد على التاريخ. هذا هو الـ `Schema` الأساسي الذي ترث منه جميع `QuerySchemas` التي يتم إنشاؤها بواسطة `create_crud_schemas`.
- **الحقول الإضافية:**
  - `created_after` (DateTime)
  - `created_before` (DateTime)

#### مثال: إنشاء `Query Schema` مخصص
يمكنك بسهولة إنشاء `Schema` استعلام مخصص لنقطة نهاية معينة عن طريق الوراثة من `BaseFilterQuerySchema`.

```python
from flask_devkit.helpers.schemas import BaseFilterQuerySchema
from apiflask.fields import String, Float

class ProductSearchSchema(BaseFilterQuerySchema):
    # يرث تلقائيًا: page, per_page, sort_by, deleted_state,
    # created_after, created_before.

    # أضف فلاتر مخصصة لنقطة نهاية البحث عن المنتجات
    name__ilike = String(
        required=False,
        metadata={"description": "Filter by product name (case-insensitive)."}
    )
    price__gte = Float(
        required=False,
        metadata={"description": "Filter for products with price greater than or equal to this value."}
    )
```

## 2. Schemas الاستجابة (Response Schemas)

### `MessageSchema`
- **الوصف:** `Schema` بسيط جدًا يُستخدم لإرجاع رسائل نصية عامة.
- **الحقول:**
  - `message` (String)
- **مثال على الاستجابة:**
  ```json
  {
    "message": "Operation completed successfully."
  }
  ```

## 3. Mixins

### `UpdateSchemaMixin`
- **الوصف:** هذا ليس `Schema` كاملاً، بل هو `Mixin` تتم إضافته إلى جميع `UpdateSchemas` التي يتم إنشاؤها بواسطة `create_crud_schemas`.
- **الغرض:** يضيف قاعدة تحقق من الصحة تمنع إرسال طلبات `PATCH` بجسم JSON فارغ `{}`, مما يضمن أن كل طلب تحديث يحتوي على حقل واحد على الأقل.
