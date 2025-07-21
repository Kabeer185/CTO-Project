from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import *
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.conf.urls.static import static



class ApiRootView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({
            'google_login': request.build_absolute_uri('/google/'),
            'facebook_login': request.build_absolute_uri('/facebook/'),
        })

router = DefaultRouter()
router.register(r'signup',SignUpView,basename='signup')
router.register(r'regenerate_otp',RegenerateOTPViewSet,basename='regenerate_otp')
router.register(r'varify_otp',VerifyOTPView,basename='varify_otp')
router.register(r'login',LoginView,basename='login')
router.register(r'edit_profile',UserProfileViewSet,basename='edit_profile')
router.register(r'create_post',PostViewSet,basename='create_post')
router.register(r'like_post',PostLikeViewSet,basename='like_post')
router.register(r'comment_post',PostCommentViewSet,basename='comment_post')
router.register(r'friend_requests', FriendRequestViewSet, basename='friend_requests')
router.register(r'all_users', AllUsersViewSet, basename='all_users')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'main_profile', MainProfileViewSet, basename='main_profile')



urlpatterns = [
    path('',include(router.urls)),
    path(r'password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('accounts/', include('allauth.urls'), name='socialaccount_signup'),
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('google/',GoogleConnect.as_view(),name='google_connect'),
    path('facebook/',FacebookConnect.as_view(),name='facebook_connect'),
    path('redirect/',UserRedirectView.as_view(),name='redirect'),
    path('',ApiRootView.as_view(),name='api_root'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)