import os
import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Catálogo Privado", page_icon="🔒", layout="centered")

USUARIOS_REGISTRADOS = {
    "admin": "admin",
    "leticia": "Aceitera2026",
    "abraham": "Jefe2026",
    "dailyn": "Lubricantes2026",
    "jackelin": "Repuestos2026"
}

NOMBRES_COMPLETOS = {
    "admin": "Administrador General",
    "leticia": "Maria Leticia Osorio",
    "abraham": "Luis Abraham Mellado Osorio",
    "dailyn": "Dailyn Siomara Del Cid",
    "jackelin": "Jackelin"
}

USUARIOS_BUSQUEDA_CODIGO = ["admin", "leticia"]
ARCHIVO_EXCEL = "datos.xlsx"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = ""
if "resultados_busqueda" not in st.session_state:
    st.session_state["resultados_busqueda"] = None

def limpiar_texto(valor):
    texto = str(valor).replace("\n", " ").replace("\r", " ").strip()
    return "" if texto.lower() in ["nan", "none", "nat"] else texto

@st.cache_data(ttl=15)
def cargar_catalogo():
    if not os.path.exists(ARCHIVO_EXCEL):
        return None
    df = pd.read_excel(ARCHIVO_EXCEL, header=None).fillna("").astype(str)
    for col in df.columns:
        df[col] = df[col].str.replace(r"\.0$", "", regex=True).str.strip()
    return df

def extraer_5_columnas(lista_cruda):
    cinco = []
    for item in lista_cruda:
        if len(cinco) < 5:
            cinco.append(limpiar_texto(item))
    while len(cinco) < 5:
        cinco.append("")
    c_marca, c_modelo, c_anio, c_del, c_tra = cinco
    return c_marca, c_modelo, c_anio, c_del, c_tra

def validar_anio(texto_celda, anio_buscado):
    if not anio_buscado:
        return False
    texto_celda = limpiar_texto(texto_celda)
    if anio_buscado in texto_celda:
        return True
    for inicio, fin in re.findall(r"(\d{4})\s*-\s*(\d{4})", texto_celda):
        if int(inicio) <= int(anio_buscado) <= int(fin):
            return True
    return False

def buscar_por_vehiculo(txt_marca, txt_modelo, txt_anio):
    df_catalogo = cargar_catalogo()
    if df_catalogo is None:
        return None
    coincidencias = []
    for _, fila in df_catalogo.iterrows():
        lista = fila.values.tolist()
        if len(lista) < 3:
            continue
        marca, modelo, anio, cod_del, cod_tra = extraer_5_columnas(lista)
        val_marca = marca.lower()
        if not val_marca or "hoja de" in val_marca or "catálogo" in val_marca or val_marca == "marca":
            continue
        if (txt_marca in val_marca) and (txt_modelo in modelo.lower()) and validar_anio(anio, txt_anio):
            coincidencias.append((marca.upper(), modelo, anio, cod_del, cod_tra))
    return coincidencias

def buscar_por_codigo(txt_codigo):
    df_catalogo = cargar_catalogo()
    if df_catalogo is None:
        return None
    coincidencias = []
    for _, fila in df_catalogo.iterrows():
        lista = fila.values.tolist()
        if len(lista) < 3:
            continue
        marca, modelo, anio, cod_del, cod_tra = extraer_5_columnas(lista)
        val_marca = marca.lower()
        if not val_marca or "hoja de" in val_marca or "catálogo" in val_marca or val_marca == "marca":
            continue
        if (txt_codigo in cod_del.lower()) or (txt_codigo in cod_tra.lower()):
            coincidencias.append((marca.upper(), modelo, anio, cod_del, cod_tra))
    return coincidencias

# -------------------------------------------------------
# PANTALLA 1: INICIO DE SESIÓN
# -------------------------------------------------------
if not st.session_state["autenticado"]:
    st.title("🔒 Acceso al Catálogo")
    st.write("Por favor, ingrese sus credenciales de seguridad.")
    with st.form("login_form"):
        input_usuario = st.text_input("Usuario").strip().lower()
        input_clave = st.text_input("Contraseña", type="password").strip()
        if st.form_submit_button("Ingresar", use_container_width=True):
            if input_usuario in USUARIOS_REGISTRADOS and USUARIOS_REGISTRADOS[input_usuario] == input_clave:
                st.session_state["autenticado"] = True
                st.session_state["usuario_actual"] = input_usuario
                st.session_state["resultados_busqueda"] = None
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos.")

# -------------------------------------------------------
# PANTALLA 2: EL BUSCADOR AUTOMOTRIZ
# -------------------------------------------------------
else:
    usuario_activo = st.session_state["usuario_actual"]
    nombre_mostrado = NOMBRES_COMPLETOS.get(usuario_activo, usuario_activo.capitalize())
    
    col_titulo, col_logout = st.columns([0.65, 0.35])
    with col_logout:
        st.write(f"👤 **{nombre_mostrado}**")
        if st.button("🚪 Salir", use_container_width=True):
            st.session_state["autenticado"] = False
            st.session_state["usuario_actual"] = ""
            st.session_state["resultados_busqueda"] = None
            st.rerun()
    with col_titulo:
        st.title("🚘 Catálogo")
        st.caption("Buscador Automotriz")

    if usuario_activo in USUARIOS_BUSQUEDA_CODIGO:
        tab_vehiculo, tab_codigo = st.tabs(["🚗 Buscar por Vehículo", "🔢 Buscar por Código"])
        with tab_vehiculo:
            with st.form("buscador_vehiculo_privilegiado"):
                txt_marca = st.text_input("1. Marca * (ej: Toyota, Kia, Honda...)").strip().lower()
                txt_modelo = st.text_input("2. Modelo / Motor * (ej: Corolla, Hilux...)").strip().lower()
                txt_anio = st.text_input("3. Año exacto * (ej: 2015, 2004...)").strip()
                if st.form_submit_button("🔍 Buscar", use_container_width=True):
                    if not txt_marca or not txt_modelo or not txt_anio:
                        st.warning("⚠️ Es obligatorio llenar las 3 casillas.")
                        st.session_state["resultados_busqueda"] = None
                    elif not txt_anio.isdigit() or len(txt_anio) != 4:
                        st.warning("⚠️ Escribe un año válido de 4 dígitos.")
                        st.session_state["resultados_busqueda"] = None
                    else:
                        st.session_state["resultados_busqueda"] = buscar_por_vehiculo(txt_marca, txt_modelo, txt_anio)
        with tab_codigo:
            with st.form("buscador_codigo_privilegiado"):
                txt_codigo = st.text_input("Código de pastilla (ej: 717, D1210, 24332...)").strip().lower()
                if st.form_submit_button("🔍 Buscar", use_container_width=True):
                    if not txt_codigo:
                        st.warning("⚠️ Escribe un código.")
                        st.session_state["resultados_busqueda"] = None
                    else:
                        st.session_state["resultados_busqueda"] = buscar_por_codigo(txt_codigo)
    else:
        with st.form("buscador_form_general"):
            txt_marca = st.text_input("1. Marca * (ej: Toyota, Kia, Honda...)").strip().lower()
            txt_modelo = st.text_input("2. Modelo / Motor * (ej: Corolla, Hilux...)").strip().lower()
            txt_anio = st.text_input("3. Año exacto * (ej: 2015, 2004...)").strip()
            if st.form_submit_button("🔍 Buscar", use_container_width=True):
                if not txt_marca or not txt_modelo or not txt_anio:
                    st.warning("⚠️ Es obligatorio llenar las 3 casillas.")
                    st.session_state["resultados_busqueda"] = None
                elif not txt_anio.isdigit() or len(txt_anio) != 4:
                    st.warning("⚠️ Escribe un año válido de 4 dígitos.")
                    st.session_state["resultados_busqueda"] = None
                else:
                    st.session_state["resultados_busqueda"] = buscar_por_vehiculo(txt_marca, txt_modelo, txt_anio)

    # -------------------------------------------------------
    # DESPLIEGUE COMPACTO DE RESULTADOS (1 BLOQUE POR VEHÍCULO)
    # -------------------------------------------------------
    resultados = st.session_state["resultados_busqueda"]
    if resultados is not None:
        if len(resultados) > 0:
            st.success(f"📦 {len(resultados)} registro(s) encontrado(s)")
            for marca, modelo, anio, cod_del, cod_tra in resultados:
                st.info(f"🚘 **{marca} — {modelo or 'N/A'} ({anio or 'N/A'})**\n\n🔹 **Delantera:** {cod_del or 'No asignada'}\n\n🛑 **Trasera:** {cod_tra or 'No asignada'}")
        else:
            st.error("❌ No se encontraron repuestos con los criterios ingresados.")
