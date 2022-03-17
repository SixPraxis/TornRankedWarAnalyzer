from string import punctuation
import sys
from tabulate import tabulate
from time import time
import datetime
from pandas import read_csv


def intro():
    print("Ranked War Analyzer by HotSoup[860380]")
    print("--------------------------------------")


def api_key_input():
    """Request API Key from user using input. Performs basic checks to validate key.
    Returns a string containing the API key."""

    print("An API key with faction API access is required.")
    key_input = input("Enter Key: ")
    key_input.strip()
    print("API Key: " + key_input)

    if len(key_input) == 16:
        for char in punctuation:
            if char in key_input:
                print("Invalid Key. Exiting..")
                sys.exit()
        return key_input
    else:
        print("Invalid Key. Exiting..")
        sys.exit()


def war_selection_table(basic_faction_info, war_list_formatted):
    """Displays faction info and a table containing recent wars.
    Prompts for a war selection. Returns ID of selected war."""

    print("\nFaction Info:")
    print(
        basic_faction_info["ID"]
        + " - "
        + basic_faction_info["tag"]
        + " - "
        + basic_faction_info["name"]
    )
    print(basic_faction_info["rank_name"] + " " + basic_faction_info["rank_division"])

    print("\nRecent Ranked Wars:")
    print(
        tabulate(
            war_list_formatted,
            headers=["#", "WarID", "Enemy", "Date", "Outcome"],
            tablefmt="github",
        )
    )

    print("Enter a war to analyze, # or WarID.")
    selected_war = int(input("> "))
    if selected_war >= 0 and selected_war < len(war_list_formatted):
        war_id = war_list_formatted[selected_war][1]
        return war_id
    else:
        for war in war_list_formatted:
            if selected_war == int(war[1]):
                war_id = selected_war
                return war_id

    print("Invalid selection.")
    sys.exit()


def download_or_import_prompt():
    source = None
    print(
        "\nChoose a data source:\n0: Download from Torn API (also creates csv files)\n1: Import war csv files (must be in same folder as program)"
    )
    source = input("> ")
    try:
        source = int(source)
    except:
        print("Must be 0 or 1, no extra characters, exiting..")
        sys.exit()
    if source == 0 or source == 1:
        return source
    else:
        print("Must be 0 or 1, exiting..")
        sys.exit()


def export_df_to_csv(df, war_id, type_str):
    df.to_csv("war-" + str(war_id) + "-" + type_str + ".csv")
    print("Saved " + "war-" + str(war_id) + "-" + type_str + ".csv for future use..")


def import_csv_to_df(filepath):
    df = None
    try:
        df = read_csv(filepath, index_col=0)
    except (FileNotFoundError):
        print(
            "Files not found, please make sure both wardata csv files are in the same folder as the program.\nIf you do not have the files, run the program in download mode to create them."
        )
        sys.exit()
    print("Imported " + filepath + " ..")
    return df


def display_mode_prompt():
    display_mode = None
    print(
        "\nChoose a graph display mode:\n0: Save graphs to single html file\n1: Save graphs to .png files\n2: Save to image files and html file\n3: Display in browser(buggy, not recommended)"
    )
    display_mode = input("> ")
    try:
        display_mode = int(display_mode)
    except:
        print("Must be 0, 1, 2, or 3, no extra characters, exiting..")
        sys.exit()
    if display_mode == 0 or display_mode == 1 or display_mode == 2 or display_mode == 3:
        return display_mode
    else:
        print("Must be 0, 1, 2, or 3, exiting..")
        sys.exit()


def display_figs(figs, display_mode, war_data, war_id, summary_table):
    """Determine how to display a graph figure
    Modes:
    0 -- Save to single html file
    1 -- Save to images(png)
    2 -- Save to images and html file
    3 -- Display in browser(buggy, not recommended)
    """
    div_list = []
    for fig in figs:
        fig_title = fig.layout.title.text.replace(" ", "_")
        if display_mode == 0:
            div_list.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))
            print("Added " + fig_title + " chart to the html file.")
        elif display_mode == 1:
            fig.write_image("war-" + str(war_id) + "-" + fig_title + ".png")
            print("Saved " + "war-" + str(war_id) + "-" + fig_title + ".png")
        elif display_mode == 2:
            div_list.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))
            print("Added " + fig_title + " chart to the html file.")
            fig.write_image("war-" + str(war_id) + "-" + fig_title + ".png")
            print("Saved " + "war-" + str(war_id) + "-" + fig_title + ".png")
        elif display_mode == 3:
            fig.show()
            print("Displayed " + fig_title + " chart in browser.")

    if display_mode == 0 or display_mode == 2:
        save_to_single_html_file(div_list, war_data, war_id, summary_table)


def save_to_single_html_file(div_list, war_data, war_id, summary_table):
    """Adds information headers and saves all created charts to one html file"""
    factions = list(war_data["factions"].keys())
    html_string = (
        "<html><head><h1>"
        + war_data["factions"][factions[0]]["name"]
        + " vs "
        + war_data["factions"][factions[1]]["name"]
        + "</h1>"
        + "<h2>"
        + str(datetime.datetime.fromtimestamp(war_data["war"]["start"]))
        + "</h2>"
        + summary_table
        + "</head>"
    )
    for div in div_list:
        html_string += div
        html_string += "<hr>"

    html_string += "</html>"
    t = int(time())
    with open("war-" + str(war_id) + "-" + "charts-" + str(t) + ".html", "w") as file:
        file.write(html_string)

    print("Saved " + "war-" + str(war_id) + "-" + "charts-" + str(t) + ".html file.")
