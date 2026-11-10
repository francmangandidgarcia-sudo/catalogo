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
    txt_marca = str_m.text_input("1. Marca (Columna A - ej: Acura, Audi...)").strip().lower()
    txt_modelo = str_m.text_input("2. Modelo / Motor (Columna B - ej: Integra, CL...)").strip().lower()
    txt_anio = str_m.text_input("3. Año exacto (Columna C - ej: 1990, 1998...)").strip()
    btn_buscar = str_m.form_submit_button("🔍 Buscar Repuestos", use_container_width=True)

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
                    
                    if len(lista_celdas) < 3:
                        continue

                    # Asignación por posiciones físicas fijas (A=0, B=1, C=2)
                    val_marca = str(lista_celdas[0]).strip().lower()
                    val_modelo = str(lista_celdas[1]).strip().lower()
                    val_anio_celda = str(lista_celdas[2]).strip()

                    # Saltamos cabeceras o filas vacías si las hay
                    if "hoja de" in val_marca or "catálogo" in val_marca:
                        continue

                    # Comprobación de criterios cruzados por columnas individuales
                    cumple_marca = not txt_marca or (txt_marca in val_marca)
                    cumple_modelo = not txt_modelo or (txt_modelo in val_modelo)
                    cumple_anio = not txt_anio or validar_anio(val_anio_celda, txt_anio)

                    if cumple_marca and cumple_modelo and cumple_anio:
                        filas_coincidentes.append(lista_celdas)

                # Desplegar resultados encontrados
                if len(filas_coincidentes) > 0:
                    str_m.success(f"📦 {len(filas_coincidentes)} registro(s) encontrado(s)")

                    for item in filas_coincidentes:
                        marca_head = str(item[0]).strip().upper() if str(item[0]).strip() else "MARCA GENERAL"
                        modelo_sub = str(item[1]).strip() if str(item[1]).strip() else "N/A"
                        anio_sub = str(item[2]).strip() if str(item[2]).strip() else "N/A"
                        
                        val_delantera = str(item[3]).strip() if len(item) > 3 else ""
                        val_trasera = str(item[4]).strip() if len(item) > 4 else ""

                        with str_m.container(border=True):
                            str_m.markdown(f"### {marca_head}")
                            str_m.markdown(f"**Mod:** {modelo_sub} | **Años:** {anio_sub}")

                            col1, col2 = str_m.columns(2)
                            with col1:
                                if val_delantera:
                                    str_m.info(f"🚘 **Delantera:**\n{val_delantera}")
                                else:
                                    str_m.write("🚘 *Delantera: No asignada*")
                            with col2:
                                if val_trasera:
                                    str_m.success(f"🛑 **Trasera:**\n{val_trasera}")
                                else:
                                    str_m.write("🛑 *Trasera: No asignada*")
                else:
                    str_m.error("❌ No se encontraron repuestos con los criterios ingresados.")

            except Exception as e:
                str_m.error(f"Error al procesar el archivo Excel local:\n{str(e)}")
