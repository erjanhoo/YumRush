from django.urls import path
from .views import *
urlpatterns = [
    #AUTHTENTICATION
    path('registration/', UserRegisterView.as_view()),
    path('login/', UserLoginView.as_view()),
    path('logout/', UserLogoutView.as_view()),

    #PROFILE
    path('profile/', UserProfileView.as_view()),
    path('profile_update/', UserProfileUpdateView.as_view()),
    path('balance_top_up/', UserBalanceTopUpView.as_view()),
    path('user_transactions_history/', UserTransactionHistoryView.as_view()),

    #OTP
    path('login_otp_verification/', UserLoginOTPVerificationView.as_view()),
    path('registration_otp_verification/', UserRegistrationOTPVerificationView.as_view()),
    path('resend_registration_otp/', ResendRegistrationOTPView.as_view()),
    path('resend_login_otp/', ResendLoginOTPView.as_view()),

    #MANAGER
    path('manager/courier_account_creation/', CourierAccountCreationView.as_view()),
    path('manager/create_product/', ProductCreateView.as_view()),
    path('manager/update_product/', ProductUpdateView.as_view()),
    path('manager/delete_product/', ProductDeleteView.as_view()),

]