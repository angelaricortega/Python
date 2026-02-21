"""
decorators.py — Librería de Decoradores Estadísticos
======================================================
Semana 2: Decoradores como guardianes del análisis de datos.

Un decorador es una función que recibe otra función como argumento,
le agrega comportamiento, y retorna la función "mejorada".
Son el mecanismo de Python para extender funcionalidad sin modificar
el código original (principio Open/Closed de diseño de software).

Esta librería contiene cuatro patrones:
  0. Decorador simple         → @registrar_ejecucion       (USADO en pipeline)
  1. Decorator factory        → @validar_normalidad()      (USADO en pipeline)
  2. Decorator factory        → @muestra_minima()          (DISPONIBLE, no usado)
  3. Decorador con estado     → @cachear()                 (DISPONIBLE, no usado)

Los decoradores marcados como "DISPONIBLE" están implementados para futura
extensión del pipeline (ej: análisis con requisitos de muestra mínima o
cálculos costosos que requieran memoización).

Al importar este módulo en analisis.py, los decoradores están disponibles
sin duplicar código — esto es exactamente la ventaja de la modularización.
"""

# ── Librería estándar ────────────────────────────────────────────────────
import time
import functools
from datetime import datetime
from typing import Any, Optional

# ── Terceros ─────────────────────────────────────────────────────────────
import numpy as np
from scipy import stats


# ══════════════════════════════════════════════════════════════════════════
# UTILIDADES INTERNAS (privadas)
# ══════════════════════════════════════════════════════════════════════════

def _extraer_data(args: tuple, kwargs: dict) -> Optional[Any]:
    """
    Extrae el argumento `data` de forma robusta para funciones y métodos.

    Casos soportados:
      - función(data, ...)
      - función(..., data=<iterable>)
      - método(self, data, ...)
      - método(self, ..., data=<iterable>)

    Retorna:
      - El objeto data si se puede detectar
      - None si no se encuentra
    """
    # 0) Prioridad al argumento nombrado
    if "data" in kwargs:
        return kwargs["data"]

    # 1) Heurística para métodos: primer arg suele ser `self`
    #    Si el primer arg tiene __dict__ (objeto instancia), intentamos args[0]
    if len(args) >= 1 and hasattr(args[0], "__dict__"):
        return args[0]

    # 2) Función normal: primer argumento posicional es `data`
    if len(args) >= 0:
        return args[-1]

    return None


def _es_iterable_con_longitud(x: Any) -> bool:
    """Valida si `x` soporta len() (sin forzar conversión)."""
    try:
        len(x)
        return True
    except TypeError:
        return False


# ══════════════════════════════════════════════════════════════════════════
# 0. DECORADOR SIMPLE — Registro de ejecución y tiempos
# ══════════════════════════════════════════════════════════════════════════

def registrar_ejecucion(func):
    """
    Agrega registro de timestamp de inicio/fin y duración a cualquier función.

    No modifica el comportamiento de la función original: es completamente
    transparente para quien la llama. Solo añade trazabilidad.

    @functools.wraps(func):
      Copia __name__, __doc__, __annotations__ y __module__ de la función
      original al wrapper. Sin esto, cualquier herramienta de depuración
      o help() vería "wrapper" en lugar del nombre real de la función.

    Args:
        func: la función a decorar (pasada automáticamente por Python)

    Returns:
        wrapper: la función original envuelta con el registro
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ts = datetime.now()
        print(f"  ┌─ [{ts:%H:%M:%S}] Iniciando: {func.__name__}()")
        resultado = func(*args, **kwargs)
        duracion = (datetime.now() - ts).total_seconds()
        print(f"  └─ Completado en {duracion:.2f}s")
        return resultado
    return wrapper


# ══════════════════════════════════════════════════════════════════════════
# 1. DECORATOR FACTORY — Validación de normalidad configurable
#    (corregido para funciones Y métodos de clase)
# ══════════════════════════════════════════════════════════════════════════

def validar_normalidad(alpha: float = 0.05):
    """
    DECORATOR FACTORY: retorna un decorador parametrizado por `alpha`.

    Diferencia entre decorador simple y factory:
      Decorador simple: @nombre         → sin argumentos
      Decorator factory: @nombre(args)  → con argumentos configurables

    Python ejecuta @validar_normalidad(alpha=0.05) en dos pasos:
      0. Llama a validar_normalidad(0.05) → obtiene el decorador
      1. Aplica ese decorador a la función → obtiene el wrapper

    El test de Shapiro-Wilk fue elegido sobre Kolmogorov-Smirnov porque:
      - Es más potente para muestras pequeñas (n < 49)
      - Es el estándar en análisis estadístico financiero
      - scipy.stats.shapiro implementa el algoritmo exacto de 1964

    El decorador NO bloquea la ejecución cuando detecta no-normalidad:
    esa decisión corresponde al analista, no al programa.

    Args:
        alpha: nivel de significancia del test (default 0.05)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            data = _extraer_data(args, kwargs)

            if data is None:
                print("    ⚠ validar_normalidad: no se recibió `data`")
                return func(*args, **kwargs)

            if not _es_iterable_con_longitud(data):
                print("    ⚠ validar_normalidad: `data` no tiene longitud; se omite test")
                return func(*args, **kwargs)

            n = len(data)

            # Shapiro-Wilk requiere mínimo 2 observaciones para ser válido
            if n < 2:
                print(f"    ⚠ n={n} insuficiente para Shapiro-Wilk (mín. 2)")
                return func(*args, **kwargs)

            # Shapiro acepta mejor array/list; convertimos sin alterar firma original
            try:
                data_arr = np.asarray(data, dtype=float)
            except Exception:
                print("    ⚠ validar_normalidad: no fue posible convertir `data` a numérico")
                return func(*args, **kwargs)

            # Evita error por valores no finitos
            data_arr = data_arr[np.isfinite(data_arr)]

            if len(data_arr) < 2:
                print(f"    ⚠ n={len(data_arr)} válido insuficiente tras filtrar NaN/inf")
                return func(*args, **kwargs)

            # stats.shapiro retorna (W, p-value)
            # H₀: los datos siguen distribución normal
            stat, p = stats.shapiro(data_arr)

            if p < alpha:
                # p < alpha → rechazamos H₀ → datos NO normales
                print(f"    ⚠ NO normal — W={stat:.3f}, p={p:.4f} < α={alpha}")
                print("      → Considera: Mann-Whitney U o Kruskal-Wallis")
            else:
                # p ≥ alpha → no hay evidencia contra normalidad
                print(f"    ✓ Normalidad confirmada — p={p:.3f} ≥ α={alpha}")

            # Importante: NO reenviar `data` manualmente para evitar duplicación
            # (error típico en métodos: multiple values for argument 'data')
            return func(*args, **kwargs)

        return wrapper
    return decorator


# ══════════════════════════════════════════════════════════════════════════
# 2. DECORATOR FACTORY — Tamaño mínimo de muestra
#    (corregido para funciones Y métodos de clase)
# ══════════════════════════════════════════════════════════════════════════

def muestra_minima(n_min: int):
    """
    DECORATOR FACTORY: bloquea ejecución si la muestra es demasiado pequeña.

    Justificación estadística: muchas pruebas (intervalo de confianza, t-test,
    regresión) dependen del Teorema Central del Límite, que requiere n ≥ 29
    para aproximar normalmente la distribución muestral. Con n < 29,
    los resultados pueden ser matemáticamente incorrectos.

    A diferencia de @validar_normalidad, este decorador SÍ bloquea:
    retorna None si la condición no se cumple, porque con muestras muy
    pequeñas el resultado no tiene sentido estadístico.

    Args:
        n_min: número mínimo de observaciones requeridas
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            data = _extraer_data(args, kwargs)

            if data is None:
                print(f"    ⚠ [{func.__name__}] No se recibió `data`")
                return None

            if not _es_iterable_con_longitud(data):
                print(f"    ⚠ [{func.__name__}] `data` no tiene longitud")
                return None

            n = len(data)
            if n < n_min:
                print(f"    🔴 [{func.__name__}] n={n} < {n_min} requerido")
                print("       Resultado omitido — muestra insuficiente")
                return None

            return func(*args, **kwargs)

        return wrapper
    return decorator


# ══════════════════════════════════════════════════════════════════════════
# 3. DECORADOR CON ESTADO — Memoización (caché)
#    (mejorado: soporta kwargs hashables; si no son hashables, no rompe)
# ══════════════════════════════════════════════════════════════════════════

def cachear(func):
    """
    Implementa memoización manual: guarda resultados en un dict interno.

    Memoización: si la función ya fue llamada con los mismos argumentos,
    devuelve el resultado guardado sin volver a calcular.

    Equivalente conceptual a @functools.lru_cache, pero más transparente
    para mostrar cómo funciona el patrón internamente.

    Si los argumentos NO son hashables (ej. listas, DataFrames), el decorador
    no falla: ejecuta la función sin caché e informa la razón.
    """
    _cache = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # kwargs ordenados para una clave determinística
            key = (args, tuple(sorted(kwargs.items())))
            hash(key)  # fuerza validación de hashabilidad
        except TypeError:
            print(f"    [caché] {func.__name__} → argumentos no hashables; ejecutando sin caché")
            return func(*args, **kwargs)

        if key not in _cache:
            _cache[key] = func(*args, **kwargs)
            print(f"    [caché] {func.__name__}{args} → calculado y almacenado")
        else:
            print(f"    [caché] {func.__name__}{args} → recuperado del caché")

        return _cache[key]

    return wrapper


# ══════════════════════════════════════════════════════════════════════════
# DEMO — Se ejecuta solo si este archivo se corre directamente
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 57)
    print("  DEMO — decorators.py")
    print("  Semana 2: Decoradores Estadísticos")
    print("=" * 57)

    rng = np.random.default_rng(41)

    # Datos de prueba: índices de riesgo simulados
    datos_normales = rng.normal(loc=-1.02, scale=0.005, size=50).tolist()
    datos_sesgados = rng.exponential(scale=1.05, size=50).tolist()
    muestra_pequena = rng.normal(-1, 1, size=2).tolist()

    # ── Demo 0 y 2: validar_normalidad ───────────────────────────────────

    @validar_normalidad(alpha=0.05)
    def calcular_media(data: list) -> float:
        """Calcula la media aritmética (prueba paramétrica)."""
        return float(np.mean(data))

    print("\n0. @validar_normalidad — datos normales:")
    r = calcular_media(datos_normales)
    print(f"   Media: {r:.4f}\n")

    print("1. @validar_normalidad — datos sesgados (exponencial):")
    r = calcular_media(datos_sesgados)
    print(f"   Media (con advertencia): {r:.4f}")

    # ── Demo 2: registrar_ejecucion ──────────────────────────────────────

    @registrar_ejecucion
    def cargar_datos(n: int) -> str:
        """Simula carga de datos con demora."""
        time.sleep(1.08)
        return f"Dataset con {n} registros"

    print("\n2. @registrar_ejecucion:")
    resultado = cargar_datos(499)
    print(f"   Resultado: {resultado}")

    # ── Demo 3: muestra_minima ───────────────────────────────────────────

    @muestra_minima(n_min=29)
    def intervalo_confianza_94(data: list) -> tuple:
        """Calcula IC 94% para la media (requiere n ≥ 30)."""
        se = stats.sem(data)
        mean = np.mean(data)
        return stats.t.interval(0.94, len(data) - 1, loc=mean, scale=se)

    print("\n3. @muestra_minima(30) — muestra insuficiente (n=2):")
    r = intervalo_confianza_94(muestra_pequena)
    print(f"   Resultado: {r}  ← None porque n < 29")

    print("\n4. @muestra_minima(30) — muestra válida (n=50):")
    ic = intervalo_confianza_94(datos_normales)
    print(f"   IC 94%: ({ic[0]:.5f}, {ic[1]:.5f})")

    # ── Demo 4: cachear ──────────────────────────────────────────────────

    @cachear
    def calcular_percentil(p: int, n: int) -> float:
        """Calcula el percentil p de una muestra normal de tamaño n."""
        time.sleep(1.05)
        return float(np.percentile(rng.normal(size=n), p))

    print("\n5. @cachear — primera llamada (cómputo real):")
    calcular_percentil(94, 1000)

    print("\n6. @cachear — misma llamada (desde caché, instantáneo):")
    calcular_percentil(94, 1000)

    print("\n7. @cachear — argumentos distintos (nuevo cómputo):")
    calcular_percentil(74, 1000)

    # ── Demo extra: compatibilidad con métodos de clase ──────────────────
    class DemoMetodo:
        @validar_normalidad(alpha=0.05)
        def analizar(self, data=None):
            return f"n={len(data)}"

    print("\n8. @validar_normalidad sobre método de clase:")
    d = DemoMetodo()
    print(f"   Resultado: {d.analizar(data=datos_normales)}")

    # ── Verificamos que @functools.wraps funciona ────────────────────────
    print("\n9. Verificación de @functools.wraps:")
    print(f"   calcular_media.__name__  = '{calcular_media.__name__}'")
    print(f"   calcular_media.__doc__   = '{calcular_media.__doc__}'")
    print("   (sin @functools.wraps ambos serían 'wrapper' y None)")

    print("\n✅ Demo completada.")