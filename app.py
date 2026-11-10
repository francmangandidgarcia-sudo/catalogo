import os
import re
import pandas as pd
import streamlit as str_m

# Configuración de apariencia estilo App Móvil
str_m.set_page_config(
    page_title="Catálogo Privado", page_icon="🔒", layout="centered"
)

# =======================================================
# CONFIGURACIÓN DE MÚLTIPLES USUARIOS Y CONTRASENAS
# =======================================================
# Puedes añadir todos los usuarios que quieras siguiendo este formato:
# "usuario": "contraseña"
USUARIOS_REGISTRADOS = {
    "admin": "admin",
    "Leticia": "aceitera2026",
    "dailyn": "taller2026",
    "jackelin": "taller2026"
}
# =======================================================

# Inicializar la variable de control de sesión si no existe
if "autenticado" not in str_m.session_state:
    str_m.session_state["autenticado"] = False
if "usuario_actual" not in str_m.session_state:
    str_m.session_state["usuario_actual"] = ""

# -------------------------------------------------------
# PANTALLA 1: FORMULARIO DE INICIO DE SESIÓN
# -------------------------------------------------------
if not str_m.session_state["autenticado"]:
    str_m.title("🔒 Acceso al Catálogo")
    str_m.write("Por favor, ingrese sus credenciales de seguridad.")

    with str_m.form("login_form"):
        input_usuario = str_m.text_input("Usuario").strip().lower() # Convertimos a minúsculas para evitar fallos
        input_clave = str_m.text_input("Contraseña", type="password").strip()
        btn_login = str_m.form_submit_button("Ingresar", use_container_width=True)

    if btn_login:
        # Verificamos si el usuario existe en nuestra lista y si la contraseña coincide
        if input_usuario in USUARIOS_REGISTRADOS and USUARIOS_REGISTRADOS[input_usuario] == input_clave:
            str_m.session_state["autenticado"] = True
            str_m.session_state["usuario_actual"] = input_usuario
            str_m.rerun()  # Recarga la app para liberar el buscador
        else:
            str_m.error("❌ Usuario o contraseña incorrectos. Intente de nuevo.")

# -------------------------------------------------------
# PANTALLA 2: EL BUSCADOR AUTOMOTRIZ (SOLO SI SE AUTENTICÓ)
# -------------------------------------------------------
else:
    # Botón de Cerrar Sesión colocado discretamente arriba junto al saludo
    col_titulo, col_logout = str_m.columns([0.7, 0.3])
    with col_logout:
        # Muestra el nombre de quien inició sesión y el botón de salir
        str_m.write(f"👤: {str_m.session_state['usuario_actual'].capitalize()}")
        if str_m.button("🚪 Salir", use_container_width=True):
            str_m.session_state["autenticado"] = False
            str_m.session_state["usuario_actual"] = ""
            str_m.rerun()

    with col_titulo:
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
            archivo_excel = "datos.xlsx"

            if not os.path.exists(archivo_excel):
                str_m.error("❌ No se encontró el archivo 'datos.xlsx' en el servidor.")
            else:
                try:
                    df = pd.read_excel(archivo_excel, header=None)

                    # Limpieza absoluta de formatos numéricos decimales (.0)
                    df_str = df.fillna("").astype(str)
                    for col in df_str.columns:
                        df_str[col] = df_str[col].str.replace(r"\.0$", "", regex=True).str.strip()

                    filas_coincidentes = []

                    for idx, fila in df_str.iterrows():
                        lista_celdas = fila.values.tolist()
                        
                        if len(lista_celdas) < 3:
                            continue

                        # Mapeo exacto por columnas fijas
                        val_marca = str(lista_celdas[0]).strip().lower()
                        val_modelo = str(lista_celdas[1]).strip().lower()
                        val_anio_celda = str(lista_celdas[2]).strip()

                        if "hoja de" in val_marca or "catálogo" in val_marca:
                            continue

                        cumple_marca = not txt_marca or (txt_marca in val_marca)
                        cumple_modelo = not txt_modelo or (txt_modelo in val_modelo)
                        cumple_anio = not txt_anio or validar_anio(val_anio_celda, txt_anio)

                        if cumple_marca and cumple_modelo and cumple_anio:
                            filas_coincidentes.append(lista_celdas)

                    if len(filas_coincidentes) > 0:
                        str_m.success(f"📦 {len(filas_coincidentes)} registro(s) encontrado(s)")

                        for item in filas_coincidentes:
                            marca_head = str(item[0]).strip().upper() if str(item[0]).strip() else "MARCA"
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
                    str_m.error(f"Error al procesar el archivo Excel:\n{str(e)}")
