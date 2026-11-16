# Eco-HAB Affinity Social Maps

Streamlit app for generating affinity and social distance heatmaps, a ranking legend, and vector social maps from Eco-HAB CSV exports.

## Run locally

In the project directory, with Python 3.12:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Deploy on Streamlit Community Cloud

Upload `app.py`, `affinity.py`, `requirements.txt`, and this README to the same directory in your GitHub repository. In [Streamlit Community Cloud](https://share.streamlit.io/), select **Create app**, choose the repository and branch, and set the main file path to `app.py` (or `streamlit/app.py` with the supplied repository layout). Select Python 3.12 in the advanced settings and deploy.

## Input and output

Upload two CSVs from the same recording session and click **Generate maps**.

| Export | Required columns |
| --- | --- |
| `ranking.csv` | `animal_id`, `day`, `hour`, `phase`, `mu` |
| `pairwise_meetings.csv` | `animal_id`, `animal_id_2`, `time_together`, `day`, `hour`, `phase`, `phase_count` |

At least two mice must appear in both datasets. Affinity uses mean hourly time spent together for each unordered pair and is normalized relative to the mean across observed pairs. Power is the mean rank difference divided by the number of shared mice minus one. Social distance is the vector length from `(1, 0)` to `(affinity, power)`.

**Download results (ZIP)** downloads three Excel matrices and the PNG figures. Manual uploads work without sample files in the repository.

## Example data

To enable **Load example data**, add `ranking.csv` and `pairwise_meetings.csv` next to `app.py` in your GitHub repository. The button analyzes those files directly.
