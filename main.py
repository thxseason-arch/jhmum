import datetime
import os
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import s3fs
import streamlit as st
import xarray as xr

# Configuração da página Streamlit
st.set_page_config(page_title="GOES Satélite", page_icon="🛰️", layout="centered")

st.title("🛰️ Monitor Satelital GOES-16 / GOES-19")
st.write("Selecione os parâmetros abaixo para gerar e visualizar a imagem de satélite.")

# --- Painel de Controlos ---
col1, col2 = st.columns(2)

with col1:
    sat = st.selectbox(
        "Satélite:",
        options=["noaa-goes16", "noaa-goes19"],
        format_func=lambda x: "GOES-16 (East)" if "16" in x else "GOES-19 (East)",
    )
    band = st.selectbox(
        "Produto / Banda:",
        options=["C04", "C02", "C13"],
        format_func=lambda x: {
            "C04": "Banda 04 (Cirrus - 1.37 µm)",
            "C02": "Banda 02 (Visível - 0.64 µm)",
            "C13": "Banda 13 (Infravermelho - 10.3 µm)",
        }[x],
    )

with col2:
    date_val = st.date_input(
        "Data:", value=datetime.date.today() - datetime.timedelta(days=1)
    )
    hour_val = st.selectbox(
        "Hora (UTC):",
        options=list(range(24)),
        index=18,
        format_func=lambda h: f"{h:02d}:00 UTC",
    )

# Coordenadas fixas (Brasil / América do Sul)
bbox = {"min_lon": -60.0, "max_lon": -40.0, "min_lat": -25.0, "max_lat": -5.0}


# --- Funções Auxiliares de Processamento ---
def create_cirrus_colormap():
    colors = [
        (0.00, "#05070a"),
        (0.03, "#1f150a"),
        (0.08, "#634212"),
        (0.15, "#b88128"),
        (0.25, "#f5d378"),
        (0.38, "#ffffff"),
        (1.00, "#ffffff"),
    ]
    return mcolors.LinearSegmentedColormap.from_list("cirrus_amber", colors)


def fetch_and_render():
    fs = s3fs.S3FileSystem(anon=True)
    doy = date_val.strftime("%j")
    year = date_val.strftime("%Y")
    path = f"{sat}/ABI-L2-CMIPF/{year}/{doy}/{hour_val:02d}/"

    files = fs.ls(path)
    target_files = [
        f for f in files if f"M6{band}" in f or f"M3{band}" in f or f"M4{band}" in f
    ]

    if not target_files:
        raise FileNotFoundError("Nenhum dado encontrado para a data/hora selecionada.")

    local_nc = "temp_goes.nc"
    fs.get(target_files[0], local_nc)

    with xr.open_dataset(local_nc, engine="h5netcdf") as ds:
        proj_info = ds.goes_imager_projection
        h = float(proj_info.perspective_point_height)
        lon_0 = float(proj_info.longitude_of_projection_origin)
        sweep = str(proj_info.sweep_angle_axis)

        p = ccrs.Geostationary(
            central_longitude=lon_0, satellite_height=h, sweep_angle_axis=sweep
        )
        pc = ccrs.PlateCarree()

        x1_m, y1_m = p.transform_point(bbox["min_lon"], bbox["min_lat"], pc)
        x2_m, y2_m = p.transform_point(bbox["max_lon"], bbox["max_lat"], pc)

        x_min_m, x_max_m = sorted([x1_m, x2_m])
        y_min_m, y_max_m = sorted([y1_m, y2_m])

        data_slice = ds["CMI"].sel(
            x=slice(x_min_m / h, x_max_m / h), y=slice(y_max_m / h, y_min_m / h)
        )
        cmi_data = np.nan_to_num(data_slice.values, nan=0.0)

        fig = plt.figure(figsize=(8, 8), dpi=150, facecolor="#05070a")
        ax = plt.axes(projection=p, facecolor="#05070a")
        ax.set_extent([x_min_m, x_max_m, y_min_m, y_max_m], crs=p)

        cmap = create_cirrus_colormap() if band == "C04" else "gray"
        norm = mcolors.Normalize(vmin=0.002, vmax=0.30) if band == "C04" else None

        ax.imshow(
            cmi_data,
            origin="upper",
            extent=[x_min_m, x_max_m, y_min_m, y_max_m],
            transform=p,
            cmap=cmap,
            norm=norm,
        )
        ax.add_feature(
            cfeature.COASTLINE, edgecolor="black", linewidth=0.9, zorder=5
        )
        ax.add_feature(
            cfeature.BORDERS,
            edgecolor="black",
            linewidth=0.6,
            linestyle=":",
            zorder=5,
        )

        # Mira central
        cx, cy = (x_min_m + x_max_m) / 2.0, (y_min_m + y_max_m) / 2.0
        ax.plot(
            [cx],
            [cy],
            marker="+",
            color="white",
            markersize=20,
            markeredgewidth=2,
            zorder=6,
        )

        ax.axis("off")
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

        out_img = "goes_result.png"
        plt.savefig(
            out_img, bbox_inches="tight", pad_inches=0, facecolor="#05070a"
        )
        plt.close(fig)

    if os.path.exists(local_nc):
        os.remove(local_nc)

    return out_img


# --- Ação do Botão ---
if st.button("🚀 Gerar Imagem de Satélite", type="primary"):
    # Animação e Indicador de Carregamento
    with st.spinner("⏳ A ligar à AWS S3 da NOAA e a processar a imagem..."):
        try:
            image_path = fetch_and_render()
            st.success("✅ Imagem de satélite processada com sucesso!")
            st.image(image_path, use_container_width=True)
        except Exception as e:
            st.error(f"❌ Erro ao processar: {str(e)}")
