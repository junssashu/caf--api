from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CAFPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'pageSize'
    page_query_param = 'page'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'data': data,
            'total': self.page.paginator.count,
            'page': self.page.number,
            'pageSize': self.get_page_size(self.request),
        })
