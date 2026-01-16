"""
Script para extraer todos los nicknames únicos y generar mapeo_jugadores.csv
Usa rapidfuzz para sugerir agrupaciones de nicknames similares.
"""
import pandas as pd
import openpyxl
from collections import defaultdict
from rapidfuzz import fuzz, process
import re
import sqlite3

# Configuración de las hojas con datos de jugadores
# Solo incluimos hojas que tienen la columna 'Nick' con datos de jugadores
PLAYER_SHEETS = {
    'PATOS MX': {'header_row': 3, 'nick_col': 'Nick'},
    'PP PATOS MX': {'header_row': 6, 'nick_col': 'Nick'},
    'X': {'header_row': 4, 'nick_col': 'Nick'},
    'MATA ASES': {'header_row': 4, 'nick_col': 'Nick'},
    'Bros': {'header_row': 7, 'nick_col': 'Nick'},
    'Hoja1': {'header_row': 3, 'nick_col': 'Nick'},
    'PPP': {'header_row': 4, 'nick_col': 'Nick'},
    'Paradise': {'header_row': 5, 'nick_col': 'Nick'},
    'Club GG RAGNAR': {'header_row': 4, 'nick_col': 'Nick'},
    'Suprema': {'header_row': 6, 'nick_col': 'Nick'},
    'Club GG NPM': {'header_row': 4, 'nick_col': 'Nick'},
}

def clean_nickname(nick: str) -> str:
    """Limpia y normaliza un nickname."""
    if pd.isna(nick) or nick is None:
        return ""
    nick = str(nick).strip()
    # Eliminar caracteres especiales comunes pero mantener acentos
    nick = re.sub(r'[\s\-_\.]+', ' ', nick)
    return nick.strip()


def extract_all_nicknames(filepath: str) -> dict:
    """
    Extrae todos los nicknames únicos de todas las hojas.
    Retorna un diccionario {nickname: [lista de clubes donde aparece]}
    """
    all_nicknames = defaultdict(set)
    
    print("=" * 60)
    print("EXTRACCIÓN DE NICKNAMES")
    print("=" * 60)
    
    for sheet_name, config in PLAYER_SHEETS.items():
        try:
            df = pd.read_excel(
                filepath, 
                sheet_name=sheet_name, 
                header=config['header_row'] - 1
            )
            
            if config['nick_col'] in df.columns:
                nicks = df[config['nick_col']].dropna().unique()
                valid_nicks = 0
                for nick in nicks:
                    cleaned = clean_nickname(nick)
                    if cleaned and len(cleaned) > 1:  # Ignorar nicks muy cortos
                        all_nicknames[cleaned].add(sheet_name)
                        valid_nicks += 1
                
                print(f"✅ {sheet_name}: {valid_nicks} nicknames extraídos")
            else:
                print(f"⚠️  {sheet_name}: Columna 'Nick' no encontrada")
                
        except Exception as e:
            print(f"❌ {sheet_name}: Error - {e}")
    
    return all_nicknames


def group_similar_nicknames(nicknames: list, threshold: int = 75) -> dict:
    """
    Agrupa nicknames similares usando rapidfuzz.
    Retorna un diccionario {nickname: nombre_sugerido}
    """
    # Ordenar por longitud (los más largos primero, suelen ser más descriptivos)
    sorted_nicks = sorted(nicknames, key=len, reverse=True)
    
    groups = {}  # {representative: [similar_nicks]}
    assigned = set()
    
    for nick in sorted_nicks:
        if nick in assigned:
            continue
            
        # Este nickname será el representante de su grupo
        nick_lower = nick.lower()
        similar = [nick]
        assigned.add(nick)
        
        # Buscar nicknames similares
        for other in sorted_nicks:
            if other in assigned:
                continue
            
            # Calcular similitud
            ratio = fuzz.ratio(nick_lower, other.lower())
            partial_ratio = fuzz.partial_ratio(nick_lower, other.lower())
            token_ratio = fuzz.token_sort_ratio(nick_lower, other.lower())
            
            max_ratio = max(ratio, partial_ratio, token_ratio)
            
            if max_ratio >= threshold:
                similar.append(other)
                assigned.add(other)
        
        groups[nick] = similar
    
    return groups


def create_mapping_csv(all_nicknames: dict, output_file: str = "mapeo_jugadores.csv"):
    """
    Crea el archivo CSV de mapeo de jugadores.
    """
    nicknames_list = list(all_nicknames.keys())
    print(f"\n📊 Total de nicknames únicos: {len(nicknames_list)}")
    
    # Agrupar nicknames similares
    print("\n🔍 Agrupando nicknames similares...")
    groups = group_similar_nicknames(nicknames_list, threshold=70)
    print(f"📦 Grupos formados: {len(groups)}")
    
    # Crear DataFrame para el CSV
    rows = []
    group_id = 0
    
    for representative, similar_nicks in groups.items():
        group_id += 1
        
        # Si hay múltiples nicks similares, usar el más largo como sugerencia
        if len(similar_nicks) > 1:
            suggested_name = max(similar_nicks, key=len)
            # Limpiar y capitalizar
            suggested_name = suggested_name.title()
        else:
            suggested_name = ""  # Dejar vacío para que el usuario lo llene
        
        for nick in similar_nicks:
            clubs = ", ".join(sorted(all_nicknames.get(nick, [])))
            rows.append({
                'original_nick': nick,
                'nombre_real_sugerido': suggested_name if len(similar_nicks) > 1 else "",
                'grupo_id': group_id,
                'clubes': clubs,
                'count_similar': len(similar_nicks)
            })
    
    # Ordenar por grupo y luego por nick
    df = pd.DataFrame(rows)
    df = df.sort_values(['grupo_id', 'original_nick'])
    
    # Guardar CSV
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ Archivo creado: {output_file}")
    
    # Estadísticas
    singles = len([g for g in groups.values() if len(g) == 1])
    multiples = len([g for g in groups.values() if len(g) > 1])
    print(f"\n📈 Estadísticas:")
    print(f"   - Nicknames únicos (sin similares): {singles}")
    print(f"   - Grupos con múltiples similares: {multiples}")
    print(f"   - Total nicknames agrupados: {sum(len(g) for g in groups.values() if len(g) > 1)}")
    
    return df


def insert_clubs_to_db(all_nicknames: dict, db_path: str = "poker_tracker.db"):
    """
    Inserta los clubes encontrados en la base de datos.
    """
    # Obtener todos los clubes únicos
    all_clubs = set()
    for clubs in all_nicknames.values():
        all_clubs.update(clubs)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for club_name in sorted(all_clubs):
        try:
            cursor.execute("INSERT INTO clubs (club_name) VALUES (?)", (club_name,))
        except sqlite3.IntegrityError:
            pass  # El club ya existe
    
    conn.commit()
    
    # Verificar
    cursor.execute("SELECT * FROM clubs ORDER BY club_name")
    clubs = cursor.fetchall()
    print(f"\n🏢 Clubes insertados en la base de datos: {len(clubs)}")
    for club in clubs:
        print(f"   - ID {club[0]}: {club[1]}")
    
    conn.close()


if __name__ == "__main__":
    filepath = "Club Patos (Autoguardado).xlsx"
    
    # Extraer nicknames
    all_nicknames = extract_all_nicknames(filepath)
    
    # Crear CSV de mapeo
    df = create_mapping_csv(all_nicknames)
    
    # Insertar clubes en la DB
    insert_clubs_to_db(all_nicknames)
    
    print("\n" + "=" * 60)
    print("🎉 PROCESO COMPLETADO")
    print("=" * 60)
    print("\n📝 Próximos pasos:")
    print("   1. Revisa el archivo 'mapeo_jugadores.csv'")
    print("   2. Completa la columna 'nombre_real_sugerido' para cada nickname")
    print("   3. Los nicknames similares ya están agrupados (columna 'grupo_id')")
    print("   4. Si varios nicks pertenecen a la misma persona, usa el mismo nombre_real")
