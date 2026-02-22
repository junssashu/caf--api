from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, telephone, password=None, **extra_fields):
        if not telephone:
            raise ValueError('Le numero de telephone est requis.')
        user = self.model(telephone=telephone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, telephone, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('nom', 'Super Admin')
        return self.create_user(telephone, password, **extra_fields)
