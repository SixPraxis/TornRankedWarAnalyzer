from time import strftime, localtime

def extract_faction_info(data):
    """Get ID, name, tag, rank_name, rank_division of faction, returns dictionary"""
    basic_faction_info = {
        "ID": str(data["ID"]),
        "name": data["name"],
        "tag": data["tag"],
        "rank_name": data["rank"]["name"],
        "rank_division": str(data["rank"]["division"]),
    }

    return basic_faction_info

def extract_wars(data):
    """Search the main news results for wars, returns list"""
    wars = []
    for article in data["mainnews"]:
        if "in a ranked war" in (article_news := data["mainnews"][article]["news"]):
            timestamp = strftime(
                "%Y-%b-%d", localtime(data["mainnews"][article]["timestamp"])
            )
            warID = article_news.split("rankID=")[1].split(">")[0]
            faction1 = article_news.split(">")[1].split("</")[0]
            faction1ID = article_news.split("ID=")[1].split(">")[0]
            faction2 = article_news.split(">")[3].split("</")[0]
            faction2ID = article_news.split("ID=")[2].split(">")[0]

            war = {}
            war["warID"] = warID
            war["faction1"] = faction1
            war["faction1ID"] = faction1ID
            war["faction2"] = faction2
            war["faction2ID"] = faction2ID
            war["timestamp"] = timestamp
            wars.append(war)

    return wars

# def extract_war_chains(news_data, war_time_info):
#     """Searches main new for chains that occured during the war time frame, returns list of chain IDs"""
#     war_start_time = int(war_time_info["start"])
#     war_end_time = int(war_time_info["end"])
#     chain_id = None  # SEARCH NEWS DATA AND GET CHAIN ID
#     return chain_id

def format_war_list(war_list, basic_faction_info):
    """Prepares the war list for display as a table"""
    war_list_formatted = []
    war_index = 0
    for war in war_list:
        enemy_faction = "faction2"
        outcome = "Win"
        if war["faction2ID"] == basic_faction_info["ID"]:
            enemy_faction = "faction1"
            outcome = "Loss"

        war_formatted = [
            str(war_index),
            war["warID"],
            war[enemy_faction],
            war["timestamp"],
            outcome,
        ]
        war_list_formatted.append(war_formatted)
        war_index += 1

    return war_list_formatted