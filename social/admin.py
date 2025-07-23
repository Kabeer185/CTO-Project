from django.contrib import admin
from .models import *


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'username', 'image', 'date_of_birth', 'gender',
        'email', 'phone_number', 'password', 'address',
        'is_verified', 'about'
    ]


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'token', 'otp_expiry', 'is_verified',
        'max_otp_try', 'otp_max_out'
    ]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'post_type', 'location', 'bird_species','activity','duration','datetime',
        'created_at', 'like_count', 'comment_count'
    ]


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'post', 'created_at'
    ]


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'post', 'parent', 'text', 'created_at'
    ]


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'sender', 'receiver', 'status', 'created_at'
    ]
