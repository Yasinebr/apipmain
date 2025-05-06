from rest_framework import serializers
from .models import Person, FaceEncoding, RecognitionLog, ExternalCamera


class PersonSerializer(serializers.ModelSerializer):
    """سریالایزر برای مدل Person"""

    class Meta:
        model = Person
        fields = ['id', 'first_name', 'last_name', 'national_id', 'registered_at']
        read_only_fields = ['id', 'registered_at']


class RegisterFaceSerializer(serializers.Serializer):
    """سریالایزر برای ثبت چهره جدید"""
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    national_id = serializers.CharField(max_length=10)
    image = serializers.CharField()  # تصویر به صورت base64

    def validate_national_id(self, value):
        """اعتبارسنجی کد ملی"""
        # بررسی طول کد ملی
        if len(value) != 10:
            raise serializers.ValidationError("کد ملی باید ۱۰ رقم باشد.")

        # بررسی عددی بودن کد ملی
        if not value.isdigit():
            raise serializers.ValidationError("کد ملی باید فقط شامل اعداد باشد.")

        # می‌توان بررسی‌های بیشتری مانند الگوریتم اعتبارسنجی کد ملی اضافه کرد

        return value

    def validate_image(self, value):
        """اعتبارسنجی تصویر base64"""
        if not value:
            raise serializers.ValidationError("تصویر الزامی است.")

        # بررسی اینکه آیا رشته حاوی داده‌های base64 معتبر است
        try:
            # حذف پیشوند base64 اگر وجود داشته باشد
            if ',' in value:
                value = value.split(',', 1)[1]

            # تلاش برای رمزگشایی base64
            import base64
            base64.b64decode(value)
        except Exception as e:
            raise serializers.ValidationError(f"فرمت تصویر base64 نامعتبر است: {str(e)}")

        return value


class RecognizeFaceSerializer(serializers.Serializer):
    """سریالایزر برای تشخیص چهره"""
    image = serializers.CharField()  # تصویر به صورت base64


class UpdatePersonSerializer(serializers.ModelSerializer):
    """سریالایزر برای به‌روزرسانی اطلاعات شخصی"""

    class Meta:
        model = Person
        fields = ['first_name', 'last_name', 'national_id']


class UpdateFaceSerializer(serializers.Serializer):
    """سریالایزر برای به‌روزرسانی تصویر چهره"""
    image = serializers.CharField()  # تصویر جدید به صورت base64


class RecognitionLogSerializer(serializers.ModelSerializer):
    """سریالایزر برای لاگ‌های تشخیص"""
    person_name = serializers.SerializerMethodField()

    class Meta:
        model = RecognitionLog
        fields = ['id', 'person', 'person_name', 'timestamp', 'location', 'ip_address']
        read_only_fields = ['id', 'person', 'timestamp', 'ip_address']

    def get_person_name(self, obj):
        """دریافت نام کامل شخص"""
        return f"{obj.person.first_name} {obj.person.last_name}"


# به فایل face_api/serializers.py اضافه شود
class ExternalCameraSerializer(serializers.ModelSerializer):
    """سریالایزر برای مدل دوربین خارجی"""

    url_with_auth = serializers.SerializerMethodField()

    class Meta:
        model = ExternalCamera
        fields = ['id', 'name', 'protocol', 'url', 'username', 'password',
                  'location', 'is_active', 'url_with_auth']
        read_only_fields = ['id', 'url_with_auth']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def get_url_with_auth(self, obj):
        # فقط برای MJPEG و HTTP که مستقیماً در مرورگر قابل استفاده هستند
        if obj.protocol in ['mjpeg', 'http']:
            return obj.get_url_with_auth()
        return None