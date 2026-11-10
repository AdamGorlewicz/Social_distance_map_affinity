from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import colormaps
from matplotlib.lines import Line2D
from urllib.parse import quote


# Input files for one session.
RANKING_CSV = Path(r"C:\Users\agorlewicz\Desktop\EcoHab\do chmury\example data\ranking.csv")
MATCH_CSV = Path(r"C:\Users\agorlewicz\Desktop\EcoHab\do chmury\example data\pairwise_meetings.csv")

# Output directory for social maps.
OUTPUT_DIR = Path(r"C:\Users\agorlewicz\Desktop\EcoHab\do chmury\results_affinity")

# Analysis and plot settings.
N_DARK_PHASES = None  # Use a positive integer or None to include all phases.
SCORE_COL = "mu"
FONT_SIZE = 14
EGO_POSITION = (1, 0)


def select_phases(df, n_dark_phases):
    phases = sorted(df["_dark_phase_id"].unique())
    chosen = phases if n_dark_phases is None else phases[:n_dark_phases]
    return df[df["_dark_phase_id"].isin(chosen)].copy()


def prepare_ranking(ranking, match, match_file, score_col, n_dark_phases):
    phase_by_hour = match[["day", "hour", "phase_count"]].copy()
    for column in phase_by_hour.columns:
        phase_by_hour[column] = pd.to_numeric(
            phase_by_hour[column], errors="coerce"
        )

    if phase_by_hour.isna().any().any():
        raise ValueError(f"{match_file}: invalid day, hour, or phase_count values.")

    if "phase" in match.columns:
        phase_by_hour = phase_by_hour.loc[match["phase"].eq("dark_phase")]

    phase_by_hour = phase_by_hour.drop_duplicates().rename(
        columns={"phase_count": "_dark_phase_id"}
    )
    phase_by_hour = select_phases(phase_by_hour, n_dark_phases)

    ranking = ranking.merge(
        phase_by_hour, on=["day", "hour"], how="left", validate="many_to_one"
    )
    ranking = ranking.dropna(subset=["_dark_phase_id"])

    phase_values = (
        ranking.groupby(["_dark_phase_id", "animal_id"], as_index=False)[score_col]
        .mean()
    )
    scores_wide = phase_values.pivot(
        index="_dark_phase_id", columns="animal_id", values=score_col
    ).sort_index()

    ranks_wide = scores_wide.rank(axis=1, ascending=False, method="average")
    mean_rank = ranks_wide.mean(axis=0).rename("mean_rank")
    return ranks_wide, mean_rank


def prepare_match_matrix(match, match_file, n_dark_phases):
    pair_columns = ["animal_id", "animal_id_2"]
    match = match.loc[match["phase"].eq("dark_phase")].copy()
    match["_dark_phase_id"] = pd.to_numeric(match["phase_count"], errors="raise")
    match = select_phases(match, n_dark_phases)
    match = match.loc[match["animal_id"].ne(match["animal_id_2"])].copy()
    if match.empty or match[pair_columns].isna().any().any():
        raise ValueError(f"{match_file}: expected pairs of mice in the selected dark phases.")

    match["time_together"] = pd.to_numeric(match["time_together"], errors="raise")
    if not np.isfinite(match["time_together"]).all() or match["time_together"].lt(0).any():
        raise ValueError(f"{match_file}: invalid time_together values.")

    # Sum time across locations within each measured hour.
    match[pair_columns] = np.sort(match[pair_columns].to_numpy(), axis=1)
    hourly = match.groupby([*pair_columns, "day", "hour"])["time_together"].sum()
    if not hourly.between(0, 3600.001).all():
        raise ValueError(f"{match_file}: invalid time_together total for a pair and hour.")

    # Each exported hour represents 3600 seconds of observation.
    pairs = (hourly.groupby(level=pair_columns).mean() / 3600).clip(upper=1).unstack()
    return pairs.combine_first(pairs.T)


def load_session(ranking_file, match_file):
    ranking = pd.read_csv(ranking_file, dtype={"animal_id": str})
    match = pd.read_csv(match_file, dtype={"animal_id": str, "animal_id_2": str})
    _, mean_rank = prepare_ranking(ranking, match, match_file, SCORE_COL, N_DARK_PHASES)
    match_matrix = prepare_match_matrix(match, match_file, N_DARK_PHASES)

    mice = sorted(set(mean_rank.index) & set(match_matrix.index))
    if len(mice) < 2:
        raise ValueError("At least two mice must appear in both ranking and match data.")

    match_matrix = match_matrix.reindex(index=mice, columns=mice)
    pair_values = match_matrix.to_numpy()[np.triu_indices(len(mice), k=1)]
    observed = pair_values[~np.isnan(pair_values)]
    if not observed.size:
        raise ValueError("No measured pairs in the analysis cohort.")
    cohort_mean = observed.mean()
    # Leave 0/0 undefined, as in the agonism script.
    affinity = (match_matrix - cohort_mean) / (match_matrix + cohort_mean)

    rank = mean_rank.reindex(mice).to_numpy(dtype=float)
    power = (rank[:, None] - rank[None, :]) / (len(mice) - 1)
    power_matrix = pd.DataFrame(power, index=mice, columns=mice)

    folder = ranking_file.parent.name
    name = {"control-before": "Pre-surgery", "control-after": "Post-surgery"}.get(folder, folder)
    return {
        "session": name,
        "mice": mice,
        "affinity_matrix": affinity,
        "power_matrix": power_matrix,
        "distance_matrix": np.hypot(affinity - EGO_POSITION[0], power_matrix - EGO_POSITION[1]),
    }


def plot_mouse_legend(mice, color_map):
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="None",
            markersize=9,
            markerfacecolor=color_map[mouse],
            markeredgecolor=color_map[mouse],
            label=mouse,
        )
        for mouse in mice
    ]

    fig, ax = plt.subplots(figsize=(5, max(2, 0.42 * len(mice) + 0.6)))
    ax.axis("off")
    ax.legend(handles=handles, loc="center", frameon=False, fontsize=FONT_SIZE)
    fig.tight_layout()
    return fig


def plot_social_map(session, ego, color_map):
    fig, ax = plt.subplots()
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.axhline(0, color="black", linewidth=0.8, zorder=1)
    ax.axvline(0, color="black", linewidth=0.8, zorder=1)
    ax.scatter(*EGO_POSITION, s=65, color=color_map[ego], zorder=10, clip_on=False)
    ax.annotate(
        "Ego",
        xy=EGO_POSITION,
        xytext=(-6, 6),
        ha="right",
        textcoords="offset points",
        fontsize=8,
        color="black",
    )

    for other in session["mice"]:
        if other == ego:
            continue

        affinity = session["affinity_matrix"].loc[ego, other]
        power = session["power_matrix"].loc[ego, other]
        if pd.isna(affinity):
            continue

        ax.annotate(
            "",
            xy=(affinity, power),
            xytext=EGO_POSITION,
            arrowprops={
                "arrowstyle": "->",
                "linewidth": 1.3,
                "color": color_map[other],
                "alpha": 0.85,
            },
            zorder=3,
        )
        ax.scatter(
            affinity, power, s=40, color=color_map[other], zorder=5, clip_on=False
        )

    ax.set_xlim(-1, 1)
    power_limit = max(1.0, session["power_matrix"].abs().max().max())
    ax.set_ylim(-power_limit, power_limit)
    ax.set_aspect("equal", adjustable="box")

    ticks = np.linspace(-1, 1, 5)
    ax.set_xticks(ticks)
    ax.set_yticks(np.linspace(-power_limit, power_limit, 5))
    ax.tick_params(axis="both", labelsize=10, width=0.5, colors="black")
    ax.set_xlabel("Affinity", fontsize=10)
    ax.set_ylabel("Power", fontsize=10)
    ax.set_title(session["session"], y=1.10, fontsize=10)

    ax.grid(linestyle=":", linewidth=0.5, color="grey", alpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#E8E8E8")
    ax.spines["bottom"].set_color("#E8E8E8")

    fig.tight_layout()
    return fig


def main():
    for input_file in (RANKING_CSV, MATCH_CSV):
        if not input_file.is_file():
            raise FileNotFoundError(f"Input CSV not found: {input_file}")

    session = load_session(RANKING_CSV, MATCH_CSV)
    mice = session["mice"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Leave the diagonal blank in each workbook.
    diagonal = np.eye(len(mice), dtype=bool)

    for filename, matrix in (
        ("affinity.xlsx", session["affinity_matrix"]),
        ("social_distance.xlsx", session["distance_matrix"]),
        ("power.xlsx", session["power_matrix"]),
    ):
        output_file = OUTPUT_DIR / filename
        matrix.mask(diagonal).to_excel(
            output_file,
            index_label="Ego / Partner",
            na_rep="",
            engine="openpyxl",
        )

    # Use the same mouse colors in the legend and all social maps.
    cmap = colormaps.get_cmap("tab20")
    color_map = {
        mouse: cmap(i / (len(mice) - 1))
        for i, mouse in enumerate(mice)
    }

    legend_fig = plot_mouse_legend(mice, color_map)
    legend_file = OUTPUT_DIR / "mouse_color_legend.png"
    legend_fig.savefig(legend_file, dpi=300, bbox_inches="tight")

    for ego in mice:
        fig = plot_social_map(session, ego, color_map)

        # Encode characters that could be interpreted as path separators.
        ego_id = quote(str(ego), safe="")
        output_file = OUTPUT_DIR / f"social_map_ego_{ego_id}.png"

        fig.savefig(output_file, dpi=300, bbox_inches="tight")

    plt.show()


if __name__ == "__main__":
    main()
