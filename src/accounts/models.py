from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    name = models.CharField(max_length=100)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    email = models.EmailField(
        blank=True,        
        null=True,             
        max_length=254     
    )

    def __str__(self):
        return self.name if self.name else self.username

