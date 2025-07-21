# Set up postgresql database
sudo docker compose up

# Build 
`poetry install`
or
`pip install -e .` `pip install -r requirements.txt`
# Collect data from external API and store it in the database
`python3 src/services/data_synchronizer.py`
# Analyze data
`python3 src/data_analyzer/data_analyzer.py`