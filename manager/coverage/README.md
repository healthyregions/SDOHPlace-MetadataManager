## SDOH & Place Dataset Coverage Checker Notebook
An interactive IPython notebook for running the SDOH&Place Dataset Coverage Checker

## Accessing the Notebook
We offer two ways to access a copy of this notebook

### Online: Google Colab
This notebook is intended for use online with Google Colab

Visit https://colab.research.google.com and open this notebook using our GitHub repository URL:
`https://github.com/healthyregions/SDOHPlace-MetadataManager`

1. Navigate to https://colab.research.google.com/
    * You should see the "Open Notebook" dialog appears in the center of the screen
2. Choose GitHub on the left side and enter this repository & branch name
    * `repository` = `https://github.com/healthyregions/SDOHPlace-MetadataManager`
    * `branch` = `main`
    * You should see the `SDOHCoverage.ipynb` notebook is found and listed below
3. Choose the `manager/coverage/SDOHCoverage.ipynb` notebook below to import it into Google Colab
    * You should see the notebook is loaded and is now interactive

### Offline: JupyterLab
Alternatively, you can run Jupyter locally to execute this notebook

Run a Jupyter notebook server using Python:
```bash
% pip install jupyter
% python -m notebook
```

Or run a local copy of JupyterLab in Docker:
1. Change to the new `coverage` directory: `cd manager/coverage/`
2. Run the JupyterLab container: `docker compose up -d`
3. Navigate to http://localhost:8888
    * Login with token = `sdoh`
  
#### Shutdown
When you are finished using the notebook, you can shutdown the JupyterLab container:
```bash
docker compose down
```

## Using the Notebook
1. Run one of the two setup methods above (or for funsies, try out both!)
2. Execute the first and second cells (Shift + Enter)
3. Upload your CSV data into the Notebook's workspace
    * For example: you can use [SVI_2010_US.csv](https://uofi.app.box.com/s/fqtslnfkpmgi32pb1cah1eyvmimvp740/file/1765513583484)
4. Enter 3 user inputs into the widgets from the second cell's output
    * `input_file` = `path/to/SVI_2010_US.csv`
    * `geography` = `tract`
    * `id_field` = `HEROPID`
5. Execute the third cell to run the coverage checker on the inputs above
    * You should see that the highlight IDs are reported at the end - these are the IDs that are missing from the dataset, so we generate a string that will exclude them from the map

