class ResolverError(Exception):
    """Error base para resolvers de IDs."""
    pass


class EntityNotFoundError(ResolverError):
    """La entidad solicitada no existe."""
    pass


class MultipleEntitiesFoundError(ResolverError):
    """La búsqueda no es suficientemente específica."""
    pass
