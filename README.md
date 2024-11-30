# sonarr-episode-trimmer 

This is an updated fork of [https://gitlab.com/spoatacus/sonarr-episode-trimmer](https://gitlab.com/spoatacus/sonarr-episode-trimmer/-/tree/master) with added Docker support, the new `/episode/monitor` endpoint, and webhook mode.

## Usage with Docker

### Building the image
1. Rename `settings.config.example` to `settings.config` and update the necessary details.
2. From the same folder as your config, build the Docker image: 
```
docker build -t jonfairbanks/sonarr-episode-trimmer .
```

### Running the image
Use the following commands to run the Docker image:
- To complete the clean-up task: 
```
docker run --rm --name=sonarr-trimmer jonfairbanks/sonarr-episode-trimmer
```
- To use a configuration file on the host machine: 
```
docker run --rm -v host_dir:/config --name=sonarr-trimmer jonfairbanks/sonarr-episode-trimmer --config /config/myconfig
```
- To list the series: 
```
docker run --rm --name=sonarr-trimmer jonfairbanks/sonarr-episode-trimmer --list-series
```
- To pass API configuration through environment variables: 
```
docker run --rm --name=sonarr-trimmer -e URL=http://myurl -e API_KEY=1234 jonfairbanks/sonarr-episode-trimmer --list-series
```

### Automating clean-up tasks
To automate the clean-up task, add a similar entry to your cron with `crontab -e`:
```
0 * * * * docker run --rm --name sonarr-trimmer jonfairbanks/sonarr-episode-trimmer
```

#### Webhook mode

In this mode, the Docker image can be run as a web endpoint, which can be triggered by a Sonarr webhook. This is useful for configuring an automated clean-up process for your Sonarr library.

To run the image in webhook mode:

- Use the following command to start the container with the web endpoint:
  
  ```
  docker run -d --name=sonarr-trimmer -p 5000:5000 jonfairbanks/sonarr-episode-trimmer --web
  ```
  
- The web endpoint will be available at `http://localhost:5000/webhook` (replace "localhost" with your IP or DNS name if needed).
  
- Configure a Sonarr webhook to trigger the clean-up process:
  
  - Give the webhook a name, such as "clean up".
  
  - Select the "On Import" event (this is when a file is downloaded).
  
  - Select a tag for the series that should be cleaned up (if any).
  
  - Enter the URL of the endpoint (`http://<your-ip>:5000/webhook`) in the "URL" field. Note that the endpoint will not perform clean-up when testing, so you can safely test the connection.
  
- Alternatively, you can use Sonarr tags to trigger the clean-up process:
  
  - Give any series for which the number of kept episodes is the same the same tag in Sonarr, e.g. `keep-last`.
  
  - Select this tag for your Sonarr webhook connection.
  
  - To specify the number of episodes to keep, add it to the path of the webhook URL, e.g. `http://<your-ip>:5000/webhook/1` will keep only 1 episode (i.e., the last one).
  
  - Note that this webhook option will execute clean-up for the triggering series with the given number, so don't use it without tags unless you want all of your series cleaned.
  
- It is recommended to pass the API configuration as environment variables when using the webhook mode. This way, you don't need to edit any configuration files or rebuild the image.
