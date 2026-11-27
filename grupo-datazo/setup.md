# Team project setup

Use Python 3.9 or later.

From this folder, install the runtime dependency with:

    python -m pip install -r requirements.txt

PyYAML is the current runtime dependency. Add a package only when the pipeline needs it.

Run the listing and test-property quality report from this folder with:

    python src/data_quality.py

Prepare and report the geographic layers with:

    python src/geospatial_preparation.py

The planned run command is python src/mvp.py. It will work when checklist item 3.1.2 is complete.
