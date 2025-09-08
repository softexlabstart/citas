class SedeFilteredMixin:
    """
    A mixin to filter a queryset by 'sede_id' from query parameters.
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        sede_id = self.request.query_params.get('sede_id')
        if sede_id:
            queryset = queryset.filter(sede_id=sede_id)
        return queryset