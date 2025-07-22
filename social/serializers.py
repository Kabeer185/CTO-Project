import random
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from allauth.account import app_settings
from .models import *



class UserSerializer(serializers.ModelSerializer):
    # email = serializers.EmailField(required=app_settings.SIGNUP_FIELDS['email']['required'])
    # username = serializers.CharField(required=app_settings.SIGNUP_FIELDS['username']['required'])
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=True)
    gender = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['id','username','image','date_of_birth','gender','email','phone_number','password','address','about']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate_gender(self, value):
        valid_genders = dict(User.GENDER_CHOICES)
        if value not in valid_genders:
            raise serializers.ValidationError({"detail": 'gender must be one of {}'.format(valid_genders)})
        return value

    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"detail": "This email is already registered."})
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"detail": "This username is already registered."})
        return data

    def create(self, validated_data):
        validated_data["is_verified"] = False
        user = User(
            username=validated_data['username'],
            date_of_birth=validated_data['date_of_birth'],
            gender=validated_data['gender'],
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
        )
        user.set_password(validated_data['password'])
        user.save()

        OTP.objects.create(
            user=user,
            token=f"{random.randint(0, 99999):05d}",
            otp_expiry=timezone.now() + timedelta(seconds=120),
            is_verified=False
        )
        return user



class UserMinimalSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['username', 'image']

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None



class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['token']


    def validate_token(self, value):
        if not value:
            raise serializers.ValidationError({"detail":"OTP is required."})
        return value

class RegenerateOTPSerializer(serializers.Serializer):
    # email=serializers.EmailField(required=app_settings.SIGNUP_FIELDS['email']['required'])
    email = serializers.EmailField(required=True)




class LoginSerializer(serializers.Serializer):
    # email=serializers.EmailField(required=app_settings.SIGNUP_FIELDS['email']['required'])
    email = serializers.EmailField(required=True)
    password=serializers.CharField(required=True)

    def validate(self,data):
        email=data.get('email')
        password=data.get('password')
        if not email or not password:
            raise serializers.ValidationError({'detail':'Email And Password is Required'})

        user = User.objects.filter(email=email).first()
        if not user or not user.check_password(password):
            raise serializers.ValidationError({"detail": "Email or Password Incorrect"})
        data['user']=user
        return data




class UserProfileSerializer(serializers.ModelSerializer):
    gender = serializers.ChoiceField(choices=User.GENDER_CHOICES, required=False)
    class Meta:
        model = User
        fields=['id','username','image','date_of_birth','phone_number','gender','address','about']
        extra_kwargs={
            'username': {'required': False}
        }



    def validate(self, data):

        user_instance = self.instance
        username = data.get('username')
        if username and User.objects.filter(username=username).exclude(pk=user_instance.pk).exists():
            raise serializers.ValidationError({"detail":"This username is already taken."})

        return data


class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id','user', 'post_type', 'content', 'about', 'image', 'video']
        extra_kwargs = {
            'user': {'read_only': True},
            'post_type': {'required': False},
        }

    def validate(self, data):
        content = data.get('content')
        image = data.get('image')
        video = data.get('video')
        post_type = data.get('post_type')

        if not post_type:
            if video:
                data['post_type'] = 'video'
            elif image:
                data['post_type'] = 'image'
            elif content:
                data['post_type'] = 'text'
            else:
                raise serializers.ValidationError({"detail":"At least one of content, image, or video is required."})

        post_type = data['post_type']
        if post_type == 'text' and not content:
            raise serializers.ValidationError({"detail":"Text content is required for text posts."})
        if post_type == 'image' and not image:
            raise serializers.ValidationError({"detail":"Image is required for image posts."})
        if post_type == 'video' and not video:
            raise serializers.ValidationError({"detail":"Video is required for video posts."})

        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PostCommentReplySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = PostComment
        fields = ['id', 'user', 'text', 'created_at']


class PostCommentInlineSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    replies = PostCommentReplySerializer(many=True, read_only=True)

    class Meta:
        model = PostComment
        fields = ['id', 'user', 'text', 'created_at', 'replies']


class PostListSerializer(serializers.ModelSerializer):
    user =UserMinimalSerializer(read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'post_type', 'content', 'about',
            'image', 'video', 'like_count', 'comment_count',
            'comments', 'created_at'
        ]

    def get_comments(self, obj):
        top_level_comments = obj.comments_post.filter(parent=None).order_by('-created_at')
        return PostCommentInlineSerializer(top_level_comments, many=True).data


class PostLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLike
        fields = ['id', 'user', 'post', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def validate(self, data):
        user = self.context['request'].user
        post = data['post']
        if PostLike.objects.filter(user=user, post=post).exists():
            raise serializers.ValidationError({"detail":"You have already liked this post."})
        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PostCommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = PostComment
        fields = ['id', 'user', 'post', 'parent', 'text', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def validate(self, data):
        parent = data.get('parent')
        post = data.get('post')

        if parent and parent.post != post:
            raise serializers.ValidationError({"detail":"Reply must be on the same post as the parent comment."})

        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)




class FriendRequestSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField(read_only=True)
    receiver = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = FriendRequest
        fields = ['id', 'sender', 'receiver', 'status', 'created_at']
        read_only_fields = ['id', 'sender', 'status', 'created_at']


    def validate(self, data):
        sender = self.context['request'].user
        receiver = data['receiver']

        if sender == receiver:
            raise serializers.ValidationError({"detail":"You cannot send a friend request to yourself."})

        if FriendRequest.objects.filter(sender=sender, receiver=receiver, status='pending').exists():
            raise serializers.ValidationError({"detail":"Friend request already sent and pending."})

        if FriendRequest.objects.filter(sender=sender, receiver=receiver, status='accepted').exists():
            raise serializers.ValidationError({"detail":"You are already friends."})

        return data

    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


