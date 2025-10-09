from django.contrib.auth.hashers import make_password
from django.utils import timezone
import datetime

from django.contrib.auth import authenticate
from django.core.mail import send_mail
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import UpdateAPIView, CreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import TemporaryRegistration
from .services import *
from .serializers import *
from django.conf import settings
from django.db import IntegrityError

from product.models import Product


#AUTHENTICATION
class UserRegisterView(APIView):
    @swagger_auto_schema(
        tags=['auth'],
        operation_description="Register a new user account",
        request_body=UserRegisterSerializer,
        responses={
            201: openapi.Response(
                description="User created successfully, OTP code sent",
                examples={
                    "application/json": {
                        "user_id": 1,
                        "username": "newuser",
                        "email": "user@example.com",
                        "message": "OTP код отправлен на ваш email"
                    }
                }
            ),
            400: "Bad request - validation errors"
        }
    )
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Проверяем существует ли пользователь с таким email
                if MyUser.objects.filter(email=serializer.validated_data['email']).exists():
                    return Response(
                        {'error': 'Пользователь с таким email уже существует'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Проверяем существует ли уже временная регистрация с таким email
                if TemporaryRegistration.objects.filter(email=serializer.validated_data['email']).exists():
                    TemporaryRegistration.objects.filter(email=serializer.validated_data['email']).delete()

                temp_reg = TemporaryRegistration(
                    username=serializer.validated_data['username'],
                    email=serializer.validated_data['email'],
                )
                temp_reg.password = make_password(serializer.validated_data['password'])

                otp_code = generateOTP()
                temp_reg.otp = otp_code
                temp_reg.otp_created_at = timezone.now()
                temp_reg.save()

                try:
                    send_mail(
                        subject='Подтверждение регистрации',
                        message=f'Добро пожаловать! Ваш код подтверждения: {otp_code}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[temp_reg.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    # Если отправка email не удалась, удаляем временную регистрацию
                    temp_reg.delete()
                    return Response(
                        {'error': 'Ошибка отправки email. Попробуйте позже.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                response_data = {
                    'user_id': temp_reg.id,
                    'username': temp_reg.username,
                    'email': temp_reg.email,
                    'message': 'OTP код отправлен на ваш email. Подтвердите регистрацию.'
                }
                return Response(response_data, status=status.HTTP_201_CREATED)

            except IntegrityError:
                return Response(
                    {'error': 'Пользователь с такими данными уже существует'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class UserLoginView(APIView):
    @swagger_auto_schema(
        tags=['auth'],
        operation_description="Authenticate user with email and password",
        request_body=UserLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "user_id": 1,
                        "email": "user@example.com",
                        "username": "username"
                    }
                }
            ),
            200: openapi.Response(
                description="2FA enabled - OTP code sent",
                examples={
                    "application/json": {
                        "user_id": 1
                    }
                }
            ),
            400: "Invalid credentials",
            404: "User not found"
        }
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = authenticate(
                request=request,
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
            )
            if user:
                if user.is_2fa_enabled:
                    otp_code = generateOTP()
                    user.otp = otp_code
                    user.otp_created_at = timezone.now()
                    user.save()
                    user_email = user.email

                    send_mail(
                        subject='Code',
                        message=f'Your OTP code is {otp_code}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user_email],
                        fail_silently=False,
                    )

                    data = {
                        'user_id':user.id,
                    }
                    return Response(data, status=status.HTTP_200_OK)
                else:
                    refresh = RefreshToken.for_user(user)
                    return Response(
                        {
                            'refresh':str(refresh),
                            'access':str(refresh.access_token),
                            'user_id':user.id,
                            'user_role':user.role,
                            'email':user.email,
                            'username':user.username
                        }, status=status.HTTP_200_OK
                    )
            return Response({'error':'User not found'},status=status.HTTP_404_NOT_FOUND)
        return Response({'error':'Not valid credentials'},status=status.HTTP_400_BAD_REQUEST)



class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['auth'],
        operation_description="Logout the current user by blacklisting their JWT token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='JWT refresh token to blacklist'
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Successfully logged out",
                examples={
                    "application/json": {
                        "detail": "Successfully logged out."
                    }
                }
            ),
            401: "Authentication credentials not provided"
        },
        security=[{"Bearer": []}]
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)


#PROFILE

class UserProfileView(APIView):
    @swagger_auto_schema(
        tags=['user'],
        operation_description="Get the authenticated user's profile information",
        responses={
            200: UserProfileSerializer,
            401: "Authentication credentials not provided"
        },
        security=[{"Bearer": []}]
    )

    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)



class UserProfileUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = MyUser.objects.all()
    serializer_class = UserProfileUpdateSerializer

    @swagger_auto_schema(
        tags=['user'],
        operation_description="Update the authenticated user's profile information",
        request_body=UserProfileUpdateSerializer,
        responses={
            200: UserProfileUpdateSerializer,
            400: "Bad request - validation errors",
            401: "Authentication credentials not provided",
            403: "Permission denied - cannot update other users' profiles"
        },
        security=[{"Bearer": []}]
    )
    def get_object(self):
        return self.request.user



class UserBalanceTopUpView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserBalanceTopUpSerializer

    @swagger_auto_schema(
        tags=['user'],
        operation_description="Top up user balance",
        request_body=UserBalanceTopUpSerializer,
        responses={
            200: openapi.Response(
                description="Balance updated successfully",
                examples={
                    "application/json": {
                        "balance": "150.00",
                        "message": "Balance topped up successfully"
                    }
                }
            ),
            400: "Invalid amount"
        },
        security=[{"Bearer": []}]
    )
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            user = request.user

            user.balance = user.balance + amount
            user.save()
            return Response({
                'balance': user.balance,
                'message': 'Balance topped up successfully'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_object(self):
        return self.request.user


#OTP VALIDATION
class UserLoginOTPVerificationView(APIView):
    @swagger_auto_schema(
        tags=['auth'],
        operation_description="Verify OTP code for two-factor authentication",
        request_body=UserOTPVerificationSerializer,
        responses={
            200: openapi.Response(
                description="OTP verification successful",
                examples={
                    "application/json": {
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "user_id": 1,
                        "email": "user@example.com",
                        "username": "username"
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request",
                examples={
                    "application/json": {
                        "error": "invalid OTP code"
                    }
                }
            ),
            404: openapi.Response(
                description="User not found",
                examples={
                    "application/json": {
                        "error": "User not found"
                    }
                }
            )
        }
    )
    def post(self, request):
        serializer = UserOTPVerificationSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            temp_id = serializer.validated_data['user_id']
            entered_otp = serializer.validated_data['otp_code']

            try:
                temp_reg = TemporaryRegistration.objects.get(id=temp_id)
            except TemporaryRegistration.DoesNotExist:
                return Response({'error':'Registration request not found'}, status=status.HTTP_404_NOT_FOUND)

            otp_expiry_minutes = 3
            user_otp = temp_reg.otp
            current_time = timezone.now()

            if temp_reg.otp_created_at and (current_time - temp_reg.otp_created_at).total_seconds() > (otp_expiry_minutes * 60):
                temp_reg.otp = None
                temp_reg.otp_created_at = None
                temp_reg.save()
                return Response({'error':'OTP code has expired. Send a new one'}, status=status.HTTP_400_BAD_REQUEST)


            if not verifyOTP(entered_otp, user_otp):
                return Response({'error':'invalid OTP code'},status=status.HTTP_400_BAD_REQUEST)
            temp_reg.otp = None
            temp_reg.save()

            user = MyUser(
                username=temp_reg.username,
                email=temp_reg.email,
            )
            user.password = temp_reg.password
            user.save()

            temp_reg.delete()

            refresh = RefreshToken.for_user(user)
            user_id = user.id

            return Response(
                {
                    'refresh':str(refresh),
                    'access':str(refresh.access_token),
                    'user_id':user_id,
                    'user_role':user.role,
                    'email':user.email,
                    'username':user.username
                }, status=status.HTTP_200_OK
            )
        return Response({'error':'Invalid information provided'}, status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationOTPVerificationView(APIView):
    @swagger_auto_schema(
        tags=['auth'],
        operation_description="Verify OTP code for new user registration and complete the registration process",
        request_body=UserOTPVerificationSerializer,
        responses={
            200: openapi.Response(
                description="Registration completed successfully",
                examples={
                    "application/json": {
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "user_id": 1,
                        "email": "user@example.com",
                        "username": "username",
                        "message": "Registration completed successfully"
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request",
                examples={
                    "application/json": {
                        "error": "Invalid OTP code"
                    }
                }
            ),
            404: openapi.Response(
                description="User not found",
                examples={
                    "application/json": {
                        "error": "User not found"
                    }
                }
            )
        }
    )
    def post(self, request):
        serializer = UserOTPVerificationSerializer(data=request.data)

        if serializer.is_valid():
            temp_id = serializer.validated_data['user_id']
            entered_otp = serializer.validated_data['otp_code']

            try:
                temp_reg = TemporaryRegistration.objects.get(id=temp_id)
            except TemporaryRegistration.DoesNotExist:
                return Response(
                    {'error': 'Регистрационный запрос не найден'},
                    status=status.HTTP_404_NOT_FOUND
                )

            otp_expiry_minutes = 10
            current_time = timezone.now()

            if temp_reg.otp_created_at and (current_time - temp_reg.otp_created_at).total_seconds() > (otp_expiry_minutes * 60):
                temp_reg.delete()
                return Response(
                    {'error': 'OTP код истек. Пройдите регистрацию заново'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Проверка OTP кода
            if not verifyOTP(entered_otp, temp_reg.otp):
                return Response(
                    {'error': 'Неверный OTP код'},
                    status=status.HTTP_400_BAD_REQUEST
                )


            try:
                if MyUser.objects.filter(email=temp_reg.email).exists():
                    temp_reg.delete()
                    return Response(
                        {'error': 'Пользователь с таким email уже существует'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                user = MyUser(
                    username=temp_reg.username,
                    email=temp_reg.email,
                )
                user.password = temp_reg.password
                user.save()

                temp_reg.delete()

                refresh = RefreshToken.for_user(user)

                return Response(
                    {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        'user_id': user.id,
                        'user_role': user.role,
                        'email': user.email,
                        'username': user.username,
                        'message': 'Регистрация успешно завершена'
                    },
                    status=status.HTTP_200_OK
                )

            except IntegrityError:
                temp_reg.delete()
                return Response(
                    {'error': 'Ошибка создания пользователя. Попробуйте заново'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#MANAGER

class CourierAccountCreationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'manager':
            return Response({'error':'not enough rights'}, status=status.HTTP_403_FORBIDDEN)

        serializer = CourierAccountCreationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):

            courier = MyUser(
                email=serializer.validated_data['email'],
                username=serializer.validated_data['username'],
                phone_number=serializer.validated_data['phone_number'],
                role='courier',
                is_2fa_enabled=False
            )
            courier.set_password(serializer.validated_data['password']),
            courier.save()
            return Response(status=status.HTTP_201_CREATED)


class ProductCreateView(CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreationSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['product'],
        operation_description="Create a new product in the system (manager-only operation).",
        request_body=ProductCreationSerializer,
        responses={
            201: openapi.Response(
                description="Product successfully created",
                examples={
                    "application/json": {
                        "id": 1,
                        "name": "Hamburger",
                        "original_price": "10.00",
                        "discounted_price": "8.99",
                        "category": {"id": 1, "name": "Burgers"},
                        "description": "Delicious hamburger",
                        "image": "http://example.com/media/products/hamburger.jpg",
                        "ingredients": "Beef, lettuce, tomato, sesame bun",
                        "grams": 300,
                        "company": {"id": 1, "name": "FastFoodCo"}
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid input",
                examples={
                    "application/json": {"error": "Invalid input data"}
                }
            ),
            403: openapi.Response(
                description="Permission denied",
                examples={
                    "application/json": {"error": "Not enough rights"}
                }
            )
        },
        security=[{"Bearer": []}]
    )

    def post(self, request):
        if request.user.role != 'manager':
            return Response({'error':'not enough rights'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProductCreationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                product = Product(
                    name=serializer.validated_data['name'],
                    original_price=serializer.validated_data['original_price'],
                    discounted_price=serializer.validated_data['discounted_price'],
                    description=serializer.validated_data['description'],
                    image=serializer.validated_data['image'],
                    category=serializer.validated_data['category'],
                    grams=serializer.validated_data['grams'],
                    ingredients=serializer.validated_data['ingredients'],
                    company=request.user.company
                )
                product.save()
                return Response(ProductCreationSerializer(product).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'error': 'Invalid input'}, status=status.HTTP_400_BAD_REQUEST)


class ProductUpdateView(UpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreationSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['product'],
        operation_description="Update an existing product in the system by ID (manager-only operation).",
        request_body=ProductCreationSerializer,
        responses={
            200: openapi.Response(
                description="Product successfully updated",
                examples={
                    "application/json": {
                        "id": 1,
                        "name": "Updated Hamburger",
                        "original_price": "10.00",
                        "discounted_price": "8.50",
                        "category": {"id": 1, "name": "Burgers"},
                        "description": "Updated description",
                        "image": "http://example.com/media/products/hamburger_updated.jpg",
                        "ingredients": "Beef, lettuce, tomato, sesame bun",
                        "grams": 350,
                        "company": {"id": 1, "name": "FastFoodCo"}
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid input",
                examples={
                    "application/json": {"error": "Invalid input data"}
                }
            ),
            403: openapi.Response(
                description="Permission denied",
                examples={
                    "application/json": {"error": "Not enough rights"}
                }
            ),
            404: openapi.Response(
                description="Product not found",
                examples={
                    "application/json": {"error": "Product not found"}
                }
            )
        },
        security=[{"Bearer": []}]
    )


    def post(self, request):
        if request.user.role != 'manager':
            return Response({'error':'not enough rights'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProductCreationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                product = Product.objects.get(id=serializer.validated_data['id'])
                product.name = serializer.validated_data['name']
                product.original_price = serializer.validated_data['original_price']
                product.discounted_price = serializer.validated_data['discounted_price']
                product.description = serializer.validated_data['description']
                product.image = serializer.validated_data['image']
                product.category = serializer.validated_data['category']
                product.grams = serializer.validated_data['grams']
                product.ingredients = serializer.validated_data['ingredients']
                product.save()
                return Response(ProductCreationSerializer(product).data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'error': 'Invalid input'}, status=status.HTTP_400_BAD_REQUEST)


class ProductDeleteView(DestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreationSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['product'],
        operation_description="Delete an existing product from the system by ID (manager-only operation).",
        manual_parameters=[
            openapi.Parameter(
                name='pk',
                in_=openapi.IN_PATH,
                description='ID of the product to delete',
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description="Product successfully deleted",
                examples={
                    "application/json": {
                        "message": "Product Hamburger successfully deleted."
                    }
                }
            ),
            403: openapi.Response(
                description="Permission denied",
                examples={
                    "application/json": {"error": "Not enough rights"}
                }
            ),
            404: openapi.Response(
                description="Product not found",
                examples={
                    "application/json": {"error": "Product not found."}
                }
            )
        },
        security=[{"Bearer": []}]
    )

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {'message': f'Product {instance.name} successfully deleted.'},
                status=status.HTTP_200_OK
            )
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)




