# sonarr-episode-trimmer
 
Updated fork of [https://gitlab.com/spoatacus/sonarr-episode-trimmer](https://gitlab.com/spoatacus/sonarr-episode-trimmer/-/tree/master)

## Changes

- Docker Support
- Migrate to the new /episode/monitor endpoint
- Added webhook mode

## Running with Docker

### Build
- Rename *settings.config.example* to *settings.config* and update necessary details
- From the same folder as your config, build the Docker image: `docker build -t jonfairbanks/sonarr-episode-trimmer .`

### Execute 
Run the image to complete the clean-up task: 
    `docker run --rm --name=sonarr-trimmer jonfairbanks/sonarr-episode-trimmer`
The configuration file can be on the host machine: 
    `docker run --rm -v host_dir:/config --name=sonarr-trimmer jonfairbanks/sonarr-episode-trimmer --config /config/myconfig`
Run the image to list the series: 
    `docker run --rm --name=sonarr-trimmer jonfairbanks/sonarr-episode-trimmer --list-series`
API configuration can be passed through environment variables: 
    `docker run --rm --name=sonarr-trimmer -e URL=http://myurl -e API_KEY=1234 jonfairbanks/sonarr-episode-trimmer --list-series`

### Automate
To automate this clean-up, create a similar entry in cron with `crontab -e`:
```
0 * * * * docker run --rm --name sonarr-trimmer jonfairbanks/sonarr-episode-trimmer
```
### Webhook mode
Run the image in webhook mode: 
    `docker run -d --name=sonarr-trimmer -p 5000:5000 jonfairbanks/sonarr-episode-trimmer --web`
In this mode a web endpoint at `http://localhost:5000/webhoook` (please use the appropriate urls with the ip/dns as they may apply in your case) that will launch clean-up. This is useful for configuring a sonnar connect webhook, give it a name like `clean up`, select only `On Import`(this is when a file is downloaded), select tag for clean-up series (if any) and put the URL of the end point. The endpoint will not perform cleanup when testing, so feel free to test the connection.

Another way to configure the webhook is to use Sonarr tags. Give any series for which the number of kept episodes is the same the same tag in Sonarr, e.g. `keep-last`, select it for your Sonnar webhook connection, for the url of the webhook you can select the number of episodes by adding it to the path, e.g. `http://localhost:5000/webhoook/1` will keep only 1 episode i.e. the last one. This webhook option will execute cleanup for the triggering series with the given number, so don't use it without tags, unless you want ALL of your series cleaned. When using this option it is recommended to pass the API configuration as environment variables, this way you don't need to edit any configuration file nor rebuild the image. 
