
from django.utils.timezone import now, timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator

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
    ticket_price = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=10)
    total_tickets = models.PositiveIntegerField()
    available_tickets = models.PositiveIntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """ Ensure available tickets match total tickets on creation. """
        if not self.pk:
            self.available_tickets = self.total_tickets
        super().save(*args, **kwargs)

    def reserve_tickets(self, quantity):
        """ Temporarily reduce available tickets when a user selects tickets. """
        if self.available_tickets >= quantity:
            self.available_tickets -= quantity
            self.save()
        else:
            raise ValueError("Not enough tickets available")

    def release_tickets(self, quantity):
        """ Restore available tickets if order expires or fails. """
        self.available_tickets += quantity
        self.save()

    def __str__(self):
        return self.name

class Ticket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="tickets")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    def save(self, *args, **kwargs):
        """ Adjust ticket availability correctly when updating a reservation. """
        if self.pk:  # If updating an existing ticket
            old_quantity = Ticket.objects.get(pk=self.pk).quantity

            if old_quantity != self.quantity:
                if (self.event.available_tickets + old_quantity) - self.quantity >= 0:
                    self.event.release_tickets(old_quantity)
                    self.event.reserve_tickets(self.quantity)
                else:
                    raise ValueError(f"Not enough tickets available for event {self.event.name}.")
        else:
            self.event.reserve_tickets(self.quantity)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Increase available tickets and delete order if it's empty."""
        order = self.order
        event = self.event

        # Increase available tickets before deleting the ticket
        event.release_tickets(self.quantity)

        super().delete(*args, **kwargs)

        # Check if there are any tickets left in the order
        if not order.tickets.exists():
            order.delete()

    def __str__(self):
        return f"Ticket for {self.event.name} - {self.user.email}"

class Order(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 1, "Pending"
        CONFIRMED = 2, "Confirmed"
        FAILED = 3, "Failed"
        EXPIRED = 4, "Expired"
        REFUND = 5, "Refund"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    status = models.IntegerField(choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    @property
    def total_price(self):
        """Calculate the total price of all tickets in the order."""
        return sum(ticket.event.ticket_price * ticket.quantity for ticket in self.tickets.all())

    def save(self, *args, **kwargs):
        """ Set expiration to 15 minutes from creation. """
        if not self.pk:
            self.expires_at = now() + timedelta(minutes=15)
        super().save(*args, **kwargs)

    def confirm_order(self):
        """ Finalize ticket purchase when payment is successful. """
        self.status = self.Status.CONFIRMED
        self.save()

    def fail_order(self):
        """ Restore tickets if payment fails. """
        for ticket in self.tickets.all():
            ticket.event.release_tickets(ticket.quantity)
        self.status = self.Status.FAILED
        self.tickets.all().delete()
        self.save()

    def expire_order(self):
        """ Restore tickets if order expires. """
        if self.status == self.Status.PENDING and now() >= self.expires_at:
            self.fail_order()
            self.status = self.Status.EXPIRED
            self.save()

    def refund_order(self):
        """ Restore tickets if order is deleted. """
        if self.status == self.Status.CONFIRMED:
            self.fail_order()
            self.status = self.Status.REFUND
            self.save()

    def __str__(self):
        return f"Order {self.id} - {self.user.email} - {self.get_status_display()}"
