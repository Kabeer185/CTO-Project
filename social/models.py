import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    GENDER_CHOICES = [
        ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other'),
    ]
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    phone_number = models.CharField(max_length=11, null=True, blank=True)
    date_of_birth = models.DateTimeField(null=True, blank=True, )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    is_verified = models.BooleanField(default=False)
    address = models.CharField(max_length=150, null=True, blank=True)
    image = models.ImageField(null=True, blank=True)
    about = models.TextField(null=True, blank=True)


class OTP(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='otp')
    token=models.CharField(max_length=5,blank=True,null=True)
    otp_expiry=models.DateTimeField(null=True, blank=True)
    is_verified=models.BooleanField(default=False)
    max_otp_try=models.CharField(max_length=4,default=5)
    otp_max_out=models.DateTimeField(null=True, blank=True)


class Post(models.Model):
    POST_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(null=True, blank=True)
    about = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='posts/images/', null=True, blank=True)
    video = models.FileField(upload_to='posts/videos/', null=True, blank=True)
    location = models.CharField(max_length=25, null=True, blank=True)
    bird_species=models.CharField(max_length=25, null=True, blank=True)
    activity=models.CharField(max_length=25, null=True, blank=True)
    duration=models.CharField(max_length=100,null=True, blank=True)
    datetime=models.DateTimeField(null=True, blank=True)
    post_type = models.CharField(max_length=10, choices=POST_TYPE_CHOICES, default='text')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.post_type} - {self.created_at.strftime('%Y-%m-%d')}"


    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments_post.count()



class PostLike(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} liked {self.post}"




class PostComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments_post')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.parent:
            return f"{self.user.username} replied to comment on {self.post}"
        return f"{self.user.username} commented on {self.post}"



class FriendRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.status})"
