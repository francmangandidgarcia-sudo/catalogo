import os
import re
import pandas as pd
import streamlit as str_m

# Configuración de apariencia estilo App Móvil
str_m.set_page_config(
    page_title="Catálogo de Frenos", page_icon="🚘", layout="centered"
)

str_m.title("🚘 Catálogo de Pastillas/Frenos")
str_m.write("Buscador Automotriz Local Autónomo")

# Función matemática para verificar años y rangos (Ej: 1990-1993)
def validar_anio(texto_celda, anio_buscado):
    if not anio_buscado:
        return True
    texto_celda = str(texto_celda).strip()

    if anio_buscado in texto_celda:
        return True

    rangos = re.findall(r"(\d{4})\s*-\s*(\d{4})", texto_celda)
    for inicio, fin in rangos:
        if int(inicio) <= int(anio_buscado) <= int(fin):
            return True
    return False

# Formulario de entradas en pantalla con las casillas separadas
with str_m.form("buscador_form"):
    txt_marca = str_m.text_input("1. Marca (ej: Acura, Audi...)").strip().lower()
    txt_modelo = str_m.text_input("2. Modelo / Motor (ej: Integra, CL...)").strip().lower()
    txt_anio = str_m.text_input("3. Año exacto (ej: 1990, 1998...)").strip()
    btn_buscar = str_m.form_submit_button("🔍 Buscar", use_container_width=True)

if btn_buscar:
    if not txt_marca and not txt_modelo and not txt_anio:
        str_m.warning("⚠️ Escribe al menos un dato para filtrar.")
    else:
        # LEER DIRECTAMENTE TU EXCEL LOCAL EN EL ESCRITORIO
        archivo_excel = "datos.xlsx"

        if not os.path.exists(archivo_excel):
            str_m.error("❌ No se encontró el archivo 'datos.xlsx' en el Escritorio. Por favor, colócalo ahí.")
        else:
            try:
                # Leemos el Excel de forma plana sin asumir títulos de columnas
                df = pd.read_excel(archivo_excel, header=None)

                # Limpieza absoluta de formatos numéricos decimales (.0) de Excel
                df_str = df.fillna("").astype(str)
                for col in df_str.columns:
                    df_str[col] = df_str[col].str.replace(r"\.0$", "", regex=True).str.strip()

                filas_coincidentes = []

                # Recorrido inteligente por la estructura ordenada de tu documento
                for idx, fila in df_str.iterrows():
                    lista_celdas = fila.values.tolist()
                    

streamlit
pandas
openpyxl
