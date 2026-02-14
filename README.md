# 🏦 Sistema de Análisis de Riesgo Crediticio  
### Análisis Geo-Espacial del Sistema Financiero Colombiano

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Pandas](https://img.shields.io/badge/pandas-2.x-blue.svg)
![Status](https://img.shields.io/badge/status-production--ready-success.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## 📌 Resumen Ejecutivo

Pipeline modular de análisis de riesgo crediticio usando datos abiertos del sistema financiero colombiano.

Incluye:

- Ingesta de datos  
- Análisis Exploratorio (EDA)  
- Limpieza estadística  
- Construcción de métricas  
- Visualización profesional  
- Reporte automático  

---

## 🧠 Marco Teórico

### Riesgo Crediticio

Pérdida Esperada (EL):

```

EL = PD × LGD × EAD

```

Donde:

- PD: Probabilidad de Incumplimiento  
- LGD: Pérdida dada el Incumplimiento  
- EAD: Exposición al Incumplimiento  

---

### Índice de Riesgo (Proxy NPL)

```

Índice de Riesgo = (C + D + E) / Cartera Total

```

C = Subestándar  
D = Dudosa  
E = Pérdida  

---

### Ratio de Liquidez

```

Ratio de Liquidez = Captaciones / Colocaciones

```

- < 1 → Tensión de fondeo  
- > 1 → Estructura estable  

---

## 🏗 Arquitectura del Pipeline

```

Fuente de Datos
↓
Ingesta
↓
EDA
↓
Limpieza
↓
Ingeniería de Variables
↓
Cálculo de Métricas
↓
Visualización
↓
Reporte

```

---

## 📊 Hallazgos Principales

- Cartera total: 73 billones COP  
- Índice promedio: 0.27%  
- 66% municipios sin riesgo alto  
- Alta concentración geográfica  
- Desequilibrio estructural de liquidez  

---

## 📁 Estructura

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

## 👩‍💻 Autores

Angela Rico
Sebastian Ramirez

USTA – 2026

---

## 📜 Licencia

MIT

```

