from io import BytesIO
from pathlib import Path
from threading import Lock
from zipfile import ZIP_DEFLATED, ZipFile

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import streamlit as st
from urllib.parse import quote

from affinity import (
    calculate_affinity,
    calculate_ranking,
    load_data,
    plot_affinity_matrix,
    plot_ranking_legend,
    plot_social_distance_matrix,
    plot_social_maps,
)


@st.cache_resource
def plot_lock():
    return Lock()


def png_bytes(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
    return buffer.getvalue()


def analyze(ranking_file, meetings_file):
    ranking, meetings = load_data(ranking_file, meetings_file)
    _, mean_rank = calculate_ranking(ranking, meetings)
    affinity = calculate_affinity(meetings)
    ranks = mean_rank.loc[mean_rank.index.isin(affinity.index)]
    if len(ranks) < 2:
        raise ValueError("At least two mice must appear in both files.")

    with plot_lock():
        figures_before = set(plt.get_fignums())
        try:
            maps, distance = plot_social_maps(affinity, ranks)
            figures = {
                "affinity_matrix.png": plot_affinity_matrix(affinity, ranks),
                "social_distance_matrix.png": plot_social_distance_matrix(distance, ranks),
                "mouse_color_legend.png": plot_ranking_legend(ranks),
            }
            figures.update(
                (map_filename(mouse), fig) for mouse, fig in zip(ranks.index, maps)
            )
            images = {name: png_bytes(fig) for name, fig in figures.items()}
        finally:
            for number in set(plt.get_fignums()) - figures_before:
                plt.close(number)

    archive = BytesIO()
    mice = sorted(ranks.index)
    rank_values = ranks.reindex(mice).to_numpy()
    power = pd.DataFrame(
        (rank_values[:, None] - rank_values[None, :]) / (len(mice) - 1),
        index=mice, columns=mice,
    )
    power = power.mask(np.eye(len(mice), dtype=bool))
    with ZipFile(archive, "w", ZIP_DEFLATED) as results:
        for name, data in images.items():
            results.writestr(name, data)
        for name, matrix in (
            ("affinity.xlsx", affinity),
            ("social_distance.xlsx", distance),
            ("power.xlsx", power),
        ):
            workbook = BytesIO()
            matrix.reindex(index=mice, columns=mice).to_excel(
                workbook, index_label="Ego / Partner", engine="openpyxl"
            )
            results.writestr(name, workbook.getvalue())
    return ranks, images, archive.getvalue(), affinity, distance


def map_filename(mouse):
    return f"social_map_ego_{quote(str(mouse), safe='')}.png"


def main():
    st.set_page_config(page_title="Eco-HAB | Affinity Maps", layout="wide")
    st.title("Eco-HAB social maps (affinity)")

    with st.sidebar:
        ranking = st.file_uploader("Ranking", type="csv", key="ranking")
        meetings = st.file_uploader("Pairwise meetings", type="csv", key="meetings")

        st.markdown("Demo")
        use_example = st.button("Load example data")

    uploads_ready = ranking is not None and meetings is not None
    upload_ids = (ranking.file_id, meetings.file_id) if uploads_ready else None
    if st.session_state.get("upload_ids") != upload_ids:
        st.session_state.pop("analysis", None)
        st.session_state["upload_ids"] = upload_ids

    generate = uploads_ready and st.button("Generate maps", type="primary")
    if use_example or generate:
        st.session_state.pop("analysis", None)
        try:
            with st.spinner("Calculating matrices and generating maps…"):
                if use_example:
                    folder = Path(__file__).resolve().parent
                    ranking = folder / "ranking.csv"
                    meetings = folder / "pairwise_meetings.csv"
                st.session_state.analysis = analyze(ranking, meetings)
                st.session_state.analysis_source = "Example data" if use_example else "Uploaded data"
        except FileNotFoundError:
            st.error("Place ranking.csv and pairwise_meetings.csv next to app.py to use example data.")
        except (KeyError, ValueError, TypeError) as error:
            st.error(f"Check your CSV files. {error}")

    if "analysis" not in st.session_state:
        if not uploads_ready and not use_example:
            st.info("Upload files with ranking and meetings data or select 'Load example data'.")
        return

    st.caption(st.session_state.get("analysis_source", "Results"))
    ranks, images, archive, affinity, distance = st.session_state.analysis
    st.download_button(
        "Download results (ZIP)", archive, "results_affinity.zip", "application/zip"
    )
    ranking_tab, affinity_tab, maps_tab, distance_tab = st.tabs(
        ["Ranking", "Affinity", "Social Maps", "Social Distance"]
    )
    with ranking_tab:
        st.image(images["mouse_color_legend.png"], width=560)
        st.dataframe(ranks.to_frame())
    with affinity_tab:
        st.image(images["affinity_matrix.png"], width=560)
        st.dataframe(affinity.sort_index().sort_index(axis=1).round(3))
    with maps_tab:
        ego = st.selectbox("Focal mouse", ranks.index)
        st.image(images[map_filename(ego)], width=560)
    with distance_tab:
        st.image(images["social_distance_matrix.png"], width=560)
        st.dataframe(distance.sort_index().sort_index(axis=1).round(3))



if __name__ == "__main__":
    main()
