"""
api_client.py — Cliente HTTP Robusto para API de Datos Abiertos
=================================================================
Semana 2: OOP + requests.Session para conexiones eficientes.

CONCEPTO CLAVE — requests.Session:
  Sin Session: cada requests.get() abre y cierra una conexión TCP+TLS
               (handshake ≈ 48-200ms por petición)
  Con Session: la conexión se mantiene abierta (HTTP Keep-Alive)
               y se reutiliza para peticiones múltiples

ANALOGÍA:
  Sin Session: llamar por teléfono, colgar, y volver a marcar para cada frase
  Con Session: mantener la llamada abierta para toda la conversación

POR QUÉ OOP (Programación Orientada a Objetos):
  Encapsulamos estado (session, base_url, timeout) y comportamiento
  (obtener_datos, cerrar) en una sola clase. Esto permite:
    - Reutilizar el cliente en múltiples partes del código
    - Mantener la configuración en un solo lugar
    - Extender funcionalidad sin modificar código existente

MANEJO DE ERRORES:
  Capturamos cada tipo de error por separado para mensajes útiles:
    - Timeout: servidor tardó demasiado
    - HTTPError: código de estado 4xx o 5xx
    - JSONDecodeError: respuesta llegó pero no es JSON válido
    - ConnectionError: sin conexión de red o DNS fallido

  Capturar Exception genérico ocultaría la causa real del error.
"""

# ── Librería estándar ────────────────────────────────────────────────────
from typing import Optional

# ── Terceros ─────────────────────────────────────────────────────────────
import requests
from requests.exceptions import (
    Timeout,
    HTTPError,
    JSONDecodeError,
    ConnectionError,
    RequestException,
)

# ── Locales ──────────────────────────────────────────────────────────────
from config import API_BASE, HTTP_TIMEOUT, DEFAULT_LIMIT


# ══════════════════════════════════════════════════════════════════════════
# CLIENTE HTTP PARA API DE DATOS ABIERTOS
# ══════════════════════════════════════════════════════════════════════════

class ClienteAPIFinanciero:
    """
    Cliente HTTP robusto para la API de Datos Abiertos Colombia (Socrata).

    ATRIBUTOS:
      base_url   : URL base de la API (ej: https://www.datos.gov.co/resource/...)
      timeout    : tiempo máximo de espera en segundos
      session    : sesión HTTP persistente (reutiliza conexión TCP)

    MÉTODOS PÚBLICOS:
      obtener_datos(limite)  : descarga registros de la API
      cerrar()               : libera recursos de la sesión

    USO TÍPICO:
      cliente = ClienteAPIFinanciero(API_BASE, timeout=15)
      try:
          datos = cliente.obtener_datos(limite=500)
      finally:
          cliente.cerrar()  # siempre liberar recursos
    """

    def __init__(self, base_url: str = API_BASE, timeout: int = HTTP_TIMEOUT):
        """
        CONSTRUCTOR (__init__):
          Se ejecuta automáticamente al crear la instancia.
          Aquí configuramos lo que el objeto necesita "recordar".

        Args:
            base_url: URL base de la API (default: API_BASE de config.py)
            timeout: tiempo máximo de espera en segundos (default: 15)
        """
        self.base_url = base_url
        self.timeout = timeout

        # Session: "túnel permanente" con el servidor
        # Mejora el rendimiento al no reconectar en cada petición
        self.session = requests.Session()

        # Headers globales: se envían en TODAS las peticiones
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "RiesgoCredito-USTA/1.0",  # identificar el cliente
        })

        print(f"  ✓ Cliente API inicializado: {self.base_url[:50]}...")
        print(f"  ✓ Timeout: {self.timeout}s")
        print(f"  ✓ Session: conexión persistente activada")

    def obtener_datos(self, limite: int = DEFAULT_LIMIT) -> list[dict]:
        """
        Descarga registros de la API de Datos Abiertos.

        PARÁMETROS DE LA API SOCRATA:
          $limit  : cantidad máxima de registros a devolver
          $offset : desplazamiento para paginación (no usado aquí)

        Args:
            limite: cantidad máxima de registros a descargar (default: 500)

        Returns:
            list[dict]: lista de diccionarios, cada uno es un registro
                       lista vacía si hubo error o no hay datos

        ERRORES MANEJADOS:
          Timeout         → servidor tardó más de `timeout` segundos
          HTTPError       → código de estado 4xx o 5xx
          JSONDecodeError → respuesta no es JSON válido
          ConnectionError → sin conexión de red
        """
        # Construir URL con parámetros
        url = f"{self.base_url}?$limit={limite}&$offset=0"

        try:
            # Petición GET usando la sesión (conexión persistente)
            resp = self.session.get(url, timeout=self.timeout)

            # raise_for_status() lanza HTTPError si status >= 400
            # Esto evita procesar respuestas de error como si fueran exitosas
            resp.raise_for_status()

            # Parsear JSON a lista de diccionarios Python
            datos = resp.json()

            print(f"  ✓ Datos descargados: {len(datos)} registros")
            return datos

        except Timeout:
            # Servidor no respondió en `timeout` segundos
            print(f"    ⚠ Timeout ({self.timeout}s) — servidor no responde")
            print("      → Activando datos sintéticos (fallback)")
            return self._datos_sinteticos()

        except HTTPError as e:
            # Código de estado HTTP 4xx o 5xx
            status = e.response.status_code
            print(f"    ✗ Error HTTP {status}")

            if status == 404:
                print("      → Endpoint no encontrado (404)")
            elif status == 429:
                print("      → Rate limit excedido (429) — demasiadas peticiones")
            elif status >= 500:
                print("      → Error del servidor (5xx) — reintentar más tarde")
            else:
                print(f"      → Verifique la URL o permisos de acceso")
            return []

        except JSONDecodeError:
            # La respuesta llegó pero no es JSON válido
            print("    ✗ La respuesta no es JSON válido")
            print(f"      → Contenido recibido: {resp.text[:200]}")
            return []

        except ConnectionError:
            # Sin conexión de red o DNS fallido
            print("    ✗ Sin conexión de red")
            print("      → Activando datos sintéticos (fallback)")
            return self._datos_sinteticos()

        except RequestException as e:
            # Error genérico de requests (capturar todo lo demás)
            print(f"    ✗ Error inesperado: {e}")
            return []

    def _datos_sinteticos(self, n: int = 50) -> list[dict]:
        """
        Genera datos sintéticos para fallback cuando la API no está disponible.

        PROPÓSITO:
          - Permitir que el pipeline se ejecute sin conexión
          - Demostrar funcionalidad en entornos sin acceso a internet
          - Testing reproducible (datos fijos)

        Args:
            n: cantidad de registros a generar (default: 50)

        Returns:
            list[dict]: lista de diccionarios con datos simulados
        """
        import numpy as np

        # Semilla fija para reproducibilidad
        rng = np.random.default_rng(42)

        # Municipios principales de Colombia
        municipios_base = [
            "Bogotá D.C.", "Medellín", "Cali", "Barranquilla",
            "Cartagena", "Bucaramanga", "Pereira", "Manizales",
            "Santa Marta", "Ibagué", "Pasto", "Cúcuta",
        ]

        datos = []
        for i in range(n):
            municipio = rng.choice(municipios_base)

            # Generar cartera con distribución log-normal (realista)
            total_cartera = float(rng.lognormal(mean=18, sigma=2))

            # Captaciones correlacionadas con cartera
            total_captaciones = total_cartera * rng.uniform(0.8, 1.5)

            # Distribuir cartera en categorías (A es mayoría)
            cartera_a = total_cartera * rng.uniform(0.70, 0.90)
            cartera_b = total_cartera * rng.uniform(0.05, 0.15)
            cartera_c = total_cartera * rng.uniform(0.02, 0.08)
            cartera_d = total_cartera * rng.uniform(0.01, 0.05)
            cartera_e = total_cartera * rng.uniform(0.00, 0.03)

            datos.append({
                "nombre_municipio": municipio,
                "cartera_categoria_a": round(cartera_a, 2),
                "cartera_categoria_b": round(cartera_b, 2),
                "cartera_categoria_c": round(cartera_c, 2),
                "cartera_categoria_d": round(cartera_d, 2),
                "cartera_categoria_e": round(cartera_e, 2),
                "total_cartera": round(total_cartera, 2),
                "total_captaciones": round(total_captaciones, 2),
            })

        print(f"  ℹ Datos sintéticos generados: {n} registros")
        return datos

    def cerrar(self):
        """
        Libera recursos de la sesión HTTP.

        POR QUÉ CERRAR:
          - Libera la conexión TCP (buena práctica)
          - Evita advertencias de recursos no liberados
          - Necesario si se crean múltiples clientes en el mismo script
        """
        self.session.close()
        print("  ✓ Sesión HTTP cerrada")


# ══════════════════════════════════════════════════════════════════════════
# DEMO — Ejecutar con: python api_client.py
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  DEMO — api_client.py")
    print("  Semana 2: Cliente HTTP Robusto con OOP")
    print("=" * 65)

    # ── 1. Crear cliente ─────────────────────────────────────────────────
    print("\n1. Inicializando cliente API:")
    cliente = ClienteAPIFinanciero(timeout=15)

    # ── 2. Obtener datos ─────────────────────────────────────────────────
    print("\n2. Descargando datos de la API:")
    datos = cliente.obtener_datos(limite=100)

    if datos:
        print(f"\n3. Primeros 3 registros:")
        for i, reg in enumerate(datos[:3], 1):
            print(f"   [{i}] {reg.get('nombre_municipio', 'N/A')}: "
                  f"${reg.get('total_cartera', 0):,.0f} COP")

    # ── 3. Cerrar sesión ─────────────────────────────────────────────────
    print("\n4. Cerrando cliente:")
    cliente.cerrar()

    print("\n✅ Demo completada.")
