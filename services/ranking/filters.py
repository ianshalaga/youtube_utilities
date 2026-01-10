"""
Filtros semánticos para ranking.
"""


def filter_by_country(duels, country_map, country):
    for duel in duels:
        if country_map.get(duel.player_a) == country:
            yield duel
