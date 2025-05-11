from django.http import HttpResponse, StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
import subprocess
import threading
import time
from rest_framework import viewsets
from .models import ExternalCamera, Person, FaceEncoding, RecognitionLog
from .serializers import (
    PersonSerializer, RegisterFaceSerializer, RecognizeFaceSerializer,
    UpdatePersonSerializer, UpdateFaceSerializer, RecognitionLogSerializer,
    ExternalCameraSerializer
)
from .face_utils import (
    base64_to_image, extract_face_encoding, find_matching_person,
    analyze_face, detect_faces, get_face_recognition_settings
)


class RegisterFaceAPIView(APIView):
    """API برای ثبت چهره جدید با استفاده از DeepFace"""

    def post(self, request):
        serializer = RegisterFaceSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # بررسی آیا کاربری با این کد ملی از قبل وجود دارد
        national_id = serializer.validated_data['national_id']
        if Person.objects.filter(national_id=national_id).exists():
            return Response(
                {"error": "کاربری با این کد ملی قبلاً ثبت شده است."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # تبدیل تصویر base64 به تصویر PIL
        image_data = serializer.validated_data['image']
        try:
            image = base64_to_image(image_data)
        except Exception as e:
            return Response(
                {"error": f"خطا در پردازش تصویر: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # استخراج embedding چهره با DeepFace
        face_encoding = extract_face_encoding(image)
        if face_encoding is None:
            return Response(
                {"error": "هیچ چهره‌ای در تصویر تشخیص داده نشد."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # آنالیز چهره برای اطلاعات اضافی
        face_analysis = analyze_face(image)

        # دریافت تنظیمات تشخیص چهره
        config = get_face_recognition_settings()
        model_name = config.get('model')

        # ایجاد کاربر و ذخیره embedding چهره
        with transaction.atomic():
            # ایجاد شخص جدید
            person = Person.objects.create(
                first_name=serializer.validated_data['first_name'],
                last_name=serializer.validated_data['last_name'],
                national_id=national_id
            )

            # ایجاد embedding چهره
            face_encoding_obj = FaceEncoding(person=person)
            face_encoding_obj.set_encoding(
                face_encoding,
                model_name=model_name,
                face_analysis=face_analysis
            )
            face_encoding_obj.save()

        return Response({
            "success": True,
            "message": "ثبت‌نام با موفقیت انجام شد.",
            "person": PersonSerializer(person).data,
            "analysis": face_analysis
        }, status=status.HTTP_201_CREATED)


class RecognizeFaceAPIView(APIView):
    """API برای تشخیص چهره با استفاده از DeepFace"""

    def post(self, request):
        serializer = RecognizeFaceSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # تبدیل تصویر base64 به تصویر PIL
        image_data = serializer.validated_data['image']
        try:
            image = base64_to_image(image_data)
        except Exception as e:
            return Response(
                {"error": f"خطا در پردازش تصویر: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # استخراج embedding چهره با DeepFace
        face_encoding = extract_face_encoding(image)
        if face_encoding is None:
            return Response(
                {"error": "هیچ چهره‌ای در تصویر تشخیص داده نشد."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # آنالیز چهره برای اطلاعات اضافی
        face_analysis = analyze_face(image)

        # دریافت تمام embedding های موجود
        face_encodings = list(FaceEncoding.objects.all())  # تبدیل به لیست
        known_encodings = [face_enc.get_encoding() for face_enc in face_encodings]

        # یافتن تطابق
        match_index = find_matching_person(face_encoding, known_encodings)

        if match_index is not None:
            # تشخیص موفق
            matched_face_encoding = face_encodings[match_index]  # حالا می‌توانیم اندیس‌دهی کنیم
            person = matched_face_encoding.person

            # محاسبه میزان اطمینان بر اساس فاصله
            from .deepface_wrapper import deepface_lib
            distance = deepface_lib.compare_embeddings(face_encoding, known_encodings[match_index])
            confidence = 1.0 - distance  # تبدیل فاصله به میزان اطمینان

            # ثبت لاگ تشخیص
            RecognitionLog.objects.create(
                person=person,
                ip_address=request.META.get('REMOTE_ADDR'),
                confidence=confidence,
                analysis=face_analysis
                # مکان را می‌توان از درخواست یا از سرویس‌های geolocation دریافت کرد
            )

            return Response({
                "success": True,
                "message": f"سلام {person.first_name}",
                "person": PersonSerializer(person).data,
                "confidence": round(confidence * 100, 2),  # به درصد
                "analysis": face_analysis
            })
        else:
            # عدم تشخیص
            return Response({
                "success": False,
                "message": "کاربر شناسایی نشد.",
                "analysis": face_analysis
            })


class UpdatePersonAPIView(APIView):
    """API برای به‌روزرسانی اطلاعات شخصی"""

    def get(self, request, national_id):
        """دریافت اطلاعات شخص با کد ملی"""
        person = get_object_or_404(Person, national_id=national_id)
        return Response(PersonSerializer(person).data)

    def put(self, request, national_id):
        """به‌روزرسانی اطلاعات شخصی"""
        person = get_object_or_404(Person, national_id=national_id)
        serializer = UpdatePersonSerializer(person, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "اطلاعات با موفقیت به‌روزرسانی شد.",
                "person": PersonSerializer(person).data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateFaceAPIView(APIView):
    """API برای به‌روزرسانی تصویر چهره"""

    def put(self, request, national_id):
        person = get_object_or_404(Person, national_id=national_id)
        serializer = UpdateFaceSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # تبدیل تصویر base64 به تصویر PIL
        image_data = serializer.validated_data['image']
        try:
            image = base64_to_image(image_data)
        except Exception as e:
            return Response(
                {"error": f"خطا در پردازش تصویر: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # استخراج embedding چهره با DeepFace
        face_encoding = extract_face_encoding(image)
        if face_encoding is None:
            return Response(
                {"error": "هیچ چهره‌ای در تصویر تشخیص داده نشد."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # آنالیز چهره برای اطلاعات اضافی
        face_analysis = analyze_face(image)

        # دریافت تنظیمات تشخیص چهره
        config = get_face_recognition_settings()
        model_name = config.get('model')

        # به‌روزرسانی یا ایجاد embedding چهره
        try:
            face_encoding_obj = person.face_encoding
        except FaceEncoding.DoesNotExist:
            face_encoding_obj = FaceEncoding(person=person)

        face_encoding_obj.set_encoding(
            face_encoding,
            model_name=model_name,
            face_analysis=face_analysis
        )
        face_encoding_obj.save()

        return Response({
            "success": True,
            "message": "تصویر چهره با موفقیت به‌روزرسانی شد.",
            "analysis": face_analysis
        })


class RecognitionLogListAPIView(APIView):
    """API برای دریافت لیست لاگ‌های تشخیص"""

    def get(self, request, national_id=None):
        if national_id:
            # دریافت لاگ‌های یک شخص خاص
            person = get_object_or_404(Person, national_id=national_id)
            logs = RecognitionLog.objects.filter(person=person)
        else:
            # دریافت همه لاگ‌ها
            logs = RecognitionLog.objects.all()

        serializer = RecognitionLogSerializer(logs, many=True)
        return Response(serializer.data)


class RTSPStreamingThread:
    def __init__(self, rtsp_url, fps=10):
        self.rtsp_url = rtsp_url
        self.fps = fps
        self.frame = None
        self.process = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

    def start(self):
        threading.Thread(target=self._capture_stream).start()

    def _capture_stream(self):
        command = [
            'ffmpeg',
            '-i', self.rtsp_url,
            '-f', 'image2pipe',
            '-pix_fmt', 'bgr24',
            '-vcodec', 'rawvideo',
            '-an', '-sn',
            '-'
        ]

        try:
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE)

            while not self.stop_event.is_set():
                # FFmpegからフレームを取得
                raw_frame = self.process.stdout.read(1920 * 1080 * 3)  # 解像度によって調整

                if not raw_frame:
                    break

                # OpenCVでデコード
                import numpy as np
                import cv2
                frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape((1080, 1920, 3))

                # フレームを保存
                with self.lock:
                    ret, jpeg = cv2.imencode('.jpg', frame)
                    self.frame = jpeg.tobytes()

                # フレームレート制御
                time.sleep(1 / self.fps)

        except Exception as e:
            print(f"RTSPStreaming Errors: {e}")
        finally:
            if self.process:
                self.process.terminate()
                self.process = None

    def get_frame(self):
        with self.lock:
            return self.frame

    def stop(self):
        self.stop_event.set()
        if self.process:
            self.process.terminate()


class RTSPStreamView(APIView):
    """RTSPストリームを提供するビュー"""

    streams = {}  # 複数のストリームを管理するための辞書

    def get(self, request, camera_id):
        # RTSPのURLはデータベースまたは設定ファイルから取得するべき
        rtsp_url = self._get_rtsp_url(camera_id)

        if not rtsp_url:
            return HttpResponse("Camera not found", status=404)

        # ストリームが存在しない場合は作成
        if camera_id not in self.streams:
            stream = RTSPStreamingThread(rtsp_url)
            stream.start()
            self.streams[camera_id] = stream

        return StreamingHttpResponse(
            self._stream_generator(camera_id),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )

    def _get_rtsp_url(self, camera_id):
        # 実際の実装では、データベースなどから取得
        # テスト用ダミーURLを返す
        return f"rtsp://example.com/camera/{camera_id}"

    def _stream_generator(self, camera_id):
        stream = self.streams.get(camera_id)

        if not stream:
            return

        while True:
            frame = stream.get_frame()

            if frame is None:
                time.sleep(0.1)
                continue

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


class ExternalCameraViewSet(viewsets.ModelViewSet):
    """API برای مدیریت دوربین‌های خارجی"""
    queryset = ExternalCamera.objects.all()
    serializer_class = ExternalCameraSerializer

    def get_queryset(self):
        queryset = ExternalCamera.objects.all()

        # فیلتر کردن بر اساس پروتکل
        protocol = self.request.query_params.get('protocol', None)
        if protocol:
            queryset = queryset.filter(protocol=protocol)

        # فیلتر کردن دوربین‌های فعال
        active_only = self.request.query_params.get('active', None)
        if active_only and active_only.lower() in ['true', '1', 't']:
            queryset = queryset.filter(is_active=True)

        return queryset

class AnalyzeFaceAPIView(APIView):
    """API برای آنالیز چهره (سن، جنسیت، احساسات، نژاد)"""

    def post(self, request):
        serializer = RecognizeFaceSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # تبدیل تصویر base64 به تصویر PIL
        image_data = serializer.validated_data['image']
        try:
            image = base64_to_image(image_data)
        except Exception as e:
            return Response(
                {"error": f"خطا در پردازش تصویر: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # آنالیز چهره با DeepFace
        face_analysis = analyze_face(image)
        if not face_analysis:
            return Response(
                {"error": "هیچ چهره‌ای در تصویر تشخیص داده نشد."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # یافتن چهره‌ها در تصویر
        faces = detect_faces(image)

        return Response({
            "success": True,
            "analysis": face_analysis,
            "faces_count": len(faces),
            "faces": faces
        })


class DetectMultipleFacesAPIView(APIView):
    """API برای تشخیص چندین چهره در یک تصویر"""

    def post(self, request):
        serializer = RecognizeFaceSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # تبدیل تصویر base64 به تصویر PIL
        image_data = serializer.validated_data['image']
        try:
            image = base64_to_image(image_data)
        except Exception as e:
            return Response(
                {"error": f"خطا در پردازش تصویر: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # یافتن چهره‌ها در تصویر
        faces = detect_faces(image)
        if not faces:
            return Response(
                {"error": "هیچ چهره‌ای در تصویر تشخیص داده نشد."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # برای هر چهره، آنالیز و تشخیص را انجام می‌دهیم
        results = []
        for i, face_data in enumerate(faces):
            # استخراج تصویر چهره
            face_image = face_data.get('face')

            # استخراج embedding چهره
            face_encoding = extract_face_encoding(face_image)

            # آنالیز چهره
            face_analysis = analyze_face(face_image)

            # دریافت تمام embedding های موجود
            face_encodings = list(FaceEncoding.objects.all())
            known_encodings = [face_enc.get_encoding() for face_enc in face_encodings]

            # یافتن تطابق
            match_index = find_matching_person(face_encoding, known_encodings)

            face_result = {
                "face_index": i,
                "facial_area": face_data.get('facial_area', {}),
                "confidence": face_data.get('confidence', 0),
                "analysis": face_analysis,
                "matched": False
            }

            if match_index is not None:
                # تشخیص موفق
                matched_face_encoding = face_encodings[match_index]
                person = matched_face_encoding.person

                # محاسبه میزان اطمینان بر اساس فاصله
                from .deepface_wrapper import deepface_lib
                distance = deepface_lib.compare_embeddings(face_encoding, known_encodings[match_index])
                confidence = 1.0 - distance  # تبدیل فاصله به میزان اطمینان

                # ثبت لاگ تشخیص
                RecognitionLog.objects.create(
                    person=person,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    confidence=confidence,
                    analysis=face_analysis
                )

                face_result["matched"] = True
                face_result["person"] = PersonSerializer(person).data
                face_result["match_confidence"] = round(confidence * 100, 2)

            results.append(face_result)

        return Response({
            "success": True,
            "faces_count": len(faces),
            "faces": results
        })