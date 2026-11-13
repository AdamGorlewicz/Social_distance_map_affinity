import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from urllib.parse import quote

# input folders

ranking_file = Path(r"C:\Users\agorlewicz\Desktop\EcoHab\do chmury\example data\ranking.csv")
meetings_file = Path(r"C:\Users\agorlewicz\Desktop\EcoHab\do chmury\example data\pairwise_meetings.csv")

# output folder

output_dir = Path(r"C:\Users\agorlewicz\Desktop\EcoHab\do chmury\results_affinity")

# definitions

#color map for crosscorellation matrix

my_color = [
    '#E8E8E8', '#E7E7E8', '#E5E6E7', '#E4E6E7',
    '#E3E5E6', '#E2E4E6', '#E0E3E6', '#DFE2E5',
    '#DEE2E5', '#DDE1E4', '#DBE0E4', '#DADFE3',
    '#D9DEE3', '#D7DEE3', '#D6DDE2', '#D5DCE2',
    '#D4DBE1', '#D2DAE1', '#D1DAE1', '#D0D9E0',
    '#CED8E0', '#CDD7DF', '#CCD6DF', '#CBD6DF',
    '#C9D5DE', '#C8D4DE', '#C7D3DD', '#C6D2DD',
    '#C4D2DD', '#C3D1DC', '#C2D0DC', '#C0CFDB',
    '#BFCEDB', '#BECDDA', '#BDCDDA', '#BBCCDA',
    '#BACBD9', '#B9CAD9', '#B8C9D8', '#B6C9D8',
    '#B5C8D8', '#B4C7D7', '#B2C6D7', '#B1C5D6',
    '#B0C5D6', '#AFC4D6', '#ADC3D5', '#ACC2D5',
    '#ABC1D4', '#A9C1D4', '#A8C0D4', '#A7BFD3',
    '#A6BED3', '#A4BDD2', '#A3BDD2', '#A2BCD1',
    '#A1BBD1', '#9FBAD1', '#9EB9D0', '#9DB9D0',
    '#9BB8CF', '#9AB7CF', '#99B6CF', '#98B5CE',
    '#96B5CE', '#95B4CD', '#94B3CD', '#93B2CD',
    '#91B1CC', '#90B1CC', '#8FB0CB', '#8DAFCB',
    '#8CAECB', '#8BADCA', '#8AADCA', '#88ACC9',
    '#87ABC9', '#86AAC8', '#85A9C8', '#83A9C8',
    '#82A8C7', '#81A7C7', '#7FA6C6', '#7EA5C6',
    '#7DA5C6', '#7CA4C5', '#7AA3C5', '#79A2C4',
    '#78A1C4', '#76A1C4', '#75A0C3', '#749FC3',
    '#739EC2', '#719DC2', '#709DC2', '#6F9CC1',
    '#6E9BC1', '#6C9AC0', '#6B99C0', '#6A98BF',
    '#6898BF', '#6797BF', '#6696BE', '#6595BE',
    '#6394BD', '#6294BD', '#6193BD', '#6092BC',
    '#5E91BC', '#5D90BB', '#5C90BB', '#5A8FBB',
    '#598EBA', '#588DBA', '#578CB9', '#558CB9',
    '#548BB9', '#538AB8', '#5189B8', '#5088B7',
    '#4F88B7', '#4E87B6', '#4C86B6', '#4B85B6',
    '#4A84B5', '#4984B5', '#4783B4', '#4682B4'
]

# this function imports dataframes from csv files

def load_data(ranking_file, meetings_file):
    ranking = pd.read_csv(ranking_file, dtype={"animal_id": str})
    meetings = pd.read_csv(meetings_file, dtype={"animal_id": str, "animal_id_2": str},)
    return ranking, meetings

# this function calculates ranking
# ranks contains the rank of each animal in each phase, 
# and mean_rank contains each animal’s average rank across all phases.

def calculate_ranking(ranking, meetings):
    phases = meetings[["day", "hour", "phase", "phase_count"]].drop_duplicates()
    data = ranking.merge(phases, on=["day", "hour", "phase"])
    mean_mu = data.groupby(["phase", "phase_count", "animal_id"])["mu"].mean()
    scores = mean_mu.unstack("animal_id")
    ranks = scores.rank(axis=1, ascending=False)
    mean_rank = ranks.mean().sort_values(kind="stable").rename("mean_rank")
    return ranks, mean_rank

# this function plots ID of each mouse based on the ranking
# dominant mouse is at the top

def plot_ranking_legend(mean_rank):
    fig0, ax = plt.subplots()
    ax.set_axis_off()
    for mouse_id in mean_rank.sort_values(kind="stable").index:
        ax.scatter([], [], label=str(mouse_id))
    ax.legend(title="ranking\n", loc="center", frameon=False)
    return fig0

# this function calculates affinity

def calculate_affinity(meetings):
    pair = ["animal_id", "animal_id_2"]
    data = meetings.loc[meetings["animal_id"] != meetings["animal_id_2"]].copy()
    data[pair] = np.sort(data[pair].to_numpy(), axis=1)
    hourly_time = data.groupby(pair + ["day", "hour", "phase"])["time_together"].sum()
    pair_mean = hourly_time.groupby(level=pair).mean()
    cohort_mean = pair_mean.mean()
    affinity = (pair_mean - cohort_mean) / (pair_mean + cohort_mean)
    matrix = affinity.unstack("animal_id_2")
    return matrix.combine_first(matrix.T)

# this function calculates affinity pairwise matrix

def add_mouse_markers(ax, matrix, plot_ranks):
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    color_map = {
        mouse_id: colors[i % len(colors)]
        for i, mouse_id in enumerate(plot_ranks.index)
    }

    ax.scatter(
        np.arange(len(matrix.columns)) + 0.5,
        np.full(len(matrix.columns), -0.03),
        c=[color_map.get(mouse_id, "lightgrey") for mouse_id in matrix.columns],
        s=30,
        transform=ax.get_xaxis_transform(),
        clip_on=False,
    )
    ax.scatter(
        np.full(len(matrix.index), -0.03),
        np.arange(len(matrix.index)) + 0.5,
        c=[color_map.get(mouse_id, "lightgrey") for mouse_id in matrix.index],
        s=30,
        transform=ax.get_yaxis_transform(),
        clip_on=False,
    )
    ax.xaxis.labelpad = 14
    ax.yaxis.labelpad = 14


def plot_affinity_matrix(affinity, plot_ranks):
    mouse_ids = sorted(affinity.index)
    matrix = affinity.reindex(index=mouse_ids, columns=mouse_ids)
    mask = np.triu(np.ones(matrix.shape, dtype=bool))
    fig1, ax = plt.subplots()
    sns.heatmap(
        matrix,
        mask=mask,
        cmap=my_color,
        vmin=-1,
        vmax=1,
        center=0,
        square=True,
        linewidths=0.5,
        xticklabels=False,
        yticklabels=False,
        cbar_kws={"shrink": 0.5, "label": "affinity"},
        ax=ax,
    )
    ax.tick_params(width=0)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.set_title("affinity", fontsize=14)
    ax.set_xlabel("# mouse", fontsize=14)
    ax.set_ylabel("# mouse", fontsize=14)
    add_mouse_markers(ax, matrix, plot_ranks)
    return fig1

# this function calculates social distances and creates vector social maps

def plot_social_maps():
    ranks = mean_rank.loc[mean_rank.index.isin(affinity.index)].sort_values(kind="stable")
    mouse_ids = ranks.index
    n_mice = len(mouse_ids)
    ego_position = (1, 0)
    social_distance = pd.DataFrame(
        np.nan,
        index=mouse_ids,
        columns=mouse_ids,
    )
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    color_map = {
        mouse_id: colors[i % len(colors)]
        for i, mouse_id in enumerate(mouse_ids)
    }
    figures = []
    ticks = [-1, -0.5, 0, 0.5, 1]
    for ego in mouse_ids:
        fig, ax = plt.subplots(figsize=(5, 5), layout="constrained")

        ax.axhline(0, color="black", linewidth=0.8)
        ax.axvline(0, color="black", linewidth=0.8)
        ax.scatter(
            *ego_position,
            s=65,
            color=color_map[ego],
            zorder=10,
            clip_on=False,
        )
        ax.annotate(
            "Ego",
            xy=ego_position,
            xytext=(-6, 6),
            textcoords="offset points",
            ha="right",
        )
        for partner in mouse_ids.drop(ego):
            x = affinity.loc[ego, partner]
            if pd.isna(x):
                continue
            y = (ranks.loc[ego] - ranks.loc[partner]) / (n_mice - 1)
            social_distance.loc[ego, partner] = np.hypot(x - 1, y)
            color = color_map[partner]
            ax.annotate(
                "",
                xy=(x, y),
                xytext=ego_position,
                arrowprops={
                    "arrowstyle": "->",
                    "color": color,
                    "linewidth": 1.3,
                },
            )
            ax.scatter(x, y, s=40, color=color, zorder=5, clip_on=False)
        ax.set(
            title=f"{ego}\n",
            xlabel="affinity",
            ylabel="power",
            xlim=(-1, 1),
            ylim=(-1, 1),
            xticks=ticks,
            yticks=ticks,
        )
        ax.set_aspect("equal")
        ax.xaxis.label.set_size(14)
        ax.yaxis.label.set_size(14)
        ax.tick_params(axis="both", labelsize=12, length=6, width=1.2)
        ax.set_axisbelow(True)
        ax.grid(linestyle=":", linewidth=0.5, color="lightgrey")
        for spine in ax.spines.values():
            spine.set_color("lightgrey")
            spine.set_linewidth(0.8)
        figures.append(fig)
    return figures, social_distance

# this function creates social distance crosscorellation matrix

def plot_social_distance_matrix(social_distance, plot_ranks):
    mouse_ids = sorted(social_distance.index)
    matrix = social_distance.reindex(index=mouse_ids, columns=mouse_ids)
    mask = np.triu(np.ones(matrix.shape, dtype=bool))
    fig, ax = plt.subplots()
    sns.heatmap(
        matrix,
        mask=mask,
        cmap=my_color,
        vmin=0,
        square=True,
        linewidths=0.5,
        xticklabels=False,
        yticklabels=False,
        cbar_kws={"shrink": 0.5, "label": "social distance"},
        ax=ax,
    )
    ax.tick_params(width=0)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.set_title("social distance", fontsize=14)
    ax.set_xlabel("# mouse", fontsize=14)
    ax.set_ylabel("# mouse", fontsize=14)
    add_mouse_markers(ax, matrix, plot_ranks)
    return fig

# process

ranking, meetings = load_data(ranking_file, meetings_file)
ranks, mean_rank = calculate_ranking(ranking, meetings)
affinity = calculate_affinity(meetings)
plot_ranks = mean_rank.loc[mean_rank.index.isin(affinity.index)].sort_values(kind="stable")
fig0 = plot_affinity_matrix(affinity, plot_ranks)
fig1 = plot_ranking_legend(plot_ranks)
figures, social_distance = plot_social_maps()
fig2 = plot_social_distance_matrix(social_distance, plot_ranks)
output_dir.mkdir(parents=True, exist_ok=True)

# save results

mice = sorted(plot_ranks.index)
rank_values = plot_ranks.reindex(mice).to_numpy()
power = pd.DataFrame(
    (rank_values[:, None] - rank_values[None, :]) / (len(mice) - 1),
    index=mice,
    columns=mice,
)
diagonal = np.eye(len(mice), dtype=bool)
for filename, matrix in (
    ("affinity.xlsx", affinity),
    ("social_distance.xlsx", social_distance),
    ("power.xlsx", power),
):
    matrix.reindex(index=mice, columns=mice).mask(diagonal).to_excel(
        output_dir / filename,
        index_label="Ego / Partner",
        na_rep="",
        engine="openpyxl",
    )
fig0.savefig(output_dir / "affinity_matrix.png", dpi=300, bbox_inches="tight")
fig1.savefig(output_dir / "mouse_color_legend.png", dpi=300, bbox_inches="tight")
fig2.savefig(output_dir / "social_distance_matrix.png", dpi=300, bbox_inches="tight")
for ego, fig in zip(plot_ranks.index, figures):
    ego_id = quote(str(ego), safe="")
    fig.savefig(
        output_dir / f"social_map_ego_{ego_id}.png",
        dpi=300,
        bbox_inches="tight",
    )
plt.show()


