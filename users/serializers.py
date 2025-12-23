from django.template.defaultfilters import first
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],  # 🔒 проверка сложности пароля
    )

    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "department",
            "position",
            "role"
        ]
        read_only_fields = ["role"]

    def get_role(self, obj):
        if not obj.is_active:
            return "inactive"
        elif obj.is_superuser:
            return "admin"
        elif obj.is_staff:
            return "staff"
        else:
            return "user"

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            department=validated_data.get("department"),
            position=validated_data.get("position"),
            password=validated_data["password"]
        )

        return user


class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "department",
            "position",
            "is_active"
        ]

        extra_kwargs = {
            "email": {"required": False},
            "is_active": {"required": False},
        }

    def validate_email(self, value):
        """Корректная проверка уникальности email при PATCH/PUT."""
        if User.objects.exclude(pk=self.instance.pk).filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value

    def validate(self, attrs):
        """Проверки уровня бизнес-логики для безопасности."""

        request_user = self.context["request"].user  # кто редактирует
        target_user = self.instance  # кого редактируют

        # -------------------------------
        # 1) Staff не может редактировать админов
        # -------------------------------
        if request_user.is_staff and not request_user.is_superuser:
            if target_user.is_superuser:
                raise serializers.ValidationError(
                    "У вас нет прав редактировать администратора."
                )

        # -------------------------------
        # 2) Запрет на самодеактивацию
        # -------------------------------
        if "is_active" in attrs:
            if target_user == request_user and attrs["is_active"] is False:
                raise serializers.ValidationError(
                    "Вы не можете деактивировать сами себя."
                )

        return attrs

class ChangeRoleSerializer(serializers.ModelSerializer):
    # Это единственное поле, которое пользователь (админ) присылает
    role = serializers.ChoiceField(
        choices=["admin", "staff", "user", "inactive"],
        required=True
    )

    def validate(self, attrs):
        new_role = attrs["role"]
        user_to_edit: User = self.context["user_to_edit"]  # человек, которому меняют роль
        acting_user: User = self.context["request"].user  # человек, который делает запрос

        # 1. Обычный пользователь менять роли не может вообще
        if not acting_user.is_staff and not acting_user.is_superuser:
            raise serializers.ValidationError("У вас нет прав менять роли.")

        # 2. staff → не может назначать admin
        if acting_user.is_staff and not acting_user.is_superuser:
            if new_role == "admin":
                raise serializers.ValidationError(
                    "Сотрудник (staff) не может назначить роль admin."
                )

        # 3. Нельзя снять роль admin с самого себя
        if acting_user == user_to_edit and new_role != "admin":
            raise serializers.ValidationError(
                "Администратор не может лишить себя роли admin."
            )

        return attrs

    def save(self, **kwargs):
        new_role = self.validated_data["role"]
        user_to_edit = self.context["user_to_edit"]

        # Меняем реальные поля модели
        if new_role == "inactive":
            user_to_edit.is_active = False
            user_to_edit.is_staff = False
            user_to_edit.is_superuser = False

        elif new_role == "user":
            user_to_edit.is_active = True
            user_to_edit.is_staff = False
            user_to_edit.is_superuser = False

        elif new_role == "staff":
            user_to_edit.is_active = True
            user_to_edit.is_staff = True
            user_to_edit.is_superuser = False

        elif new_role == "admin":
            user_to_edit.is_active = True
            user_to_edit.is_staff = True
            user_to_edit.is_superuser = True

        user_to_edit.save()
        return user_to_edit