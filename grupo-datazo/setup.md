# Team project setup

Use Python 3.9 or later.

From this folder, install the runtime dependency with:

    python -m pip install -r requirements.txt

PyYAML is the current runtime dependency. Add a package only when the pipeline needs it.

Run the complete MVP from this folder with:

    python src/mvp.py

Possible duplicate candidates remain separate. Include them in calculations with:

    python src/mvp.py --include-candidates

Exclude them from calculations with:

    python src/mvp.py --exclude-candidates

Without either option, the value in `config/parametros.yaml` applies.

This command refreshes the input-quality reports and prepared layers, then writes one JSON record and one Markdown card for each supplied test property. It also writes `output/validation_report.md`.

The focused commands `python src/data_quality.py` and `python src/geospatial_preparation.py` remain available when only those reports need to be refreshed.
