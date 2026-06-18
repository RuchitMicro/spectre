from rest_framework                         import  serializers
from rest_framework_simplejwt.serializers   import  TokenObtainPairSerializer
from rest_framework                         import  serializers

from django.db                              import  transaction
from django.core.mail                       import  send_mail
from django.conf                            import  settings
from django.utils.http                      import  urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding                  import  force_bytes, force_str
from django.contrib.auth.tokens             import  default_token_generator

from rest_framework.exceptions              import  ValidationError

from .models                                import  Profile

from django.contrib.auth                    import  get_user_model
User = get_user_model()




class UserRegistrationSerializer(serializers.ModelSerializer):
    password        = serializers.CharField(write_only=True)

    class Meta:
        model   = User
        fields  = (
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
        )

    @transaction.atomic
    def create(self, validated_data):
        password     = validated_data.pop('password')

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        # Update profile created by signal
        profile = user.profile
        profile.save()

        return user
    

class ProfileUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False)

    class Meta:
        model = Profile
        fields = [
            "first_name",
            "last_name",
            "email",
        ]

    def validate_email(self, value):
        user = self.instance.user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        user = instance.user

        user.first_name = validated_data.get("first_name", user.first_name)
        user.last_name = validated_data.get("last_name", user.last_name)
        user.email = validated_data.get("email", user.email)
        user.save()

        instance.save()

        return instance
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom data to the token response
        data.update({'user_id': self.user.id})
        data.update({'username': self.user.username})
        data.update({'email': self.user.email})

        return data

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise ValidationError("User with this email does not exist.")
        return value

    def save(self):
        user = User.objects.get(email=self.validated_data['email'])
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
        send_mail(
            'Password Reset Request',
            f'Click the link to reset your password: {reset_link}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            uid = force_str(urlsafe_base64_decode(data['uid']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise ValidationError('Invalid UID')

        if not default_token_generator.check_token(user, data['token']):
            raise ValidationError('Invalid token')

        return data

    def save(self):
        uid = force_str(urlsafe_base64_decode(self.validated_data['uid']))
        user = User.objects.get(pk=uid)
        user.set_password(self.validated_data['new_password'])
        user.save()

