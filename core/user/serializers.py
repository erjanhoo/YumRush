from .models import MyUser, Transactions
from order.models import Delivery
from product.models import Product
from rest_framework import serializers
from decimal import Decimal


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ('username', 'email', 'password')


    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        return value

    def validate_email(self, value):
        if MyUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value


    def create(self, validated_data):
        user = MyUser(**validated_data)

        user.set_password(validated_data['password'])
        user.save()

        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserOTPVerificationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    otp_code = serializers.CharField(max_length=6, min_length=6)


class UserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = MyUser
        fields = ('id', 'username', 'email', 'phone_number', 'avatar', 'address', 'is_2fa_enabled', 'created_date', 'role', 'balance')

    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ('username', 'email', 'phone_number', 'avatar', 'address', 'is_2fa_enabled')
        read_only_fields = ('email', )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.avatar:
            request = self.context.get('request')
            if request:
                representation['avatar'] = request.build_absolute_uri(instance.avatar.url)
            else:
                representation['avatar'] = instance.avatar.url
        else:
            representation['avatar'] = None
        return representation


class UserBalanceTopUpSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))

class UserTransactionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Transactions
        fields = ('id', 'user', 'amount', 'date')


class UserDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = '__all__'


#MANAGER
class CourierAccountCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ('username', 'email', 'password', 'phone_number', )


class ProductCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('name', 'original_price', 'discounted_price', 'category', 'description', 'image', 'ingredients', 'grams')


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        return value


class ChangeEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate_new_email(self, value):
        if MyUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use")
        return value


class ChangeUsernameSerializer(serializers.Serializer):
    new_username = serializers.CharField(required=True, max_length=255)
    password = serializers.CharField(write_only=True, required=True)


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)






