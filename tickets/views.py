import random
import requests

from .models import User, Event, Ticket, Order
from .serializers import EventSerializer, TicketSerializer, OrderSerializer, RegisterSerializer
from .permissions import IsAdminOrReadOnly, IsAdminOrOwner, OnlyGetMethod, DisableMethodsPermission

from django.db import transaction

from rest_framework import viewsets, generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAdminOrReadOnly]

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwner, OnlyGetMethod]

    def get_queryset(self):
        """Admins see all tickets, regular users see only their own."""
        user = self.request.user

        if user.is_staff:
            return Ticket.objects.all()
        return Ticket.objects.filter(user=user)
    

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwner, DisableMethodsPermission]

    def get_queryset(self):
        """Ensure users can only see their own orders unless they are admin."""
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)
    
    @action(detail=False, methods=["post"])
    def reserve(self, request):
        """ Reserve tickets and create/update an order. """
        user = request.user
        tickets_data = request.data.get("tickets", [])

        if not tickets_data:
            return Response({"error": "No tickets provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Find or create a pending order
        order = Order.objects.filter(user=user, status=Order.Status.PENDING).first()
        if not order:
            order = Order.objects.create(user=user)

        valid_tickets = []
        errors = []

        with transaction.atomic():
            for ticket_data in tickets_data:
                try:
                    event = Event.objects.get(id=ticket_data["event"])
                except Event.DoesNotExist:
                    errors.append({"event_id": ticket_data["event"], "error": "Event not found."})
                    continue

                quantity = ticket_data["quantity"]

                # Check if the user already has a reservation for this event
                existing_ticket = Ticket.objects.filter(order=order, event=event, user=user).first()
                if existing_ticket:
                    if quantity == 0:
                        existing_ticket.delete()
                        if not order.tickets.exists():  # Order was also deleted
                            return Response({"message": "Order deleted because no tickets were left."}, status=status.HTTP_204_NO_CONTENT)
                        return Response({"message": "Ticket deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
                    else:
                        try:
                            if quantity < 1 or quantity > 5:
                                errors.append({"event": event.name, "error": "Ticket quantity must be between 1 and 5."})
                                continue
                            existing_ticket.quantity = quantity
                            existing_ticket.save()
                            valid_tickets.append(existing_ticket)
                        except ValueError as e:
                            errors.append({"event": event.name, "error": str(e)})
                else:
                    ticket_data["order"] = order.id
                    ticket_data["user"] = user.id
                    serializer = TicketSerializer(data=ticket_data)

                    try:
                        serializer.is_valid(raise_exception=True)
                        ticket = serializer.save()
                        valid_tickets.append(ticket)
                    except ValidationError as e:
                        errors.append({"event": event.name, "error": e.detail})

        if valid_tickets:
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": "All reservations failed.", "details": errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def purchase(self, request, pk=None):
        """Call the internal payment API and confirm or fail the order."""
        order = self.get_object()
        if order.status != Order.Status.PENDING:
            return Response(
                {"error": "Order is not pending, cannot process payment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment_api_url = "http://localhost:8000/api/payments/"
            response = requests.get(payment_api_url)
            response_data = response.json()

            if response.status_code == 200 and response_data.get("result"):
                order.confirm_order()
                return Response({"message": "Payment successful, order confirmed!"}, status=status.HTTP_200_OK)
            else:
                order.fail_order()
                return Response(
                    {"error": "Payment failed, order cancelled.", "details": response_data},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except requests.RequestException as e:
            return Response(
                {"error": "Payment service unavailable. Please try again later.", "details": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @action(detail=True, methods=["delete"])
    def cancel(self, request, pk=None):
        """ Cancel an order (delete). """
        order = self.get_object()

        if order.status != Order.Status.CONFIRMED:
            return Response({"error": "Only confirmed orders can be canceled."}, status=status.HTTP_400_BAD_REQUEST)

        order.refund_order()

        return Response({"message": "Order canceled and tickets refunded."}, status=status.HTTP_200_OK)


class PaymentViewSet(APIView):
    """Handles payment processing"""

    def get(self, *args, **kwargs):
        """Simulate payment processing and return success or failure."""
        result = random.choice([True, False])
        return Response({"result": result}, status=status.HTTP_200_OK)       
