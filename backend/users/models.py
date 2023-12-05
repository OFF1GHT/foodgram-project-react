from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

from .constants import MAX_LENGTH, MAX_LENGTH_EMAIL


class CustomUser(AbstractUser):
    username = models.CharField(max_length=MAX_LENGTH, unique=True)
    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL, unique=True, db_index=True
    )
    first_name = models.CharField(max_length=MAX_LENGTH)
    last_name = models.CharField(max_length=MAX_LENGTH)
    password = models.CharField(max_length=MAX_LENGTH)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriber',
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscribing',
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('user', 'author')

    def clean(self):
        if self.user == self.author:
            raise ValidationError(
                "Пользователь не может подписаться на самого себя."
            )
