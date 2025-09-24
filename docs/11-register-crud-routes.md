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
    schemas: Dict[str, Type],
    entity_name: str,
    *,
    id_field: str = "uuid",
    routes_config: Dict[str, Dict[str, Any]] | None = None,
):
```

- **`bp`**: الـ `Blueprint` الذي سيتم تسجيل المسارات عليه.
- **`service`**: نسخة من الخدمة (`BaseService` أو فئة فرعية منها) التي تحتوي على منطق الأعمال.
- **`schemas`**: قاموس يحتوي على الـ Schemas التي تم إنشاؤها بواسطة `create_crud_schemas`.
- **`entity_name`**: اسم الكيان (e.g., `"product"`)، يُستخدم لإنشاء أسماء الصلاحيات الافتراضية (e.g., `"create:product"`).
- **`id_field`**: الحقل الذي سيتم استخدامه في عنوان URL للتعرف على السجلات (`"id"` أو `"uuid"`). الافتراضي هو `"uuid"`.
- **`routes_config`**: قاموس للتحكم الدقيق في كل مسار يتم إنشاؤه. هذا هو مفتاح التخصيص.

## تخصيص المسارات باستخدام `routes_config`

يتيح لك قاموس `routes_config` التحكم الكامل في كل نقطة نهاية. هيكل القاموس كالتالي:

```python
routes_config = {
    "route_name": {  # e.g., "list", "create", "delete"
        "enabled": bool,
        "auth_required": bool,
        "permission": str | None,
        "decorators": List[Callable] | None,
    }
}
```

- **`enabled`**: `True` لتفعيل المسار، `False` لتعطيله. (بشكل افتراضي، `restore` و `force_delete` معطلان).
- **`auth_required`**: `True` لتطبيق المُزين `@jwt_required()`. (الافتراضي `True`).
- **`permission`**: اسم الصلاحية المطلوبة للوصول إلى المسار. إذا كانت `None`، لا يتم التحقق من أي صلاحية.
- **`decorators`**: قائمة من المُزينات (decorators) الإضافية التي تريد تطبيقها على المسار.

### مثال عملي: واجهة برمجة تطبيقات للمنتجات

لنفترض أن لدينا `ProductService` و `product_schemas`. ونريد إنشاء واجهة برمجة تطبيقات (API) للمنتجات بالقواعد التالية:
1.  قائمة المنتجات (`GET /`) يجب أن تكون عامة (لا تتطلب مصادقة).
2.  إنشاء منتج جديد يتطلب صلاحية `create:product`.
3.  حذف منتج يتطلب صلاحية خاصة `manage:inventory`.
4.  يجب تعطيل الحذف النهائي (`force_delete`) تمامًا.
5.  نريد تسجيل نشاط إنشاء كل منتج باستخدام مُزين مخصص.

```python
# my_project/routes.py

from .services import product_service
from .schemas import product_schemas
from .decorators import log_product_creation # مُزين مخصص

# 1. تعريف إعدادات المسارات
product_routes_config = {
    "list": {
        "auth_required": False, # جعل قائمة المنتجات عامة
        "permission": None,
    },
    "create": {
        "permission": "create:product",
        "decorators": [log_product_creation], # إضافة مُزين مخصص
    },
    "delete": {
        "permission": "manage:inventory", # صلاحية مخصصة
    },
    "force_delete": {
        "enabled": False, # تعطيل الحذف النهائي
    },
}

# 2. إنشاء الـ Blueprint
products_bp = APIBlueprint("product", __name__, url_prefix="/products")

# 3. تسجيل مسارات CRUD
register_crud_routes(
    bp=products_bp,
    service=product_service,
    schemas=product_schemas,
    entity_name="product",
    id_field="uuid", # استخدام UUID في الـ URL
    routes_config=product_routes_config,
)
```

بهذه الطريقة، يمكنك توليد واجهات برمجة تطبيقات كاملة ومعقدة في بضعة أسطر فقط، مع الحفاظ على التحكم الكامل في الأمان والسلوك لكل نقطة نهاية.
