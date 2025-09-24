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
- `input_schema` (اختياري): الـ `Schema` للتحقق من صحة جسم الطلب (request body).
- `output_schema` (اختياري): الـ `Schema` لتنسيق جسم الاستجابة (response body).
- `permission` (اختياري): الصلاحية المطلوبة للوصول إلى نقطة النهاية.
- `auth_required` (اختياري): `True` (افتراضي) لطلب المصادقة عبر JWT.
- `apply_unit_of_work` (اختياري): `True` لتغليف الدالة في معاملة قاعدة بيانات (transaction). (افتراضي `False`).
- `status_code` (اختياري): رمز حالة HTTP للنجاح (افتراضي `200`).
- `doc` (اختياري): قاموس لتمرير معلومات إضافية إلى وثائق OpenAPI (e.g., `{"summary": "..."}`).
- `decorators` (اختياري): قائمة بأي مُزينات مخصصة إضافية تريد تطبيقها.

## مثال عملي: الموافقة على مستند

لنفترض أن لدينا نموذج `Document` ونريد إنشاء نقطة نهاية `POST /documents/<int:doc_id>/approve` للموافقة عليه.

1.  **اكتب دالة العرض (View Function):**
    هذه هي دالة بايثون البسيطة التي تحتوي على منطق العمل الأساسي.

    ```python
    # services.py
    class DocumentService(BaseService[Document]):
        def approve(self, doc_id: int, approver: User, comments: str):
            doc = self.get_by_id(doc_id)
            if not doc:
                raise NotFoundError("Document", doc_id)
            if doc.status == "APPROVED":
                raise BusinessLogicError("Document is already approved.")

            doc.status = "APPROVED"
            doc.approved_by = approver
            doc.approval_comments = comments
            # ... المزيد من المنطق
            return doc
    ```

    ```python
    # routes.py

    # دالة العرض التي سيتم تسجيلها
    def approve_document_view(doc_id: int, json_data: dict):
        """
        تستدعي الخدمة للموافقة على المستند.
        """
        document_service = g.devkit.get_service("document")
        current_user = g.devkit.get_service("user").get_by_uuid(get_jwt_identity())
        comments = json_data.get("comments")

        return document_service.approve(doc_id, current_user, comments)
    ```

2.  **سجل المسار باستخدام `register_custom_route`:**
    الآن، بدلاً من تزيين `approve_document_view` يدويًا، نستخدم الدالة المساعدة.

    ```python
    # routes.py (تكملة)

    from flask_devkit.helpers.routing import register_custom_route
    from .schemas import ApprovalSchema, DocumentSchema # افترض وجود هذه الـ Schemas

    # ...
    register_custom_route(
        bp=documents_bp,
        rule="/<int:doc_id>/approve",
        view_func=approve_document_view,
        methods=["POST"],
        input_schema=ApprovalSchema,
        output_schema=DocumentSchema,
        auth_required=True,
        permission="approve:document",
        apply_unit_of_work=True, # مهم، لأننا نُجري تحديثًا
        status_code=200,
        doc={"summary": "Approve a document"}
    )
    ```

بهذه الطريقة، يمكنك بناء نقاط نهاية مخصصة ومعقدة بسرعة مع الحفاظ على نفس معايير الأمان والتحقق من الصحة المطبقة في جميع أنحاء المكتبة.
