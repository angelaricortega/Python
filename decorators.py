"""
decorators.py - Decoradores personalizados para el análisis
"""

import functools
import time
import logging
from typing import Any, Callable, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def timer(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = end - start
        
        if elapsed < 60:
            tiempo_str = f"{elapsed:.2f} segundos"
        else:
            minutos = int(elapsed // 60)
            segundos = elapsed % 60
            tiempo_str = f"{minutos} min {segundos:.2f} seg"
        
        print(f"⏱️  {func.__name__} ejecutada en {tiempo_str}")
        logger.info(f"TIMER:{func.__name__}:{elapsed:.2f}s")
        return result
    return wrapper

def log_execution(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        print(f"\n🔄 INICIO: {func.__name__}")
        logger.info(f"START:{func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            print(f"✅ FIN: {func.__name__}")
            logger.info(f"END:{func.__name__}")
            return result
        except Exception as e:
            print(f"❌ ERROR en {func.__name__}: {str(e)}")
            logger.error(f"ERROR:{func.__name__}:{str(e)}")
            raise
    return wrapper

def validar_dataframe(columnas_requeridas: Optional[list] = None):
    if columnas_requeridas is None:
        columnas_requeridas = ['cartera_total']
    
    def decorador(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(df, *args, **kwargs) -> Any:
            if not hasattr(df, 'columns'):
                raise TypeError("❌ El argumento no es un DataFrame")
            
            columnas_df = set(df.columns)
            faltantes = set(columnas_requeridas) - columnas_df
            
            if faltantes:
                error_msg = f"❌ Columnas faltantes: {faltantes}"
                print(error_msg)
                raise ValueError(error_msg)
            
            print(f"✅ DataFrame validado: {len(columnas_requeridas)} columnas requeridas presentes")
            return func(df, *args, **kwargs)
        return wrapper
    return decorador