#!/usr/bin/env python3

import argparse
import configparser
import json
import logging
import logging.handlers
import os
import requests
import sys

from flask import Flask, request, jsonify
from operator import itemgetter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    stream=sys.stdout,
)

# setup weekly log file
log_path = os.path.join(os.path.dirname(__file__), "logs")
log_file = os.path.join(log_path, "debug.log")
if not os.path.exists(log_path):
    os.mkdir(os.path.dirname(log_file))
file_handler = logging.handlers.TimedRotatingFileHandler(
    log_file, when="D", interval=7, backupCount=4
)
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))
logging.getLogger().addHandler(file_handler)

app = Flask("Sonarr-Episode-Trimmer")

# make a request to the sonarr api
def api_request(action, params=None, method="GET", body=None):
    if params is None:
        params = {}
    if CONFIG.has_option("API", "key"):
        params["apikey"] = CONFIG.get("API", "key")
    else:
        params["apikey"] = os.getenv("API_KEY")

    if CONFIG.has_option("API", "url_base"):
        url_base = CONFIG.get("API", "url_base")
    elif os.getenv("URL_BASE") is not None:
        url_base = os.getenv("URL_BASE")
    else:
        url_base = ""

    if CONFIG.has_option("API", "api_version"):
        api_version = CONFIG.get("API", "api_version")
    elif os.getenv("API_VERSION") is not None:
        api_version = os.getenv("API_VERSION")
    else:
        api_version = "v3"

    if CONFIG.has_option("API", "url"):
        url = "%s%s/api/%s/%s" % (CONFIG.get("API", "url"), url_base, api_version, action)
    else:
        url = "%s%s/api/%s/%s" % (os.getenv("URL"), url_base, api_version, action)

    headers = { 'Content-Type': 'application/json' }

    print(url)

    if body is None:
        r = requests.request(method, url, params=params)
    else:
        r = requests.request(method, url, params=params, headers=headers, data=body)

    if r.status_code < 200 or r.status_code > 299:
        logging.error("%s %s", r.status_code, r.reason)
        logging.error(r.text)

    if not r.content:
        return {}

    return r.json()


def unmonitor_episode(episode):
    air_date = episode["airDate"] if "airDate" in episode else ""
    episode_id = int(episode["id"])
    logging.info(
        "Unmonitoring episode: season=%s, episode=%s, airdate=%s, id=%s",
        episode["seasonNumber"],
        episode["episodeNumber"],
        air_date,
        episode_id,
    )

    if not DEBUG:
        body = {"episodeIds": [episode_id], "monitored": False}
        api_request("episode/monitor", method="PUT", body=json.dumps(body))


# remove old episodes from a series
def clean_series(series_id, keep_episodes):
    # get the episodes for the series
    all_episodes = api_request("episode", {"seriesId": series_id})

    # filter only downloaded episodes
    episodes = [episode for episode in all_episodes if episode["hasFile"]]

    # sort episodes
    episodes = sorted(episodes, key=itemgetter("seasonNumber", "episodeNumber"))

    logging.debug("# of episodes downloaded: %s", len(episodes))
    logging.debug("# of episodes to delete: %s", len(episodes[:-keep_episodes]))

    # filter monitored episodes
    monitored_episodes = [episode for episode in all_episodes if episode["monitored"]]
    logging.debug("# of episodes monitored: %s", len(monitored_episodes))
    monitored_episodes = sorted(
        monitored_episodes, key=itemgetter("seasonNumber", "episodeNumber")
    )

    # unmonitor episodes older than the last one downloaded
    # do this to keep older episodes that failed to download, from being searched for
    logging.info("Unmonitoring old episodes:")
    if len(episodes) > 0 and len(monitored_episodes) > 0:
        try:
            for episode in monitored_episodes[: monitored_episodes.index(episodes[0])]:
                unmonitor_episode(episode)
        except ValueError:
            logging.warn("There is an episode with a file that is unmonitored")

    # process episodes
    for episode in episodes[:-keep_episodes]:
        logging.info("Processing episode: %s", episode["title"])

        # get information about the episode's file
        episode_file = api_request("episodefile/%s" % episode["episodeFileId"])

        # delete episode
        logging.info("Deleting file: %s", episode_file["path"])
        if not DEBUG:
            api_request("episodefile/%s" % episode_file["id"], method="DELETE")

        # mark the episode as unmonitored
        unmonitor_episode(episode)


@app.route("/webhook", methods=["POST"])
def webhook():
    content = request.json
    if content["eventType"] != "Test" and content["eventType"] != "EpisodeFileDelete":
        series = api_request("series")
        cleanup_series = []
        # build mapping of titles to series
        series = {x["cleanTitle"]: x for x in series}
        for s in CONFIG.items("Series"):
            if s[0] in series:
                cleanup_series.append(
                    (series[s[0]]["id"], int(s[1]), series[s[0]]["title"])
                )
            else:
                logging.warning("series '%s' from config not found in sonarr", s[0])
        for s in cleanup_series:
            logging.info("Processing: %s", s[2])
            logging.debug("%s: %s", s[0], s[1])
            clean_series(s[0], s[1])
    return jsonify(success=True)


@app.route("/webhook/<int:episodes>", methods=["POST"])
def webhook_episode(episodes):
    content = request.json
    if content["eventType"] != "Test" and content["eventType"] != "EpisodeFileDelete":
        clean_series(content["series"]["id"], episodes)
    return jsonify(success=True)


if __name__ == "__main__":
    global CONFIG
    global DEBUG

    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run the script in debug mode. No modifications to "
        "the sonarr library or filesystem will be made.",
    )
    parser.add_argument(
        "--config", type=str, required=False, help="Path to the configuration file."
    )
    parser.add_argument(
        "--list-series",
        action="store_true",
        help="Get a list of shows with their 'cleanTitle' for use"
        " in the configuration file",
    )
    parser.add_argument(
        "--custom-script",
        action="store_true",
        help="Run in 'Custom Script' mode. This mode is meant "
        "for adding the script to sonarr as a 'Custom "
        "Script'. It will run anytime a new episode is "
        "downloaded, but will only cleanup the series of "
        "the downloaded episode.",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Starts in webmode, where you can set it up as a webhook connector"
        "in Sonnar and get it invoked from its trigger operations",
    )
    args = parser.parse_args()

    DEBUG = args.debug
    if DEBUG:
        logging.getLogger().setLevel(logging.DEBUG)

    # load config file
    CONFIG = configparser.ConfigParser()
    if args.config is not None:
        CONFIG.read(args.config)

    if args.web:
        app.run(host="0.0.0.0", threaded=True, port=5000)

    # get all the series in the library
    series = api_request("series")

    # print out a list of series
    if args.list_series:
        series = sorted(series, key=itemgetter("title"))
        for s in series:
            print(f"{s['title']}: {s['cleanTitle']}")
    # cleanup series
    else:
        cleanup_series = []

        # custom script mode
        if args.custom_script:
            # verify it was a download event
            if os.environ["sonarr_eventtype"] == "Download":
                series = {x["id"]: x for x in series}
                config_series = {x[0]: x[1] for x in CONFIG.items("Series")}
                series_id = int(os.environ["sonarr_series_id"])
                # check if this episode is in a series in our config
                if series[series_id]["cleanTitle"] in config_series:
                    num_episodes = int(config_series[series[series_id]["cleanTitle"]])
                    title = series[series_id]["title"]

                    cleanup_series.append((series_id, num_episodes, title))
        # cronjob mode
        else:
            # build mapping of titles to series
            series = {x["cleanTitle"]: x for x in series}

            for s in CONFIG.items("Series"):
                if s[0] in series:
                    cleanup_series.append(
                        (series[s[0]]["id"], int(s[1]), series[s[0]]["title"])
                    )
                else:
                    logging.warning("series '%s' from config not found in sonarr", s[0])

        for s in cleanup_series:
            logging.info("Processing: %s", s[2])
            logging.debug("%s: %s", s[0], s[1])
            clean_series(s[0], s[1])
