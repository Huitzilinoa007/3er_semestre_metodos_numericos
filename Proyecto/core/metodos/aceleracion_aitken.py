# Aceleración de Aitken (Δ²): con tres términos seguidos de una sucesión estima hacia dónde converge,
# y llega mucho más rápido que la sucesión original.
def aceleracion_aitken(x0, x1, x2):
    denominador = x2 - 2 * x1 + x0

    # Aquí se protege la división: si el denominador es casi cero la fórmula se vuelve inestable.
    if abs(denominador) < 1e-14:
        raise ValueError("El denominador es demasiado cercano a cero. Inestabilidad numérica detectada.")

    # Fórmula de Aitken: x0 - (x1 - x0)^2 / (x2 - 2*x1 + x0)
    return x0 - ((x1 - x0) ** 2) / denominador
