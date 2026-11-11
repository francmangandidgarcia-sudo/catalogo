import os
import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Consulta de Catálogo", page_icon="🚘", layout="centered")

USUARIOS = {
    "admin": "admin",
    "leticia": "aceitera2026",
    "abraham": "jefe2026",
    "dailyn": "Lubricante2026",
    "jackelin": "Repuesto2026"
}

ARCHIVO_EXCEL = "datos.xlsx"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario" not in st.session_state:
    st.session_state["usuario"] = ""

def limpiar_texto(val):
    t = str(val).replace("\n", " ").replace("\r", " ").strip()
    return "" if t.lower() in ["nan", "none", "nat"] else t

def limpiar_entero(val):
    t = limpiar_texto(val)
    return int(float(t)) if t.replace(".", "", 1).isdigit() else 0

def extraer_7(lista):
    siete = []
    for x in lista:
        if len(siete) < 7:
            siete.append(limpiar_texto(x))
    while len(siete) < 7:
        siete.append("")
    c0, c1, c2, c3, c4, c5, c6 = siete
    return c0, c1, c2, c3, c4, c5, c6

def validar_anio(celda, buscado):
    if not buscado:
        return True
    celda = limpiar_texto(celda)
    if buscado in celda:
        return True
    for ini, fin in re.findall(r"(\d{4})\s*-\s*(\d{4})", celda):
        if int(ini) <= int(buscado) <= int(fin):
            return True
    return False

# --- PANTALLA DE LOGIN ---
if not st.session_state["autenticado"]:
    st.title("🔒 Consulta de Catálogo")
    with st.form("login"):
        u = st.text_input("Usuario").strip().lower()
        c = st.text_input("Contraseña", type="password").strip()
        if st.form_submit_button("Ingresar", use_container_width=True):
            if u in USUARIOS and USUARIOS[u] == c:
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = u
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos.")

# --- BUSCADOR DE SOLO LECTURA ---
else:
    c1, c2 = st.columns([0.7, 0.3])
    with c1:
        st.title("🚘 Catálogo de Frenos")
        st.caption("Consulta de Códigos y Disponibilidad")
    with c2:
        st.write(f"👤: **{st.session_state['usuario'].capitalize()}**")
        if st.button("🚪 Salir", use_container_width=True):
            st.session_state["autenticado"] = False
            st.rerun()

    with st.form("buscar"):
        b_marca = st.text_input("1. Marca (ej: Toyota, Kia...)").strip().lower()
        b_modelo = st.text_input("2. Modelo / Motor (ej: Corolla, Hilux...)").strip().lower()
        b_anio = st.text_input("3. Año exacto (ej: 2015...)").strip()
        btn = st.form_submit_button("🔍 Buscar Repuesto", use_container_width=True)

    if btn:
        if not b_marca and not b_modelo and not b_anio:
            st.warning("⚠️ Escribe al menos un dato para buscar.")
        elif not os.path.exists(ARCHIVO_EXCEL):
            st.error("❌ No se encontró el archivo datos.xlsx.")
        else:
            df = pd.read_excel(ARCHIVO_EXCEL, header=None).fillna("").astype(str)
            encontrados = []
            for _, fila in df.iterrows():
                m, mod, a, sd, cd, st_tra, ct = extraer_7(fila.values.tolist())
                if not m or "hoja de" in m.lower() or "catálogo" in m.lower() or m.lower() == "marca":
                    continue
                if (not b_marca or b_marca in m.lower()) and (not b_modelo or b_modelo in mod.lower()) and validar_anio(a, b_anio):
                    encontrados.append((m.upper(), mod, a, limpiar_entero(sd), cd, limpiar_entero(st_tra), ct))

            if len(encontrados) > 0:
                st.success(f"📦 {len(encontrados)} registro(s) encontrado(s)")
                for m, mod, a, sd, cd, st_tra, ct in encontrados:
                    with st.container(border=True):
                        st.markdown(f"### 🚘 {m} — {mod} ({a})")
                        col_d, col_t = st.columns(2)
                        with col_d:
                            st.info(f"🔹 **Delantera:** {cd if cd else 'N/A'}\n\nExistencia: **{sd} u.**")
                        with col_t:
                            st.success(f"🛑 **Trasera:** {ct if ct else 'N/A'}\n\nExistencia: **{st_tra} u.**")
            else:
                st.error("❌ No se encontraron repuestos con esos datos.")
