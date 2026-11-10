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

# Formulario de entradas en pantalla
with str_m.form("buscador_form"):
    txt_marca_modelo = str_m.text_input("1. Marca o Modelo (ej: Integra, Legend, CL...)").strip().lower()
    txt_anio = str_m.text_input("2. Año exacto (ej: 1990, 1998...)").strip()
    btn_buscar = str_m.form_submit_button("🔍 Buscar Repuestos", use_container_width=True)

if btn_buscar:
    if not txt_marca_modelo and not txt_anio:
        str_m.warning("⚠️ Escribe al menos un dato para filtrar.")
    else:
        # LEER DIRECTAMENTE TU EXCEL LOCAL EN EL ESCRITORIO
        archivo_excel = "datos.xlsx"

        if not os.path.exists(archivo_excel):
            str_m.error("❌ No se encontró el archivo 'datos.xlsx' en el Escritorio. Por favor, colócalo ahí.")
        else:
            try:
                # Leemos el Excel local de forma plana sin asumir títulos
                df = pd.read_excel(archivo_excel, header=None)

                # Limpieza absoluta de formatos numéricos decimales (.0) de Excel
                df_str = df.fillna("").astype(str)
                for col in df_str.columns:
                    df_str[col] = df_str[col].str.replace(r"\.0$", "", regex=True).str.strip()

                filas_coincidentes = []

                # Recorrido inteligente por la estructura de tu documento
                for idx, fila in df_str.iterrows():
                    lista_celdas = fila.values.tolist()
                    
                    if len(lista_celdas) < 3:
                        continue

                    # Mapeo según tu lista desalineada:
                    val_col0 = str(lista_celdas[0]).strip().lower()
                    val_marca_modelo = str(lista_celdas[1]).strip().lower()
                    val_anio_celda = str(lista_celdas[2]).strip()

                    # Saltamos cabeceras del archivo
                    if "hoja de" in val_marca_modelo or "catálogo" in val_marca_modelo:
                        continue

                    # Comprobación flexible en las columnas A y B para la marca/modelo
                    cumple_marca = not txt_marca_modelo or (txt_marca_modelo in val_marca_modelo) or (txt_marca_modelo in val_col0)
                    cumple_anio = not txt_anio or validar_anio(val_anio_celda, txt_anio)

                    if cumple_marca and cumple_anio:
                        filas_coincidentes.append(lista_celdas)

                # Desplegar resultados encontrados
                if len(filas_coincidentes) > 0:
                    str_m.success(f"📦 {len(filas_coincidentes)} registro(s) encontrado(s)")

                    for item in filas_coincidentes:
                        # Armamos el título combinando la columna A y B por si acaso
                        parte0 = str(item[0]).strip()
                        parte1 = str(item[1]).strip()
                        cabecera = f"{parte0} {parte1}".strip().upper()
                        
                        anio_sub = str(item[2]).strip() if str(item[2]).strip() else "N/A"
                        val_delantera = str(item[3]).strip() if len(item) > 3 else ""
                        val_trasera = str(item[4]).strip() if len(item) > 4 else ""

                        with str_m.container(border=True):
                            str_m.markdown(f"### {cabecera}")
                            str_m.markdown(f"**Años de aplicación:** {anio_sub}")

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
