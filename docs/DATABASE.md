# Documentación de Base de Datos

La aplicación utiliza **SQLite** (`poker_tracker.db`).

## Diagrama E-R Simplificado
*   **Players** (1) ---- (N) **Records**
*   **Clubs** (1) ---- (N) **Records**
*   **Players** (1) ---- (N) **Nickname Mappings**

## Esquema de Tablas

### `players`
Almacena la identidad única de cada jugador real.
*   `id` (PK): Identificador único.
*   `real_name`: Nombre real del jugador (Ej: "Juan Pérez").
*   `status`: Estado ('active', 'inactive', 'banned').

### `clubs`
Catálogo de clubes de poker.
*   `id` (PK): Identificador único.
*   `club_name`: Nombre del club (Ej: "PP PATOS MX").

### `records`
El registro principal de actividad (una sesión o semana de juego).
*   `id` (PK): Identificador único.
*   `week`: Identificador de semana (Ej: "19 May - 25 May").
*   `player_id` (FK): Referencia a `players`.
*   `club_id` (FK): Referencia a `clubs`.
*   `raw_nickname`: El nickname usado en esa sesión específica.
*   `profit`: Ganancia bruta.
*   `rake`: Comisión tomada.
*   `total`: Balance neto (`profit - rake`).

### `nickname_mappings`
Resuelve la relación "Un jugador tiene muchos nicknames en diferentes clubes".
*   `id` (PK): Identificador.
*   `original_nick`: El apodo usado en la app de poker.
*   `player_id` (FK): A quién pertenece este apodo.
*   `club_id` (FK): En qué club se usa (opcional).
