from datetime import datetime
import streamlit as st

def get_current_week_info():
    """Calcula la información de la semana actual (fecha inicio/fin)."""
    # Meses en español
    meses_es = {
        1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
    }
    return meses_es
