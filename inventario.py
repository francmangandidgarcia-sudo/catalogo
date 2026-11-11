import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Gestión de Inventario", page_icon="📦", layout="centered")

USUARIOS_ADMIN = {
    "admin": "admin",
    "leticia": "aceitera2026"
}

ARCHIVO_EXCEL = "datos.xlsx"

if "auth_inv" not in st.session_state:
    st.session_state["auth_inv"] = False
if "user_inv" not in st.session_state:
    st.session_state["user_inv"] = ""
if "res_inv" not in st.session_state:
    st.session_state["res_inv"] = None

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

def guardar_cantidad(fila_idx, col_idx, nueva_cant):
    df = pd.read_excel(ARCHIVO_EXCEL, header=None)
    while len(df.columns) <= col_idx:
        df[len(df.columns)] = ""
    df.iat[fila_idx, col_idx] = int(nueva_cant)
    df.to_excel(ARCHIVO_EXCEL, index=False, header=False)

# --- LOGIN EXCLUSIVO ---
if not st.session_state["auth_inv"]:
    st.title("📦 Control de Existencias")
    st.write("Acceso exclusivo para administración de bodega.")
    with st.form("login_inv"):
        u = st.text_input("Usuario Administrador").strip().lower()
        c = st.text_input("Contraseña", type="password").strip()
        if st.form_submit_button("Ingresar", use_container_width=True):
            if u in USUARIOS_ADMIN and USUARIOS_ADMIN[u] == c:
                st.session_state["auth_inv"] = True
                st.session_state["user_inv"] = u
                st.rerun()
            else:
                st.error("❌ Acceso denegado. Usuario sin privilegios.")

# --- PANEL DE SUMAS Y RESTAS ---
else:
    c1, c2 = st.columns([0.7, 0.3])
    with c1:
        st.title("📦 Ajuste de Stock")
        st.caption("Los cambios se reflejan en el catálogo general")
    with c2:
        st.write(f"👤: **{st.session_state['user_inv'].capitalize()}**")
        if st.button("🚪 Salir", use_container_width=True):
            st.session_state["auth_inv"] = False
            st.session_state["res_inv"] = None
            st.rerun()

    with st.form("buscar_cod_inv"):
        cod_buscado = st.text_input("Escribe el código de la pastilla (ej: 717, 24332...)").strip().lower()
        if st.form_submit_button("🔍 Buscar Código", use_container_width=True):
            if not cod_buscado:
                st.warning("⚠️ Escribe un código para buscar.")
            elif not os.path.exists(ARCHIVO_EXCEL):
                st.error("❌ No se encontró el archivo datos.xlsx.")
            else:
                df = pd.read_excel(ARCHIVO_EXCEL, header=None).fillna("").astype(str)
                lista_res = []
                for idx, fila in df.iterrows():
                    datos = extraer_7(fila.values.tolist())
                    m, _, _, _, cd, _, ct = datos
                    if not m or "hoja de" in m.lower() or "catálogo" in m.lower() or m.lower() == "marca":
                        continue
                    if (cod_buscado in cd.lower()) or (cod_buscado in ct.lower()):
                        lista_res.append((int(idx), datos))
                st.session_state["res_inv"] = lista_res

    resultados = st.session_state["res_inv"]
    if resultados is not None:
        if len(resultados) > 0:
            st.success(f"✅ {len(resultados)} coincidencia(s) encontrada(s)")
            for i, (fila_idx, datos) in enumerate(resultados):
                m, mod, a, sd, cd, st_tra, ct = datos
                cant_d = limpiar_entero(sd)
                cant_t = limpiar_entero(st_tra)

                with st.container(border=True):
                    st.markdown(f"### 🚘 {m.upper()} — {mod} ({a})")
                    cantidad_op = st.number_input("Unidades a sumar o restar:", min_value=1, value=1, step=1, key=f"num_{i}_{fila_idx}")

                    st.write("---")
                    st.info(f"🔹 **Delantera:** {cd if cd else 'Sin código'} | Stock actual: **{cant_d} u.**")
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("➕ Agregar Delantera", key=f"ad_{i}_{fila_idx}", use_container_width=True):
                            guardar_cantidad(fila_idx, 3, cant_d + cantidad_op)
                            st.session_state["res_inv"] = None
                            st.rerun()
                    with b2:
                        if st.button("➖ Restar Delantera", key=f"rd_{i}_{fila_idx}", use_container_width=True):
                            if cant_d >= cantidad_op:
                                guardar_cantidad(fila_idx, 3, cant_d - cantidad_op)
                                st.session_state["res_inv"] = None
                                st.rerun()
                            else:
                                st.error("No hay suficientes unidades.")

                    st.write("---")
                    st.success(f"🛑 **Trasera:** {ct if ct else 'Sin código'} | Stock actual: **{cant_t} u.**")
                    b3, b4 = st.columns(2)
                    with b3:
                        if st.button("➕ Agregar Trasera", key=f"at_{i}_{fila_idx}", use_container_width=True):
                            guardar_cantidad(fila_idx, 5, cant_t + cantidad_op)
                            st.session_state["res_inv"] = None
                            st.rerun()
                    with b4:
                        if st.button("➖ Restar Trasera", key=f"rt_{i}_{fila_idx}", use_container_width=True):
                            if cant_t >= cantidad_op:
                                guardar_cantidad(fila_idx, 5, cant_t - cantidad_op)
                                st.session_state["res_inv"] = None
                                st.rerun()
                            else:
                                st.error("No hay suficientes unidades.")
        else:
            st.error("❌ No se encontró ningún repuesto con ese código.")
