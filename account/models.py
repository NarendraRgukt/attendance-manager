from django.db import models


import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, username, email,password=None,first_name=None,last_name=None):
        if not email:
            raise ValueError("Please enter the email")
        if not username:
            raise ValueError("please enter username")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email,first_name=first_name,last_name=last_name)
        user.is_active=True
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self,username,email,password=None):
        user=self.create_user(username,email,password)
        user.is_superuser=True
        user.is_staff=True
        user.is_active=True
        user.save(using=self._db)
        return user



class User(AbstractBaseUser, PermissionsMixin):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    username = models.CharField(max_length=245, unique=True)
    email = models.EmailField(max_length=245, unique=True)
    first_name = models.CharField(max_length=245,null=True)
    last_name = models.CharField(max_length=245,null=True)
    is_active=models.BooleanField(default=True)
    is_staff=models.BooleanField(default=False)
    date_joined=models.DateTimeField(auto_now_add=True)
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']


    objects = UserManager()

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.username
