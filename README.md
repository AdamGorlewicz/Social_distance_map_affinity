# Eco-HAB Social Maps from Affinity

`social_map_affinity.py` generates a vector social map for each mouse using affinity and differences in hierarchical rank. It also exports pairwise matrices and a color legend.

## Installation

```bash
python -m pip install numpy pandas matplotlib seaborn openpyxl
```

## Input files

Use two Eco-HAB CSV exports from the same recording session. Keep mouse IDs consistent across files.

| File | Required columns |
| --- | --- |
| `ranking.csv` | `animal_id`, `day`, `hour`, `phase`, `mu` |
| `pairwise_meetings.csv` | `day`, `hour`, `phase`, `phase_count`, `animal_id`, `animal_id_2`, `time_together` |

## Run the script

Edit the paths at the top of the script. For example, with both CSVs in a `data` folder relative to the working directory, use:

```python
ranking_file = Path("data/ranking.csv")
meetings_file = Path("data/pairwise_meetings.csv")
output_dir = Path("results_affinity")
```

Run from that working directory:

```bash
python social_map_affinity.py
```

The script creates the output directory if needed, saves the results, and displays the figures.

## Calculations

**Ranking.** The script matches ranking records to phase counts by day, hour, and phase label. Within each matched phase, it averages each mouse’s `mu` scores and ranks mice from highest to lowest, using average ranks for ties. Each mouse’s mean rank is the average across phases with available scores. Both light and dark phases are included when available.

**Affinity.** For each unordered pair, sum time spent together across locations within each recorded day, hour, and phase label. Average those totals across the pair’s recorded hours. Each observed pair contributes equally to the cohort mean. Unobserved pairs remain blank. The normalized coordinate is `A = (pair value − cohort mean) / (pair value + cohort mean)`. A value of zero corresponds to the cohort mean. Negative and positive values indicate pair values below and above it, respectively.

**Power and social distance.** Maps use mice present in both the mean ranking and the interaction matrix. For focal mouse `i` and partner `j`, power is `P = (rank_i − rank_j) / (N − 1)`, where `N` is the number of mice included in the maps. At least two shared mice are needed. Each arrow starts at `(1, 0)` and ends at `(A, P)`. Its length is `sqrt((1 − A)² + P²)`. Distance is symmetric. Both heatmaps display only the lower triangle.

## Output files

| File | Contents |
| --- | --- |
| `affinity.xlsx` | Pairwise affinity |
| `social_distance.xlsx` | Social distance for each pair |
| `power.xlsx` | Relative rank difference for each pair |
| `affinity_matrix.png` | Affinity heatmap |
| `social_distance_matrix.png` | Social distance heatmap |
| `mouse_color_legend.png` | Mouse IDs ordered by mean rank |
| `social_map_ego_<ID>.png` | One vector map for each focal mouse |

Excel rows identify focal mice and columns identify partners. Diagonal cells and undefined values are blank. Colored markers along the heatmap axes match the mouse colors in the ranking legend.
