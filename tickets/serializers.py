from .models import User, Event, Ticket, Order

from django.utils.timezone import now

from rest_framework import serializers

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["id", "email", "username", "password", "first_name", "last_name"]

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        user.set_password(validated_data["password"])
        user.save()
        return user

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"

    def update(self, instance, validated_data):
        updated_fields = []
        
        if "total_tickets" in validated_data:
            old_total = instance.total_tickets
            new_total = validated_data["total_tickets"]
            ticket_difference = new_total - old_total
            if abs(ticket_difference) < 0:
                raise serializers.ValidationError({"total_tickets": "Total tickets cannot be less than already sold tickets."})
            instance.available_tickets += ticket_difference

        if "date" in validated_data:
            if validated_data["date"].date() < now().date():
                raise serializers.ValidationError({"date": "Event date must be in the future."})

        for attr, value in validated_data.items():
            if getattr(instance, attr) != value: 
                updated_fields.append(attr)
                setattr(instance, attr, value)

        instance.save()

        return instance

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = "__all__"

    def validate(self, data):
        """ Ensure the event has enough available tickets. """
        event = data["event"]
        quantity = data["quantity"]

        if quantity < 1 or quantity > 5:
            raise serializers.ValidationError({"quantity": "You can only reserve between 1 and 5 tickets."})
        
        if event.available_tickets < quantity:
            raise serializers.ValidationError(
                f"Not enough tickets available for event {event.name}."
            )
        return data

class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "status", "created_at", "tickets", "total_price"]

    def get_total_price(self, obj):
        return obj.total_price
    
    def create(self, validated_data):
        """ Create an order and reserve tickets. """
        tickets_data = validated_data.pop("tickets")
        order = Order.objects.create(**validated_data)

        for ticket_data in tickets_data:
            Ticket.objects.create(order=order, **ticket_data)

        return order