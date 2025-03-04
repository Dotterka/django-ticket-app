
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(_('email address'), unique=True)
    native_name = models.CharField(max_length=50)
    phone_no = models.CharField(max_length=15, blank=True, null=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    # Avoid conflicts with Django's default User model
    groups = models.ManyToManyField(
        "auth.Group", related_name="custom_user_set", blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission", related_name="custom_user_permissions_set", blank=True
    )

    def __str__(self):
        return self.username


class Event(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    date = models.DateTimeField()
    location = models.CharField(max_length=100)
    available_tickets = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Ticket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="tickets")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")

    def __str__(self):
        return f"Ticket for {self.event.name} - {self.user.email}"


class Order(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 1, "Pending"
        CONFIRMED = 2, "Confirmed"
        FAILED = 3, "Failed"
        EXPIRED = 4, "Expired"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    status = models.IntegerField(choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.email} - {self.get_status_display()}"
