"""
Script v2 para extraer todos los nicknames con sus nombres reales asociados.
Detecta automáticamente la columna de nombre real (anterior a Nick).
"""
import pandas as pd
import openpyxl
from collections import defaultdict
from rapidfuzz import fuzz
import re
import sqlite3

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


def clean_text(text: str) -> str:
    """Limpia y normaliza texto."""
    if pd.isna(text) or text is None:
        return ""
    text = str(text).strip()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def find_nick_column(df, header_row: int) -> int:
    """Encuentra el índice de la columna 'Nick'."""
    header = df.iloc[header_row - 1]
    for idx, val in enumerate(header):
        if str(val).lower().strip() == 'nick':
            return idx
    return -1


def extract_nicknames_with_names(filepath: str) -> list:
    """
    Extrae todos los nicknames con sus nombres reales asociados.
    Retorna una lista de diccionarios con nick, nombre_real, club.
    """
    all_records = []
    
    print("=" * 60)
    print("EXTRACCIÓN DE NICKNAMES CON NOMBRES REALES")
    print("=" * 60)
    
    for sheet_name, header_row in PLAYER_SHEETS.items():
        try:
            df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
            
            nick_col = find_nick_column(df, header_row)
            if nick_col < 1:
                print(f"⚠️  {sheet_name}: No se encontró columna Nick o no tiene columna anterior")
                continue
            
            name_col = nick_col - 1  # Columna de nombre real está antes del Nick
            
            # Extraer datos desde la fila después del encabezado
            data = df.iloc[header_row:, [name_col, nick_col]].copy()
            data.columns = ['nombre_real', 'nick']
            
            # Limpiar y filtrar
            data['nombre_real'] = data['nombre_real'].apply(clean_text)
            data['nick'] = data['nick'].apply(clean_text)
            data = data[(data['nick'].str.len() > 1) & (data['nombre_real'].str.len() > 1)]
            data['club'] = sheet_name
            
            all_records.extend(data.to_dict('records'))
            
            print(f"✅ {sheet_name}: {len(data)} registros extraídos")
            
        except Exception as e:
            print(f"❌ {sheet_name}: Error - {e}")
    
    return all_records


def consolidate_mappings(records: list) -> pd.DataFrame:
    """
    Consolida los registros para crear el mapeo final.
    Para cada nick, busca el nombre real más común o consistente.
    """
    # Agrupar por nick
    nick_to_names = defaultdict(lambda: defaultdict(int))
    nick_to_clubs = defaultdict(set)
    
    for record in records:
        nick = record['nick'].lower()
        name = record['nombre_real']
        club = record['club']
        
        nick_to_names[nick][name] += 1
        nick_to_clubs[nick].add(club)
    
    # Crear DataFrame consolidado
    rows = []
    for nick_lower, names in nick_to_names.items():
        # Encontrar el nombre más común
        most_common_name = max(names.items(), key=lambda x: x[1])[0]
        
        # Obtener el nick original (con mayúsculas como aparece más frecuentemente)
        original_nicks = [r['nick'] for r in records if r['nick'].lower() == nick_lower]
        nick_counts = defaultdict(int)
        for n in original_nicks:
            nick_counts[n] += 1
        original_nick = max(nick_counts.items(), key=lambda x: x[1])[0]
        
        clubs = ", ".join(sorted(nick_to_clubs[nick_lower]))
        all_names = list(names.keys())
        
        rows.append({
            'original_nick': original_nick,
            'nombre_real': most_common_name,
            'nombres_alternativos': "; ".join([n for n in all_names if n != most_common_name]) if len(all_names) > 1 else "",
            'clubes': clubs,
            'frecuencia': sum(names.values())
        })
    
    df = pd.DataFrame(rows)
    df = df.sort_values('nombre_real')
    
    return df


def normalize_player_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza los nombres de jugadores para unificar variaciones.
    """
    # Agrupar nombres similares
    names = df['nombre_real'].unique().tolist()
    name_groups = {}  # nombre_normalizado -> [nombres_variantes]
    
    for name in sorted(names, key=len, reverse=True):
        if name in [n for variants in name_groups.values() for n in variants]:
            continue
        
        # Buscar nombres similares
        similar = [name]
        for other in names:
            if other == name or other in [n for variants in name_groups.values() for n in variants]:
                continue
            
            ratio = fuzz.ratio(name.lower(), other.lower())
            token_ratio = fuzz.token_set_ratio(name.lower(), other.lower())
            
            if max(ratio, token_ratio) >= 85:
                similar.append(other)
        
        # Usar el nombre más largo como canónico
        canonical = max(similar, key=len)
        name_groups[canonical] = similar
    
    # Crear mapeo de normalización
    name_mapping = {}
    for canonical, variants in name_groups.items():
        for variant in variants:
            name_mapping[variant] = canonical
    
    # Aplicar normalización
    df['nombre_real_normalizado'] = df['nombre_real'].map(name_mapping)
    
    return df


def save_mapping_csv(df: pd.DataFrame, output_file: str = "mapeo_jugadores_v2.csv"):
    """Guarda el mapeo en CSV."""
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ Archivo creado: {output_file}")
    return df


def save_unique_players_csv(df: pd.DataFrame, output_file: str = "jugadores_unicos.csv"):
    """
    Crea un CSV con los jugadores únicos basado en nombre real normalizado.
    """
    # Agrupar por nombre normalizado
    player_data = []
    
    for name, group in df.groupby('nombre_real_normalizado'):
        nicks = group['original_nick'].unique().tolist()
        clubs = set()
        for c in group['clubes']:
            clubs.update(c.split(', '))
        
        player_data.append({
            'nombre_real': name,
            'nicknames': "; ".join(nicks),
            'num_nicknames': len(nicks),
            'clubes': ", ".join(sorted(clubs)),
            'num_clubes': len(clubs)
        })
    
    players_df = pd.DataFrame(player_data)
    players_df = players_df.sort_values('nombre_real')
    players_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ Archivo creado: {output_file}")
    
    return players_df


if __name__ == "__main__":
    filepath = "Club Patos (Autoguardado).xlsx"
    
    # Extraer nicknames con nombres
    records = extract_nicknames_with_names(filepath)
    print(f"\n📊 Total registros extraídos: {len(records)}")
    
    # Consolidar mapeos
    df = consolidate_mappings(records)
    print(f"📊 Nicknames únicos: {len(df)}")
    
    # Normalizar nombres
    df = normalize_player_names(df)
    
    # Guardar CSV de mapeo completo
    save_mapping_csv(df, "mapeo_jugadores_v2.csv")
    
    # Guardar CSV de jugadores únicos
    players_df = save_unique_players_csv(df, "jugadores_unicos.csv")
    
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"✅ Jugadores únicos identificados: {len(players_df)}")
    print(f"✅ Total de nicknames mapeados: {len(df)}")
    
    # Mostrar algunos jugadores con múltiples nicks
    multi_nick = players_df[players_df['num_nicknames'] > 1].head(10)
    if not multi_nick.empty:
        print("\n🎮 Jugadores con múltiples nicknames:")
        for _, row in multi_nick.iterrows():
            print(f"   {row['nombre_real']}: {row['nicknames']}")
