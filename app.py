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
        df.iloc[fila_index, columna_index] = int(nueva_cantidad)
        df.to_excel(ARCHIVO_EXCEL, index=False, header=False)
        return True
    except PermissionError:
        str_m.error("❌ No se pudo guardar. Por favor, CIERRA el archivo 'datos.xlsx' en tu computadora y vuelve a intentarlo.")
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
# PANTALLA 2: EL BUSCADOR Y GESTOR DE STOCK DOBLE
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

    with str_m.form("buscador_form"):
        txt_marca = str_m.text_input("1. Marca (ej: Acura, Audi...)").strip().lower()
        txt_modelo = str_m.text_input("2. Modelo / Motor (ej: Integra...)").strip().lower()
        txt_anio = str_m.text_input("3. Año exacto (ej: 1990, 1998...)").strip()
        btn_buscar = str_m.form_submit_button("🔍 Buscar Repuesto", use_container_width=True)
        
        if btn_buscar:
            if not txt_marca and not txt_modelo and not txt_anio:
                str_m.warning("⚠️ Escribe al menos un dato para filtrar.")
                str_m.session_state["resultados_busqueda"] = None
            else:
                df_catalogo = cargar_catalogo_real()
                
                if df_catalogo is None:
                    str_m.session_state["resultados_busqueda"] = None
                else:
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

    # -------------------------------------------------------
    # DESPLIEGUE DE RESULTADOS Y ACTUALIZADOR DE STOCK DOBLE
    # -------------------------------------------------------
    resultados = str_m.session_state["resultados_busqueda"]
    
    if resultados is not None:
        if len(resultados) > 0:
            str_m.success(f"📦 {len(resultados)} registro(s) encontrado(s)")
            
            for item in resultados:
                fila_idx = item["index"]
                celdas = item["data"]
                
                marca_head = str(celdas[0]).strip().upper() if celdas[0] else "MARCA"
                modelo_sub = str(celdas[1]).strip() if celdas[1] else "N/A"
                anio_sub = str(celdas[2]).strip() if celdas[2] else "N/A"
                
                # Mapeo de columnas según el nuevo Excel de 7 columnas
                stock_del = str(celdas[3]).strip() if len(celdas) > 3 else "0"
                cod_delantero = str(celdas[4]).strip() if len(celdas) > 4 else ""
                stock_tra = str(celdas[5]).strip() if len(celdas) > 5 else "0"
                cod_trasero = str(celdas[6]).strip() if len(celdas) > 6 else ""
                
                try:
                    cant_del = int(stock_del) if stock_del and stock_del.lower() != "nan" else 0
                    cant_tra = int(stock_tra) if stock_tra and stock_tra.lower() != "nan" else 0
                except ValueError:
                    cant_del, cant_tra = 0, 0
                
                with str_m.container(border=True):
                    str_m.markdown(f"### 🚘 {marca_head}")
                    str_m.markdown(f"**Modelo/Motor:** {modelo_sub} | **Años:** {anio_sub}")
                    
                    # Selector de cantidad de piezas a modificar
                    unidades_cambio = str_m.number_input("Cantidad de piezas a modificar:", min_value=1, value=1, step=1, key=f"cant_{fila_idx}")
                    
                    col_del, col_tra = str_m.columns(2)
                    
                    # --- BLOQUE PASTILLA DELANTERA (Columna D) ---
                    with col_del:
                        str_m.info(f"🚘 **Delantera:**\n{cod_delantero if cod_delantero and cod_delantero.lower() != 'nan' else 'No asignada'}")
                        if cant_del == 0:
                            str_m.error("⚠️ Stock Del.: 0 u.")
                        else:
                            str_m.markdown(f"📦 Stock Del.: **{cant_del} u.**")
                        
                        c_del_restar, c_del_sumar = str_m.columns(2)
                        with c_del_restar:
                            if str_m.button("➖ Restar", key=f"del_res_{fila_idx}", use_container_width=True):
                                if cant_del >= unidades_cambio:
                                    if actualizar_stock_en_excel(fila_idx, 3, cant_del - unidades_cambio):
                                        str_m.toast("📉 Stock delantero actualizado", icon="✅")
                                        str_m.session_state["resultados_busqueda"] = None
                                        str_m.rerun()
                                else:
                                    str_m.error("No hay stock suficiente")
                        with c_del_sumar:
                            if usuario_activo in USUARIOS_PERMITIDOS_SUMAR:
