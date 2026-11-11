import os
import re
import pandas as pd
import streamlit as str_m

str_m.set_page_config(
    page_title="Catálogo Privado",
    page_icon="🔒",
    layout="centered"
)

USUARIOS_REGISTRADOS = {
    "admin": "admin",
    "leticia": "aceitera2026",
    "abraham": "jefe2026",
    "dailyn": "Lubricante2026",
    "jackelin": "Repuesto2026"
}

USUARIOS_PRIVILEGIADOS = ["admin", "leticia"]
ARCHIVO_EXCEL = "datos.xlsx"

if "autenticado" not in str_m.session_state:
    str_m.session_state["autenticado"] = False
if "usuario_actual" not in str_m.session_state:
    str_m.session_state["usuario_actual"] = ""
if "resultados_busqueda" not in str_m.session_state:
    str_m.session_state["resultados_busqueda"] = None

def limpiar_texto(valor):
    texto = str(valor).replace("\n", " ").replace("\r", " ").strip()
    if texto.lower() in ["nan", "none", "nat"]:
        return ""
    return texto

def cargar_catalogo_real():
    if not os.path.exists(ARCHIVO_EXCEL):
        return None
    df = pd.read_excel(ARCHIVO_EXCEL, header=None).fillna("").astype(str)
    for col in df.columns:
        df[col] = df[col].str.replace(r"\.0$", "", regex=True).str.strip()
    return df

def actualizar_stock_en_excel(fila_index, columna_index, nueva_cantidad):
    df = pd.read_excel(ARCHIVO_EXCEL, header=None)
    total_cols = len(df.columns)
    while total_cols <= columna_index:
        df[total_cols] = ""
        total_cols = len(df.columns)
    df.iat[fila_index, columna_index] = int(nueva_cantidad)
    df.to_excel(ARCHIVO_EXCEL, index=False, header=False)
    return True

def validar_anio(texto_celda, anio_buscado):
    if not anio_buscado:
        return True
    texto_celda = limpiar_texto(texto_celda)
    if anio_buscado in texto_celda:
        return True
    rangos = re.findall(r"(\d{4})\s*-\s*(\d{4})", texto_celda)
    for inicio, fin in rangos:
        if int(inicio) <= int(anio_buscado) <= int(fin):
            return True
    return False

def limpiar_entero(valor):
    texto = limpiar_texto(valor)
    if texto == "":
        return 0
    if texto.replace(".", "", 1).isdigit():
        return int(float(texto))
    return 0

def extraer_7_datos(lista_cruda):
    siete = []
    for item in lista_cruda:
        if len(siete) < 7:
            siete.append(limpiar_texto(item))
    while len(siete) < 7:
        siete.append("")
    c_marca, c_modelo, c_anio, c_cant_d, c_cod_d, c_cant_t, c_cod_t = siete
    return c_marca, c_modelo, c_anio, c_cant_d, c_cod_d, c_cant_t, c_cod_t

# -------------------------------------------------------
# PANTALLA 1: INICIO DE SESIÓN
# -------------------------------------------------------
if not str_m.session_state["autenticado"]:
    str_m.title("🔒 Acceso al Catálogo")
    str_m.write("Por favor, ingrese sus credenciales de seguridad.")
    
    with str_m.form("login_form"):
        input_usuario = str_m.text_input("Usuario").strip().lower()
        input_clave = str_m.text_input("Contraseña", type="password").strip()
        btn_login = str_m.form_submit_button("Ingresar", use_container_width=True)
        
        if btn_login:
            if input_usuario in USUARIOS_REGISTRADOS and USUARIOS_REGISTRADOS[input_usuario] == input_clave:
                str_m.session_state["autenticado"] = True
                str_m.session_state["usuario_actual"] = input_usuario
                str_m.session_state["resultados_busqueda"] = None
                str_m.rerun()
            else:
                str_m.error("❌ Usuario o contraseña incorrectos.")

# -------------------------------------------------------
# PANTALLA 2: EL BUSCADOR SEGÚN ROL
# -------------------------------------------------------
else:
    usuario_activo = str_m.session_state["usuario_actual"]
    es_privilegiado = usuario_activo in USUARIOS_PRIVILEGIADOS
    
    col_titulo, col_logout = str_m.columns([0.65, 0.35])
    with col_logout:
        str_m.write(f"👤: **{usuario_activo.capitalize()}**")
        if str_m.button("🚪 Salir", use_container_width=True):
            str_m.session_state["autenticado"] = False
            str_m.session_state["usuario_actual"] = ""
            str_m.session_state["resultados_busqueda"] = None
            str_m.rerun()
            
    with col_titulo:
        str_m.title("🚘 Catálogo")
        str_m.caption("Catálogo Calibrado v2")

    if es_privilegiado:
        tab_vehiculo, tab_codigo = str_m.tabs(["🚗 Buscar por Vehículo", "🔢 Ingreso por Código"])
    else:
        tab_lista = str_m.tabs(["🚗 Buscar por Vehículo"])
        for t in tab_lista:
            tab_vehiculo = t
        tab_codigo = None

    # --- PESTAÑA A: VEHÍCULO ---
    with tab_vehiculo:
        with str_m.form("buscador_vehiculo_form"):
            txt_marca = str_m.text_input("1. Marca (ej: Toyota, Kia...)").strip().lower()
            txt_modelo = str_m.text_input("2. Modelo / Motor (ej: Camry, Hilux...)").strip().lower()
            txt_anio = str_m.text_input("3. Año exacto (ej: 2004...)").strip()
            btn_buscar_v = str_m.form_submit_button("🔍 Buscar por Vehículo", use_container_width=True)
            
            if btn_buscar_v:
                if not txt_marca and not txt_modelo and not txt_anio:
                    str_m.warning("⚠️ Escribe al menos un dato para filtrar.")
                    str_m.session_state["resultados_busqueda"] = None
                else:
                    df_catalogo = cargar_catalogo_real()
                    if df_catalogo is not None:
                        filas_coincidentes = []
                        for idx, fila in df_catalogo.iterrows():
                            lista_celdas = fila.values.tolist()
                            if len(lista_celdas) < 3:
                                continue
                            
                            c_marca, c_modelo, c_anio, _, _, _, _ = extraer_7_datos(lista_celdas)
                            val_marca = c_marca.lower()
                            val_modelo = c_modelo.lower()
                            
                            if "hoja de" in val_marca or "catálogo" in val_marca or val_marca == "marca" or val_marca == "":
                                continue
                                
                            cumple_marca = not txt_marca or (txt_marca in val_marca)
                            cumple_modelo = not txt_modelo or (txt_modelo in val_modelo)
                            cumple_anio = not txt_anio or validar_anio(c_anio, txt_anio)
                            
                            if cumple_marca and cumple_modelo and cumple_anio:
                                filas_coincidentes.append({"index": int(idx), "data": lista_celdas, "modo": "vehiculo"})
                        str_m.session_state["resultados_busqueda"] = filas_coincidentes

    # --- PESTAÑA B: CÓDIGO (SOLO ADMIN Y LETICIA) ---
    if tab_codigo is not None:
        with tab_codigo:
            with str_m.form("buscador_codigo_form"):
                txt_codigo = str_m.text_input("Código de pastilla a ingresar (ej: 717, WVA-24332...)").strip().lower()
                btn_buscar_c = str_m.form_submit_button("🔍 Buscar Código para Sumar", use_container_width=True)
                
                if btn_buscar_c:
                    if not txt_codigo:
                        str_m.warning("⚠️ Escribe un código para buscar.")
                        str_m.session_state["resultados_busqueda"] = None
                    else:
                        df_catalogo = cargar_catalogo_real()
                        if df_catalogo is not None:
                            filas_coincidentes = []
                            for idx, fila in df_catalogo.iterrows():
                                lista_celdas = fila.values.tolist()
                                if len(lista_celdas) < 3:
                                    continue
                                
                                c_marca, _, _, _, c_cod_d, _, c_cod_t = extraer_7_datos(lista_celdas)
                                val_marca = c_marca.lower()
                                
                                if "hoja de" in val_marca or "catálogo" in val_marca or val_marca == "marca" or val_marca == "":
                                    continue

                                cod_del = c_cod_d.lower()
                                cod_tra = c_cod_t.lower()
                                
                                if (txt_codigo in cod_del) or (txt_codigo in cod_tra):
                                    filas_coincidentes.append({"index": int(idx), "data": lista_celdas, "modo": "codigo"})
                            str_m.session_state["resultados_busqueda"] = filas_coincidentes

    # -------------------------------------------------------
    # VISOR DE RESULTADOS SIN COLUMNAS ANIDADAS (100% LINEAL)
    # -------------------------------------------------------
    str_m.write("---")
    str_m.write("### Resultados del Catálogo")
    
    if str_m.button("🧹 Limpiar Pantalla", use_container_width=True):
        str_m.session_state["resultados_busqueda"] = None
        str_m.rerun()

    resultados = str_m.session_state["resultados_busqueda"]
    
    if resultados is not None:
        if len(resultados) > 0:
            str_m.success(f"📦 {len(resultados)} registro(s) encontrado(s)")
            
            for i, item in enumerate(resultados):
                fila_idx = item.get("index", i)
                lista_cruda = item.get("data", [])
                modo_busqueda = item.get("modo", "vehiculo")
                
                col_marca, col_modelo, col_anio, col_cant_del, col_cod_del, col_cant_tra, col_cod_tra = extraer_7_datos(lista_cruda)
                
                marca_head = col_marca.upper() if col_marca else "SIN MARCA"
                modelo_sub = col_modelo if col_modelo else "N/A"
                anio_sub = col_anio if col_anio else "N/A"
                cant_del = limpiar_entero(col_cant_del)
