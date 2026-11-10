# Social maps of mice from time spent together

This Python script analyzes one Eco-HAB recording session and creates a social map for each focal mouse (ego). A partner's horizontal coordinate represents affinity based on time spent together. Its vertical coordinate represents the difference in hierarchical rank. Social distance is the length of the arrow from ego to the partner.

## Installation

```bash
python -m pip install numpy pandas "matplotlib>=3.5" openpyxl
```

## Input data

Use two comma-separated exports from the same Eco-HAB session.

| File | Required columns | Contents |
| --- | --- | --- |
| `ranking.csv` | `animal_id`, `day`, `hour`, `mu` | Mouse ID, recording day and hour, and ranking score |
| `pairwise_meetings.csv` | `animal_id`, `animal_id_2`, `day`, `hour`, `phase`, `phase_count`, `time_together` | Pair IDs, recording day and hour, phase label and ID, and time together in seconds |

Mouse IDs must match across exports. The script uses meeting records labeled `dark_phase` for both the affinity calculation and phase matching. Each selected day and hour must map to one phase ID. The script sums all records for a pair and hour across locations. A location column may be present in the export and is optional for the calculation. Time values must be finite and nonnegative, and each pair's hourly total must fit within 3,600 seconds, with a 0.001-second rounding tolerance.

## Running the script

Save the script as `social_map_affinity.py` and replace the local paths at the top of the file. This example uses paths relative to the directory from which you run the script.

```python
RANKING_CSV = Path("data/ranking.csv")
MATCH_CSV = Path("data/pairwise_meetings.csv")
OUTPUT_DIR = Path("results_affinity")
N_DARK_PHASES = None
SCORE_COL = "mu"
```

```bash
python social_map_affinity.py
```

If you keep the original filename, run `python "social_map_affinity(3).py"`. By default, the script uses all available dark phases. Set `N_DARK_PHASES` to a positive integer to use that many phase IDs in ascending order. The script creates the output directory and overwrites files with matching names. Use a separate output directory for each session.

## Method

### Affinity

The script treats each pair as unordered and excludes self-pairs. For each pair and recorded hour, it sums time together in seconds and divides by 3,600, assuming a full hour of observation. It averages these fractions over the hours recorded for that pair to obtain its mean fraction. Hours without a record for that pair are excluded from the average.

The analysis cohort includes mice present in both the phase-matched ranking and the pairwise meeting matrix. At least two mice and one observed pair within that cohort are required. The cohort mean gives equal weight to each observed unordered pair.

```math
A_{ij} = \frac{f_{ij} - \bar{f}}{f_{ij} + \bar{f}}
```

Here, `f_ij` is the mean hourly fraction for the pair and the barred term is the cohort mean. For a positive cohort mean, affinity is −1 for a measured pair with zero time together, zero at the cohort mean, and positive above that mean. Affinity is symmetric and undefined for unobserved pairs or when the cohort mean is zero.

### Relative power

The script matches hourly ranking scores to phases using day and hour. Within each matched phase, it averages the available scores for each mouse and ranks the means in descending order. The highest mean receives rank 1 and ties receive the average of the occupied ranks. The script computes phase ranks before restricting the analysis to the shared cohort, then averages each mouse's available phase ranks.

```math
P_{ij} = \frac{R_i - R_j}{N - 1}
```

Here, `R_i` and `R_j` are the focal mouse's and partner's mean ranks, and `N` is the cohort size. Positive values indicate that the partner ranks higher on average than the focal mouse.

### Social distance

By default, ego is at (1, 0) and each partner is at its affinity and relative power coordinates. At a fixed power difference, higher affinity shortens the arrow.

```math
D_{ij} = \sqrt{(A_{ij} - 1)^2 + P_{ij}^2}
```

With the default ego position, distance is symmetric and dimensionless. The plot omits partners with undefined affinity.

## Output files

| File | Contents |
| --- | --- |
| `mean_fraction.xlsx` | Mean hourly fraction of time spent together for each pair |
| `affinity.xlsx` | Affinity matrix |
| `power.xlsx` | Normalized rank difference matrix |
| `social_distance.xlsx` | Social distance matrix |
| `social_map_ego_<ID>.png` | One social map per focal mouse |
| `mouse_color_legend.png` | Shared legend linking mouse IDs to colors |

Workbook rows represent focal mice and columns represent partners. Diagonal cells and undefined values are blank. Maps use a horizontal affinity scale from −1 to 1 and expand the vertical power scale if needed.
