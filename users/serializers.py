from rest_framework import serializers
# from .models import User
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
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