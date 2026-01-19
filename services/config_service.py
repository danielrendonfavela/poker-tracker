import sqlite3
from services.database import get_connection

def get_config(key: str):
    """Obtiene un valor de configuración por su clave."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_config WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_config(key: str, value: str):
    """Guarda o actualiza una configuración."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO app_config (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()

def is_app_configured():
    """Verifica si la instalación inicial se ha completado."""
    return get_config('setup_completed') == 'true'

def initialize_app(club_name: str, admin_name: str, currency: str):
    """Inicializa la app guardando la configuración inicial y creando el club por defecto."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Guardar configuraciones
        cursor.execute("INSERT OR REPLACE INTO app_config (key, value) VALUES ('club_name', ?)", (club_name,))
        cursor.execute("INSERT OR REPLACE INTO app_config (key, value) VALUES ('admin_name', ?)", (admin_name,))
        cursor.execute("INSERT OR REPLACE INTO app_config (key, value) VALUES ('currency', ?)", (currency,))
        
        # 2. Crear club por defecto si no existe
        # Primero verificamos si ya existe algún club para no duplicar si se re-corre
        cursor.execute("SELECT count(*) FROM clubs")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO clubs (club_name) VALUES (?)", (club_name,))
        
        # 3. Marcar setup como completado
        cursor.execute("INSERT OR REPLACE INTO app_config (key, value) VALUES ('setup_completed', 'true')")
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error initializing app: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
