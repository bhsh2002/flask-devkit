# 2. الفئة الرئيسية: `DevKit`

تعتبر فئة `DevKit` هي المحور المركزي للمكتبة. هي مسؤولة عن تنسيق جميع المكونات، بما في ذلك الخدمات (Services)، والمستودعات (Repositories)، وتسجيل المسارات (Routes)، وأوامر CLI.

## نظرة عامة

يتم إنشاء كائن واحد من هذه الفئة في تطبيقك، والذي يعمل كواجهة لإعداد وتخصيص سلوك المكتبة.

```python
from flask_devkit import DevKit

# إنشاء نسخة من الفئة
devkit = DevKit()
```

## معلمات الإنشاء (Constructor Parameters)

تقبل فئة `DevKit` معلمتين اختياريتين عند إنشائها:

```python
class DevKit:
    def __init__(
        self,
        app: Optional[APIFlask] = None,
        additional_claims_loader: Optional[Callable] = None,
    ):
        # ...
```

- **`app` (اختياري):** يمكنك تمرير كائن `APIFlask` مباشرة إلى المُنشئ. إذا قمت بذلك، فسيتم استدعاء `devkit.init_app(app)` تلقائيًا. هذا اختصار مفيد للتطبيقات البسيطة.

- **`additional_claims_loader` (اختياري):** هذه معلمة قوية جدًا. يمكنك تمرير دالة (callable) ستقوم المكتبة باستدعائها عند إنشاء أي `access_token`. تتيح لك هذه الدالة إضافة أي بيانات مخصصة إلى حمولة JWT (JWT payload).

### مثال على `additional_claims_loader`

لنفترض أنك تريد إضافة اسم العرض (display name) الخاص بالمستخدم إلى كل توكن JWT.

```python
from apiflask import APIFlask
from flask_devkit import DevKit
from flask_devkit.users.models import User

# 1. قم بتعريف دالة تحميل المطالبات المخصصة
#    يجب أن تقبل كائن المستخدم كمعلمة
def add_custom_claims(user: User) -> dict:
    """
    تُرجع هذه الدالة قاموسًا (dictionary) سيتم دمجه
    في حمولة JWT.
    """
    return {
        "display_name": f"User_{user.id}",
        "tenant_id": "some_tenant_id" # مثال آخر
    }

app = APIFlask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SECRET_KEY"] = "a-secure-secret-key"

# 2. قم بتمرير الدالة إلى مُنشئ DevKit
devkit = DevKit(additional_claims_loader=add_custom_claims)
devkit.init_app(app)

# الآن، أي JWT يتم إنشاؤه عبر /login سيحتوي على الحقول المخصصة
```

عند تسجيل الدخول، سيبدو جزء من حمولة JWT هكذا:

```json
{
  "sub": "user-uuid-goes-here",
  "user_id": 1,
  "roles": ["admin"],
  "permissions": ["create:user", "read:user", ...],
  "display_name": "User_1",
  "tenant_id": "some_tenant_id",
  "iat": 1678886400,
  "exp": 1678972800
}
```

هذه الميزة ضرورية لتمرير معلومات إضافية تحتاجها الواجهة الأمامية (Frontend) أو الخدمات الأخرى دون الحاجة إلى استعلامات إضافية لقاعدة البيانات.
