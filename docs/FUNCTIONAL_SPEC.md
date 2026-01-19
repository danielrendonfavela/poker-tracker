# Especificación Funcional Detallada - Poker Tracker (Dev Monolith)

Este documento detalla **exactamente** qué hace cada vista de la aplicación actual (`dev`) para garantizar paridad funcional del 100% durante el refactoring.

## 1. Dashboard (`🏠 Dashboard`)
**Objetivo**: Vista de alto nivel de todo el sistema.

*   **Entradas**: Ninguna.
*   **Lógica de Carga**:
    *   `load_dashboard_stats()`: Queries `COUNT(*)` en players, clubs, records.
    *   Financiero: `SUM(profit)`, `SUM(rake)` de todos los records.
    *   `load_club_summary()`: Agrupa records por club.
*   **Elementos UI**:
    *   Fila 1 Métricas: Jugadores, Clubes, Registros, Semanas.
    *   Fila 2 Métricas: Nicknames, Profit Total, Rake Total, Balance Total.
    *   Tabla "Resumen por Club": Columnas [Club, Registros, Jugadores, Semanas, Profit Total, Rake Total, Balance Total].
*   **Formato**: Moneda en `$`, miles con comas.

## 2. Jugadores (`👥 Jugadores`)
**Objetivo**: Análisis histórico de jugadores.

### Tab 1: Resumen de Ganancias
*   **Entradas**:
    *   `search` (Texto): Filtra por nombre de jugador (case-insensitive).
    *   `sort_by` (Select): Opciones `profit_total`, `rake_total`, `partidas`.
*   **Lógica**:
    *   `load_player_summary()`: Query agrupada por jugador.
*   **Métricas Dinámicas**: Recalcula "Profit Total", "Rake Total" basado en los jugadores filtrados visibles.
*   **Tabla**: [Jugador, Partidas, Profit Total, Rake Total, Balance, Clubes].

### Tab 2: Nicknames por Jugador
*   **Entradas**: `search_nick` (Texto).
*   **Lógica**: Busca en `nombre_real` OR `nicknames`.
*   **Tabla**: [Nombre Real, Nicknames (concatenados), # Nicks, Clubes (concatenados), # Clubes].

## 3. Clubes (`🏢 Clubes`)
**Objetivo**: Auditoría de desempeño de clubes.

*   **Entradas**: Ninguna.
*   **Métricas**: Total Clubes, Profit Global, Rake Global, Registros Totales.
*   **Tabla**: Misma structure que Dashboard [Club, Registros, Jugadores, Semanas, Profit, Rake, Balance].

## 4. Por Semana (`📅 Por Semana`)
**Objetivo**: Análisis temporal profundo.

*   **Filtro Global**: `selected_club` (Selectbox: "Todos" + lista de DB).
    *   *Nota*: Afecta a TODAS las tabs internas.

### Tab 1: Resumen Semanal
*   **Lógica**:
    *   `load_weekly_summary(club_name)`: Si es "Todos", agrupa por `week, club_name`. Si es específico, filtra `WHERE club_name = ?`.
*   **Métricas**: Total Semanas, Profit Total, Rake Total, Jugadores Promedio/Semana.
*   **Tabla**: [Semana, Club, Registros, Jugadores, Profit Total, Rake Total, Balance].

### Tab 2: Detalle por Semana
*   **Selector**: `selected_week` (Formato "YYYY - Semana"). Se puebla via `get_available_weeks(club_name)`.
*   **Lógica**: `load_week_details(week, club)`.
*   **UI**:
    *   Métricas de ESA semana (Jugadores, Profit, Rake, Balance).
    *   **Tabla Principal**: Detalle registro a registro [Año, Semana, Club, Jugador, Nickname, Profit, Rake, Balance].
    *   **Top 5 Ganadores**: `nlargest(5, 'profit')`.
    *   **Top 5 Perdedores**: `nsmallest(5, 'profit')`.

## 5. Balance (`💰 Balance`)
**Objetivo**: Herramienta de cálculo financiero para pagos.

*   **Entradas Críticas**:
    *   `selected_week` (Selectbox).
*   **Gestión de Estado (Session State)**:
    *   `st.session_state.club_config`: Diccionario persistente.
    *   Se inicializa con `default_config` hardcodeada (ej: PATOS MX: Com 11%, RB 42.4%, TC 10.0).
*   **UI Dinámica**:
    *   Expander "⚙️ Configuración por Club".
    *   Itera sobre los clubes presentes en la semana seleccionada.
    *   Genera 3 inputs numéricos POR CLUB: `Com%`, `RB%`, `TC`.
    *   Estos inputs actualizan `st.session_state.club_config` en tiempo real.
*   **Cálculo en Vivo**:
    *   Itera sobre el DataFrame de la semana.
    *   Para cada fila (club): Busca su config en session_state.
    *   `Comisión = Rake * (Com%)`
    *   `Rakeback = Rake * (RB%)`
    *   `Total USD = Rake - Comisión - Rakeback`
    *   `MXN = Total USD * TC`
*   **Salida**:
    *   Tabla con columnas financieras detalladas: [Club, Rake, Com%, Comisión, RB%, RB, Total, TC, MXN].
    *   **Profit Club (MXN Total)**: Tarjeta verde grande con la suma de MXN.
    *   Gráfico de Barras (Plotly) comparando MXN por club.

## 6. Registros (`📝 Registros`)
**Objetivo**: Vista cruda ("Raw Data") para auditoría.

*   **Filtros (Cascada)**:
    1.  `Semana` (Todas / Lista).
    2.  `Club` (Todos / Lista).
    3.  `Jugador` (Todos / Lista).
*   **Lógica**: Carga TODO `load_records()` y luego aplica filtros pandas `.loc[]`.
*   **Métricas**: Recalculadas sobre la vista filtrada.
*   **Tabla**: [ID, Semana, Jugador, Club, Nickname, Profit, Rake, Total].

## 7. Agregar Datos (`➕ Agregar Datos`)
**Objetivo**: Ingesta de datos.

### Tab 1: Nuevo Jugador
*   **Formulario**:
    *   Nombre Real (Obligatorio).
    *   Estado (active/inactive).
    *   Nickname (Opcional).
    *   Club para nickname (Opcional).
*   **Lógica**:
    *   Inserta en `players`.
    *   Si hay nickname, inserta en `nickname_mappings`.

### Tab 2: Nueva Semana
*   **Configuración Cabeza**:
    *   Fecha Inicio (DateInput, default Lunes actual).
    *   Fecha Fin (DateInput, default +6 días).
    *   Club (Selectbox).
    *   *Genera string `week_format` automático (ej: "19 May - 25 May")*.

#### Subtab: Registro Múltiple (Batch Entry) **[CRÍTICO]**
Es la funcionalidad más compleja de migrar.
*   **Session State**: `st.session_state.pending_records` (Lista de dicts).
*   **Formulario Inline**:
    *   Jugador (Select), Nickname (Text), Profit (Num), Rake (Num).
    *   Botón "➕ Agregar": Añade a la lista en memoria `pending_records` y hace `rerun()`.
*   **Vista Previa**:
    *   Si hay registros pendientes, muestra Tabla temporal.
    *   Métricas temporales (Profit del lote, Rake del lote).
*   **Persistencia**:
    *   Botón "💾 Guardar Todos": Llama a `add_multiple_weekly_records(list)`.
    *   Botón "🗑️ Limpiar Lista": Resetea la lista.

### Tab 3: Re-importar
*   Botón placeholder actualmente.
