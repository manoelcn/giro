from rest_framework.response import Response
from rest_framework.views import exception_handler

from core.domain.exceptions import GiroException


STATUS_ERRORS = {
    400: ('VALIDATION_ERROR', 'Dados inválidos.'),
    401: ('AUTHENTICATION_REQUIRED', 'Autenticação necessária.'),
    403: ('ACCESS_DENIED', 'Acesso negado.'),
    404: ('NOT_FOUND', 'Recurso não encontrado.'),
}


def giro_exception_handler(exc, context):
    if isinstance(exc, GiroException):
        data = {'code': exc.code, 'detail': exc.detail}
        if exc.fields:
            data['fields'] = exc.fields
        return Response(data, status=exc.status_code)

    response = exception_handler(exc, context)
    if response is None:
        return None

    code, detail = STATUS_ERRORS.get(
        response.status_code,
        ('REQUEST_FAILED', 'Não foi possível concluir a solicitação.'),
    )
    data = {'code': code, 'detail': detail}
    if response.status_code == 400:
        fields = response.data
        data['fields'] = fields if isinstance(fields, dict) else {'non_field_errors': fields}
    response.data = data
    return response
