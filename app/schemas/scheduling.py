from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema

from scheduling.serializers import (
    AppointmentCreateSerializer,
    AppointmentRescheduleSerializer,
    AppointmentSerializer,
    AvailabilitySlotSerializer,
)

company_slug_parameter = OpenApiParameter(
    name="company_slug",
    description="Slug público da barbearia.",
    required=True,
    type=str,
    location=OpenApiParameter.PATH,
)

appointment_id_parameter = OpenApiParameter(
    name="appointment_id",
    description="Identificador do agendamento.",
    required=True,
    type=str,
    location=OpenApiParameter.PATH,
)

availability_schema = extend_schema(
    summary="Listar horários disponíveis",
    description="Retorna os horários disponíveis para serviço, barbeiro e data informados.",
    parameters=[
        company_slug_parameter,
        OpenApiParameter("date", str, OpenApiParameter.QUERY, required=True),
        OpenApiParameter("barber_id", str, OpenApiParameter.QUERY, required=True),
        OpenApiParameter("service_id", str, OpenApiParameter.QUERY, required=True),
    ],
    responses={200: AvailabilitySlotSerializer(many=True), 400: None, 404: None},
    auth=[],
)

appointment_create_list_schema = extend_schema(
    summary="Listar ou criar meus agendamentos",
    description="Lista os agendamentos do usuário autenticado ou cria um novo agendamento confirmado.",
    parameters=[company_slug_parameter],
    request=AppointmentCreateSerializer,
    responses={200: AppointmentSerializer(many=True), 201: AppointmentSerializer},
    examples=[
        OpenApiExample(
            "Criar agendamento",
            value={
                "service_id": "00000000-0000-0000-0000-000000000000",
                "barber_id": "00000000-0000-0000-0000-000000000000",
                "appointment_date": "2026-07-23",
                "start_time": "09:00",
                "notes": "Cliente prefere atendimento rápido.",
            },
            request_only=True,
        )
    ],
)

appointment_detail_schema = extend_schema(
    summary="Detalhar meu agendamento",
    description="Retorna um agendamento do usuário autenticado.",
    parameters=[company_slug_parameter, appointment_id_parameter],
    responses={200: AppointmentSerializer, 404: None},
)

appointment_cancel_schema = extend_schema(
    summary="Cancelar meu agendamento",
    description="Cancela um agendamento do usuário autenticado quando o status permite.",
    parameters=[company_slug_parameter, appointment_id_parameter],
    responses={200: AppointmentSerializer, 400: None, 404: None},
)

appointment_reschedule_schema = extend_schema(
    summary="Reagendar meu agendamento",
    description="Reagenda um compromisso aplicando as mesmas regras de disponibilidade.",
    parameters=[company_slug_parameter, appointment_id_parameter],
    request=AppointmentRescheduleSerializer,
    responses={200: AppointmentSerializer, 400: None, 404: None},
)
