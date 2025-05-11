"""
توابع کمکی برای تشخیص چهره با استفاده از DeepFace
"""
import numpy as np
import base64
import io
import json
from PIL import Image
from django.conf import settings
from .deepface_wrapper import deepface_lib


def get_face_recognition_settings():
    """دریافت تنظیمات تشخیص چهره از فایل settings.py"""
    config = settings.FACE_RECOGNITION_SETTINGS
    return {
        'model': config.get('MODEL', 'VGG-Face'),
        'detector': config.get('DETECTOR', 'retinaface'),
        'distance_metric': config.get('DISTANCE_METRIC', 'cosine'),
        'enforce_detection': config.get('ENFORCE_DETECTION', True)
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
    """استخراج embedding چهره از تصویر با استفاده از DeepFace

    Args:
        image: تصویر PIL یا آرایه numpy

    Returns:
        encoding: آرایه numpy حاوی embedding چهره یا None اگر چهره‌ای یافت نشد
    """
    # تبدیل تصویر PIL به آرایه numpy اگر هنوز نیست
    if isinstance(image, Image.Image):
        image = np.array(image)

    config = get_face_recognition_settings()

    # استفاده از DeepFace برای استخراج embedding چهره
    try:
        embedding_results = deepface_lib.represent(
            image=image,
            enforce_detection=config['enforce_detection']
        )

        # اگر هیچ embedding ای یافت نشد، None برگردان
        if not embedding_results or len(embedding_results) == 0:
            return None

        # اولین embedding را استفاده می‌کنیم
        first_result = embedding_results[0]
        embedding = first_result.get('embedding', None)

        if embedding is None:
            return None

        return np.array(embedding)
    except Exception as e:
        print(f"Error in extracting face encoding: {str(e)}")
        return None


def find_matching_person(face_encoding, known_encodings):
    """یافتن تطابق بین embedding چهره و encoding های موجود"""

    if face_encoding is None or len(known_encodings) == 0:
        return None

    # تبدیل به numpy array برای بررسی صحیح مقایسه‌ها
    face_encoding = np.array(face_encoding)
    known_encodings = np.array(known_encodings)

    config = get_face_recognition_settings()

    distances = []
    for known_encoding in known_encodings:
        distance = deepface_lib.compare_embeddings(face_encoding, known_encoding)
        distances.append(distance)

    distances = np.array(distances)

    min_index = np.argmin(distances)
    min_distance = distances[min_index]

    if deepface_lib.is_match(min_distance):
        return min_index

    return None



def analyze_face(image):
    """آنالیز چهره برای تشخیص سن، جنسیت، احساسات و نژاد

    Args:
        image: تصویر PIL یا آرایه numpy

    Returns:
        dict: اطلاعات آنالیز چهره یا None اگر چهره‌ای یافت نشد
    """
    # تبدیل تصویر PIL به آرایه numpy اگر هنوز نیست
    if isinstance(image, Image.Image):
        image = np.array(image)

    config = get_face_recognition_settings()

    # استفاده از DeepFace برای آنالیز چهره
    try:
        analysis = deepface_lib.analyze(
            image=image,
            enforce_detection=config['enforce_detection']
        )
        return analysis
    except Exception as e:
        print(f"Error in analyzing face: {str(e)}")
        return None


def detect_faces(image):
    """تشخیص چهره‌ها در تصویر

    Args:
        image: تصویر PIL یا آرایه numpy

    Returns:
        list: لیستی از dict های حاوی اطلاعات چهره‌های تشخیص داده شده
    """
    # تبدیل تصویر PIL به آرایه numpy اگر هنوز نیست
    if isinstance(image, Image.Image):
        image = np.array(image)

    config = get_face_recognition_settings()

    # استفاده از DeepFace برای تشخیص چهره‌ها
    try:
        faces = deepface_lib.extract_faces(
            image=image,
            enforce_detection=config['enforce_detection']
        )
        return faces
    except Exception as e:
        print(f"Error in detecting faces: {str(e)}")
        return []