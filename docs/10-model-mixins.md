# 10. إعادة استخدام حقول النماذج: Model Mixins

عند بناء تطبيق، ستجد أن العديد من نماذج قاعدة البيانات (Models) تشترك في نفس الحقول، مثل `id`، `created_at`، و `updated_at`. بدلاً من تكرار تعريف هذه الحقول في كل نموذج، توفر `Flask-DevKit` مجموعة من "الـ Mixins" الجاهزة.

الـ Mixin هو فئة بسيطة تحتوي على مجموعة من الأعمدة والسلوكيات المعرفة مسبقًا والتي يمكنك "خلطها" مع نماذج `SQLAlchemy` الخاصة بك.

## الـ Mixins المتوفرة

توفر المكتبة أربعة `Mixins` أساسية في وحدة `flask_devkit.core.mixins`.

### 1. `IDMixin`

- **الغرض:** يضيف مفتاحًا أساسيًا (primary key) رقميًا قياسيًا.
- **العمود المضاف:**
  - `id`: `INTEGER`, `primary_key=True`, `autoincrement=True`

### 2. `UUIDMixin`

- **الغرض:** يضيف معرفًا فريدًا عالميًا (UUID) لكل سجل. هذا مفيد جدًا كمعرف عام وآمن لعرضه في عناوين URL بدلاً من كشف الـ `id` الرقمي المتزايد.
- **العمود المضاف:**
  - `uuid`: `CHAR(36)`, `unique=True`, `index=True`, `default=generate_uuid`

### 3. `TimestampMixin`

- **الغرض:** يضيف طوابع زمنية تلقائية لتتبع وقت إنشاء وتحديث السجلات.
- **الأعمدة المضافة:**
  - `created_at`: يتم تعيينه تلقائيًا عند إنشاء السجل.
  - `updated_at`: يتم تحديثه تلقائيًا في كل مرة يتم فيها تعديل السجل.

### 4. `SoftDeleteMixin`

- **الغرض:** يضيف الدعم لميزة "الحذف الناعم" (Soft Delete).
- **العمود المضاف:**
  - `deleted_at`: `TIMESTAMP`, `nullable=True`. عندما يكون هذا الحقل `NULL`، يعتبر السجل نشطًا. عندما يحتوي على تاريخ، يعتبر السجل محذوفًا (ولكنه لا يزال موجودًا في قاعدة البيانات). `BaseRepository` يتعامل مع هذا المنطق تلقائيًا.

## كيفية استخدامها

ببساطة، قم بالوراثة من الـ Mixins التي تحتاجها عند تعريف النموذج الخاص بك، بالإضافة إلى `db.Model`.

### مثال: نموذج `Article`

لنفترض أننا نريد إنشاء نموذج لمقالات المدونة. نريد أن يكون لكل مقال `id` و `uuid`، وأن يتم تتبع أوقات الإنشاء والتحديث، وأن يدعم الحذف الناعم.

```python
from sqlalchemy import Column, String, Text, ForeignKey
from flask_devkit.database import db
from flask_devkit.core.mixins import (
    IDMixin,
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
)

class Article(db.Model, IDMixin, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    نموذج يمثل مقال مدونة، مع جميع الميزات المدمجة.
    """
    __tablename__ = "articles"

    # الحقول الخاصة بالنموذج
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # علاقة اختيارية
    author = db.relationship("User")
```

**النتيجة:**
بمجرد تعريف هذا النموذج، فإنه يحتوي تلقائيًا على جميع الأعمدة التالية دون الحاجة إلى كتابتها يدويًا:
- `id`
- `uuid`
- `created_at`
- `updated_at`
- `deleted_at`
- `title`
- `content`
- `author_id`

بالإضافة إلى ذلك، سيعمل هذا النموذج بسلاسة مع جميع ميزات `BaseRepository` و `BaseService`، بما في ذلك التقسيم إلى صفحات، والفلترة، والحذف الناعم.
