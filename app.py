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
# CONFIGURACIÓN DE USUARIOS, CONTRASEÑAS Y NOMBRES REALES
# =======================================================
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

# =======================================================
# FUNCIONES DE LECTURA Y BÚSQUEDA INTELIGENTE
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

def analizar_fila(lista_cruda):
    celdas = [limpiar_texto(x) for x in lista_cruda]
    while len(celdas) < 5:
        celdas.append("")
    
    marca = celdas[0]
    modelo = celdas[1]
    anio = celdas[2]
    
    # Si el Excel tiene 5 columnas exactas (A=Marca, B=Modelo, C=Año, D=Del, E=Tra)
    if len(celdas) == 5:
        cod_del = celdas[3]
        cod_tra = celdas[4]
    else:
        # Si quedaron columnas vacías en medio (ej. 7 columnas), toma las posiciones 4 y 6 o las no vacías
        cod_del = celdas[3] if celdas[3] else (celdas[4] if len(celdas) > 4 else "")
        cod_tra = celdas[4] if (celdas[3] and celdas[4]) else (celdas[6] if len(celdas) > 6 else (celdas[5] if len(celdas) > 5 else ""))
        
    return marca, modelo, anio, cod_del, cod_tra

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
    df_catalogo = cargar_catalogo_rapido()
    if df_catalogo is None:
        return None
    coincidencias = []
    for _, fila in df_catalogo.iterrows():
        lista = fila.values.tolist()
        if len(lista) < 3:
            continue
        marca, modelo, anio, cod_del, cod_tra = analizar_fila(lista)
        val_marca = marca.lower()
        if not val_marca or "hoja de" in val_marca or "catálogo" in val_marca or val_marca == "marca":
            continue
        if (txt_marca in val_marca) and (txt_modelo in modelo.lower()) and validar_anio(anio, txt_anio):
            coincidencias.append((marca.upper(), modelo, anio, cod_del, cod_tra))
    return coincidencias

def buscar_por_codigo(txt_codigo):
    df_catalogo = cargar_catalogo_rapido()
    if df_catalogo is None:
        return None
    coincidencias = []
    for _, fila in df_catalogo.iterrows():
        lista = fila.values.tolist()
        if len(lista) < 3:
            continue
        marca, modelo, anio, cod_del, cod_tra = analizar_fila(lista)
        val_marca = marca.lower()
        if not val_marca or "hoja de" in val_marca or "catálogo" in val_marca or val_marca == "marca":
            continue
        # Busca el código en cualquier celda de la fila después del año
        resto_fila = " ".join([limpiar_texto(c).lower() for c in lista[3:]])
        if txt_codigo in resto_fila:
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
                st.error("❌ Usuario o contraseña incorrectos. Intente de nuevo.")

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

    # --- VISTA CON 2 PESTAÑAS PARA ADMIN Y LETICIA ---
    if usuario_activo in USUARIOS_BUSQUEDA_CODIGO:
        tab_vehiculo, tab_codigo = st.tabs(["🚗 Buscar por Vehículo", "🔢 Buscar por Código"])
        
        with tab_vehiculo:
            with st.form("buscador_vehiculo_privilegiado"):
                txt_marca = st.text_input("1. Marca * (ej: Toyota, Kia, Honda...)").strip().lower()
                txt_modelo = st.text_input("2. Modelo / Motor * (ej: Corolla, Hilux...)").strip().lower()
                txt_anio = st.text_input("3. Año exacto * (ej: 2015, 2004...)").strip()
                
                if st.form_submit_button("🔍 Buscar", use_container_width=True):
                    if not txt_marca or not txt_modelo or not txt_anio:
                        st.warning("⚠️ Es obligatorio llenar las 3 casillas (Marca, Modelo y Año).")
                        st.session_state["resultados_busqueda"] = None
                    elif not txt_anio.isdigit() or len(txt_anio) != 4:
                        st.warning("⚠️ Por favor, escribe un año válido de 4 dígitos (ej: 2015).")
                        st.session_state["resultados_busqueda"] = None
                    else:
                        res = buscar_por_vehiculo(txt_marca, txt_modelo, txt_anio)
                        if res is None:
                            st.error("❌ Archivo 'datos.xlsx' no encontrado.")
                        st.session_state["resultados_busqueda"] = res

        with tab_codigo:
            with st.form("buscador_codigo_privilegiado"):
                txt_codigo = st.text_input("Código de pastilla (ej: 717, D1210, 24332...)").strip().lower()
                
                if st.form_submit_button("🔍 Buscar", use_container_width=True):
                    if not txt_codigo:
                        st.warning("⚠️ Escribe un código para realizar la búsqueda.")
                        st.session_state["resultados_busqueda"] = None
                    else:
                        res = buscar_por_codigo(txt_codigo)
                        if res is None:
                            st.error("❌ Archivo 'datos.xlsx' no encontrado.")
                        st.session_state["resultados_busqueda"] = res

    # --- VISTA ESTÁNDAR PARA EL RESTO DE USUARIOS ---
    else:
        with st.form("buscador_form_general"):
            txt_marca = st.text_input("1. Marca * (ej: Toyota, Kia, Honda...)").strip().lower()
            txt_modelo = st.text_input("2. Modelo / Motor * (ej: Corolla, Hilux...)").strip().lower()
            txt_anio = st.text_input("3. Año exacto * (ej: 2015, 2004...)").strip()
            
            if st.form_submit_button("🔍 Buscar", use_container_width=True):
                if not txt_marca or not txt_modelo or not txt_anio:
                    st.warning("⚠️ Es obligatorio llenar las 3 casillas (Marca, Modelo y Año) para realizar una búsqueda exacta.")
                    st.session_state["resultados_busqueda"] = None
                elif not txt_anio.isdigit() or len(txt_anio) != 4:
                    st.warning("⚠️ Por favor, escribe un año válido de 4 dígitos (ej: 2015).")
                    st.session_state["resultados_busqueda"] = None
                else:
                    res = buscar_por_vehiculo(txt_marca, txt_modelo, txt_anio)
                    if res is None:
                        st.error("❌ Archivo 'datos.xlsx' no encontrado.")
                    st.session_state["resultados_busqueda"] = res

    # -------------------------------------------------------
    # DESPLIEGUE DE RESULTADOS
    # -------------------------------------------------------
    resultados = st.session_state["resultados_busqueda"]
    
    if resultados is not None:
        if len(resultados) > 0:
            st.success(f"📦 {len(resultados)} registro(s) encontrado(s)")
