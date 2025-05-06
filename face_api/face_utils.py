"""
توابع کمکی برای تشخیص چهره
"""
import numpy as np
import base64
import io
from PIL import Image
from django.conf import settings
from .face_recognition_wrapper import face_recognition_lib


def get_face_recognition_settings():
    """دریافت تنظیمات تشخیص چهره از فایل settings.py"""
    config = settings.FACE_RECOGNITION_SETTINGS
    return {
        'tolerance': config.get('TOLERANCE', 0.6),
        'model': config.get('MODEL', 'hog'),
        'num_jitters': config.get('NUMBER_OF_TIMES_TO_UPSAMPLE', 1)
    }


def base64_to_image(base64_string):
    """تبدیل رشته base64 به تصویر PIL"""
    # حذف پیشوند base64 (مثلاً data:image/jpeg;base64,) اگر وجود داشته باشد
    if ',' in base64_string:
        base64_string = base64_string.split(',', 1)[1]

    # تبدیل رشته base64 به بایت
    image_bytes = base64.b64decode(base64_string)

    # تبدیل بایت به تصویر PIL
    image = Image.open(io.BytesIO(image_bytes))

    return image


def extract_face_encoding(image):
    """استخراج embedding چهره از تصویر

    Args:
        image: تصویر PIL یا آرایه numpy

    Returns:
        encoding: آرایه numpy حاوی embedding چهره یا None اگر چهره‌ای یافت نشد
    """
    # تبدیل تصویر PIL به آرایه numpy اگر هنوز نیست
    if isinstance(image, Image.Image):
        image = np.array(image)

    config = get_face_recognition_settings()

    # یافتن مکان چهره(ها) در تصویر
    face_locations = face_recognition_lib.face_locations(
        image,
        model=config['model'],
        number_of_times_to_upsample=config['num_jitters']
    )

    # اگر چهره‌ای یافت نشد، None برگردان
    if not face_locations:
        return None

    # اگر چندین چهره یافت شد، فقط اولین چهره را استفاده کن
    # می‌توان منطق پیچیده‌تری برای انتخاب چهره مناسب پیاده‌سازی کرد
    face_location = face_locations[0]

    # استخراج embedding چهره
    face_encoding = face_recognition_lib.face_encodings(
        image,
        [face_location],
        num_jitters=config['num_jitters']
    )[0]

    return face_encoding


def find_matching_person(face_encoding, known_encodings):
    """یافتن تطابق بین embedding چهره و encoding های موجود

    Args:
        face_encoding: embedding چهره جدید
        known_encodings: لیستی از embedding های موجود در دیتابیس

    Returns:
        index: شاخص encoding مطابق یا None اگر هیچ تطابقی یافت نشد
    """
    if not known_encodings:
        return None

    config = get_face_recognition_settings()

    # محاسبه تطابق‌ها
    matches = face_recognition_lib.compare_faces(
        known_encodings,
        face_encoding,
        tolerance=config['tolerance']
    )

    # اگر هیچ تطابقی یافت نشد
    if not any(matches):
        return None

    # محاسبه فاصله چهره‌ها (مقدار کمتر = تطابق بیشتر)
    face_distances = face_recognition_lib.face_distance(known_encodings, face_encoding)

    # یافتن بهترین تطابق (کمترین فاصله)
    best_match_index = np.argmin(face_distances)

    # اگر بهترین تطابق واقعاً یک تطابق است
    if matches[best_match_index]:
        return best_match_index

    return None