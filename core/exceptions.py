from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Conflit detecte.'
    default_code = 'CONFLICT'


class StatusConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Ce recouvrement a deja ete traite.'
    default_code = 'STATUS_CONFLICT'


def caf_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        error_code = getattr(exc, 'default_code', 'ERROR')
        if isinstance(error_code, str):
            code = error_code.upper()
        else:
            code = 'ERROR'

        if response.status_code == 400:
            code = 'VALIDATION_ERROR'
        elif response.status_code == 401:
            code = 'UNAUTHORIZED'
        elif response.status_code == 403:
            code = 'FORBIDDEN'
        elif response.status_code == 404:
            code = 'NOT_FOUND'

        detail = response.data
        if isinstance(detail, dict) and 'detail' in detail:
            message = str(detail['detail'])
            details = None
        elif isinstance(detail, dict):
            message = 'Erreur de validation'
            details = []
            for field, errors in detail.items():
                if isinstance(errors, list):
                    for err in errors:
                        details.append({'field': field, 'message': str(err)})
                else:
                    details.append({'field': field, 'message': str(errors)})
        elif isinstance(detail, list):
            message = str(detail[0]) if detail else 'Erreur'
            details = None
        else:
            message = str(detail)
            details = None

        error_body = {
            'code': code,
            'message': message,
        }
        if details:
            error_body['details'] = details

        response.data = {'error': error_body}

    return response
