from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        try:

            if isinstance(response.data, dict):
                error_detail = ""

                if 'detail' in response.data:
                    detail = response.data['detail']
                    if isinstance(detail, list):
                        error_detail = " ".join([str(msg) for msg in detail])
                    else:
                        error_detail = str(detail)

                else:
                    messages = []
                    for field, message in response.data.items():
                        if isinstance(message, list):
                            messages.extend([str(m) for m in message])
                        else:
                            messages.append(str(message))
                    error_detail = " ".join(messages)

                response.data['message'] = error_detail

            # Case 2: response.data is a list (e.g., ValidationError with string only)
            elif isinstance(response.data, list):
                error_detail = " ".join([str(item) for item in response.data])
                response.data = {
                    "detail": response.data,
                    "message": error_detail
                }

        except Exception as e:
            response.data = {
                "detail": [str(exc)],
                "message": str(exc)
            }

    return response
