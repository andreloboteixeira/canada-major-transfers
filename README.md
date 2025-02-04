# Canada Major Transfers data analysis

- Scrapping data from https://www.canada.ca/en/department-finance/programs/federal-transfers/major-federal-transfers.html to generate visualizations of the major federal transfers to the provinces and territories.
- experimenting with gpt-o3-mini-high


## How to run the app

Prerequisites:
- conda
- python >=3.12

1. Create the conda environment `canada-major-transfers`
```
make create-conda-env
```
2. Activate the environment
```
conda activate canada-major-transfers
```
4. Install all dependencies with poetry.
```
make install-deps
```
5. Run the application
```
make run
```
6. Open in in your browser
