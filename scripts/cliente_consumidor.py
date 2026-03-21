"""
cliente_consumidor.py — Cliente Python para consumir la API de Encuestas.

Bonificación +0.1: Script independiente que consume la API usando httpx,
carga datos desde un CSV y genera un reporte estadístico con pandas.

Uso:
    python scripts/cliente_consumidor.py

Requisitos:
    pip install httpx pandas openpyxl
"""

import io
from pathlib import Path

import httpx
import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────────────────────────────────────

API_BASE_URL = "http://localhost:8000"
CSV_EJEMPLO = Path(__file__).parent.parent / "datos_ejemplo" / "encuestas_ejemplo.csv"


# ─────────────────────────────────────────────────────────────────────────────
# Cliente API
# ─────────────────────────────────────────────────────────────────────────────

class ClienteEncuestasAPI:
    """
    Cliente HTTP para interactuar con la API de Encuestas.
    
    Usa httpx para requests asíncronos, permitiendo operaciones
    concurrentes eficientes.
    """

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.cliente = httpx.Client(timeout=30.0)

    def health_check(self) -> dict:
        """Verifica que la API esté activa."""
        try:
            response = self.cliente.get(f"{self.base_url}/")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            print(f"❌ Error de conexión: {e}")
            return {}

    def crear_encuesta(self, datos: dict) -> dict:
        """Crea una nueva encuesta."""
        response = self.cliente.post(
            f"{self.base_url}/encuestas/",
            json=datos
        )
        if response.status_code == 201:
            return response.json()
        else:
            print(f"❌ Error al crear: {response.status_code} - {response.text}")
            return {}

    def listar_encuestas(self) -> list:
        """Lista todas las encuestas."""
        response = self.cliente.get(f"{self.base_url}/encuestas/")
        if response.status_code == 200:
            return response.json()
        return []

    def obtener_estadisticas(self) -> dict:
        """Obtiene estadísticas agregadas."""
        response = self.cliente.get(f"{self.base_url}/encuestas/estadisticas/")
        if response.status_code == 200:
            return response.json()
        return {}

    def upload_csv(self, archivo_csv: Path) -> dict:
        """Sube un archivo CSV a la API."""
        if not archivo_csv.exists():
            print(f"❌ Archivo no encontrado: {archivo_csv}")
            return {}

        with open(archivo_csv, 'rb') as f:
            files = {'file': (archivo_csv.name, f, 'text/csv')}
            response = self.cliente.post(
                f"{self.base_url}/encuestas/upload-csv/",
                files=files
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error al subir CSV: {response.status_code} - {response.text}")
            return {}

    def export_json(self, destino: Path) -> bool:
        """Exporta encuestas a JSON."""
        response = self.cliente.get(f"{self.base_url}/encuestas/export/json/")
        if response.status_code == 200:
            with open(destino, 'wb') as f:
                f.write(response.content)
            return True
        return False

    def export_pickle(self, destino: Path) -> bool:
        """Exporta encuestas a Pickle."""
        response = self.cliente.get(f"{self.base_url}/encuestas/export/pickle/")
        if response.status_code == 200:
            with open(destino, 'wb') as f:
                f.write(response.content)
            return True
        return False

    def cerrar(self):
        """Cierra el cliente HTTP."""
        self.cliente.close()


# ─────────────────────────────────────────────────────────────────────────────
# Generación de Reporte
# ─────────────────────────────────────────────────────────────────────────────

def generar_reporte_estadisticas(estadisticas: dict) -> str:
    """
    Genera un reporte estadístico en texto formateado.
    
    Args:
        estadisticas: Diccionario con estadísticas de la API
    
    Returns:
        String formateado con el reporte
    """
    reporte = []
    reporte.append("=" * 60)
    reporte.append("📊 REPORTE ESTADÍSTICO DE ENCUESTAS")
    reporte.append("=" * 60)
    reporte.append("")
    
    # Métricas principales
    reporte.append("📈 MÉTRICAS PRINCIPALES")
    reporte.append("-" * 40)
    reporte.append(f"  Total de encuestas:        {estadisticas.get('total_encuestas', 0)}")
    reporte.append(f"  Edad promedio:             {estadisticas.get('edad_promedio', 0):.1f} años")
    reporte.append(f"  Rango de edades:           {estadisticas.get('edad_minima', 0)} - {estadisticas.get('edad_maxima', 0)} años")
    reporte.append(f"  Promedio preguntas:        {estadisticas.get('promedio_respuestas_por_encuesta', 0):.1f}")
    reporte.append("")
    
    # Distribución por estrato
    reporte.append("🏠 DISTRIBUCIÓN POR ESTRATO")
    reporte.append("-" * 40)
    estrato = estadisticas.get('distribucion_por_estrato', {})
    for clave, valor in sorted(estrato.items()):
        barra = "█" * min(valor, 50)
        reporte.append(f"  {clave:15} {valor:4} {barra}")
    reporte.append("")
    
    # Distribución por departamento
    reporte.append("🗺️  DISTRIBUCIÓN POR DEPARTAMENTO")
    reporte.append("-" * 40)
    depto = estadisticas.get('distribucion_por_departamento', {})
    for clave, valor in sorted(depto.items(), key=lambda x: x[1], reverse=True)[:10]:
        barra = "█" * min(valor, 50)
        reporte.append(f"  {clave:25} {valor:4} {barra}")
    reporte.append("")
    
    # Distribución por género
    reporte.append("👥 DISTRIBUCIÓN POR GÉNERO")
    reporte.append("-" * 40)
    genero = estadisticas.get('distribucion_por_genero', {})
    for clave, valor in sorted(genero.items(), key=lambda x: x[1], reverse=True):
        barra = "█" * min(valor, 50)
        reporte.append(f"  {clave:20} {valor:4} {barra}")
    reporte.append("")
    
    # Distribución por nivel educativo
    reporte.append("🎓 DISTRIBUCIÓN POR NIVEL EDUCATIVO")
    reporte.append("-" * 40)
    educativo = estadisticas.get('distribucion_por_nivel_educativo', {})
    for clave, valor in sorted(educativo.items(), key=lambda x: x[1], reverse=True):
        barra = "█" * min(valor, 50)
        reporte.append(f"  {clave:20} {valor:4} {barra}")
    reporte.append("")
    
    reporte.append("=" * 60)
    
    return "\n".join(reporte)


def crear_dataframe_desde_encuestas(encuestas: list) -> pd.DataFrame:
    """
    Convierte lista de encuestas en DataFrame de pandas.
    
    Args:
        encuestas: Lista de diccionarios con datos de encuestas
    
    Returns:
        DataFrame con datos normalizados
    """
    filas = []
    for enc in encuestas:
        fila = {
            'id_encuesta': enc.get('id_encuesta'),
            'fecha_registro': enc.get('fecha_registro'),
            'nombre': enc.get('encuestado', {}).get('nombre'),
            'edad': enc.get('encuestado', {}).get('edad'),
            'genero': enc.get('encuestado', {}).get('genero'),
            'estrato': enc.get('encuestado', {}).get('estrato'),
            'departamento': enc.get('encuestado', {}).get('departamento'),
            'municipio': enc.get('encuestado', {}).get('municipio'),
            'nivel_educativo': enc.get('encuestado', {}).get('nivel_educativo'),
            'ocupacion': enc.get('encuestado', {}).get('ocupacion'),
        }
        
        # Agregar respuestas como columnas
        for resp in enc.get('respuestas', []):
            col_name = f"p{resp['pregunta_id']}_{resp['tipo_pregunta']}"
            fila[col_name] = resp['valor']
        
        filas.append(fila)
    
    return pd.DataFrame(filas)


# ─────────────────────────────────────────────────────────────────────────────
# Función Principal
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """
    Función principal que demuestra el uso del cliente.
    
    Flujo:
    1. Verifica conexión con la API
    2. Carga datos desde CSV (si existe)
    3. Obtiene estadísticas
    4. Genera reporte con pandas
    5. Exporta datos a JSON y Pickle
    """
    print("\n" + "=" * 60)
    print("🚀 CLIENTE CONSUMIDOR DE API DE ENCUESTAS")
    print("=" * 60 + "\n")

    # Inicializar cliente
    cliente = ClienteEncuestasAPI()

    try:
        # 1. Health check
        print("1️⃣  Verificando conexión con la API...")
        health = cliente.health_check()
        if health:
            print(f"   ✅ API activa: {health.get('estado', 'desconocido')}")
            print(f"   📊 Encuestas registradas: {health.get('encuestas_registradas', 0)}")
        else:
            print("   ❌ No se pudo conectar a la API")
            print(f"   💡 Asegúrese de ejecutar: uvicorn main:app --reload --port 8000")
            return
        print()

        # 2. Upload de CSV (si existe)
        print("2️⃣  Cargando datos desde CSV...")
        if CSV_EJEMPLO.exists():
            resultado = cliente.upload_csv(CSV_EJEMPLO)
            if resultado:
                print(f"   ✅ Procesados: {resultado.get('total_procesados', 0)}")
                print(f"   ✅ Exitosos: {resultado.get('exitosos', 0)}")
                print(f"   ❌ Errores: {resultado.get('fallidos', 0)}")
            else:
                print("   ⚠️ No se pudo cargar el CSV")
        else:
            print(f"   ⚠️ Archivo no encontrado: {CSV_EJEMPLO}")
            print("   💡 Puede crear un CSV con datos de ejemplo")
        print()

        # 3. Obtener estadísticas
        print("3️⃣  Obteniendo estadísticas...")
        estadisticas = cliente.obtener_estadisticas()
        if estadisticas:
            print("   ✅ Estadísticas obtenidas")
        else:
            print("   ⚠️ No hay estadísticas disponibles")
        print()

        # 4. Generar reporte
        print("4️⃣  Generando reporte estadístico...")
        if estadisticas:
            reporte = generar_reporte_estadisticas(estadisticas)
            print(reporte)
            
            # Guardar reporte en archivo
            archivo_reporte = Path(__file__).parent.parent / "reporte_estadisticas.txt"
            with open(archivo_reporte, 'w', encoding='utf-8') as f:
                f.write(reporte)
            print(f"\n   📄 Reporte guardado en: {archivo_reporte}")
        print()

        # 5. Exportar datos
        print("5️⃣  Exportando datos...")
        directorio_export = Path(__file__).parent.parent / "export"
        directorio_export.mkdir(exist_ok=True)
        
        json_path = directorio_export / "encuestas.json"
        pickle_path = directorio_export / "encuestas.pkl"
        
        if cliente.export_json(json_path):
            print(f"   ✅ JSON exportado: {json_path}")
        
        if cliente.export_pickle(pickle_path):
            print(f"   ✅ Pickle exportado: {pickle_path}")
        print()

        # 6. Listar encuestas y crear DataFrame
        print("6️⃣  Creando DataFrame con pandas...")
        encuestas = cliente.listar_encuestas()
        if encuestas:
            df = crear_dataframe_desde_encuestas(encuestas)
            print(f"   ✅ DataFrame creado: {len(df)} filas, {len(df.columns)} columnas")
            print(f"\n   📊 Primeras 5 filas:")
            print(df.head().to_string())
            
            # Estadísticas descriptivas con pandas
            if 'edad' in df.columns:
                print(f"\n   📈 Estadísticas descriptivas (edad):")
                print(df['edad'].describe())
        else:
            print("   ⚠️ No hay encuestas para mostrar")
        print()

    finally:
        cliente.cerrar()

    print("=" * 60)
    print("✅ PROCESO COMPLETADO")
    print("=" * 60 + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Punto de Entrada
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Ejecución directa del script:
        python scripts/cliente_consumidor.py
    
    Requiere que la API esté corriendo en http://localhost:8000
    """
    main()
