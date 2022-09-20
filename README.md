# sonarr-episode-trimmer
 
Updated fork of [https://gitlab.com/spoatacus/sonarr-episode-trimmer](https://gitlab.com/spoatacus/sonarr-episode-trimmer/-/tree/master)

# Changes

- Docker Support
- Migrate to the new /episode/monitor endpoint

# Running with Docker

- Rename *settings.config.example* to *settings.config* and update necessary details
- From the same folder as your config, build the Docker image: `docker build -t jonfairbanks/sonarr-episode-trimmer .`
- Run the image to complete the clean-up task: `docker run --rm --name=sonarr-trimmer jonfairbanks/sonarr-episode-trimmer`

To automate this clean-up, create a similar entry in cron with `crontab -e`:
```
0 * * * * docker run --rm --name sonarr-trimmer jonfairbanks/sonarr-episode-trimmer
```