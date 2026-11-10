import os
import re
import pandas as pd
import streamlit as str_m

# Configuración de apariencia estilo App Móvil
str_m.set_page_config(
    page_title="Catálogo Privado",
    page_icon="🔒",
    layout="centered"
)

# =======================================================
# CONFIGURACIÓN DE USUARIOS, CONTRASEÑAS Y ROLES
# =======================================================
USUARIOS_REGISTRADOS = {
    "admin": "admin",
    "leticia": "aceitera2026",
    "abraham": "jefe2026",
    "dailyn": "Lubricante2026",
    "jackelin": "Repuesto2026"
}

USUARIOS_PERMITIDOS_SUMAR = ["admin", "leticia", "abraham"]
ARCHIVO_EXCEL = "datos.xlsx"

# =======================================================
# INICIALIZACIÓN DEL ESTADO DE LA SESIÓN
# =======================================================
if "autenticado" not in str_m.session_state:
    str_m.session_state["autenticado"] = False
if "usuario_actual" not in str_m.session_state:
    str_m.session_state["usuario_actual"] = ""
if "resultados_busqueda" not in str_m.session_state:
    str_m.session_state["resultados_busqueda"] = None

# =======================================================
# FUNCIONES DE CONTROL DE EXCEL
# =======================================================
def cargar_catalogo_real():
    if not os.path.exists(ARCHIVO_EXCEL):
        return None
    try:
        df = pd.read_excel(ARCHIVO_EXCEL, header=None).fillna("").astype(str)
        for col in df.columns:
            df[col] = df[col].str.replace(r"\.0$", "", regex=True).str.strip()
        return df
    except Exception as e:
        str_m.error(f"Error al leer el archivo Excel: {e}")
        return None

def actualizar_stock_en_excel(fila_index, columna_index, nueva_cantidad):
    try:
        df = pd.read_excel(ARCHIVO_EXCEL, header=None)
        # Asegurar dimensiones mínimas del DataFrame
        while df.shape[1] < 7:
            df[df.shape[1]] = ""
        df.iloc[fila_index, columna_index] = int(nueva_cantidad)
        df.to_excel(ARCHIVO_EXCEL, index=False, header=False)
        return True
    except PermissionError:
        str_m.error("❌ Archivo 'datos.xlsx' abierto en otra PC. Ciérralo y reintenta.")
        return False
    except Exception as e:
        str_m.error(f"Error inesperado al guardar en Excel: {e}")
        return False

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

def limpiar_entero(valor):
    if not valor or str(valor).lower() == "nan":
        return 0
    try:
        return int(float(str(valor).strip()))
    except ValueError:
        return 0

# -------------------------------------------------------
# PANTALLA 1: FORMULARIO DE INICIO DE SESIÓN
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
                str_m.rerun()
            else:
                str_m.error("❌ Usuario o contraseña incorrectos. Intente de nuevo.")

# -------------------------------------------------------
# PANTALLA 2: EL BUSCADOR GESTIONADO POR ROLES Y STOCK
# -------------------------------------------------------
else:
    usuario_activo = str_m.session_state["usuario_actual"]
    
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
        str_m.caption("Buscador Local Automotriz")

    # CONFIGURACIÓN DINÁMICA DE PESTAÑAS SEGÚN EL USUARIO
    if usuario_activo == "admin":
        tab_vehiculo, tab_codigo = str_m.tabs(["🚗 Buscar por Vehículo", "🔢 Buscar por Código (Solo Admin)"])
    else:
        tab_vehicules_list = str_m.tabs(["🚗 Buscar por Vehículo"])
        tab_vehiculo = tab_vehicules_list[0]
        tab_codigo = None

    # --- PESTAÑA A: BUSCADOR POR VEHÍCULO (PARA TODOS) ---
    with tab_vehiculo:
        with str_m.form("buscador_vehiculo_form"):
            txt_marca = str_m.text_input("1. Marca (ej: Toyota, Acura...)").strip().lower()
            txt_modelo = str_m.text_input("2. Modelo / Motor (ej: Yaris...)").strip().lower()
            txt_anio = str_m.text_input("3. Año exacto (ej: 2015...)").strip()
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
                            
                            val_marca = str(lista_celdas[0]).strip().lower()
                            val_modelo = str(lista_celdas[1]).strip().lower()
                            val_anio_celda = str(lista_celdas[2]).strip()
                            
                            if "hoja de" in val_marca or "catálogo" in val_marca or "marca" in val_marca:
                                continue
                                
                            cumple_marca = not txt_marca or (txt_marca in val_marca)
                            cumple_modelo = not txt_modelo or (txt_modelo in val_modelo)
                            cumple_anio = not txt_anio or validar_anio(val_anio_celda, txt_anio)
                            
                            if cumple_marca and cumple_modelo and cumple_anio:
                                filas_coincidentes.append({"index": idx, "data": lista_celdas})
                        str_m.session_state["resultados_busqueda"] = filas_coincidentes
                        str_m.rerun()

    # --- PESTAÑA B: BUSCADOR POR CÓDIGO (SOLO VISIBLE SI ES ADMIN) ---
    if tab_codigo is not None:
        with tab_codigo:
            with str_m.form("buscador_codigo_form"):
                txt_codigo = str_m.text_input("Ingrese el código del repuesto (ej: WVA-24332, 24332...)").strip().lower()
                btn_buscar_c = str_m.form_submit_button("🔍 Buscar por Código", use_container_width=True)
                
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
                                
                                val_marca = str(lista_celdas[0]).strip().lower()
                                if "hoja de" in val_marca or "catálogo" in val_marca or "marca" in val_marca:
                                    continue

                                # Mapear las columnas E (índice 4) y G (índice 6) de forma segura
                                cod_del_celda = str(lista_celdas[4]).strip().lower() if len(lista_celdas) > 4 else ""
                                cod_tra_celda = str(lista_celdas[6]).strip().lower() if len(lista_celdas) > 6 else ""
                                
                                if (txt_codigo in cod_del_celda) or (txt_codigo in cod_tra_celda):
                                    filas_coincidentes.append({"index": idx, "data": lista_celdas})
                            str_m.session_state["resultados_busqueda"] = filas_coincidentes
                            str_m.rerun()

    # -------------------------------------------------------
    # VISOR DE RESULTADOS PERSISTENTE (FUERA DE LAS PESTAÑAS)
    # -------------------------------------------------------
    str_m.write("### Resultados del Catálogo")
    resultados = str_m.session_state["resultados_busqueda"]
    
    if resultados is not None:
        if len(resultados) > 0:
            str_m.success(f"📦 {len(resultados)} registro(s) encontrado(s)")
            
            for item in resultados:
                fila_idx = item["index"]
                celdas = item["data"]
                
                marca_head = str(celdas[0]).strip().upper() if len(celdas) > 0 else "MARCA NO ASIGNADA"
