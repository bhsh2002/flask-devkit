# 7. طبقة الوصول للبيانات: `BaseRepository`

تعتبر `BaseRepository` فئة عامة (Generic) توفر تجريدًا لعمليات قاعدة البيانات الشائعة (CRUD). الهدف منها هو تقليل الكود المكرر وتوفير واجهة متسقة للتفاعل مع أي نموذج (Model) من نماذج `SQLAlchemy`.

يتم استخدام هذه الفئة عادةً داخل طبقة الخدمة (Service Layer) ولا يتم استدعاؤها مباشرة من المسارات (Routes).

## الإنشاء (Initialization)

عندما تقوم خدمة بإنشاء نسخة من مستودع، فإنها تمرر له شيئين:

1.  **`model`**: فئة النموذج (e.g., `User`) التي سيعمل عليها المستودع.
2.  **`db_session`**: جلسة `SQLAlchemy` الحالية لإجراء عمليات قاعدة البيانات.

```python
# داخل BaseService
repo_cls = repository_class or BaseRepository
self.repo = repo_cls(model=self.model, db_session=self._db_session)
```

## التوابع الرئيسية (Core Methods)

توفر `BaseRepository` مجموعة من التوابع الجاهزة للاستخدام:

### عمليات الكتابة (Write Operations)

- **`create(data: Dict[str, Any]) -> T`**
  - **الوصف:** تنشئ سجلاً جديدًا في قاعدة البيانات من قاموس (dictionary) بيانات.
  - **مثال:** `user_repo.create({"username": "test", "password_hash": "..."})`

- **`delete(entity: T, soft: bool = True)`**
  - **الوصف:** تحذف سجلاً. إذا كان النموذج يستخدم `SoftDeleteMixin` وكانت `soft=True` (الافتراضي)، فسيتم إجراء حذف ناعم (soft delete) عن طريق تعيين `deleted_at`. وإلا، فسيتم حذفه نهائيًا.

- **`force_delete(entity: T)`**
  - **الوصف:** تقوم بحذف السجل نهائيًا من جدوله الأصلي وأرشفة نسخة منه في جدول `archived_records`.

- **`restore(entity: T)`**
  - **الوصف:** تسترجع سجلاً تم حذفه حذفًا ناعمًا عن طريق تعيين `deleted_at` إلى `NULL`.

### عمليات القراءة (Read Operations)

- **`get_by_id(id_: Any, deleted_state: str = "active") -> Optional[T]`**
  - **الوصف:** تجلب سجلاً واحدًا بواسطة مفتاحه الأساسي (`id`).

- **`get_by_uuid(uuid: str, deleted_state: str = "active") -> Optional[T]`**
  - **الوصف:** تجلب سجلاً واحدًا بواسطة `uuid`.

- **`find_one_by(filters: Dict[str, Any], deleted_state: str = "active") -> Optional[T]`**
  - **الوصف:** تبحث عن سجل واحد يطابق شروط الفلترة.

- **`paginate(...) -> PaginationResult[T]`**
  - **الوصف:** هذا هو أقوى تابع للاستعلام. يقوم بإجراء استعلام مع تقسيم النتائج إلى صفحات (pagination)، وفلترة، وترتيب.
  - **المعلمات:**
    - `page`: رقم الصفحة (افتراضي: 1).
    - `per_page`: عدد العناصر في كل صفحة (افتراضي: 20).
    - `filters`: قاموس يحتوي على الفلاتر (انظر قسم الفلترة أدناه).
    - `order_by`: قائمة بأسماء الحقول للترتيب (e.g., `['-created_at', 'name']`).
    - `deleted_state`: للتحكم في كيفية التعامل مع السجلات المحذوفة (`active`, `all`, `deleted_only`).
  - **القيمة المعادة:** كائن `PaginationResult` يحتوي على `items` والبيانات الوصفية للصفحات.

## الفلترة والترتيب المتقدم

تدعم `BaseRepository` بناء استعلامات ديناميكية قوية من خلال قاموس `filters` الذي يتم تمريره إلى `paginate` أو `find_one_by`.

**الصيغة:** `{"field_name": "operator__value"}`

- **`eq` (يساوي - الافتراضي):** `{"username": "john"}`
- **`ne` (لا يساوي):** `{"status": "ne__archived"}`
- **`gt` (أكبر من):** `{"age": "gt__18"}`
- **`gte` (أكبر من أو يساوي):** `{"age": "gte__18"}`
- **`lt` (أصغر من):** `{"created_at": "lt__2023-01-01"}`
- **`lte` (أصغر من أو يساوي):** `{"created_at": "lte__2023-01-01"}`
- **`like` (يشبه - حساس لحالة الأحرف):** `{"name": "like__John%"}`
- **`ilike` (يشبه - غير حساس لحالة الأحرف):** `{"name": "ilike__john%"}`
- **`in` (ضمن قائمة):** `{"status": "in__active|pending"}` (يتم الفصل بين القيم بـ `|`)

يمكنك أيضًا دمج شروط متعددة لنفس الحقل باستخدام فاصلة `,`:
`{"age": "gte__18,lte__65"}` (العمر بين 18 و 65).

## معالجة الأخطاء

جميع التوابع في `BaseRepository` مزينة بـ `@handle_db_errors`، الذي يقوم تلقائيًا بالتقاط استثناءات `SQLAlchemy` وتحويلها إلى استثناءات مخصصة وواضحة من `Flask-DevKit`، مثل `DuplicateEntryError` و `DatabaseError`. هذا يضمن أن طبقة الخدمة لا تحتاج إلى التعامل مع تفاصيل أخطاء قاعدة البيانات.
