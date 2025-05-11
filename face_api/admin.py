from django.contrib import admin
from .models import Person, FaceEncoding, RecognitionLog, ExternalCamera


class FaceEncodingInline(admin.StackedInline):
    model = FaceEncoding
    can_delete = False
    readonly_fields = ['encoding_data', 'model_name', 'face_analysis', 'created_at', 'updated_at']
    max_num = 1

    def get_face_analysis_display(self, obj):
        """نمایش آنالیز چهره به صورت خوانا"""
        if not obj.face_analysis:
            return "آنالیز چهره موجود نیست"

        analysis = obj.face_analysis
        result = ""

        # سن
        if 'age' in analysis:
            result += f"سن: {analysis['age']} سال\n"

        # جنسیت
        if 'gender' in analysis:
            gender = analysis['gender']
            if gender == 'Woman':
                gender = 'زن'
            elif gender == 'Man':
                gender = 'مرد'
            result += f"جنسیت: {gender}\n"

        # احساسات
        if 'emotion' in analysis:
            emotions = analysis['emotion']
            sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
            result += "احساسات:\n"
            for emotion, score in sorted_emotions:
                result += f"  - {emotion}: {score * 100:.2f}%\n"

        # نژاد
        if 'race' in analysis:
            races = analysis['race']
            sorted_races = sorted(races.items(), key=lambda x: x[1], reverse=True)
            result += "نژاد/قومیت:\n"
            for race, score in sorted_races:
                result += f"  - {race}: {score * 100:.2f}%\n"

        return result

    get_face_analysis_display.short_description = 'آنالیز چهره'


class RecognitionLogInline(admin.TabularInline):
    model = RecognitionLog
    readonly_fields = ['timestamp', 'location', 'ip_address', 'confidence', 'analysis']
    can_delete = False
    max_num = 10
    extra = 0


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'national_id', 'registered_at']
    search_fields = ['first_name', 'last_name', 'national_id']
    list_filter = ['registered_at']
    readonly_fields = ['registered_at', 'updated_at']
    inlines = [FaceEncodingInline, RecognitionLogInline]


@admin.register(RecognitionLog)
class RecognitionLogAdmin(admin.ModelAdmin):
    list_display = ['person', 'timestamp', 'location', 'ip_address', 'confidence_percent']
    search_fields = ['person__first_name', 'person__last_name', 'person__national_id']
    list_filter = ['timestamp']
    readonly_fields = ['person', 'timestamp', 'location', 'ip_address', 'confidence', 'analysis']

    def confidence_percent(self, obj):
        """نمایش میزان اطمینان به صورت درصد"""
        return f"{obj.confidence * 100:.2f}%"

    confidence_percent.short_description = 'میزان اطمینان'


@admin.register(ExternalCamera)
class ExternalCameraAdmin(admin.ModelAdmin):
    list_display = ['name', 'protocol', 'location', 'is_active']
    list_filter = ['protocol', 'is_active']
    search_fields = ['name', 'location']


@admin.register(FaceEncoding)
class FaceEncodingAdmin(admin.ModelAdmin):
    list_display = ['person', 'model_name', 'created_at', 'updated_at']
    list_filter = ['model_name', 'created_at']
    search_fields = ['person__first_name', 'person__last_name', 'person__national_id']
    readonly_fields = ['person', 'encoding_data', 'model_name', 'face_analysis', 'created_at', 'updated_at']