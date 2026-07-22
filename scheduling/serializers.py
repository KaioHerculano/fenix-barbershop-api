from rest_framework import serializers

from scheduling.models import WorkingHour


class WorkingHourSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingHour
        fields = [
            "id",
            "weekday",
            "start_time",
            "end_time",
        ]
