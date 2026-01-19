# Poker Tracker (Monolithic Version)

## Descripción General
Poker Tracker es una aplicación web construida con **Streamlit** para la gestión contable de clubes de poker. Permite rastrear ganancias, rake, deudas y desempeño de jugadores a través de múltiples clubes y semanas.

## Características Principales
*   **Dashboard**: Vista general de métricas (Profit, Rake, Jugadores Activos).
*   **Gestión de Jugadores**: Base de datos de jugadores y sus alias (nicknames).
*   **Gestión de Clubes**: Configuración y seguimiento de clubes.
*   **Reportes Semanales**: Desglose de desempeño por semana.
*   **Balance**: Cálculo de comisiones, rakeback y tipos de cambio.
*   **Carga de Datos**: Interfaz para captura manual y masiva de registros.

## Estructura del Proyecto
El proyecto sigue una arquitectura **Monolítica** simplificada:
*   `app.py`: Contiene **toda** la lógica de la aplicación (Interfaz, Base de Datos, Lógica de Negocio).
*   `poker_tracker.db`: Base de datos SQLite.
*   `setup_db.py`: Script de inicialización de la base de datos.
*   `import_data.py` / `analyze_excel.py`: Scripts auxiliares para manipulación de datos.

## Requisitos
*   Python 3.8+
*   Librerías: `streamlit`, `pandas`, `sqlite3`

## Ejecución
Para iniciar la aplicación:

```bash
streamlit run app.py
```

La aplicación estará disponible en `http://localhost:8501`.
