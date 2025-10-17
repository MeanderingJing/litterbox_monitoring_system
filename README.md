# Overview of the Litterbox Monitoring System (LitterLog)
The litterbox monitoring system aims to address the challenge of tracking feline health and behavior patterns that are often invisible to pet owners. It targets health-conscious cat owners who need reliable, continuous monitoring to detect early signs of urinary tract infections (UTI) that first manifest through changes in litterbox usage patterns, as well as to track treatment progress and recovery by monitoring improvements in litterbox behavior during active UTI treatment.

The end-to-end solution combines edge computing (implemented as a litterbox simulator here), ETL processing, data analysis, and user-friendly web interface, delivering predictive health insights that can detect subtle deviations before they become apparent to cat owners.

This is an on-going project that is constantly being improved.

# System Diagram
![System Diagram](https://github.com/MeanderingJing/litterbox_monitoring_system/blob/main/LitterLog-high-level-diagram.png)

# Spin up the backend using Docker compose
`sudo docker compose up`
## What does the docker compose command do?
- Spin up the PostgreSQL database
- Spin up the RabbitMQ service
- Run the litterbox simulator in docker container, which produces litterbox usage data to RabbitMQ
- Run the data persister in docker container, which consumes messages from RabbitMQ and send it to the database

# Run backend flask app locally for development
`flask run`

Using `flask run` locally instead of Docker for this allows fast iteration, as I don't need to rebuild the container every time when there're code changes.

For production, use gunicorn and nginx (my own production server), a third-party platform-as-a-service (Heroku, Fly.io, etc), or a cloud provider.

# Run frontend locally for development
`npm run dev`

For production, deploy to Vercel or a cloud provider.
## Litterlog Sign in Page
![Sign in Page](https://github.com/MeanderingJing/litterbox_monitoring_system/blob/docker/add-dockerfiles-compose/Litterlog_sign_in.png)
## Litter Box Usage Visualization
![Litter Box Usage Visualization](https://github.com/MeanderingJing/litterbox_monitoring_system/blob/docker/add-dockerfiles-compose/litterbox_usage_data_visualization.png)



