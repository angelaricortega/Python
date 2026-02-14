# 🏦 Sistema de Análisis de Riesgo Crediticio  
### Análisis Geo-Espacial del Sistema Financiero Colombiano

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Pandas](https://img.shields.io/badge/pandas-2.x-blue.svg)
![Status](https://img.shields.io/badge/status-production--ready-success.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## 📌 Resumen Ejecutivo

Este proyecto implementa un **pipeline generalizable de análisis de riesgo financiero**, aplicado al sistema financiero colombiano utilizando datos abiertos oficiales.

El objetivo no es solo analizar una base específica, sino construir una arquitectura reutilizable para:

- Medición agregada de riesgo crediticio  
- Evaluación de concentración geográfica  
- Análisis de tensión de liquidez  
- Generación automatizada de métricas comparables  

El diseño es **modular y extensible**, lo que permite adaptar el sistema a otros datasets financieros, carteras privadas o series macroeconómicas sin modificar la lógica central.

---

## 📚 Justificación de la Fuente de Datos

La base seleccionada corresponde a información pública del sistema financiero colombiano con desagregación municipal y por tipo de cartera.

Se eligió porque:

- Permite análisis territorial del riesgo  
- Contiene clasificación por categorías regulatorias (A–E)  
- Incluye variables de captaciones y colocaciones  
- Presenta consistencia estructural longitudinal  

Esto permite aproximar dinámicas sistémicas sin necesidad de microdatos individuales.

---

## 🧠 Marco Conceptual

### 1️⃣ Riesgo Crediticio

La pérdida esperada en teoría financiera se define como:

```

EL = PD × LGD × EAD

```

Donde:

- PD: Probabilidad de Incumplimiento  
- LGD: Pérdida dada el Incumplimiento  
- EAD: Exposición al Incumplimiento  

Dado que no se cuenta con información individual de deudores, el sistema aproxima el deterioro crediticio mediante agregación por categorías regulatorias.

---

### 2️⃣ Índice de Riesgo (Proxy de Cartera en Mora)

```

Índice de Riesgo = (C + D + E) / Cartera Total

```

C = Subestándar  
D = Dudosa  
E = Pérdida  

Este indicador es equivalente a un **NPL Ratio agregado**, ampliamente utilizado en supervisión bancaria y análisis macroprudencial.

Su elección se justifica porque:

- Es robusto ante ausencia de microdatos  
- Es comparable entre territorios  
- Permite evaluar deterioro relativo  

---

### 3️⃣ Indicador de Tensión de Liquidez

```

Ratio de Liquidez = Captaciones / Colocaciones

```

Interpretación:

- < 1 → Dependencia de fondeo externo  
- > 1 → Estructura de fondeo estable  

Este ratio permite evaluar vulnerabilidad estructural del sistema a nivel territorial.

---

## 🏗 Arquitectura Modular del Pipeline

El sistema está diseñado como un pipeline desacoplado en etapas independientes:

```

Fuente de Datos
↓
Ingesta Parametrizada
↓
Validación Estructural
↓
EDA Automatizado
↓
Limpieza Estadística
↓
Ingeniería de Variables
↓
Cálculo de Indicadores
↓
Visualización
↓
Reporte

```

### ¿Qué significa que sea modular?

- No depende de nombres rígidos de columnas  
- Permite redefinir métricas mediante configuración  
- Separa lógica de negocio de la fuente de datos  
- Las funciones son reutilizables en otros contextos financieros  

Puede adaptarse a:

- Portafolios privados  
- Series macroeconómicas  
- Datos de otras jurisdicciones  
- Modelos de VaR o Expected Shortfall  

---

## 📊 Resultados Principales

### 📌 Tamaño del Sistema

- Cartera total analizada: 73 billones COP  

Indica una muestra con relevancia macroeconómica.

---

### 📌 Calidad Crediticia

- Índice promedio de riesgo: 0.27%  
- 66% de municipios sin exposición significativa  

Interpretación:

El sistema muestra bajo deterioro agregado, lo que sugiere estabilidad crediticia estructural en el periodo analizado.

---

### 📌 Concentración Geográfica

Se observa alta concentración del crédito en pocos municipios.

Implicaciones:

- Riesgo sistémico por correlación regional  
- Sensibilidad ante shocks locales  
- Dependencia de hubs financieros principales  

---

### 📌 Estructura de Liquidez

Predominan municipios donde:

```

Colocaciones > Captaciones

```

Esto puede indicar:

- Dependencia de fondeo mayorista  
- Integración interregional del sistema  
- Posible vulnerabilidad ante restricciones de liquidez  

---

## 🧪 Rigor Metodológico

La limpieza de datos se realizó bajo criterios estadísticos:

- Filtrado por percentiles extremos  
- Validación de tipos numéricos  
- Eliminación de registros agregados inconsistentes  
- Transformaciones reproducibles  

No hubo manipulación manual de datos.

---

## 📁 Estructura del Proyecto

```

├── analisis.py
├── decorators.py
├── requirements.txt
├── outputs/
│   ├── graficos/
│   ├── datos/
│   └── reportes/
├── .gitignore
└── README.md

````

---

## 🚀 Instalación

```bash
git clone https://github.com/angelaricortega/Python.git
cd Python

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
python analisis.py
````

---

## 📦 Dependencias

* pandas
* numpy
* matplotlib
* seaborn
* scipy
* requests

---

## 🎯 Extensiones Futuras

* Parametrización vía archivo de configuración
* Implementación de métricas VaR
* Integración con modelos econométricos
* Automatización vía CLI
* Integración CI/CD

---

## 👩‍💻 Autores

Angela Rico
Sebastian Ramirez

USTA – 2026

```



## 📜 Licencia

MIT

```

