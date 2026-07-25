from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema

from scheduling.serializers import (
    AppointmentCreateSerializer,
    AppointmentRescheduleSerializer,
    AppointmentSerializer,
    AvailabilitySlotSerializer,
)

company_slug_parameter = OpenApiParameter(
    name="company_slug",
    description="Slug publico da barbearia.",
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
    tags=["Agendamento"],
    summary="Listar horarios disponiveis",
    description="Retorna horarios disponiveis para servico, barbeiro e data informados.",
    parameters=[
        company_slug_parameter,
        OpenApiParameter(
            "date",
            str,
            OpenApiParameter.QUERY,
            required=True,
            description="Data desejada no formato YYYY-MM-DD.",
        ),
        OpenApiParameter(
            "barber_id",
            str,
            OpenApiParameter.QUERY,
            required=True,
            description="ID do barbeiro que executara o servico.",
        ),
        OpenApiParameter(
            "service_id",
            str,
            OpenApiParameter.QUERY,
            required=True,
            description="ID do servico desejado.",
        ),
    ],
    responses={200: AvailabilitySlotSerializer(many=True), 400: None, 404: None},
    auth=[],
)

appointment_create_list_schema = extend_schema(
    tags=["Agendamento"],
    summary="Listar ou criar meus agendamentos",
    description="Lista agendamentos do usuario autenticado ou cria um novo agendamento confirmado.",
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
                "notes": "Cliente prefere atendimento rapido.",
            },
            request_only=True,
        )
    ],
)

appointment_detail_schema = extend_schema(
    tags=["Agendamento"],
    summary="Detalhar meu agendamento",
    description="Retorna um agendamento do usuario autenticado.",
    parameters=[company_slug_parameter, appointment_id_parameter],
    responses={200: AppointmentSerializer, 404: None},
)

appointment_cancel_schema = extend_schema(
    tags=["Agendamento"],
    summary="Cancelar meu agendamento",
    description="Cancela um agendamento do usuario autenticado quando o status permite.",
    parameters=[company_slug_parameter, appointment_id_parameter],
    responses={200: AppointmentSerializer, 400: None, 404: None},
)

appointment_reschedule_schema = extend_schema(
    tags=["Agendamento"],
    summary="Reagendar meu agendamento",
    description="Reagenda um compromisso aplicando as mesmas regras de disponibilidade.",
    parameters=[company_slug_parameter, appointment_id_parameter],
    request=AppointmentRescheduleSerializer,
    responses={200: AppointmentSerializer, 400: None, 404: None},
    examples=[
        OpenApiExample(
            "Reagendar",
            value={
                "appointment_date": "2026-07-24",
                "start_time": "10:30",
            },
            request_only=True,
        )
    ],
)

appointment_complete_schema = extend_schema(
    tags=["Agendamento"],
    summary="Concluir agendamento",
    description=(
        "Marca um agendamento como concluido. Apenas owner da empresa ou barbeiro "
        "responsavel podem concluir. A conclusao dispara pontos de fidelidade uma unica vez."
    ),
    parameters=[company_slug_parameter, appointment_id_parameter],
    responses={200: AppointmentSerializer, 400: None, 403: None, 404: None},
)
