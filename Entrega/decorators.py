"""
decorators.py — Librería de Decoradores Estadísticos
======================================================
Semana 1: Decoradores como guardianes del análisis de datos.

CONCEPTO CLAVE:
Un decorador es una función que recibe otra función como argumento,
le agrega comportamiento, y retorna la función "mejorada".
Son el mecanismo de Python para extender funcionalidad sin modificar
el código original (principio Open/Closed de diseño de software).

ANALOGÍA ESTADÍSTICA:
Piense en un decorador como una función de verosimilitud L(θ|x):
  - La función original = el núcleo del modelo estadístico
  - El decorador = el contexto que asigna condiciones de aplicación

TIPOS DE DECORADORES EN ESTE MÓDULO:
  0. Decorador simple         → @registrar_ejecucion       (USADO en pipeline)
  1. Decorator factory        → @validar_normalidad()      (USADO en pipeline)
  2. Decorator factory        → @muestra_minima()          (DISPONIBLE)
  3. Decorador con estado     → @cachear()                 (DISPONIBLE)
  4. Decorador para métodos   → @validar_datos_df()        (NUEVO para clase)

POR QUÉ @functools.wraps:
  Sin él, la función decorada pierde su nombre y docstring.
  help(func_decorada) mostraría "wrapper" en lugar del nombre real.
  Esto rompe depuración, logging e introspección.
"""

# ── Librería estándar ────────────────────────────────────────────────────
import time
import functools
from datetime import datetime
from typing import Any, Optional, Callable
import inspect

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
      - método(self, df=DataFrame) → extrae columna por nombre

    Retorna:
      - El objeto data si se puede detectar
      - None si no se encuentra
    """
    # 0) Prioridad al argumento nombrado
    if "data" in kwargs:
        return kwargs["data"]

    # 1) Heurística para métodos: primer arg suele ser `self`
    #    Si el primer arg tiene __dict__ (objeto instancia), intentamos extraer
    if len(args) >= 1 and hasattr(args[0], "__dict__"):
        self_obj = args[0]
        # Intentar obtener desde self.df["indice_riesgo"] o similar
        df_attr = getattr(self_obj, "df", None)
        if df_attr is not None:
            # Es un DataFrame, intentar columna por defecto
            if hasattr(df_attr, "columns"):
                if "indice_riesgo" in df_attr.columns:
                    return df_attr["indice_riesgo"].dropna()
                elif len(df_attr.columns) > 0:
                    return df_attr.iloc[:, 0].dropna()
        # Si no hay DataFrame, retornar el primer arg si es iterable
        if _es_iterable_con_longitud(args[0]):
            return args[0]

    # 2) Función normal: primer argumento posicional es `data`
    if len(args) >= 1:
        return args[0]

    return None


def _extraer_df_de_self(args: tuple) -> Optional[Any]:
    """
    Extrae self.df desde el primer argumento (self) si es un objeto con atributo df.
    Usado para decoradores que necesitan validar el DataFrame completo.
    """
    if len(args) >= 1 and hasattr(args[0], "__dict__"):
        return getattr(args[0], "df", None)
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

def registrar_ejecucion(func: Callable) -> Callable:
    """
    DECORADOR SIMPLE: Agrega registro de timestamp de inicio/fin y duración.

    CONCEPTO:
      Un decorador simple NO recibe argumentos. Se aplica como @nombre.
      Python pasa la función automáticamente como argumento.

    POR QUÉ @functools.wraps(func):
      Copia __name__, __doc__, __annotations__ y __module__ de la función
      original al wrapper. Sin esto:
        - help(func_decorada) → muestra "wrapper" en lugar del nombre real
        - __doc__ → None (pierde documentación)
        - Depuración → más difícil (no sabe qué función se está ejecutando)

    APLICACIÓN EN ESTE PROYECTO:
      Se usa en TODOS los métodos del pipeline para:
        - Saber cuándo inicia cada etapa
        - Medir cuánto tarda el EDA, la limpieza, etc.
        - Trazabilidad completa del análisis

    Args:
        func: la función a decorar (pasada automáticamente por Python)

    Returns:
        wrapper: la función original envuelta con el registro
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        ts = datetime.now()
        print(f"  >> [{ts:%H:%M:%S}] Iniciando: {func.__name__}()")
        resultado = func(*args, **kwargs)
        duracion = (datetime.now() - ts).total_seconds()
        print(f"  << Completado en {duracion:.2f}s")
        return resultado
    return wrapper


# ══════════════════════════════════════════════════════════════════════════
# 1. DECORATOR FACTORY — Validación de normalidad configurable
# ══════════════════════════════════════════════════════════════════════════

def validar_normalidad(alpha: float = 0.05):
    """
    DECORATOR FACTORY: retorna un decorador parametrizado por `alpha`.

    DIFERENCIA entre decorador simple y factory:
      Decorador simple:    @nombre         → sin argumentos
      Decorator factory:   @nombre(args)   → con argumentos configurables

    CÓMO FUNCIONA (Python ejecuta en 2 pasos):
      0. Llama a validar_normalidad(0.05) → obtiene el decorador interno
      1. Aplica ese decorador a la función → obtiene el wrapper final

    TEST DE SHAPIRO-WILK:
      - H₀: los datos siguen distribución normal
      - H₁: los datos NO siguen distribución normal
      - Si p < α → rechazamos H₀ → datos NO normales
      - Si p ≥ α → no hay evidencia contra normalidad

      Por qué Shapiro-Wilk y no Kolmogorov-Smirnov:
        - Más potente para muestras pequeñas (n < 49)
        - Es el estándar en análisis estadístico financiero
        - scipy.stats.shapiro implementa el algoritmo exacto de 1964

    EL DECORADOR NO BLOQUEA:
      Cuando detecta no-normalidad, solo imprime advertencia.
      La decisión de usar tests paramétricos o no-paramétricos
      corresponde al analista, no al programa.

    Args:
        alpha: nivel de significancia del test (default 0.05)
               α = 0.05 → 95% confianza
               α = 0.01 → 99% confianza (más estricto)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Intentar extraer data desde args/kwargs
            data = _extraer_data(args, kwargs)

            # Si no hay data, intentar extraer desde self.df
            if data is None:
                data = _extraer_df_de_self(args)
                if data is not None and hasattr(data, "columns"):
                    # Es DataFrame, extraer columna numérica
                    if "indice_riesgo" in data.columns:
                        data = data["indice_riesgo"].dropna()
                    elif len(data.columns) > 0:
                        # Usar primera columna numérica
                        for col in data.columns:
                            if np.issubdtype(data[col].dtype, np.number):
                                data = data[col].dropna()
                                break

            if data is None:
                print("    ⚠ validar_normalidad: no se recibió `data`")
                return func(*args, **kwargs)

            if not _es_iterable_con_longitud(data):
                print("    ⚠ validar_normalidad: `data` no tiene longitud; se omite test")
                return func(*args, **kwargs)

            n = len(data)

            # Shapiro-Wilk requiere mínimo 3 observaciones
            if n < 3:
                print(f"    ⚠ n={n} insuficiente para Shapiro-Wilk (mín. 3)")
                return func(*args, **kwargs)

            # Convertir a array numpy, filtrar NaN/inf
            try:
                data_arr = np.asarray(data, dtype=float)
                data_arr = data_arr[np.isfinite(data_arr)]
            except Exception:
                print("    ⚠ validar_normalidad: no fue posible convertir `data` a numérico")
                return func(*args, **kwargs)

            if len(data_arr) < 3:
                print(f"    ⚠ n={len(data_arr)} válido insuficiente tras filtrar NaN/inf")
                return func(*args, **kwargs)

            # Límite práctico para evitar warnings en muestras muy grandes
            if len(data_arr) > 5000:
                data_arr = data_arr[:5000]
                print(f"    ℹ Shapiro-Wilk en submuestra de 5000 (n_original={n})")

            # Ejecutar test
            stat, p = stats.shapiro(data_arr)

            if p < alpha:
                # p < alpha → rechazamos H₀ → datos NO normales
                print(f"    ⚠ NO normal — W={stat:.4f}, p={p:.4f} < α={alpha}")
                print("      → Considera: Mann-Whitney U o Kruskal-Wallis (no-paramétricos)")
                print("      → Usa MEDIANA en lugar de MEDIA como estadístico central")
            else:
                # p ≥ alpha → no hay evidencia contra normalidad
                print(f"    ✓ Normalidad confirmada — W={stat:.4f}, p={p:.4f} ≥ α={alpha}")
                print("      → Tests paramétricos son válidos (t-test, ANOVA, etc.)")

            # NO reenviar `data` manualmente (evita duplicación de argumentos)
            return func(*args, **kwargs)

        return wrapper
    return decorator


# ══════════════════════════════════════════════════════════════════════════
# 2. DECORATOR FACTORY — Tamaño mínimo de muestra
# ══════════════════════════════════════════════════════════════════════════

def muestra_minima(n_min: int):
    """
    DECORATOR FACTORY: bloquea ejecución si la muestra es demasiado pequeña.

    JUSTIFICACIÓN ESTADÍSTICA:
      Muchas pruebas dependen del Teorema Central del Límite:
        - Intervalo de confianza para la media
        - t-test de Student
        - Regresión lineal (inferencia)
        - ANOVA

      El TCL requiere n ≥ 30 para aproximar normalmente la distribución
      muestral. Con n < 29, los resultados pueden ser matemáticamente
      incorrectos (intervalos que no cubren el parámetro real).

    A DIFERENCIA de @validar_normalidad:
      Este decorador SÍ bloquea: retorna None si la condición no se cumple,
      porque con muestras muy pequeñas el resultado no tiene sentido.

    Args:
        n_min: número mínimo de observaciones requeridas
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            data = _extraer_data(args, kwargs)

            if data is None:
                data = _extraer_df_de_self(args)
                if data is not None and hasattr(data, "columns"):
                    if "indice_riesgo" in data.columns:
                        data = data["indice_riesgo"].dropna()
                    elif len(data.columns) > 0:
                        data = data.iloc[:, 0].dropna()

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
                print("       → Recolecte más datos o use métodos exactos (bootstrap)")
                return None

            return func(*args, **kwargs)

        return wrapper
    return decorator


# ══════════════════════════════════════════════════════════════════════════
# 3. DECORADOR CON ESTADO — Memoización (caché)
# ══════════════════════════════════════════════════════════════════════════

def cachear(func: Callable) -> Callable:
    """
    DECORADOR CON ESTADO: Implementa memoización manual.

    MEMOIZACIÓN:
      Si la función ya fue llamada con los mismos argumentos,
      devuelve el resultado guardado sin volver a calcular.

      Equivalente conceptual a @functools.lru_cache(maxsize=None),
      pero más transparente para mostrar cómo funciona el patrón.

    APLICACIÓN EN ESTADÍSTICA:
      - Cálculos costosos: percentiles, bootstrap, MCMC
      - Funciones que se llaman repetidamente con mismos parámetros
      - Evita recalcular en loops o validaciones cruzadas

    LIMITACIÓN:
      Los argumentos deben ser HASHABLES (inmutables: int, str, tuple).
      Si recibe listas, DataFrames, etc., ejecuta sin caché e informa.
    """
    _cache: dict = {}

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
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
            print(f"    [caché] {func.__name__}{args} → recuperado del caché (0s)")

        return _cache[key]

    return wrapper


# ══════════════════════════════════════════════════════════════════════════
# 4. DECORADOR PARA MÉTODOS — Validación de DataFrame
#    (NUEVO: específico para métodos de clase con DataFrames)
# ══════════════════════════════════════════════════════════════════════════

def validar_datos_df(columnas_requeridas: Optional[list] = None):
    """
    DECORATOR FACTORY: valida que self.df exista y tenga columnas requeridas.

    CONCEPTO:
      Específico para métodos de clase que operan sobre DataFrames.
      Verifica:
        1. self.df existe y es un DataFrame
        2. self.df no está vacío
        3. self.df tiene las columnas requeridas (si se especifican)

    APLICACIÓN EN ESTE PROYECTO:
      Se usa en métodos de limpieza y EDA para evitar errores
      cuando el DataFrame no se ha cargado correctamente.

    Args:
        columnas_requeridas: lista de nombres de columnas que deben existir.
                            Si es None, solo verifica que df no esté vacío.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extraer self desde el primer argumento (es un método)
            if len(args) < 1:
                print(f"    🔴 [{func.__name__}] No se recibió `self`")
                return None

            self_obj = args[0]
            df = getattr(self_obj, "df", None)

            # Validar existencia
            if df is None:
                print(f"    🔴 [{func.__name__}] self.df es None")
                print("       → Ejecute primero el método que carga los datos")
                return None

            # Validar tipo
            if not hasattr(df, "columns"):
                print(f"    🔴 [{func.__name__}] self.df no es un DataFrame")
                return None

            # Validar no-vacío
            if df.empty:
                print(f"    🔴 [{func.__name__}] self.df está vacío")
                print("       → Verifique la conexión a la API o los datos de entrada")
                return None

            # Validar columnas requeridas
            if columnas_requeridas:
                faltantes = [c for c in columnas_requeridas if c not in df.columns]
                if faltantes:
                    print(f"    🔴 [{func.__name__}] Columnas faltantes: {faltantes}")
                    print(f"       Columnas disponibles: {list(df.columns)}")
                    return None

            return func(*args, **kwargs)

        return wrapper
    return decorator


# ══════════════════════════════════════════════════════════════════════════
# DEMO — Se ejecuta solo si este archivo se corre directamente
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  DEMO — decorators.py")
    print("  Semana 1: Decoradores Estadísticos")
    print("=" * 65)

    rng = np.random.default_rng(42)

    # Datos de prueba: índices de riesgo simulados
    datos_normales = rng.normal(loc=-1.02, scale=0.005, size=50).tolist()
    datos_sesgados = rng.exponential(scale=1.05, size=50).tolist()
    muestra_pequena = rng.normal(-1, 1, size=2).tolist()

    # ── Demo 0: validar_normalidad ───────────────────────────────────────

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

    # ── Demo 1: registrar_ejecucion ──────────────────────────────────────

    @registrar_ejecucion
    def cargar_datos(n: int) -> str:
        """Simula carga de datos con demora."""
        time.sleep(1.08)
        return f"Dataset con {n} registros"

    print("\n2. @registrar_ejecucion:")
    resultado = cargar_datos(499)
    print(f"   Resultado: {resultado}")

    # ── Demo 2: muestra_minima ───────────────────────────────────────────

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

    # ── Demo 3: cachear ──────────────────────────────────────────────────

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

    # ── Demo 4: compatibilidad con métodos de clase ──────────────────────
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
