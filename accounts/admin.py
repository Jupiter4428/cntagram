from django.contrib import admin

from .models import Role, User, UserRole


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # ไม่มี password ในฟอร์ม และ student_id ระบบดึงจากอีเมลเอง จึงแก้ไม่ได้
    # สิทธิ์ใช้ Role/UserRole จึงไม่แสดง groups/user_permissions ของ Django
    # pdpa_consent_at ต้องเป็นเวลาที่ผู้ใช้กดยอมรับจริง จึงห้ามแก้
    fields = [
        "student_id",
        "email",
        "personal_email",
        "nickname",
        "department",
        "is_active",
        "is_staff",
        "is_superuser",
        "email_verified_at",
        "pdpa_consent_at",
        "last_login",
        "created_at",
    ]
    readonly_fields = ["student_id", "pdpa_consent_at", "last_login", "created_at"]
    list_display = ["nickname", "email", "department", "is_active", "is_staff"]
    list_filter = ["is_active", "is_staff", "department"]
    search_fields = ["nickname", "email", "student_id"]

    def has_add_permission(self, request):
        # ผู้ใช้มาจากหน้าสมัครหรือ createsuperuser เท่านั้น (ฟอร์มนี้ไม่มีรหัสผ่าน)
        return False

    def has_delete_permission(self, request, obj=None):
        # ลบผู้ใช้ต้องผ่าน anonymize() ตาม PDPA ห้ามลบแถวตรง ๆ
        return False


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["code", "name_th"]


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "department", "granted_by", "granted_at"]
    list_filter = ["role", "department"]
    autocomplete_fields = ["user", "granted_by"]

    def get_queryset(self, request):
        # manager select_related ไว้แล้ว admin จึงข้าม list_select_related ต้อง join เอง
        return super().get_queryset(request).select_related("user", "granted_by")
