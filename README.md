# Diseño de Columnas Uniaxial y Biaxial (Aplicación Web)

Esta versión implementa el algoritmo analítico de diseño/verificación de columnas de concreto reforzado en una **aplicación web** con Flask.

## Archivos principales

- `column_design.py`: motor de cálculo estructural (esbeltez, interacción uniaxial, chequeos).
- `app.py`: servidor web y controlador de entradas/salidas.
- `templates/index.html`: interfaz web con formulario y tabla de resultados.

## Funcionalidades implementadas

1. Definición de materiales y geometría.
2. Verificación de esbeltez (arriostrada / no arriostrada).
3. Diagrama de interacción uniaxial por compatibilidad de deformaciones.
4. Evaluación de capacidad por intersección demanda/capacidad.
5. Ratio Demanda/Capacidad (D/C).
6. Verificación de cuantía longitudinal.

## Ejecución local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Luego abrir en navegador:

- http://localhost:5000

## Nota

El script `column_design.py` sigue siendo reutilizable como módulo de cálculo independiente.
