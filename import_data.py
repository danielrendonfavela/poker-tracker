"""
Script para importar todos los registros semanales del Excel a la base de datos.
Detecta automáticamente las semanas y carga los datos de Profit, Rake, Balance, etc.
"""
import pandas as pd
import sqlite3
import re
from collections import defaultdict

DATABASE_PATH = "poker_tracker.db"
EXCEL_FILE = "Club Patos (Autoguardado).xlsx"

# Configuración de las hojas con datos de jugadores
PLAYER_SHEETS = {
    'PATOS MX': 3,
    'PP PATOS MX': 6,
    'X': 4,
    'MATA ASES': 4,
    'Bros': 7,
    'Hoja1': 3,
    'PPP': 4,
    'Paradise': 5,
    'Club GG RAGNAR': 4,
    'Suprema': 6,
    'Club GG NPM': 4,
}


def get_connection():
    return sqlite3.connect(DATABASE_PATH)


def find_nick_column(df, header_row: int) -> int:
    """Encuentra el índice de la columna 'Nick'."""
    header = df.iloc[header_row - 1]
    for idx, val in enumerate(header):
        if str(val).lower().strip() == 'nick':
            return idx
    return -1


def find_column_indices(df, header_row: int) -> dict:
    """Encuentra los índices de las columnas importantes."""
    header = df.iloc[header_row - 1]
    indices = {}
    
    for idx, val in enumerate(header):
        val_lower = str(val).lower().strip()
        if val_lower == 'nick':
            indices['nick'] = idx
            indices['name'] = idx - 1  # Nombre está antes de Nick
        elif val_lower == 'profit':
            indices['profit'] = idx
        elif val_lower == 'rake':
            indices['rake'] = idx
        elif 'balance' in val_lower and 'mxn' not in val_lower:
            if 'balance' not in indices:
                indices['balance'] = idx
        elif 'balance' in val_lower and 'mxn' in val_lower:
            indices['balance_mxn'] = idx
        elif val_lower == 'rb':
            indices['rb'] = idx
        elif val_lower == 'rb %':
            indices['rb_pct'] = idx
    
    return indices


def is_week_header(value) -> bool:
    """Verifica si un valor es un encabezado de semana (ej: '20 Oct / 27 Oct')."""
    if pd.isna(value):
        return False
    val_str = str(value).strip()
    # Patrón: número + mes + / + número + mes
    pattern = r'\d{1,2}\s*\w{3,4}\s*/\s*\d{1,2}\s*\w{3,4}'
    return bool(re.search(pattern, val_str, re.IGNORECASE))


def extract_week_blocks(df, header_row: int, col_indices: dict) -> list:
    """
    Extrae bloques de datos por semana.
    Retorna lista de (week_name, rows_data)
    """
    name_col = col_indices.get('name', 0)
    nick_col = col_indices.get('nick', 1)
    
    blocks = []
    current_week = None
    current_rows = []
    
    # El encabezado tiene la primera semana
    first_week = df.iloc[header_row - 1, name_col]
    if pd.notna(first_week):
        current_week = str(first_week).strip()
    
    for row_idx in range(header_row, len(df)):
        row = df.iloc[row_idx]
        name_val = row[name_col]
        nick_val = row[nick_col]
        
        # Verificar si es un nuevo encabezado de semana
        if is_week_header(name_val):
            # Guardar el bloque anterior
            if current_week and current_rows:
                blocks.append((current_week, current_rows))
            current_week = str(name_val).strip()
            current_rows = []
            continue
        
        # Si tenemos datos válidos, agregarlos
        if pd.notna(nick_val) and str(nick_val).strip():
            row_data = {
                'name': str(name_val).strip() if pd.notna(name_val) else "",
                'nick': str(nick_val).strip(),
            }
            
            # Extraer valores numéricos
            for field in ['profit', 'rake', 'balance', 'balance_mxn', 'rb']:
                if field in col_indices:
                    val = row[col_indices[field]]
                    if pd.notna(val):
                        try:
                            row_data[field] = float(val)
                        except (ValueError, TypeError):
                            row_data[field] = 0.0
                    else:
                        row_data[field] = 0.0
            
            current_rows.append(row_data)
    
    # No olvidar el último bloque
    if current_week and current_rows:
        blocks.append((current_week, current_rows))
    
    return blocks


def import_players_to_db():
    """Importa los jugadores únicos a la tabla players."""
    jugadores_df = pd.read_csv("jugadores_unicos.csv")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    inserted = 0
    for _, row in jugadores_df.iterrows():
        try:
            cursor.execute(
                "INSERT INTO players (real_name, status) VALUES (?, 'active')",
                (row['nombre_real'],)
            )
            inserted += 1
        except sqlite3.IntegrityError:
            pass  # Ya existe
    
    conn.commit()
    conn.close()
    
    print(f"✅ Jugadores importados: {inserted}")
    return inserted


def import_nickname_mappings():
    """Importa el mapeo de nicknames."""
    mapeo_df = pd.read_csv("mapeo_jugadores_v2.csv")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Obtener IDs de jugadores y clubes
    cursor.execute("SELECT id, real_name FROM players")
    players = {name.lower(): id for id, name in cursor.fetchall()}
    
    cursor.execute("SELECT id, club_name FROM clubs")
    clubs = {name.lower(): id for id, name in cursor.fetchall()}
    
    inserted = 0
    for _, row in mapeo_df.iterrows():
        nick = row['original_nick']
        player_name = row['nombre_real_normalizado'] if pd.notna(row['nombre_real_normalizado']) else row['nombre_real']
        club_names = row['clubes'].split(', ') if pd.notna(row['clubes']) else []
        
        player_id = players.get(player_name.lower()) if pd.notna(player_name) else None
        
        for club_name in club_names:
            club_id = clubs.get(club_name.lower().strip())
            if club_id:
                try:
                    cursor.execute(
                        "INSERT INTO nickname_mappings (original_nick, player_id, club_id) VALUES (?, ?, ?)",
                        (nick, player_id, club_id)
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    pass
    
    conn.commit()
    conn.close()
    
    print(f"✅ Mapeos de nicknames importados: {inserted}")
    return inserted


def import_weekly_records():
    """Importa todos los registros semanales a la base de datos."""
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Obtener IDs de jugadores y clubes
    cursor.execute("SELECT id, club_name FROM clubs")
    clubs = {name: id for id, name in cursor.fetchall()}
    
    # Obtener mapeo de nicknames
    cursor.execute("""
        SELECT nm.original_nick, nm.player_id, c.club_name
        FROM nickname_mappings nm
        JOIN clubs c ON nm.club_id = c.id
    """)
    nick_to_player = {}
    for nick, player_id, club_name in cursor.fetchall():
        nick_to_player[(nick.lower(), club_name)] = player_id
    
    total_records = 0
    
    for sheet_name, header_row in PLAYER_SHEETS.items():
        print(f"\n📋 Procesando: {sheet_name}")
        
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, header=None)
            col_indices = find_column_indices(df, header_row)
            
            if 'nick' not in col_indices:
                print(f"   ⚠️  No se encontró columna Nick")
                continue
            
            blocks = extract_week_blocks(df, header_row, col_indices)
            club_id = clubs.get(sheet_name)
            
            if not club_id:
                print(f"   ⚠️  Club no encontrado en DB")
                continue
            
            sheet_records = 0
            for week, rows in blocks:
                for row_data in rows:
                    nick = row_data['nick']
                    player_id = nick_to_player.get((nick.lower(), sheet_name))
                    
                    profit = row_data.get('profit', 0.0)
                    rake = row_data.get('rake', 0.0)
                    total = row_data.get('balance', profit - rake)  # Balance o calcular
                    
                    cursor.execute("""
                        INSERT INTO records (week, player_id, club_id, raw_nickname, profit, rake, total)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (week, player_id, club_id, nick, profit, rake, total))
                    
                    sheet_records += 1
            
            print(f"   ✅ {sheet_records} registros ({len(blocks)} semanas)")
            total_records += sheet_records
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    conn.commit()
    conn.close()
    
    return total_records


def main():
    print("=" * 60)
    print("IMPORTACIÓN DE DATOS A LA BASE DE DATOS")
    print("=" * 60)
    
    # 1. Importar jugadores
    print("\n📥 Paso 1: Importando jugadores...")
    import_players_to_db()
    
    # 2. Importar mapeo de nicknames
    print("\n📥 Paso 2: Importando mapeo de nicknames...")
    import_nickname_mappings()
    
    # 3. Importar registros semanales
    print("\n📥 Paso 3: Importando registros semanales...")
    total = import_weekly_records()
    
    print("\n" + "=" * 60)
    print(f"🎉 IMPORTACIÓN COMPLETADA")
    print(f"   Total de registros importados: {total}")
    print("=" * 60)
    
    # Verificar
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM players")
    print(f"\n📊 Jugadores en DB: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM nickname_mappings")
    print(f"📊 Mapeos de nicknames: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM records")
    print(f"📊 Registros totales: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(DISTINCT week) FROM records")
    print(f"📊 Semanas únicas: {cursor.fetchone()[0]}")
    
    conn.close()


if __name__ == "__main__":
    main()
