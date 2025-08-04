# Week-14-Game-Tracker-Project

## Project introduction
A data pipeline that tracks new releases on major PC platforms, helping game discovery and building an understanding of what is currently being released.
Scraped new releases from Steam, Epic and GOG before adding supplementary data from their respective backend APIs.
Data included the URL, title and release date, along with price, genres, developers and publishers etc.
We planned and implemented an ELT pipeline to store clean data on new releases:
- Website/API to S3 - scrape new releases & add data from the API before storing this raw data in an S3 buckets
- S3 to RDS - transform raw data and upload to the RDS which supplies the dashboard with its data
We developed a dashboard to showcase insights about recent releases - this is currently hosted at (here)[http://35.179.94.130:8501/].

We also created a subscriber system that involves a form - users can input their email and opt in to receive weekly reports and/or notifications - this is currently hosted (here)[http://18.168.201.236:8000/].
on their favourite genres.

## Technologies used
1. ECR - Docker images
2. EventBridge Scheduler and Lambda to run pipelines
3. ECS/Fargate to host the dashboard and subscriber form
4. S3 for raw data storage - time-partitioned
5. RDS for storage of latest clean data
6. Streamlit dashboard for visualisations
7. EventBridge Step Functions and SES to send reports and notifications 

## File structures
- .github
    - Utility folder used for github configs
- assets
    - Folder containing project-related diagrams, including the ERD and architecture
- src
    - dashboard
        - Folder to store scripts used in the dashboard, and one test file
    - elt_pipeline
        - Folder to store scripts used in each pipeline
    - schema
        - Folder containing the schema script for the database, and a python script to run said schema
    - summary_report
        - Folder to store scripts used to generate weekly reports
    - terraform
        - persistent
            - Contains terraform scripts for one-time setups e.g. databases and container repos
        - repeated
            - Contains terraform scripts for repeated setups (when debugging is required) e.g. lambda functions
- tests
    - Contains testing scripts for each module

## How to run
1. Install Python 3 on your system
2. Run `python3 -m venv .venv` to make a new virtual environment
3. Run `activate .venv/bin/activate` to enter the venv
4. Run `pip install -r requirements.txt` at the top level of the project
5. To test: `python3 -m pytest test/*.py`
6. To run the dashboard (localhost): `streamlit run src/dashboard/dashboard.py`

The pipelines initially can't run locally as they have been modified to only run within a lambda function.
However each module also has a `deploy.sh` script and a dockerfile to ease deployment of new versions to the cloud repository.
Commands within the bash scripts need to be updated to match the reader's AWS user credentials, and they then need to be run from the root of the repo.
S3 and RDS-related code also rely on secrets stored on the local machine - access key pair and RDS credentials are required.
These should be stored in a .env in the same folder as the scripts for running locally.
Or the RDS creds should be stored in a `terraform.tfvars` file in `src/terraform/repeated` for deployment.

## Future improvements
- 

## Extra resources
(Steam latest releases for scraping)[https://store.steampowered.com/search/?sort_by=Released_DESC&supportedlang=english]
(Unofficial docs for requesting more data for a given store page App ID)[https://github.com/Revadike/InternalSteamWebAPI/wiki/Get-App-Details]
(Epic API)[https://dev.epicgames.com/docs/api-ref]
(GOG API)[https://gogapidocs.readthedocs.io/en/latest/]
