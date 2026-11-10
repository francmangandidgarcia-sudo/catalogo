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

# Solo estos usuarios pueden SUMAR existencias
USUARIOS_PERMITIDOS_SUMAR = ["admin", "leticia", "abraham"]

# =======================================================
# INICIALIZACIÓN DEL ESTADO DE LA SESIÓN (SESSION STATE)
# =======================================================
if "autenticado" not in str_m.session_state:
    str_m.session_state["autenticado"] = False
if "usuario_actual" not in str_m.session_state:
    str_m.session_state["usuario_actual"] = ""
if "resultados_busqueda" not in str_m.session_state:
    str_m.session_state["resultados_busqueda"] = None

# ARCHIVO FISICO
ARCHIVO_EXCEL = "datos.xlsx"

# =======================================================
# FUNCIONES DE CARGA Y ESCRITURA EN EXCEL (SIN CACHÉ PARA EVITAR ERRORES)
# =======================================================
def cargar_catalogo_real():
    if not os.path.exists(ARCHIVO_EXCEL):
        return None
    try:
        # Cargamos el archivo manteniendo la estructura original limpia
        df = pd.read_excel(ARCHIVO_EXCEL, header=None).fillna("").astype(str)
        for col in df.columns:
            df[col] = df[col].str.replace(r"\.0$", "", regex=True).str.strip()
        return df
    except Exception:
        return None

def actualizar_stock_en_excel(fila_index, nueva_cantidad):
    try:
        df = pd.read_excel(ARCHIVO_EXCEL, header=None)
        # El stock se encuentra en la columna F (Índice 5)
        df.iloc[fila_index, 5] = int(nueva_cantidad)
        df.to_excel(ARCHIVO_EXCEL, index=False, header=False)
        return True
    except Exception as e:
        str_m.error(f"Error crítico al guardar en Excel: {e}")
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
# PANTALLA 2: EL BUSCADOR AUTOMOTRIZ Y GESTOR DE STOCK
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
                    str_m.error("❌ Archivo 'datos.xlsx' no encontrado o corrupto.")
                    str_m.session_state["resultados_busqueda"] = None
                else:
                    filas_coincidentes = []
                    # Buscamos guardando el índice físico de la fila en el Excel para poder editarlo después
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
                            # Guardamos la data de la fila JUNTO con su índice de fila en el Excel original
                            filas_coincidentes.append({"index": idx, "data": lista_celdas})
                    
                    str_m.session_state["resultados_busqueda"] = filas_coincidentes

    # -------------------------------------------------------
    # DESPLIEGUE DE RESULTADOS Y ACTUALIZADOR DE STOCK
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
                val_delantera = str(celdas[3]).strip() if len(celdas) > 3 else ""
                val_trasera = str(celdas[4]).strip() if len(celdas) > 4 else ""
                val_existencia = str(celdas[5]).strip() if len(celdas) > 5 else "0"
                
                try:
                    cant_actual = int(val_existencia) if val_existencia and val_existencia.lower() != "nan" else 0
                except ValueError:
                    cant_actual = 0
                
                with str_m.container(border=True):
                    str_m.markdown(f"### 🚘 {marca_head}")
                    str_m.markdown(f"**Modelo/Motor:** {modelo_sub} | **Años:** {anio_sub}")
                    
                    # Semáforo visual del Stock actual
                    if cant_actual == 0:
                        str_m.error("⚠️ **Existencias:** Sin stock / Agotado")
                    elif cant_actual < 5:
                        str_m.warning(f"📉 **Existencias:** ¡Pocas unidades! ({cant_actual} disponibles)")
                    else:
                        str_m.markdown(f"✅ **Existencias:** {cant_actual} unidades disponibles")
                    
                    # --- SECCIÓN DE AJUSTE DE STOCK (ACTUALIZACIÓN DIRECTA EN EL EXCEL) ---
                    # Generamos una llave única para evitar conflictos en Streamlit usando el índice de fila
                    col_unidades, col_btn_restar, col_btn_sumar = str_m.columns([0.4, 0.3, 0.3])
                    
                    with col_unidades:
                        unidades_cambio = str_m.number_input("Unidades:", min_value=1, value=1, step=1, key=f"num_{fila_idx}")
                    
                    with col_btn_restar:
                        if str_m.button("➖ Restar", key=f"del_{fila_idx}", use_container_width=True):
                            if cant_actual >= unidades_cambio:
                                nuevo_stock = cant_actual - unidades_cambio
                                if actualizar_stock_en_excel(fila_idx, nuevo_stock):
                                    str_m.toast(f"✅ Inventario actualizado. Quedan {nuevo_stock} u.", icon="📉")
                                    # Forzamos una recarga interna de la búsqueda para reflejar el cambio numérico de inmediato
                                    str_m.session_state["resultados_busqueda"] = None
