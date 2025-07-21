from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import RedirectView
from django.conf import settings
from django.core.mail import send_mail
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny,IsAuthenticated,IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from .models import *

# Create your views here.


class SignUpView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        username = request.data.get('username')
        if not email or not phone_number or not username:
            raise serializers.ValidationError({"detail": "Email and Phone number is required."})


        try:
            user = User.objects.get(email=email,username=username)

            update_fields =['date_of_birth','gender','phone_number','username']
            for field in update_fields:
                if field in request.data:
                    setattr(user,field,request.data[field])
            user.save()


            OTP.objects.filter(user=user).delete()
            otp_code = f"{random.randint(0, 99999):05d}"
            OTP.objects.create(
                user=user,
                token=otp_code,
                otp_expiry=timezone.now() + timedelta(seconds=120),
                is_verified=False
            )

            send_mail(
                "Your OTP Code",
                f"Your OTP Code is {otp_code}",
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            return Response({"detail":"OTP sent successfully To log in First verify it ."},status=status.HTTP_200_OK)
        except User.DoesNotExist:

            serializer=self.serializer_class(data=request.data,context={'request':request})
            if serializer.is_valid():
                user = serializer.save()


                latest_otp=OTP.objects.filter(user=user).latest('id')
                send_mail(
                    "Your OTP Code ",
                    f"Your OTP Code is {latest_otp.token}",
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    fail_silently=False,
                )
                return Response({"detail":"Account Created Successfully  an OTP send via email "}, status=status.HTTP_201_CREATED)

            raise serializers.ValidationError(serializer.errors)



class VerifyOTPView(viewsets.ModelViewSet):
    queryset = OTP.objects.all()
    serializer_class = OTPSerializer
    permission_classes = [AllowAny]


    def create(self, request, *args, **kwargs):
        serializer=self.serializer_class(data=request.data,context={'request':request})
        if serializer.is_valid():
            token=serializer.validated_data['token']
            try:
                otp_instance=OTP.objects.get(token=token,is_verified=False)
                if otp_instance.otp_expiry<timezone.now():
                    raise serializers.ValidationError("OTP Expired")

                otp_instance.is_verified=True
                otp_instance.save()
                user=otp_instance.user
                user.is_verified=True
                user.save()
                return Response({'detail':'Account verified Successfully'}, status=status.HTTP_200_OK)
            except OTP.DoesNotExist:
                raise serializers.ValidationError("OTP Does Not Exist")

        raise serializers.ValidationError(serializer.errors)



class RegenerateOTPViewSet(viewsets.ModelViewSet):
    queryset = User.objects.none()
    permission_classes = [AllowAny]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
            raise serializers.ValidationError("Email Required")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        if user.is_verified:
            raise serializers.ValidationError("user already verified")

        otp_instance, created = OTP.objects.get_or_create(user=user)

        now = timezone.now()

        if int(otp_instance.max_otp_try) <= 0:
            if otp_instance.otp_max_out and now < otp_instance.otp_max_out:
                raise serializers.ValidationError("You reached maximum OTP try limit. Please try again after 15 minutes.")
            else:
                otp_instance.max_otp_try = 5
                otp_instance.otp_max_out = None

        otp_instance.token = f"{random.randint(0, 99999):05d}"
        otp_instance.otp_expiry = now + timedelta(seconds=120)
        otp_instance.max_otp_try = max(int(otp_instance.max_otp_try) - 1, 0)
        otp_instance.is_verified = False

        if int(otp_instance.max_otp_try) == 0:
            otp_instance.otp_max_out = now + timedelta(minutes=15)

        otp_instance.save()

        send_mail(
            "Your New OTP Code",
            f"Your new OTP is {otp_instance.token}",
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )

        return Response({"detail": "New OTP sent successfully"}, status=status.HTTP_200_OK)



class LoginView(viewsets.ModelViewSet):
    queryset = User.objects.none()
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data.get('user')
        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_verified:
            raise serializers.ValidationError("Please verify your account before logging in.")

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            "message": "Login successful",
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "gender": user.gender,
            "image": user.image.url if user.image and hasattr(user.image, 'url') else None,
            "access_token": access_token,
            "refresh_token": str(refresh),
        }, status=status.HTTP_200_OK)




class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)


        return Response({
            "detail":"User profile updated successfully",
        },status=status.HTTP_200_OK)



class UserRedirectView(LoginRequiredMixin,RedirectView):
    permanent = False
    def get_redirect_url(self):
        return "http://127.0.0.1"



class GoogleConnect(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class=OAuth2Client


    def post(self,request,*args, **kwargs):
        response=super().post(request,*args,**kwargs)

        if response.status_code != status.HTTP_200_OK:
            return response

        user=self.request.user

        if not user.is_verified:
            user.is_verified=True
            user.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            "message":"Login Successfully with google",
            "id":user.id,
            "email":user.email,
            "access_token":access_token,
            "refresh_token":str(refresh)

        },status=status.HTTP_200_OK)




class FacebookConnect(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter
    authentication_classes = []
    permission_classes = []

    def post(self,request,*args, **kwargs):
        response=super().post(request,*args,**kwargs)

        if response.status_code != status.HTTP_200_OK:
            return response

        user=self.request.user
        if not user.is_verified:
            user.is_verified=True
            user.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            'message':'Login Successfully with facebook',
            'id':user.id,
            'email':user.email,
            'access_token':access_token,
            'refresh_token':str(refresh)
        },status=status.HTTP_200_OK)



class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get_queryset(self):
        user = self.request.user
        if not user.is_verified:
            return Post.objects.none()
        return Post.objects.filter(user=user).select_related('user').prefetch_related('comments_post', 'likes')


    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PostCreateSerializer
        return PostListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



class PostLikeViewSet(viewsets.ModelViewSet):

    serializer_class = PostLikeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PostLike.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        like = self.get_object()
        if like.user != request.user:
            raise serializers.ValidationError({"detail": "You can only unlike your own likes."})

        return super().destroy(request, *args, **kwargs)


class PostCommentViewSet(viewsets.ModelViewSet):

    serializer_class = PostCommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        post_id = self.request.query_params.get('post')
        queryset = PostComment.objects.select_related('user', 'post', 'parent')

        if post_id:
            return queryset.filter(post_id=post_id).order_by('-created_at')
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)




class FriendRequestViewSet(viewsets.ModelViewSet):
    serializer_class = FriendRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return FriendRequest.objects.filter(receiver=user, status='pending')

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['patch'])
    def accept(self, request, pk=None):
        try:
            friend_request = self.get_object()
            if friend_request.receiver != request.user:
                raise serializers.ValidationError({"detail": "You can only accept requests sent to you."})


            friend_request.status = 'accepted'
            friend_request.save()
            return Response({"detail": "Friend request accepted."}, status=200)
        except FriendRequest.DoesNotExist:
            raise serializers.ValidationError({"detail": "Friend request does not exist."})


    @action(detail=True, methods=['patch'])
    def reject(self, request, pk=None):
        try:
            friend_request = self.get_object()
            if friend_request.receiver != request.user:
                raise serializers.ValidationError({"detail": "You can only reject requests sent to you."})

            friend_request.status = 'rejected'
            friend_request.save()
            return Response({"detail": "Friend request rejected."}, status=200)
        except FriendRequest.DoesNotExist:
            raise serializers.ValidationError({"detail": "Friend request does not exist."})




class AllUsersViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_verified=True)
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']




class DashboardViewSet(viewsets.ModelViewSet):

    queryset = Post.objects.all().select_related('user').prefetch_related('comments_post', 'likes').order_by('-created_at')
    serializer_class = PostListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        posts = self.get_queryset()
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)



class MainProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']


    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)
