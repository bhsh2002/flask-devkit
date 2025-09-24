# 31. تسجيل الأحداث (Logging)

توفر `Flask-DevKit` إعدادًا أساسيًا ومناسبًا للبيئة الإنتاجية لتسجيل الأحداث (Logging) بشكل تلقائي، مما يساعدك على تتبع ما يحدث في تطبيقك عند تشغيله على الخادم.

## التهيئة التلقائية

يتم استدعاء دالة `logging.init_app(app)` تلقائيًا كجزء من `DevKit.init_app(app)`. هذا يعني أنك لا تحتاج إلى القيام بأي خطوات إضافية لتفعيل التسجيل.

## السلوك في البيئات المختلفة

يختلف سلوك التسجيل بناءً على قيمة `app.debug`:

### في وضع الإنتاج (`app.debug = False`)

- يتم إنشاء معالج `RotatingFileHandler`.
- يتم كتابة جميع سجلات الأحداث من مستوى `INFO` فما فوق إلى ملف `logs/server.log` في المجلد الجذر لمشروعك.
- "Rotating" يعني أن الملف لن ينمو إلى أجل غير مسمى؛ سيتم إنشاء ملفات جديدة بعد الوصول إلى حجم معين.
- يتم تنسيق كل رسالة سجل لتشمل الطابع الزمني، المستوى، الرسالة، واسم الملف ورقم السطر الذي صدر منه السجل، مما يسهل تصحيح الأخطاء.
  ```
  2025-09-24 14:10:25,123 - werkzeug - INFO - 127.0.0.1 - - [24/Sep/2025 14:10:25] "GET /api/v1/users HTTP/1.1" 200 -
  2025-09-24 14:10:30,456 - my_app.routes - ERROR - An error occurred while processing the request [in /home/user/my_app/routes.py:50]
  ```

### في وضع التطوير (`app.debug = True`)

- **لا** يتم إضافة معالج الملفات.
- تظل سجلات الأحداث تظهر في الطرفية (console) كما هو معتاد في `Flask`، وهو السلوك المرغوب فيه أثناء التطوير.

## كيفية استخدام المسجل (Logger)

يمكنك الوصول إلى المسجل الذي تم تكوينه من أي مكان في تطبيقك عبر `current_app` من `Flask`.

```python
from flask import current_app

@bp.route('/process-data')
def process_data():
    user_id = get_jwt_identity()
    current_app.logger.info(f"User {user_id} started data processing.")

    try:
        # ... قم بعمل معقد ...
        result = some_complex_operation()
        current_app.logger.info("Data processing finished successfully.")
        return {"status": "success", "result": result}
    except Exception as e:
        # تسجيل الخطأ مع معلومات تتبع المكدس (stack trace)
        current_app.logger.error(
            f"Data processing failed for user {user_id}.",
            exc_info=True
        )
        # إطلاق استثناء مخصص ليتم معالجته مركزيًا
        raise BusinessLogicError("Could not process data.")
```

في وضع الإنتاج، سيتم كتابة رسائل `INFO` و `ERROR` هذه إلى `logs/server.log`، مما يمنحك رؤية واضحة لما حدث.
