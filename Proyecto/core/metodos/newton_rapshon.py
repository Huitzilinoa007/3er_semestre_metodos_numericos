# Alias de compatibilidad: tu archivo original se llamaba `newton_rapshon.py` (con la errata).
# Se deja para que cualquier import viejo siga funcionando; el código real está en newton_raphson.py.
from .newton_raphson import raiz_newton  # noqa: F401
