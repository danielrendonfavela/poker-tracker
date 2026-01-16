"""
Script para analizar la estructura del archivo Excel y detectar encabezados automáticamente.
"""
import openpyxl
import pandas as pd
from typing import Optional, Tuple, List

KEYWORDS = ['nick', 'profit', 'rake', 'total', 'player', 'jugador', 'nombre']

def find_header_row(sheet, max_rows: int = 50) -> Tuple[Optional[int], List[str]]:
    """
    Busca la fila de encabezado basándose en palabras clave.
    Retorna (número_de_fila, lista_de_columnas_encontradas)
    """
    for row_idx in range(1, min(max_rows + 1, sheet.max_row + 1)):
        row_values = []
        for cell in sheet[row_idx]:
            if cell.value:
                row_values.append(str(cell.value).lower().strip())
        
        # Buscar coincidencias con palabras clave
        matches = [kw for kw in KEYWORDS if any(kw in val for val in row_values)]
        if len(matches) >= 2:  # Al menos 2 palabras clave encontradas
            return row_idx, matches
    
    return None, []


def analyze_excel_file(filepath: str):
    """
    Analiza todas las hojas del archivo Excel.
    """
    wb = openpyxl.load_workbook(filepath, data_only=True)
    
    print("=" * 80)
    print(f"ANÁLISIS DEL ARCHIVO: {filepath}")
    print("=" * 80)
    
    results = {}
    
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        header_row, keywords_found = find_header_row(sheet)
        
        print(f"\n📋 Hoja: '{sheet_name}'")
        print(f"   Dimensiones: {sheet.max_row} filas x {sheet.max_column} columnas")
        
        if header_row:
            print(f"   ✅ Encabezado detectado en fila: {header_row}")
            print(f"   🔑 Keywords encontradas: {keywords_found}")
            
            # Mostrar los encabezados encontrados
            headers = []
            for cell in sheet[header_row]:
                if cell.value:
                    headers.append(str(cell.value))
            print(f"   📊 Columnas: {headers[:10]}{'...' if len(headers) > 10 else ''}")
            
            # Contar filas de datos (aproximadamente)
            data_rows = sheet.max_row - header_row
            print(f"   📈 Filas de datos (aprox): {data_rows}")
            
            results[sheet_name] = {
                'header_row': header_row,
                'keywords': keywords_found,
                'headers': headers,
                'data_rows': data_rows
            }
        else:
            print(f"   ⚠️  No se detectó encabezado con palabras clave")
            results[sheet_name] = None
    
    wb.close()
    return results


def extract_data_from_sheet(filepath: str, sheet_name: str, header_row: int) -> pd.DataFrame:
    """
    Extrae datos de una hoja específica comenzando desde la fila de encabezado.
    """
    df = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row - 1)
    # Limpiar columnas sin nombre
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df


if __name__ == "__main__":
    filepath = "Club Patos (Autoguardado).xlsx"
    results = analyze_excel_file(filepath)
    
    print("\n" + "=" * 80)
    print("RESUMEN DE HOJAS CON DATOS VÁLIDOS:")
    print("=" * 80)
    
    valid_sheets = {k: v for k, v in results.items() if v is not None}
    print(f"\n✅ Hojas con encabezado detectado: {len(valid_sheets)}")
    for sheet_name in valid_sheets:
        print(f"   - {sheet_name}")
    
    invalid_sheets = [k for k, v in results.items() if v is None]
    print(f"\n⚠️  Hojas sin encabezado detectado: {len(invalid_sheets)}")
    for sheet_name in invalid_sheets:
        print(f"   - {sheet_name}")
