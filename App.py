import streamlit as st
import requests
import datetime
import matplotlib.pyplot as plt

# Configuración del repositorio
usuario = "Daniel272000"
repo = "monitor-onts"
branch = "main"

st.set_page_config(page_title="Análisis de ONTs", layout="wide")
st.title("📊 Análisis de Rx Power desde GitHub")

# Obtener carpetas de fecha desde el repositorio
root_url = f"https://api.github.com/repos/{usuario}/{repo}/contents?ref={branch}"
resp = requests.get(root_url)
if resp.status_code != 200:
    st.error("❌ No se pudo acceder al repositorio en GitHub.")
    st.stop()

fechas = sorted([item["name"] for item in resp.json() if item["type"] == "dir" and "-" in item["name"]])
fecha_seleccionada = st.selectbox("🗓️ Selecciona la fecha:", fechas)

# Obtener subcarpetas dentro de la fecha seleccionada
sub_url = f"https://api.github.com/repos/{usuario}/{repo}/contents/{fecha_seleccionada}?ref={branch}"
resp2 = requests.get(sub_url)
if resp2.status_code != 200:
    st.error("❌ No se pudo acceder a la subcarpeta.")
    st.stop()

subcarpetas = [item["name"] for item in resp2.json() if item["type"] == "dir"]
subcarpeta = st.selectbox("📁 Selecciona la subcarpeta:", subcarpetas)

# Leer archivos .txt dentro de esa carpeta
archivos_url = f"https://api.github.com/repos/{usuario}/{repo}/contents/{fecha_seleccionada}/{subcarpeta}?ref={branch}"
resp3 = requests.get(archivos_url)
archivos_txt = [item["name"] for item in resp3.json() if item["name"].endswith(".txt")]

if not archivos_txt:
    st.warning("No hay archivos .txt disponibles para analizar.")
    st.stop()

# Diccionario para almacenar los datos
graficos_data = {}

# Análisis de cada archivo
for nombre_archivo in archivos_txt:
    url_txt = f"https://raw.githubusercontent.com/{usuario}/{repo}/{branch}/{fecha_seleccionada}/{subcarpeta}/{nombre_archivo}"
    st.markdown(f"### 📄 {nombre_archivo}")

    try:
        data = requests.get(url_txt).text.splitlines()
        datos = []
        for linea in data[6:]:
            if linea.strip() == "" or linea.startswith("-"):
                continue
            columnas = linea.split("\t")
            if len(columnas) >= 2:
                try:
                    datos.append(float(columnas[1]))
                except:
                    pass

        if not datos:
            st.warning("⚠️ No se encontraron valores válidos.")
            continue

        graficos_data[nombre_archivo] = datos
        total = len(datos)
        buenas = sum(1 for v in datos if v > -22)
        malas = sum(1 for v in datos if v <= -22)
        porc_buenas = (buenas / total) * 100 if total else 0
        porc_malas = (malas / total) * 100 if total else 0

        st.write(f"- Total: {total} ONTs")
        st.write(f"- Buenas (> -22 dBm): {buenas} ({porc_buenas:.2f}%)")
        st.write(f"- Malas (≤ -22 dBm): {malas} ({porc_malas:.2f}%)")

        if st.button(f"Mostrar gráfica de {nombre_archivo}"):
            # Gráfica de torta más pequeña
            etiquetas = [f"Buenas ({porc_buenas:.1f}%)", f"Malas ({porc_malas:.1f}%)"]
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.pie([buenas, malas], labels=etiquetas, colors=["green", "red"], autopct='%1.1f%%', startangle=140)
            ax.set_title(f"Distribución Rx Power - {nombre_archivo}")
            st.pyplot(fig)

    except Exception as e:
        st.error(f"❌ Error al procesar {nombre_archivo}: {e}")
