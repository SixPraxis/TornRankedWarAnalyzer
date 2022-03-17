import wa_io as io
import wa_requests as req
import wa_processing as proc
import wa_data_handler as dh

def main():
    io.intro()
    api_key = io.api_key_input()
    #api_key = ""  # DEBUG

    faction_data = req.requestData(api_key, 0)
    basic_faction_info = proc.extract_faction_info(faction_data)
    news_data = req.requestData(api_key, 1)

    war_list = proc.extract_wars(news_data)
    war_list_formatted = proc.format_war_list(war_list, basic_faction_info)
    war_id = io.war_selection_table(basic_faction_info, war_list_formatted)
    # war_id =   # DEBUG
    war_data = req.requestData(api_key, 2, war_id)["rankedwarreport"]
    war_time_info = war_data["war"]

    attack_df = None
    revive_df = None
    source = io.download_or_import_prompt()
    # source = 1  # DEBUG
    display_mode = io.display_mode_prompt()
    # display_mode = 0  # DEBUG
    if source == 0:
        attack_data = req.requestData(api_key, 3, war_time_info=war_time_info)
        attack_df = dh.load_dict_flatten_into_df(attack_data, "attacks")
        attack_df = dh.prepare_attack_dataframe(attack_df, war_data)
        io.export_df_to_csv(attack_df, war_id, "attacks")

        revive_data = req.requestData(api_key, 5, war_time_info=war_time_info)
        revive_df = dh.load_dict_flatten_into_df(revive_data, "revives")
        revive_df = dh.prepare_revive_dataframe(revive_df)
        io.export_df_to_csv(revive_df, war_id, "revives")
    elif source == 1:
        attack_df = io.import_csv_to_df("war-" + str(war_id) + "-attacks.csv")
        revive_df = io.import_csv_to_df("war-" + str(war_id) + "-revives.csv")

    fig0 = dh.create_war_attacks_graph(attack_df, war_data)
    fig1 = dh.create_assists_graph(attack_df, war_data)
    fig2 = dh.create_net_score_graph(attack_df, basic_faction_info)
    fig3 = dh.attacks_and_losses_player_graph(attack_df, basic_faction_info)
    fig4 = dh.create_faction_revives_graph(revive_df, basic_faction_info)
    fig5 = dh.create_player_revives_over_time_graph(revive_df, basic_faction_info)
    fig6 = dh.create_player_revives_graph(revive_df, basic_faction_info)
    fig7 = dh.create_respect_gainloss_graph(attack_df, war_data)
    figs = [fig7, fig0, fig1, fig2, fig3, fig4, fig5, fig6]
    summary_table = dh.create_faction_summary_table(
        attack_df, revive_df, war_data, basic_faction_info
    )
    io.display_figs(figs, display_mode, war_data, war_id, summary_table)


if __name__ == "__main__":
    main()
