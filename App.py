import streamlit as st
import requests
import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="Rx Power Monitor", layout="wide")
st.title("📊 Análisis de ONTs desde GitHub")

# Configuración de tu repositorio
usuario = "Daniel272000"
repo = "monitor-onts"
branch = "main"

# Obtener fecha actual automáticamente
fecha_actual = datetime.datetime.now().strftime("%d-%m-%Y")
st.info(f"📅 Analizando archivos para la fecha: `{fecha_actual}`")

# Paso 1: Detectar subcarpeta dentro de la fecha
subcarpeta_url = f"https://api.github.com/repos/{usuario}/{repo}/contents/{fecha_actual}?ref={branch}"
r = requests.get(subcarpeta_url)

if r.status_code != 200:
    st.error("❌ No se encontró la carpeta con la fecha actual en GitHub.")
    st.stop()

subcarpetas = [item["name"] for item in r.json() if item["type"] == "dir"]

if not subcarpetas:
    st.warning("⚠️ No se encontró ninguna subcarpeta dentro de la fecha.")
    st.stop()

subcarpeta = subcarpetas[0]
st.success(f"📂 Subcarpeta detectada: `{subcarpeta}`")

# Paso 2: Obtener lista de archivos .txt
archivos_url = f"https://api.github.com/repos/{usuario}/{repo}/contents/{fecha_actual}/{subcarpeta}?ref={branch}"
resp = requests.get(archivos_url)

if resp.status_code != 200:
    st.error("❌ No se pudo acceder a los archivos de la subcarpeta.")
    st.stop()

archivos_txt = [item["name"] for item in resp.json() if item["name"].endswith(".txt")]

if not archivos_txt:
    st.warning("⚠️ No hay archivos .txt disponibles.")
    st.stop()

# Paso 3: Analizar y graficar cada archivo
raw_base = f"https://raw.githubusercontent.com/{usuario}/{repo}/{branch}/{fecha_actual}/{subcarpeta}"

for nombre_archivo in archivos_txt:
    url_txt = f"{raw_base}/{nombre_archivo}"
    st.markdown(f"### 📄 {nombre_archivo}")

    try:
        data = requests.get(url_txt).text.splitlines()
        rx_powers = []
        for linea in data[6:]:
            if linea.strip() == "" or linea.startswith("-"):
                continue
            columnas = linea.split("\t")
            if len(columnas) >= 2:
                try:
                    rx_powers.append(float(columnas[1]))
                except:
                    pass

        if not rx_powers:
            st.warning("⚠️ No se encontraron valores válidos.")
            continue

        buenas = sum(1 for v in rx_powers if v > -22)
        malas = sum(1 for v in rx_powers if v <= -22)
        total = len(rx_powers)
        porc_buenas = (buenas / total) * 100 if total else 0
        porc_malas = (malas / total) * 100 if total else 0

        st.write(f"- Total: {total} ONTs")
        st.write(f"- Buenas (> -22 dBm): {buenas} ({porc_buenas:.2f}%)")
        st.write(f"- Malas (≤ -22 dBm): {malas} ({porc_malas:.2f}%)")

        # 🥧 Gráfico de torta con etiquetas personalizadas
        etiquetas = [f"Buenas ({porc_buenas:.1f}%)", f"Malas ({porc_malas:.1f}%)"]
        cantidades = [buenas, malas]
        colores = ["green", "red"]

        fig, ax = plt.subplots()
        ax.pie(cantidades, labels=etiquetas, colors=colores,
               startangle=140)
        ax.set_title(f"Distribución Rx Power - {nombre_archivo}")
        st.pyplot(fig)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo {nombre_archivo}: {e}")
