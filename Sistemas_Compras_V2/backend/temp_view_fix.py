    def get_permissions(self):
        # Temporarily allow any authenticated user to create a solicitacao
        return [permissions.IsAuthenticated()]
