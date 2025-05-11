"""
این ماژول یک wrapper برای کتابخانه deepface است.
از این طریق می‌توانیم بین نسخه اصلی و mock سوئیچ کنیم.
"""
import os
import numpy as np
import base64
import io
from PIL import Image
import cv2
import json
import tempfile

USE_MOCK = os.environ.get('USE_MOCK_FACE', '').lower() in ('true', '1', 't')


# کلاس حاوی توابع مورد نیاز برای تشخیص چهره با استفاده از DeepFace
class DeepFaceWrapper:
    def __init__(self):
        self._deepface = None
        self._detector_backend = 'retinaface'  # گزینه‌های دیگر: opencv, mtcnn, ssd, dlib
        self._model_name = 'VGG-Face'  # گزینه‌های دیگر: Facenet, Facenet512, OpenFace, DeepFace, DeepID, ArcFace, Dlib, SFace
        self._distance_metric = 'cosine'  # گزینه‌های دیگر: euclidean, euclidean_l2
        self._temp_db_path = tempfile.mkdtemp()

    def _get_library(self):
        """دریافت کتابخانه با lazy loading"""
        if self._deepface is None:
            if USE_MOCK:
                # استفاده از نسخه mock
                self._deepface = self._get_mock()
                print("WARNING: Using mock DeepFace library. This is NOT suitable for production!")
            else:
                # استفاده از نسخه اصلی
                try:
                    from deepface import DeepFace
                    self._deepface = DeepFace
                except ImportError:
                    # اگر نصب نشده باشد، از نسخه mock استفاده می‌کنیم
                    self._deepface = self._get_mock()
                    print(
                        "WARNING: Using mock DeepFace library because DeepFace could not be imported.")
        return self._deepface

    def _get_mock(self):
        """ایجاد یک نسخه mock از کتابخانه deepface"""

        class MockDeepFace:
            @staticmethod
            def extract_faces(img_path, detector_backend='retinaface', enforce_detection=True, align=True,
                              target_size=(224, 224)):
                """تقلید عملکرد extract_faces با ارائه یک مکان تصادفی چهره"""
                import random

                # اگر تصویر به صورت آرایه numpy باشد، آن را به PIL Image تبدیل می‌کنیم
                if isinstance(img_path, np.ndarray):
                    height, width = img_path.shape[:2]
                else:
                    # برای مثال فرض می‌کنیم تصویر 640x480 است
                    height, width = 480, 640

                # شبیه‌سازی تشخیص یک چهره تصادفی
                top = random.randint(0, height // 3)
                right = random.randint(2 * width // 3, width - 1)
                bottom = random.randint(2 * height // 3, height - 1)
                left = random.randint(0, width // 3)

                return [{
                    'face': np.random.rand(224, 224, 3),
                    'facial_area': {
                        'x': left,
                        'y': top,
                        'w': right - left,
                        'h': bottom - top
                    },
                    'confidence': random.uniform(0.8, 0.99)
                }]

            @staticmethod
            def represent(img_path, model_name='VGG-Face', detector_backend='retinaface', enforce_detection=True,
                          align=True):
                """تقلید عملکرد represent با تولید یک بردار embedding تصادفی"""
                # تولید یک بردار embedding تصادفی با ابعاد مناسب براساس مدل
                embedding_sizes = {
                    'VGG-Face': 2622,
                    'Facenet': 128,
                    'Facenet512': 512,
                    'OpenFace': 128,
                    'DeepFace': 4096,
                    'DeepID': 160,
                    'ArcFace': 512,
                    'Dlib': 128,
                    'SFace': 512
                }

                embedding_size = embedding_sizes.get(model_name, 2622)
                return [{
                    'embedding': np.random.rand(embedding_size),
                    'facial_area': {
                        'x': 10,
                        'y': 10,
                        'w': 100,
                        'h': 100
                    },
                    'face_confidence': 0.98
                }]

            @staticmethod
            def verify(img1_path, img2_path, model_name='VGG-Face', detector_backend='retinaface',
                       distance_metric='cosine', enforce_detection=True, align=True):
                """تقلید عملکرد verify"""
                import random

                # شبیه‌سازی یک نتیجه تصادفی
                threshold = 0.6 if distance_metric == 'cosine' else 0.4
                distance = random.uniform(0.2, 0.8)
                verified = distance < threshold

                return {
                    'verified': verified,
                    'distance': distance,
                    'threshold': threshold,
                    'model': model_name,
                    'detector_backend': detector_backend,
                    'distance_metric': distance_metric
                }

            @staticmethod
            def find(img_path, db_path, model_name='VGG-Face', detector_backend='retinaface', distance_metric='cosine',
                     enforce_detection=True, align=True, normalization='base'):
                """تقلید عملکرد find"""
                import random

                # گاهی هیچ مطابقتی پیدا نمی‌کنیم
                if random.random() > 0.7:
                    return []

                # شبیه‌سازی یک نتیجه تصادفی
                threshold = 0.6 if distance_metric == 'cosine' else 0.4
                distance = random.uniform(0.2, 0.8)
                verified = distance < threshold

                # ساخت یک مطابقت تصادفی
                return [{
                    'identity': f'person_id_{random.randint(1, 100)}',
                    'distance': distance,
                    'verified': verified,
                    'threshold': threshold
                }]

        return MockDeepFace()

    def extract_faces(self, image, enforce_detection=True):
        """استخراج چهره(ها) از تصویر

        Args:
            image: تصویر PIL یا آرایه numpy یا مسیر فایل

        Returns:
            لیستی از dict های حاوی اطلاعات چهره‌های تشخیص داده شده
        """
        deepface = self._get_library()

        # تبدیل تصویر PIL به آرایه numpy اگر هنوز نیست
        if isinstance(image, Image.Image):
            image = np.array(image)

        # استخراج چهره‌ها
        try:
            faces = deepface.extract_faces(
                img_path=image,
                detector_backend=self._detector_backend,
                enforce_detection=enforce_detection,
                align=True
            )
            return faces
        except Exception as e:
            print(f"Error in face extraction: {str(e)}")
            return []

    def represent(self, image, enforce_detection=True):
        """استخراج embedding چهره از تصویر

        Args:
            image: تصویر PIL یا آرایه numpy یا مسیر فایل

        Returns:
            لیستی از dict های حاوی embedding های چهره‌های تشخیص داده شده
        """
        deepface = self._get_library()

        # تبدیل تصویر PIL به آرایه numpy اگر هنوز نیست
        if isinstance(image, Image.Image):
            image = np.array(image)

        # استخراج embedding
        try:
            embeddings = deepface.represent(
                img_path=image,
                model_name=self._model_name,
                detector_backend=self._detector_backend,
                enforce_detection=enforce_detection,
                align=True
            )
            return embeddings
        except Exception as e:
            print(f"Error in face representation: {str(e)}")
            return []

    def verify(self, image1, image2, enforce_detection=True):
        """مقایسه دو چهره

        Args:
            image1: تصویر اول
            image2: تصویر دوم

        Returns:
            dict حاوی نتیجه مقایسه
        """
        deepface = self._get_library()

        # تبدیل تصاویر PIL به آرایه numpy اگر هنوز نیستند
        if isinstance(image1, Image.Image):
            image1 = np.array(image1)
        if isinstance(image2, Image.Image):
            image2 = np.array(image2)

        # مقایسه چهره‌ها
        try:
            result = deepface.verify(
                img1_path=image1,
                img2_path=image2,
                model_name=self._model_name,
                detector_backend=self._detector_backend,
                distance_metric=self._distance_metric,
                enforce_detection=enforce_detection,
                align=True
            )
            return result
        except Exception as e:
            print(f"Error in face verification: {str(e)}")
            return {'verified': False, 'distance': 1.0, 'threshold': 0.6, 'error': str(e)}

    def find(self, image, known_embeddings=None, enforce_detection=True):
        """یافتن مطابقت چهره در میان embedding های موجود

        Args:
            image: تصویر چهره
            known_embeddings: لیستی از (شناسه شخص، embedding) های موجود

        Returns:
            لیستی از مطابقت‌ها (شناسه شخص، فاصله)
        """
        deepface = self._get_library()

        # اگر embedding های موجود ارائه شده باشند، آنها را در پایگاه داده موقت ذخیره می‌کنیم
        if known_embeddings:
            # ذخیره embeddings در فایل‌های موقت در دایرکتوری temp_db_path
            for person_id, embedding in known_embeddings:
                # هر embedding را به عنوان یک تصویر در پایگاه داده ذخیره می‌کنیم
                # نام فایل شامل شناسه شخص است
                np.save(f"{self._temp_db_path}/{person_id}.npy", embedding)

        # تبدیل تصویر PIL به آرایه numpy اگر هنوز نیست
        if isinstance(image, Image.Image):
            image = np.array(image)

        # جستجوی چهره در پایگاه داده
        try:
            if os.path.exists(self._temp_db_path) and os.listdir(self._temp_db_path):
                results = deepface.find(
                    img_path=image,
                    db_path=self._temp_db_path,
                    model_name=self._model_name,
                    detector_backend=self._detector_backend,
                    distance_metric=self._distance_metric,
                    enforce_detection=enforce_detection,
                    align=True
                )

                # پردازش نتایج
                if results and len(results) > 0:
                    matches = []
                    for result in results:
                        # استخراج شناسه شخص از نام فایل
                        identity = result.get('identity', '')
                        if isinstance(identity, str) and identity:
                            person_id = os.path.basename(identity).split('.')[0]
                            matches.append((person_id, result.get('distance', 1.0)))
                    return matches

            return []
        except Exception as e:
            print(f"Error in face find: {str(e)}")
            return []

    def analyze(self, image, enforce_detection=True):
        """آنالیز چهره (سن، جنسیت، احساسات، نژاد)

        Args:
            image: تصویر چهره

        Returns:
            dict حاوی نتایج آنالیز
        """
        deepface = self._get_library()

        # تبدیل تصویر PIL به آرایه numpy اگر هنوز نیست
        if isinstance(image, Image.Image):
            image = np.array(image)

        # آنالیز چهره
        try:
            obj = deepface.analyze(
                img_path=image,
                detector_backend=self._detector_backend,
                enforce_detection=enforce_detection,
                align=True
            )
            return obj
        except Exception as e:
            print(f"Error in face analysis: {str(e)}")
            return {}

    def compare_embeddings(self, embedding1, embedding2):
        """مقایسه دو embedding چهره

        Args:
            embedding1: embedding اول
            embedding2: embedding دوم

        Returns:
            فاصله بین دو embedding
        """
        from scipy.spatial.distance import cosine, euclidean

        # محاسبه فاصله بر اساس معیار فاصله انتخاب شده
        if self._distance_metric == 'cosine':
            distance = cosine(embedding1, embedding2)
        elif self._distance_metric == 'euclidean':
            distance = euclidean(embedding1, embedding2)
        elif self._distance_metric == 'euclidean_l2':
            embedding1 = embedding1 / np.sqrt(np.sum(np.square(embedding1)))
            embedding2 = embedding2 / np.sqrt(np.sum(np.square(embedding2)))
            distance = euclidean(embedding1, embedding2)
        else:
            distance = cosine(embedding1, embedding2)

        return distance

    def is_match(self, distance):
        """بررسی اینکه آیا فاصله محاسبه شده نشان‌دهنده تطابق است یا خیر

        Args:
            distance: فاصله محاسبه شده

        Returns:
            Boolean: آیا تطابق وجود دارد یا خیر
        """
        # تعیین آستانه بر اساس معیار فاصله
        if self._distance_metric == 'cosine':
            threshold = 0.4  # آستانه برای فاصله cosine
        elif self._distance_metric in ['euclidean', 'euclidean_l2']:
            threshold = 0.6  # آستانه برای فاصله euclidean
        else:
            threshold = 0.4

        # برای cosine، مقدار کمتر نشان‌دهنده تطابق بیشتر است
        return distance < threshold


# ایجاد یک نمونه از کلاس برای استفاده در کل برنامه
deepface_lib = DeepFaceWrapper()