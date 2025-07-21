from django.contrib import admin

from .models import*
# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id','username','image','date_of_birth','gender','email','phone_number','password','address','is_verified','about']



@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['id','user','token','is_verified']