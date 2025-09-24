# 38. كائن قاعدة البيانات: `db`

الكائن `db` الموجود في `flask_devkit.database` هو النسخة المركزية من امتداد `Flask-SQLAlchemy`. إنه نقطة الدخول الأساسية لجميع تفاعلات قاعدة البيانات في تطبيقك، سواء كنت تستخدم نماذج `DevKit` المدمجة أو تقوم ببناء نماذجك الخاصة.

## طرق الاستخدام الرئيسية

ستتفاعل مع كائن `db` بشكل أساسي بالطرق التالية:

### 1. `db.Model` (النموذج الأساسي)
هذه هي الفئة الأساسية التي يجب أن ترث منها جميع نماذج `SQLAlchemy` الخاصة بك. الوراثة من `db.Model` تضمن أن `SQLAlchemy` تتعرف على نماذجك وتعرف كيفية ربطها بجداول قاعدة البيانات.

### 2. `db.Column`, `db.String`, `db.Integer`, etc.
تُستخدم هذه الكائنات لتعريف الأعمدة (الحقول) داخل نماذجك وأنواع البيانات الخاصة بها.

### 3. `db.ForeignKey` (المفتاح الخارجي)
تُستخدم لإنشاء علاقة على مستوى قاعدة البيانات بين جدولين.

### 4. `db.relationship` (العلاقة)
تُستخدم لإنشاء علاقة على مستوى كائن بايثون، مما يتيح لك التنقل بسهولة بين الكائنات المرتبطة (e.g., `user.posts`).

### 5. `db.session` (الجلسة)
هذه هي جلسة `SQLAlchemy` التي تدير جميع المعاملات مع قاعدة البيانات. بينما تقوم طبقة المستودع (Repository) بمعظم إدارة الجلسات تلقائيًا (خاصة مع `@unit_of_work`)، قد تحتاج إلى استخدام `db.session` مباشرة في بعض الحالات المتقدمة، مثل كتابة استعلامات معقدة جدًا أو في نصوص برمجية (scripts) مستقلة.

## مثال شامل لتعريف نموذج

يوضح هذا المثال كيفية استخدام مكونات `db` المختلفة معًا لتعريف نموذج `Post` مخصص.

```python
from flask_devkit.database import db

# 1. يجب أن يرث النموذج من db.Model
class Post(db.Model):
    __tablename__ = 'posts'

    # 2. استخدم db.Column لتعريف الحقول
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    body = db.Column(db.Text, nullable=False)

    # 3. استخدم db.ForeignKey لربط الجداول
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 4. استخدم db.relationship لإنشاء علاقة الكائن
    #    هذا يسمح لك بالوصول إلى كائن User من Post عبر post.author
    author = db.relationship('User', backref=db.backref('posts', lazy=True))

# 5. مثال على استخدام db.session مباشرة (أقل شيوعًا في التطبيق الرئيسي)
def get_all_post_titles():
    """
    دالة مساعدة قد تكون في نص برمجي لجلب جميع عناوين المشاركات.
    """
    return db.session.query(Post.title).all()
```

من خلال توفير هذا الكائن `db` المركزي، تضمن `Flask-DevKit` أن جميع أجزاء التطبيق (بما في ذلك المكتبة نفسها ونماذجك المخصصة) تشترك في نفس اتصال وجلسة قاعدة البيانات.
