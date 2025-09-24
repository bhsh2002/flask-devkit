# 32. الفلترة المتقدمة للاستعلامات

توفر `Flask-DevKit` آلية قوية ومرنة لفلترة نتائج واجهة برمجة التطبيقات (API) مباشرة من خلال معلمات الاستعلام في عنوان URL. يقوم `BaseRepository` بترجمة هذه المعلمات تلقائيًا إلى استعلامات `SQLAlchemy` معقدة.

## كيف تعمل؟

1.  عندما تقوم بإنشاء `Schemas` باستخدام `create_crud_schemas`، فإن `QuerySchema` الناتج يجمع أي معلمات استعلام غير معروفة (مثل `username__ilike`, `age__gt`) في قاموس `filters`.
2.  يتم تمرير هذا القاموس من المسار (Route) إلى الخدمة (Service)، ثم إلى تابع `paginate` أو `find_one_by` في المستودع (Repository).
3.  يقوم المستودع بتحليل هذا القاموس وبناء استعلام قاعدة البيانات ديناميكيًا.

## صيغة الفلترة (Filter Syntax)

تتبع الصيغة النمط `field__operator=value`. إذا لم يتم تحديد أي `operator`، فسيتم استخدام `eq` (يساوي) افتراضيًا.

| الصيغة في URL | العامل (Operator) | مثال |
| :--- | :--- | :--- |
| `field=value` | يساوي (Equals) | `?username=ahmed` |
| `field__ne=value` | لا يساوي (Not Equals) | `?status__ne=archived` |
| `field__gt=value` | أكبر من (Greater Than) | `?price__gt=100` |
| `field__gte=value` | أكبر من أو يساوي | `?age__gte=21` |
| `field__lt=value` | أصغر من (Less Than) | `?stock__lt=5` |
| `field__lte=value` | أصغر من أو يساوي | `?created_at__lte=2025-01-01` |
| `field__like=value` | يشبه (LIKE) - حساس لحالة الأحرف | `?name__like=Pro%` |
| `field__ilike=value` | يشبه (ILIKE) - غير حساس لحالة الأحرف | `?email__ilike=@example.com` |
| `field__in=v1\|v2` | ضمن قائمة (IN) | `?status__in=pending\|shipped` |

**ملاحظة:** في عامل `in`، يتم الفصل بين القيم المتعددة باستخدام `|`.

## دمج الشروط

### AND (للحقول المختلفة)
ببساطة، قم بإضافة معلمات استعلام متعددة. سيتم دمجها باستخدام `AND`.

**مثال:** جلب جميع المستخدمين النشطين الذين تزيد أعمارهم عن 30 عامًا.
```
GET /api/v1/users?is_active=true&age__gt=30
```
هذا يُترجم إلى: `is_active = true AND age > 30`.

### OR (لنفس الحقل)
يمكنك توفير قيم متعددة لنفس الحقل عن طريق فصلها بفاصلة `,`. سيتم دمجها باستخدام `OR`.

**مثال:** جلب جميع المنتجات التي حالتها "جديد" أو "مستعمل".
```
GET /api/v1/products?status=new,used
```
هذا يُترجم إلى: `status = 'new' OR status = 'used'`.

يمكنك أيضًا دمج هذا مع عوامل أخرى:
```
GET /api/v1/products?status__in=new|used
```
هذا يؤدي نفس الغرض.

## مثال معقد

لنفترض أنك تريد البحث عن جميع الطلبات (orders) التي:
- حالتها `shipped` أو `delivered`.
- و تم إنشاؤها بعد تاريخ 1 يونيو 2025.
- و اسم العميل يحتوي على "bahaa" (غير حساس لحالة الأحرف).

يمكنك تحقيق ذلك باستعلام واحد:
```
GET /api/v1/orders?status__in=shipped|delivered&created_at__gte=2025-06-01&customer_name__ilike=bahaa
```
