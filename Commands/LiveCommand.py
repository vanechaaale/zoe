import discord

from utilities import check_for_special_name_match, find_pro_play_matchup, pro_all, get_embed_for_player, \
    get_fuzzy_match


async def live(channel, *champion_name):
    if not isinstance(channel, discord.User) and channel is not None:
        channel = channel.channel
    original_message = ' '.join(champion_name)
    if not champion_name:
        await channel.send(
            "use **'~live <champion>'** to search for a champion in a live pro play!")
        return
    elif original_message.lower() == "all":
        await pro_all(channel)
        return
    champion_name = get_fuzzy_match(check_for_special_name_match(original_message))
    if champion_name == '':
        await channel.send(f"No champion with name '{original_message}' was found.")
        return
    matches_found = find_pro_play_matchup(champion_name)
    # Sometimes there are repeat copies of the same match
    seen = []
    if matches_found:
        for game_info in matches_found:
            if game_info not in seen:
                seen.append(game_info)
                await channel.send(embed=get_embed_for_player(game_info))
    else:
        await channel.send(f"{champion_name} isn't on Summoner's Rift right now :(")
