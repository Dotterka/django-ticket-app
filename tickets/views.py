from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated
from .models import User, Event, Ticket, Order
from .serializers import EventSerializer, TicketSerializer, OrderSerializer, RegisterSerializer
from .permissions import IsAdminOrReadOnly
from rest_framework.response import Response
from rest_framework.decorators import action
import random
from django.db import transaction
from rest_framework.exceptions import ValidationError

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

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

                if quantity < 1 or quantity > 5:
                    errors.append({"event": event.name, "error": "Ticket quantity must be between 1 and 5."})
                    continue

                # Check if the user already has a reservation for this event
                existing_ticket = Ticket.objects.filter(order=order, event=event, user=user).first()
 
                if existing_ticket:
                    try:
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
        """ Simulate a payment and confirm or fail the order. """
        order = self.get_object()
        payment_success = random.choice([True, False])

        if payment_success:
            order.confirm_order()
            return Response({"message": "Payment successful, order confirmed!"})
        else:
            order.fail_order()
            return Response({"error": "Payment failed, order cancelled."}, status=status.HTTP_400_BAD_REQUEST)