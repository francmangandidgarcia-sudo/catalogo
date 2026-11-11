import os
import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Catálogo Privado",
    page_icon="🔒",
    layout="centered"
)

# =======================================================
# CONFIGURACIÓN DE USUARIOS Y CONTRASEÑAS
# =======================================================
USUARIOS_REGISTRADOS = {
    "admin": "admin",
    "leticia": "aceitera2026",
    "abraham": "jefe2026",
    "dailyn": "Lubricante2026",
    "jackelin": "Repuesto2026"
}

ARCHIVO_EXCEL = "datos.xlsx"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = ""
if "resultados_busqueda" not in st.session_state:
    st.session_state["resultados_busqueda"] = None

# =======================================================
# FUNCIONES DE LECTURA Y BÚSQUEDA
# =======================================================
def limpiar_texto(valor):
    texto = str(valor).replace("\n", " ").replace("\r", " ").strip()
    return "" if texto.lower() in ["nan", "none", "nat"] else texto

@st.cache_data(ttl=600)
def cargar_catalogo_rapido():
    if not os.path.exists(ARCHIVO_EXCEL):
        return None
    df = pd.read_excel(ARCHIVO_EXCEL, header=None).fillna("").astype(str)
    for col in df.columns:
        df[col] = df[col].str.replace(r"\.0$", "", regex=True).str.strip()
    return df

def extraer_columnas_excel(lista_cruda):
    siete = [limpiar_texto(x) for x in lista_cruda[:7]]
    while len(siete) < 7:
        siete.append("")
    # A=Marca, B=Modelo, C=Año, D=Ignorada, E=Cod_Delantera, F=Ignorada, G=Cod_Trasera
    c_marca, c_modelo, c_anio, _, c_cod_d, _, c_cod_t = siete
    return c_marca, c_modelo, c_anio, c_cod_d, c_cod_t

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
                st.error("❌ Usuario o contraseña incorrectos. Intente de nuevo.")

# -------------------------------------------------------
# PANTALLA 2: EL BUSCADOR AUTOMOTRIZ
# -------------------------------------------------------
else:
    col_titulo, col_logout = st.columns([0.65, 0.35])
    with col_logout:
        st.write(f"👤: **{st.session_state['usuario_actual'].capitalize()}**")
        if st.button("🚪 Salir", use_container_width=True):
            st.session_state["autenticado"] = False
            st.session_state["usuario_actual"] = ""
            st.session_state["resultados_busqueda"] = None
            st.rerun()
            
    with col_titulo:
        st.title("🚘 Catálogo")
        st.caption("Buscador Automotriz")

    with st.form("buscador_form"):
        txt_marca = st.text_input("1. Marca * (ej: Toyota, Kia, Honda...)").strip().lower()
        txt_modelo = st.text_input("2. Modelo / Motor * (ej: Corolla, Hilux...)").strip().lower()
        txt_anio = st.text_input("3. Año exacto * (ej: 2015, 2004...)").strip()
        
        if st.form_submit_button("🔍 Buscar Repuesto", use_container_width=True):
            # Validación estricta: las 3 casillas deben tener texto
            if not txt_marca or not txt_modelo or not txt_anio:
                st.warning("⚠️ Es obligatorio llenar las 3 casillas (Marca, Modelo y Año) para realizar una búsqueda exacta.")
                st.session_state["resultados_busqueda"] = None
            elif not txt_anio.isdigit() or len(txt_anio) != 4:
                st.warning("⚠️ Por favor, escribe un año válido de 4 dígitos (ej: 2015).")
                st.session_state["resultados_busqueda"] = None
            else:
                df_catalogo = cargar_catalogo_rapido()
                if df_catalogo is None:
                    st.error("❌ Archivo 'datos.xlsx' no encontrado.")
                    st.session_state["resultados_busqueda"] = None
                else:
                    coincidencias = []
                    for _, fila in df_catalogo.iterrows():
                        lista = fila.values.tolist()
                        if len(lista) < 3:
                            continue
                        
                        marca, modelo, anio, cod_del, cod_tra = extraer_columnas_excel(lista)
                        val_marca = marca.lower()
                        
                        if not val_marca or "hoja de" in val_marca or "catálogo" in val_marca or val_marca == "marca":
                            continue
                            
                        cumple_marca = txt_marca in val_marca
                        cumple_modelo = txt_modelo in modelo.lower()
                        cumple_anio = validar_anio(anio, txt_anio)
                        
                        if cumple_marca and cumple_modelo and cumple_anio:
                            coincidencias.append((marca.upper(), modelo, anio, cod_del, cod_tra))
                    
                    st.session_state["resultados_busqueda"] = coincidencias

    # -------------------------------------------------------
    # DESPLIEGUE DE RESULTADOS
    # -------------------------------------------------------
    resultados = st.session_state["resultados_busqueda"]
    
    if resultados is not None:
        if len(resultados) > 0:
            st.success(f"📦 {len(resultados)} registro(s) encontrado(s)")
            
            for marca, modelo, anio, cod_del, cod_tra in resultados:
                with st.container(border=True):
                    st.markdown(f"### 🚘 {marca}")
                    st.markdown(f"**Modelo/Motor:** {modelo if modelo else 'N/A'} | **Años:** {anio if anio else 'N/A'}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if cod_del:
                            st.info(f"🔹 **Delantera:**\n{cod_del}")
                        else:
                            st.write("🔹 *Delantera: No asignada*")
                    with col2:
                        if cod_tra:
                            st.success(f"🛑 **Trasera:**\n{cod_tra}")
                        else:
                            st.write("🛑 *Trasera: No asignada*")
        else:
            st.error("❌ No se encontraron repuestos con esa combinación exacta de Marca, Modelo y Año.")
