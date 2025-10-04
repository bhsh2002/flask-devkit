# 11. التوليد التلقائي لواجهات API: `register_crud_routes`

تعتبر دالة `register_crud_routes` من أهم الأدوات التي توفرها `Flask-DevKit` لتسريع عملية التطوير. فبدلاً من كتابة الكود المكرر لكل عملية من عمليات CRUD (Create, Read, Update, Delete) يدويًا، تقوم هذه الدالة بتوليد مجموعة كاملة من نقاط النهاية (Endpoints) لـ REST API بشكل تلقائي لأي نموذج (Model) لديك.

## الفكرة الأساسية

تقوم الدالة بربط `Service` و `Schemas` مع `Blueprint` لإنشاء المسارات التالية:

- `GET /` (List)
- `POST /` (Create)
- `GET /<id>` (Get one)
- `PATCH /<id>` (Update)
- `DELETE /<id>` (Delete)
- `GET /deleted` (List soft-deleted)
- `POST /<id>/restore` (Restore)
- `DELETE /<id>/force` (Force delete)

## التوقيع (Signature)

```python
def register_crud_routes(
    bp: APIBlueprint,
    service: BaseService,
    schemas: Dict[str, Any],
    entity_name: str,
    *,
    id_field: str = "uuid",
    routes_config: Dict[str, Dict[str, Any]] | None = None,
):
```

- **`bp`**: الـ `Blueprint` الذي سيتم تسجيل المسارات عليه.
- **`service`**: نسخة من الخدمة (`BaseService` أو فئة فرعية منها) التي تحتوي على منطق الأعمال.
- **`schemas`**: قاموس يحتوي على تعريفات الـ Schemas الافتراضية.
- **`entity_name`**: اسم الكيان (e.g., `"product"`)، يُستخدم لإنشاء أسماء الصلاحيات الافتراضية.
- **`id_field`**: الحقل الذي سيتم استخدامه في عنوان URL للتعرف على السجلات (`"id"` أو `"uuid"`).
- **`routes_config`**: قاموس للتحكم الدقيق في كل مسار يتم إنشاؤه.

## تخصيص المسارات باستخدام `routes_config`

يتيح لك قاموس `routes_config` التحكم الكامل في كل نقطة نهاية. هيكل القاموس كالتالي:

```python
routes_config = {
    "route_name": {  # e.g., "list", "create", "delete"
        "enabled": bool,
        "auth_required": bool,
        "permission": str | None,
        "decorators": List[Callable] | None,
        "input_schema": Dict[str, Any] | List[Dict[str, Any]] | None,
        "output_schema": Dict[str, Any] | None,
    }
}
```

- **`enabled`**: `True` لتفعيل المسار، `False` لتعطيله.
- **`auth_required`**: `True` لتطبيق المُزين `@jwt_required()`.
- **`permission`**: اسم الصلاحية المطلوبة للوصول إلى المسار.
- **`input_schema`**: هذه هي الميزة الأقوى. يمكنك تحديد مخطط إدخال واحد أو **قائمة من مخططات الإدخال** لتجاوز السلوك الافتراضي. كل تعريف للمخطط هو قاموس يحدد `schema`, `location`, و `arg_name` (اختياري).
- **`output_schema`**: تعريف مخطط مخصص لتجاوز مخطط الإخراج الافتراضي.

### مثال 1: تخصيص بسيط

لنفترض أننا نريد جعل قائمة المنتجات عامة (لا تتطلب مصادقة).

```python
product_routes_config = {
    "list": {
        "auth_required": False,
        "permission": None,
    }
}
```

### مثال 2: تخصيص متقدم (مدخلات متعددة)

لنفترض أننا نريد لنقطة نهاية إنشاء المنتج (`create`) أن تقبل اسم المنتج من جسم الطلب (`json`) وفئة المنتج من معلمات الاستعلام (`query string`) في نفس الوقت.

```python
# schemas.py
class CategorySchema(Schema):
    category = StringField(required=True)

# routes.py
product_routes_config = {
    "create": {
        "permission": "create:product",
        # --- استخدام قائمة من المخططات ---
        "input_schema": [
            # المخطط الافتراضي من جسم الطلب
            {"schema": product_schemas["input"], "location": "json"},
            # مخطط إضافي من معلمات الاستعلام
            {"schema": CategorySchema, "location": "query"}
        ]
    }
}
```
عند استدعاء `POST /products?category=Electronics` مع جسم `{"name": "Laptop"}`، ستقوم الدالة تلقائيًا بدمج البيانات من كلا المصدرين في قاموس واحد `{"name": "Laptop", "category": "Electronics"}` قبل تمريره إلى `service.create()`.

### مثال 3: إضافة جسم طلب إلى مسار الحذف

بشكل افتراضي، لا يقبل مسار `DELETE` أي جسم طلب. لكن يمكنك الآن تفعيل هذه الميزة لطلب سبب عند الحذف.

```python
# schemas.py
class DeletionReasonSchema(Schema):
    reason = StringField(required=True, validate=Length(min=10))

# routes.py
product_routes_config = {
    "delete": {
        "permission": "delete:product",
        "input_schema": {
            "schema": DeletionReasonSchema,
            "location": "json"
        }
    }
}
```
الآن، عند استدعاء `DELETE /products/<uuid>`، يجب على العميل توفير جسم طلب يحتوي على حقل `reason`. ستكون هذه البيانات متاحة لك داخل `pre_delete_hook` في الخدمة الخاصة بك لمعالجتها (مثل تسجيلها في سجل التدقيق).
