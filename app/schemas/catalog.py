from drf_spectacular.utils import OpenApiParameter, extend_schema

from barbers.serializers import BarberSerializer
from scheduling.serializers import WorkingHourSerializer
from services.serializers import ServiceSerializer

company_slug_parameter = OpenApiParameter(
    name="company_slug",
    description="Slug público da barbearia.",
    required=True,
    type=str,
    location=OpenApiParameter.PATH,
)

service_id_parameter = OpenApiParameter(
    name="service_id",
    description="Identificador do serviço.",
    required=True,
    type=str,
    location=OpenApiParameter.PATH,
)

barber_id_parameter = OpenApiParameter(
    name="barber_id",
    description="Identificador do barbeiro.",
    required=True,
    type=str,
    location=OpenApiParameter.PATH,
)

service_list_schema = extend_schema(
    tags=["Catálogo"],
    summary="Listar serviços ativos",
    description="Retorna os serviços ativos disponíveis no catálogo público da barbearia.",
    parameters=[company_slug_parameter],
    responses={200: ServiceSerializer(many=True), 404: None},
    auth=[],
)

service_detail_schema = extend_schema(
    tags=["Catálogo"],
    summary="Detalhar serviço",
    description="Retorna os dados públicos de um serviço ativo da barbearia.",
    parameters=[company_slug_parameter, service_id_parameter],
    responses={200: ServiceSerializer, 404: None},
    auth=[],
)

barber_list_schema = extend_schema(
    tags=["Catálogo"],
    summary="Listar barbeiros ativos",
    description="Retorna os barbeiros ativos vinculados à barbearia.",
    parameters=[company_slug_parameter],
    responses={200: BarberSerializer(many=True), 404: None},
    auth=[],
)

barber_detail_schema = extend_schema(
    tags=["Catálogo"],
    summary="Detalhar barbeiro",
    description="Retorna os dados públicos de um barbeiro ativo da barbearia.",
    parameters=[company_slug_parameter, barber_id_parameter],
    responses={200: BarberSerializer, 404: None},
    auth=[],
)

barber_services_schema = extend_schema(
    tags=["Catálogo"],
    summary="Listar serviços do barbeiro",
    description="Retorna os serviços ativos que o barbeiro executa na barbearia.",
    parameters=[company_slug_parameter, barber_id_parameter],
    responses={200: ServiceSerializer(many=True), 404: None},
    auth=[],
)

working_hour_list_schema = extend_schema(
    tags=["Catálogo"],
    summary="Listar horários de funcionamento",
    description="Retorna os horários ativos de funcionamento da barbearia.",
    parameters=[company_slug_parameter],
    responses={200: WorkingHourSerializer(many=True), 404: None},
    auth=[],
)
