import sqlite3
from services.database import get_connection

CLUBS = [
    'PATOS MX',
    'PP PATOS MX',
    'X',
    'MATA ASES',
    'Bros',
    'Hoja1',
    'PPP',
    'Paradise',
    'Club GG RAGNAR',
    'Suprema',
    'Club GG NPM'
]

def seed_clubs():
    conn = get_connection()
    cursor = conn.cursor()
    
    print("🌱 Sembrando clubes...")
    for club in CLUBS:
        try:
            cursor.execute("INSERT INTO clubs (club_name) VALUES (?)", (club,))
            print(f"   ✅ {club}")
        except sqlite3.IntegrityError:
            print(f"   ⚠️  {club} ya existe")
            
    conn.commit()
    conn.close()
    print("✨ Hecho.")

if __name__ == "__main__":
    seed_clubs()
