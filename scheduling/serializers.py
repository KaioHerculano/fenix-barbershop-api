from rest_framework import serializers

from scheduling.models import Appointment, WorkingHour


class WorkingHourSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingHour
        fields = [
            "id",
            "weekday",
            "start_time",
            "end_time",
        ]


class AvailabilityQuerySerializer(serializers.Serializer):
    date = serializers.DateField()
    barber_id = serializers.UUIDField()
    service_id = serializers.UUIDField()


class AvailabilitySlotSerializer(serializers.Serializer):
    start_time = serializers.CharField()
    end_time = serializers.CharField()


class AppointmentCreateSerializer(serializers.Serializer):
    service_id = serializers.UUIDField()
    barber_id = serializers.UUIDField()
    appointment_date = serializers.DateField()
    start_time = serializers.TimeField()
    notes = serializers.CharField(required=False, allow_blank=True)


class AppointmentRescheduleSerializer(serializers.Serializer):
    appointment_date = serializers.DateField()
    start_time = serializers.TimeField()


class AppointmentSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    barber_name = serializers.CharField(source="barber.user.full_name", read_only=True)
    company_slug = serializers.CharField(source="company.slug", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "company_slug",
            "service",
            "service_name",
            "barber",
            "barber_name",
            "appointment_date",
            "start_time",
            "end_time",
            "status",
            "notes",
            "cancelled_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
