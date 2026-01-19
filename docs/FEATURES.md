# Manual de Funcionalidades

## 1. Dashboard
Vista principal que resume el estado del negocio.
*   Métricas KPI: Total Players, Total Clubs, Profit Global, Rake Global.
*   Gráficos: (Si están implementados) Tendencias de ganancias.
*    Tabla Resumen por Club.

## 2. Gestión de Jugadores
*   **Resumen de Ganancias**: Tabla filtrable de cuánto ha ganado/perdido cada jugador históricamente.
*   **Nicknames**: Muestra qué apodos están asociados a qué jugador real. Permite buscar el "dueño" de un nickname desconocido.

## 3. Por Semana
Análisis temporal.
*   **Filtro por Club**: Ver desempeño global o específico de un club.
*   **Resumen Semanal**: Tabla comparativa de todas las semanas registradas.
*   **Detalle de Semana**: Al seleccionar una semana, muestra desglose "Jugador por Jugador" para esa fecha (Top Ganadores/Perdedores).

## 4. Balance
Herramienta financiera para administradores de clubes.
*   **Configuración Financiera**: Permite ajustar `% Comisión`, `% Rakeback` y `Tipo de Cambio` por Club.
*   **Cálculo Automático**: Aplica las fórmulas:
    *   `Comisión = Rake * %Com`
    *   `Rakeback = Rake * %RB`
    *   `Total = Rake - Comisión - Rakeback`
    *   `MXN = Total * TC`

## 5. Registros (Log)
Vista cruda de la base de datos.
*   Tabla completa de todas las partidas registradas.
*   Útil para auditoría o corregir errores puntuales.

## 6. Agregar Datos (Carga)
El módulo principal de operación diaria.
*   **Nuevo Jugador**: Registrar a alguien nuevo en la base de datos.
*   **Carga Masiva (Batch Entry)**:
    1.  Seleccionar Semana y Club (Valores por defecto para todo el lote).
    2.  Usar el formulario para añadir jugadores *uno por uno* a una **Lista Temporal**.
    3.  Revisar la tabla de "Registros Pendientes".
    4.  Pulsar **Guardar Todos** para confirmar la operación en bloque.
