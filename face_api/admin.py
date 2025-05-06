from django.contrib import admin
from .models import Person, FaceEncoding, RecognitionLog


class FaceEncodingInline(admin.StackedInline):
    model = FaceEncoding
    can_delete = False
    readonly_fields = ['encoding_data', 'created_at', 'updated_at']
    max_num = 1


class RecognitionLogInline(admin.TabularInline):
    model = RecognitionLog
    readonly_fields = ['timestamp', 'location', 'ip_address']
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
    list_display = ['person', 'timestamp', 'location', 'ip_address']
    search_fields = ['person__first_name', 'person__last_name', 'person__national_id']
    list_filter = ['timestamp']
    readonly_fields = ['person', 'timestamp', 'location', 'ip_address']
