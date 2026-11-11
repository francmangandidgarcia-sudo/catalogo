import os
import re
import pandas as pd
import streamlit as str_m

str_m.set_page_config(page_title="Catálogo Privado", page_icon="🔒", layout="centered")

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
    return "" if texto.lower() in ["nan", "none", "nat"] else texto

def cargar_catalogo_real():
    if not os.path.exists(ARCHIVO_EXCEL):
        return None
    df = pd.read_excel(ARCHIVO_EXCEL, header=None).fillna("").astype(str)
    for col in df.columns:
        df[col] = df[col].str.replace(r"\.0$", "", regex=True).str.strip()
    return df

def actualizar_stock_en_excel(fila_index, columna_index, nueva_cantidad):
    df = pd.read_excel(ARCHIVO_EXCEL, header=None)
    while len(df.columns) <= columna_index:
        df[len(df.columns)] = ""
    df.iat[fila_index, columna_index] = int(nueva_cantidad)
    df.to_excel(ARCHIVO_EXCEL, index=False, header=False)

def validar_anio(texto_celda, anio_buscado):
    if not anio_buscado:
        return True
    texto_celda = limpiar_texto(texto_celda)
    if anio_buscado in texto_celda:
        return True
    for inicio, fin in re.findall(r"(\d{4})\s*-\s*(\d{4})", texto_celda):
        if int(inicio) <= int(anio_buscado) <= int(fin):
            return True
    return False

def limpiar_entero(valor):
    texto = limpiar_texto(valor)
    return int(float(texto)) if texto.replace(".", "", 1).isdigit() else 0

def extraer_7_datos(lista_cruda):
    siete = [limpiar_texto(x) for x in lista_cruda[:7]]
    while len(siete) < 7:
        siete.append("")
    return siete

# -------------------------------------------------------
# PANTALLA 1: INICIO DE SESIÓN
# -------------------------------------------------------
if not str_m.session_state["autenticado"]:
    str_m.title("🔒 Acceso al Catálogo")
    with str_m.form("login_form"):
        u = str_m.text_input("Usuario").strip().lower()
        c = str_m.text_input("Contraseña", type="password").strip()
        if str_m.form_submit_button("Ingresar", use_container_width=True):
            if u in USUARIOS_REGISTRADOS and USUARIOS_REGISTRADOS[u] == c:
                str_m.session_state["autenticado"] = True
                str_m.session_state["usuario_actual"] = u
                str_m.session_state["resultados_busqueda"] = None
                str_m.rerun()
            else:
                str_m.error("❌ Credenciales incorrectas.")

# -------------------------------------------------------
# PANTALLA 2: EL BUSCADOR SEGÚN ROL
# -------------------------------------------------------
else:
    usuario_activo = str_m.session_state["usuario_actual"]
    es_privilegiado = usuario_activo in USUARIOS_PRIVILEGIADOS
    
    c_tit, c_out = str_m.columns([0.65, 0.35])
    with c_out:
        str_m.write(f"👤: **{usuario_activo.capitalize()}**")
        if str_m.button("🚪 Salir", use_container_width=True):
            str_m.session_state["autenticado"] = False
            str_m.session_state["usuario_actual"] = ""
            str_m.session_state["resultados_busqueda"] = None
            str_m.rerun()
    with c_tit:
        str_m.title("🚘 Catálogo")
        str_m.caption("Visor Directo v4")

    if es_privilegiado:
        tab_v, tab_c = str_m.tabs(["🚗 Buscar por Vehículo", "🔢 Ingreso por Código"])
    else:
        tab_v = str_m.tabs(["🚗 Buscar por Vehículo"])[0]
        tab_c = None

    # --- PESTAÑA VEHÍCULO ---
    with tab_v:
        with str_m.form("form_vehiculo"):
            t_marca = str_m.text_input("1. Marca").strip().lower()
            t_modelo = str_m.text_input("2. Modelo / Motor").strip().lower()
            t_anio = str_m.text_input("3. Año exacto").strip()
            if str_m.form_submit_button("🔍 Buscar por Vehículo", use_container_width=True):
                if not t_marca and not t_modelo and not t_anio:
                    str_m.warning("⚠️ Escribe al menos un dato.")
                else:
                    df = cargar_catalogo_real()
                    if df is not None:
                        res = []
                        for idx, fila in df.iterrows():
                            siete = extraer_7_datos(fila.values.tolist())
                            m, mod, a = siete[0].lower(), siete[1].lower(), siete[2]
                            if not m or "hoja de" in m or "catálogo" in m or m == "marca":
                                continue
                            if (not t_marca or t_marca in m) and (not t_modelo or t_modelo in mod) and (not t_anio or validar_anio(a, t_anio)):
                                res.append((int(idx), siete, "vehiculo"))
                        str_m.session_state["resultados_busqueda"] = res

    # --- PESTAÑA CÓDIGO (SOLO ADMIN Y LETICIA) ---
    if tab_c is not None:
        with tab_c:
            with str_m.form("form_codigo"):
                t_cod = str_m.text_input("Código de pastilla").strip().lower()
                if str_m.form_submit_button("🔍 Buscar Código para Sumar", use_container_width=True):
                    if not t_cod:
                        str_m.warning("⚠️ Escribe un código.")
                    else:
                        df = cargar_catalogo_real()
                        if df is not None:
                            res = []
                            for idx, fila in df.iterrows():
                                siete = extraer_7_datos(fila.values.tolist())
                                m, cd, ct = siete[0].lower(), siete[4].lower(), siete[6].lower()
                                if not m or "hoja de" in m or "catálogo" in m or m == "marca":
                                    continue
                                if (t_cod in cd) or (t_cod in ct):
                                    res.append((int(idx), siete, "codigo"))
                            str_m.session_state["resultados_busqueda"] = res

    # -------------------------------------------------------
    # VISOR DE RESULTADOS COMPACTO (SIN LLAVES LARGAS)
    # -------------------------------------------------------
    str_m.write("---")
    if str_m.button("🧹 Limpiar Pantalla", use_container_width=True):
        str_m.session_state["resultados_busqueda"] = None
        str_m.rerun()

    resultados = str_m.session_state["resultados_busqueda"]
    if resultados is not None:
        if len(resultados) > 0:
            str_m.success(f"📦 {len(resultados)} registro(s) encontrado(s)")
            
            # Tabla resumen sin llaves
            tabla_datos = []
            for idx, s, modo in resultados:
                tabla_datos.append([s[0].upper(), s[1], s[2], limpiar_entero(s[3]), s[4] or "N/A", limpiar_entero(s[5]), s[6] or "N/A"])
            
            columnas_tabla = ["Marca", "Modelo", "Año", "Stock Del.", "Cód. Del.", "Stock Tras.", "Cód. Tras."]
            str_m.dataframe(pd.DataFrame(tabla_datos, columns=columnas_tabla), use_container_width=True, hide_index=True)
            
            # Botones de acción por cada fila
            for i, (fila_idx, s, modo) in enumerate(resultados):
                cant_d = limpiar_entero(s[3])
                cant_t = limpiar_entero(s[5])
                str_m.write(f"**🚘 {s[0].upper()} {s[1]} ({s[2]})**")
                
                if str_m.button(f"➖ Restar 1 Delantera ({s[4] or 'N/A'})", key=f"dr_{i}_{fila_idx}", use_container_width=True):
                    if cant_d > 0:
                        actualizar_stock_en_excel(fila_idx, 3, cant_d - 1)
                        str_m.session_state["resultados_busqueda"] = None
                        str_m.rerun()
                    else:
                        str_m.error("Sin stock delantero.")
                        
                if es_privilegiado and modo == "codigo":
                    if str_m.button(f"➕ Agregar 1 Delantera ({s[4] or 'N/A'})", key=f"ds_{i}_{fila_idx}", use_container_width=True):
                        actualizar_stock_en_excel(fila_idx, 3, cant_d + 1)
                        str_m.session_state["resultados_busqueda"] = None
                        str_m.rerun()
                        
                if str_m.button(f"➖ Restar 1 Trasera ({s[6] or 'N/A'})", key=f"tr_{i}_{fila_idx}", use_container_width=True):
                    if cant_t > 0:
                        actualizar_stock_en_excel(fila_idx, 5, cant_t - 1)
                        str_m.session_state["resultados_busqueda"] = None
                        str_m.rerun()
                    else:
                        str_m.error("Sin stock trasero.")
                        
                if es_privilegiado and modo == "codigo":
                    if str_m.button(f"➕ Agregar 1 Trasera ({s[6] or 'N/A'})", key=f"ts_{i}_{fila_idx}", use_container_width=True):
                        actualizar_stock_en_excel(fila_idx, 5, cant_t + 1)
                        str_m.session_state["resultados_busqueda"] = None
                        str_m.rerun()
                str_m.write("---")
        else:
            str_m.error("❌ No se encontraron repuestos.")
