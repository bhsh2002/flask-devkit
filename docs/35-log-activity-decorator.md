# 35. تتبع التنفيذ: المُزين `@log_activity`

`@log_activity` هو مُزين (decorator) بسيط ومفيد لأغراض تصحيح الأخطاء (debugging). عند تطبيقه على أي دالة، فإنه يقوم تلقائيًا بتسجيل معلومات حول استدعاء هذه الدالة، مما يساعدك على تتبع تدفق تنفيذ تطبيقك.

## ماذا يفعل؟

يقوم المُزين بتغليف الدالة وينفذ الإجراءات التالية:

1.  **قبل التنفيذ:** يسجل رسالة `INFO` تحتوي على اسم الدالة والوسائط (arguments) التي تم تمريرها إليها.
2.  **أثناء التنفيذ:** ينفذ الدالة الأصلية.
3.  **بعد النجاح:** إذا اكتملت الدالة بنجاح، يسجل رسالة `INFO` أخرى تفيد بأن الدالة قد انتهت.
4.  **في حالة الفشل:** إذا أطلقت الدالة أي استثناء (exception)، يقوم المُزين بتسجيل رسالة `ERROR` تحتوي على تفاصيل الخطأ (بما في ذلك تتبع المكدس - stack trace)، ثم يعيد إطلاق نفس الاستثناء ليتم التعامل معه كالمعتاد.

## ميزة الأمان: إخفاء البيانات الحساسة

الميزة الأكثر أهمية في هذا المُزين هي أنه يقوم تلقائيًا بإخفاء البيانات الحساسة. قبل تسجيل وسائط الدالة، يقوم بالبحث عن أسماء المفاتيح التي تحتوي على كلمات مثل `password`, `token`, `secret`, `key`, `authorization`. إذا وجد أيًا منها، فسيتم استبدال قيمتها بـ `***` في رسالة السجل.

هذا يمنع تسرب أي بيانات اعتماد أو مفاتيح سرية عن طريق الخطأ إلى ملفات السجل الخاصة بك.

## كيفية الاستخدام

يمكنك تطبيق هذا المُزين على أي دالة تريد مراقبتها، خاصة في طبقة الخدمة (Service Layer).

### مثال

لنفترض أن لديك دالة في خدمة تتصل بواجهة برمجة تطبيقات خارجية وتستخدم مفتاح API.

```python
from flask_devkit.helpers.decorators import log_activity
from flask import current_app

class ExternalApiService:
    @log_activity
    def get_user_data(self, user_id: int, api_key: str):
        """
        يجلب بيانات المستخدم من خدمة خارجية.
        """
        current_app.logger.info(f"Fetching data for user {user_id}...")
        # ... منطق الاتصال بالـ API
        if user_id == 0:
            raise ValueError("Invalid user ID")
        return {"external_data": "some data"}

# --- الاستدعاء ---
service = ExternalApiService()
# استدعاء ناجح
service.get_user_data(user_id=123, api_key="secret-api-key-12345")
# استدعاء فاشل
try:
    service.get_user_data(user_id=0, api_key="another-secret-key")
except ValueError:
    pass
```

### مخرجات السجل المتوقعة

```
# الاستدعاء الناجح
INFO:root:Activity: Calling function get_user_data with args: (<ExternalApiService object>,), kwargs: {'user_id': 123, 'api_key': '***'}
INFO:werkzeug:Fetching data for user 123...
INFO:root:Activity: Function get_user_data finished successfully.

# الاستدعاء الفاشل
INFO:root:Activity: Calling function get_user_data with args: (<ExternalApiService object>,), kwargs: {'user_id': 0, 'api_key': '***'}
INFO:werkzeug:Fetching data for user 0...
ERROR:root:Activity: Error in function get_user_data: Invalid user ID
Traceback (most recent call last):
  ...
  ValueError: Invalid user ID
```

لاحظ كيف تم إخفاء قيمة `api_key` تلقائيًا في كلا الاستدعاءين.
