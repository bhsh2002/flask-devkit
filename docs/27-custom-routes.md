# 27. بناء نقاط نهاية مخصصة: `register_custom_route`

بينما تقوم `register_crud_routes` بعمل رائع في أتمتة واجهات برمجة التطبيقات القياسية، ستحتاج حتمًا إلى إنشاء نقاط نهاية مخصصة لإجراءات فريدة في تطبيقك، مثل "الموافقة على مستند"، أو "إعادة حساب فاتورة"، أو "نشر مقال".

الدالة المساعدة `register_custom_route` تجعل هذه العملية سهلة ومتسقة مع بقية المكتبة.

## الغرض

الغرض من هذه الدالة هو تجنب كتابة مكدس طويل من المُزينات (decorators) لكل نقطة نهاية مخصصة. هي تقوم بتغليف النمط الشائع لتطبيق `@bp.input`, `@bp.output`, `@jwt_required`, `@permission_required`, و `@unit_of_work` في دالة واحدة سهلة الاستخدام.

## المعلمات (Parameters)

تقبل الدالة مجموعة شاملة من المعلمات لتغطية معظم حالات الاستخدام:

- `bp`: الـ `Blueprint` لتسجيل المسار عليه.
- `rule`: مسار الـ URL (e.g., `"/documents/<int:doc_id>/approve"`).
- `view_func`: دالة بايثون الفعلية التي تحتوي على منطق المسار.
- `methods`: قائمة بأساليب HTTP المدعومة (e.g., `["POST"]`).
- `input_schemas` (اختياري): **قائمة** من القواميس للتحقق من صحة المدخلات. كل قاموس يجب أن يحتوي على:
    - `schema`: فئة الـ `Schema`.
    - `location`: موقع البيانات (e.g., `'json'`, `'query'`, `'form'`).
    - `arg_name` (اختياري): اسم المتغير الذي سيتم تمريره إلى دالة العرض.
- `output_schema` (اختياري): الـ `Schema` لتنسيق جسم الاستجابة (response body).
- `permission` (اختياري): الصلاحية المطلوبة للوصول إلى نقطة النهاية.
- `auth_required` (اختياري): `True` (افتراضي) لطلب المصادقة عبر JWT.
- `apply_unit_of_work` (اختياري): `True` لتغليف الدالة في معاملة قاعدة بيانات (transaction). (افتراضي `False`).
- `status_code` (اختياري): رمز حالة HTTP للنجاح (افتراضي `200`).
- `doc` (اختياري): قاموس لتمرير معلومات إضافية إلى وثائق OpenAPI (e.g., `{"summary": "..."}`).
- `decorators` (اختياري): قائمة بأي مُزينات مخصصة إضافية تريد تطبيقها.

## مثال 1: إجراء بسيط (الموافقة على مستند)

لنفترض أن لدينا نقطة نهاية `POST /documents/<int:doc_id>/approve`.

1.  **اكتب دالة العرض (View Function):**

    ```python
    # routes.py
    def approve_document_view(doc_id: int, json_data: dict):
        # ... منطق العمل هنا ...
        comments = json_data.get("comments")
        # ...
        return document_service.approve(doc_id, current_user, comments)
    ```

2.  **سجل المسار:**

    ```python
    # routes.py (تكملة)
    register_custom_route(
        bp=documents_bp,
        rule="/<int:doc_id>/approve",
        view_func=approve_document_view,
        methods=["POST"],
        input_schemas=[{"schema": ApprovalSchema, "location": "json"}], # لاحظ أنها قائمة
        output_schema=DocumentSchema,
        auth_required=True,
        permission="approve:document",
        apply_unit_of_work=True,
        status_code=200,
        doc={"summary": "Approve a document"}
    )
    ```

## مثال 2: مدخلات من مصادر متعددة

لنفترض أنك تريد إنشاء نقطة نهاية تقبل معلمات تصفية من الـ `query string` وبيانات للتحديث من الـ `request body`.

1.  **اكتب دالة العرض:**
    يجب أن تقبل الدالة وسيطتين، واحدة لكل `input_schema`.

    ```python
    # routes.py
    def bulk_update_view(query_params: dict, body_data: dict):
        """
        تحديث السجلات بناءً على معايير التصفية.
        """
        category = query_params.get("category")
        new_status = body_data.get("status")
        
        # ... منطق العمل لتحديث السجلات في هذه الفئة ...
        
        return {"message": f"Records in category {category} updated to {new_status}."}
    ```

2.  **عرف الـ Schemas:**

    ```python
    # schemas.py
    class FilterSchema(Schema):
        category = String(required=True)

    class UpdateStatusSchema(Schema):
        status = String(required=True)
    ```

3.  **سجل المسار:**
    مرر قائمة من القواميس إلى `input_schemas`، مع تحديد `arg_name` لكل واحدة.

    ```python
    # routes.py (تكملة)
    register_custom_route(
        bp=my_bp,
        rule="/bulk-update",
        view_func=bulk_update_view,
        methods=["PATCH"],
        input_schemas=[
            {"schema": FilterSchema, "location": "query", "arg_name": "query_params"},
            {"schema": UpdateStatusSchema, "location": "json", "arg_name": "body_data"},
        ],
        output_schema=MessageSchema,
        auth_required=True,
        permission="bulk:update",
        apply_unit_of_work=True,
        doc={"summary": "Bulk update records based on a filter"}
    )
    ```

بهذه الطريقة، يمكنك بناء نقاط نهاية مخصصة ومعقدة بسرعة مع الحفاظ على نفس معايير الأمان والتحقق من الصحة المطبقة في جميع أنحاء المكتبة.
