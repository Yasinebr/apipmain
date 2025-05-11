from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RegisterFaceAPIView,
    RecognizeFaceAPIView,
    UpdatePersonAPIView,
    UpdateFaceAPIView,
    RecognitionLogListAPIView,
    ExternalCameraViewSet,
    RTSPStreamView,
    AnalyzeFaceAPIView,
    DetectMultipleFacesAPIView
)

app_name = 'face_api'

router = DefaultRouter()
router.register(r'cameras', ExternalCameraViewSet)


urlpatterns = [
    # ثبت چهره جدید
    path('register/', RegisterFaceAPIView.as_view(), name='register_face'),

    # تشخیص چهره
    path('recognize/', RecognizeFaceAPIView.as_view(), name='recognize_face'),

    # آنالیز چهره (سن، جنسیت، احساسات، نژاد)
    path('analyze/', AnalyzeFaceAPIView.as_view(), name='analyze_face'),

    # تشخیص چندین چهره در یک تصویر
    path('detect-multiple/', DetectMultipleFacesAPIView.as_view(), name='detect_multiple_faces'),

    # به‌روزرسانی اطلاعات شخصی
    path('update-person/<str:national_id>/', UpdatePersonAPIView.as_view(), name='update_person'),

    # به‌روزرسانی تصویر چهره
    path('update-face/<str:national_id>/', UpdateFaceAPIView.as_view(), name='update_face'),

    # دریافت لاگ‌های تشخیص
    path('logs/', RecognitionLogListAPIView.as_view(), name='all_logs'),
    path('logs/<str:national_id>/', RecognitionLogListAPIView.as_view(), name='person_logs'),

    # استریم RTSP
    path('stream/<str:camera_id>/', RTSPStreamView.as_view(), name='rtsp_stream'),

    # اضافه کردن URL‌های router
    path('', include(router.urls)),
]