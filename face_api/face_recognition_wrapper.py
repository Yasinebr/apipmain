"""
این ماژول یک wrapper برای کتابخانه face_recognition است.
از این طریق می‌توانیم بین نسخه اصلی و mock سوئیچ کنیم.
"""
import os
import numpy as np

USE_MOCK = os.environ.get('USE_MOCK_FACE', '').lower() in ('true', '1', 't')


# کلاس حاوی توابع مورد نیاز برای تشخیص چهره
class FaceRecognition:
    def __init__(self):
        self._face_recognition = None

    def _get_library(self):
        """دریافت کتابخانه با lazy loading"""
        if self._face_recognition is None:
            if USE_MOCK:
                # استفاده از نسخه mock
                self._face_recognition = self._get_mock()
                print("WARNING: Using mock face recognition library. This is NOT suitable for production!")
            else:
                # استفاده از نسخه اصلی
                try:
                    import face_recognition
                    self._face_recognition = face_recognition
                except ImportError:
                    # اگر نصب نشده باشد، از نسخه mock استفاده می‌کنیم
                    self._face_recognition = self._get_mock()
                    print(
                        "WARNING: Using mock face recognition library because face_recognition could not be imported.")
        return self._face_recognition

    def _get_mock(self):
        """ایجاد یک نسخه mock از کتابخانه face_recognition"""

        class MockFaceRecognition:
            @staticmethod
            def face_locations(image, model='hog', number_of_times_to_upsample=1):
                """تقلید عملکرد face_locations با ارائه یک مکان تصادفی چهره"""
                import random
                # شبیه‌سازی تشخیص یک چهره تصادفی
                height, width = image.shape[:2]
                top = random.randint(0, height // 3)
                right = random.randint(2 * width // 3, width - 1)
                bottom = random.randint(2 * height // 3, height - 1)
                left = random.randint(0, width // 3)

                return [(top, right, bottom, left)]

            @staticmethod
            def face_encodings(image, known_face_locations=None, num_jitters=1):
                """تقلید عملکرد face_encodings با تولید یک بردار 128 بعدی تصادفی"""
                # تولید یک بردار 128 بعدی تصادفی به عنوان embedding چهره
                return [np.random.rand(128)]

            @staticmethod
            def compare_faces(known_face_encodings, face_encoding_to_check, tolerance=0.6):
                """تقلید عملکرد compare_faces"""
                if not known_face_encodings:
                    return []

                # اولین چهره را همیشه به عنوان تطابق برمی‌گرداند
                results = [False] * len(known_face_encodings)
                if len(results) > 0:
                    results[0] = True

                return results

            @staticmethod
            def face_distance(face_encodings, face_to_compare):
                """تقلید عملکرد face_distance"""
                import random
                return np.array([random.uniform(0.3, 0.8) for _ in face_encodings])

        return MockFaceRecognition()

    # توابع wrapper برای توابع کتابخانه
    def face_locations(self, image, model='hog', number_of_times_to_upsample=1):
        lib = self._get_library()
        return lib.face_locations(image, model=model, number_of_times_to_upsample=number_of_times_to_upsample)

    def face_encodings(self, image, known_face_locations=None, num_jitters=1):
        lib = self._get_library()
        return lib.face_encodings(image, known_face_locations, num_jitters=num_jitters)

    def compare_faces(self, known_face_encodings, face_encoding_to_check, tolerance=0.6):
        lib = self._get_library()
        return lib.compare_faces(known_face_encodings, face_encoding_to_check, tolerance=tolerance)

    def face_distance(self, face_encodings, face_to_compare):
        lib = self._get_library()
        return lib.face_distance(face_encodings, face_to_compare)


# ایجاد یک نمونه از کلاس برای استفاده در کل برنامه
face_recognition_lib = FaceRecognition()