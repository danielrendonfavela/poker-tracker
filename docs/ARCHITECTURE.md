# Arquitectura del Sistema

## Estado Actual: Monolito (Rama `dev`)

La aplicación reside casi en su totalidad en un único archivo: `app.py`.

### Flujo de Datos
1.  **UI (Streamlit)**: El usuario interactúa con widgets en la barra lateral y tabs.
2.  **Lógica Directa**: Las funciones dentro de `app.py` procesan la entrada inmediatamente.
3.  **Acceso a Datos**: Las consultas SQL (`SELECT`, `INSERT`) están incrustadas directamente en las funciones auxiliares de `app.py` (ej: `get_connection()`, `load_players()`).

### Funciones Clave en `app.py`

#### Carga de Datos (Data Access)
*   `get_connection()`: Abre conexión SQLite.
*   `load_players()`, `load_clubs()`, `load_records()`: Recuperan DataFrames completos.
*   `add_player()`, `add_weekly_record()`: Inserciones a base de datos.
*   `add_multiple_weekly_records()`: Lógica crítica para la carga masiva (transaccional).

#### Vistas (Frontend)
El `main()` de `app.py` actúa como enrutador usando `if/elif` basado en la selección del Sidebar:
*   `if page == "Dashboard"`: Renderiza métricas globales.
*   `elif page == "Jugadores"`: Muestra tablas y perfiles.
*   `elif page == "Agregar Datos"`: Contiene la lógica compleja de Session State para el acumulador de registros ("Batch Entry").

### Deuda Técnica Detectada
*   **Acoplamiento**: La lógica de negocio está mezclada con la presentación.
*   **Mantenibilidad**: Un archivo de 1300+ líneas es difícil de navegar.
*   **Escalabilidad**: Difícil añadir nuevas características sin riesgo de romper las existentes.
