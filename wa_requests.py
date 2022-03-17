import json
import sys
import requests
from time import sleep

API_BASE_URL = "https://api.torn.com/"
FACTION_BASIC_URL = "faction/?selections=basic&key="
FACTION_NEWS_URL = "faction/?selections=mainnews&key="
# Ranked War Report URL needs the War ID inserted between the pair
RANKED_WAR_REPORT_URL = ["torn/", "?selections=rankedwarreport&key="]
FACTION_ATTACKS_URL = ["faction/?selections=attacks&from=", "&to=", "&key="]
# CHAIN_REPORT_URL = ["torn/", "?selections=chainreport&key="]
FACTION_REVIVES_URL = ["faction/?selections=revives&from=", "&to=", "&key="]


def requestData(api_key, mode, war_id=0, chain_id=0, war_time_info=None):
    """Performs requests to the Torn API. Requires an api_key and mode. Returns python object containing JSON data.

    modes:
    0 -- Basic Faction Info
    1 -- Faction Main News
    2 -- Ranked War Report(uses the war_id argument)
    3 -- Faction Attacks(uses war_time_info argument)
    4 --  DO NOT USE -- Chain Report(uses chain_id argument)
    5 -- Faction Revives(uses war_time_info argument)
    """

    data = None

    if mode == 0:
        print("Requesting Faction Information..")
        response = requests.get(API_BASE_URL + FACTION_BASIC_URL + api_key)

    elif mode == 1:
        print("Requesting Main News to find recent Ranked Wars..")
        response = requests.get(API_BASE_URL + FACTION_NEWS_URL + api_key)

    elif mode == 2:
        print("Requesting info for Ranked War ID " + str(war_id) + "..")
        response = requests.get(
            API_BASE_URL
            + RANKED_WAR_REPORT_URL[0]
            + str(war_id)
            + RANKED_WAR_REPORT_URL[1]
            + api_key
        )

    elif mode == 3:
        print("Requesting Faction Attacks Log from war period..")
        print("This may take some time, due to API limitations.")
        data = request_multipage_data(api_key, war_time_info, 0)
        return data

    elif mode == 4:
        pass
        # print("Requesting Faction Chain ID " + str(chain_id))
        # response = requests.get(
        #     API_BASE_URL
        #     + CHAIN_REPORT_URL[0]
        #     + str(chain_id)
        #     + CHAIN_REPORT_URL[1]
        #     + api_key
        # )
    elif mode == 5:
        print("Requesting Faction Revives Log from war period..")
        print("This may take some time, due to API limitations.")
        data = request_multipage_data(api_key, war_time_info, 1)
        return data

    data = json.loads(response.content)

    if "error" in data.keys():
        print("Error:")
        print(data)
        sys.exit()
    else:
        return data


def request_multipage_data(api_key, war_time_info, mode):
    """Torn's API limits the number of rows in the response.
    Performs multiple requests, looping the timestamp, then returns a single object.
    Requires api_key, war_time_info, mode arguments.

    Modes:
    0 -- attacks
    1 -- revives
    """

    multipage_data = dict()
    first_run = True
    time_marker = war_time_info["start"]
    download_counter = 0
    mode_url = []
    mode_descriptor = None
    timestamp_mode = None
    if mode == 0:
        mode_url.append(FACTION_ATTACKS_URL[0])
        mode_url.append(FACTION_ATTACKS_URL[1])
        mode_url.append(FACTION_ATTACKS_URL[2])
        mode_descriptor = "attacks"
        timestamp_mode = "timestamp_started"
    if mode == 1:
        mode_url.append(FACTION_REVIVES_URL[0])
        mode_url.append(FACTION_REVIVES_URL[1])
        mode_url.append(FACTION_REVIVES_URL[2])
        mode_descriptor = "revives"
        timestamp_mode = "timestamp"

    print(
        "Downloaded " + str(download_counter) + " " + mode_descriptor + "..", end="\r"
    )
    while time_marker < war_time_info["end"]:
        response = requests.get(
            API_BASE_URL
            + mode_url[0]
            + str(time_marker)
            + mode_url[1]
            + str(war_time_info["end"])
            + mode_url[2]
            + api_key
        ) # Make request to the API
        # print(response.url)
        data = json.loads(response.content)
        event_counter = 0
        if len(data[mode_descriptor]) > 0: # Check that the API returned attacks
            if first_run: # First run downloads all rows without extra checks
                multipage_data = data
                event_counter = len(multipage_data[mode_descriptor]) - 1
                first_run = False
            else:
                for key in iter(data[mode_descriptor]): # Iterate through attack keys and check our data for them to prevent duplicates
                    if key not in multipage_data[mode_descriptor]:
                        multipage_data[mode_descriptor].update({key:data[mode_descriptor][key]})
                        event_counter += 1
            if mode == 0:
                timestamp_split = response.text.split('"' + timestamp_mode + '":') # Get the last row on the page and set the new time marker to the timestamp
                time_marker = int(timestamp_split[len(timestamp_split) - 1].split(",")[0])
            elif mode == 1:
                timestamp_split = response.text.split(":{\"timestamp\":") # Get the last row on the page and set the new time marker to the timestamp
                time_marker = int(timestamp_split[len(timestamp_split) - 1].split(",")[0])

        else:
            time_marker = 4070912400
        if event_counter == 0 and (abs(time_marker - war_time_info["end"]) <= 300): # If no updates are made, check if last timestamp is within 5 minutes of the end of war
            time_marker = 4070912400
            break
        download_counter += event_counter
        print(
            "Downloaded " + str(download_counter) + " " + mode_descriptor + "..",
            end="\r",
        )
        sleep(30)  # Sleep to prevent API from sending the same result back
    print("Finished. Downloaded " + str(download_counter + 1) + " " + mode_descriptor + "!")
    
    # with open(
    #     "war-preprocessed-" + mode_descriptor + "-" + str(war_time_info["start"]) + ".json", "w"
    # ) as save_file:
    #     save_file.write(json.dumps(multipage_data))
    return multipage_data
