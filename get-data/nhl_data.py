# nhl_data.py
import requests
import pickle
import progressbar
import time

def get_teams(base_url='https://statsapi.web.nhl.com/api/v1', active=True):
    """
    Queries the NHL API for team information and returns a list of active teams.

    Parameters:
        base_url (str): base url to the nhl api
        active (bool): if True, only return data for active teams

    Returns:
        teams (list(tuples)): list containing (team-name, team-id) pairs
            for all (active) teams
    """
    # request teams data
    all_teams = requests.get(base_url + '/teams').json()['teams']

    # extract team names and ids
    if active:
        teams = [(team['name'], team['id']) for team in all_teams if team['active']]
    else:
        teams = [(team['name'], team['id']) for team in all_teams]

    return teams

def get_team_roster(team_id, base_url='https://statsapi.web.nhl.com/api/v1',
                        season=False, wait=True):
    """
    Queries the NHL API for roster information for a given team

    Parameters:
        team_id (int): nhl api team id number
        base_url (str): base url to the nhl api
        season (str): season to request roster; defaults to using active roster
        wait (bool): specifies if we should pause before requesting the data;
                        should only be False if making a single request or if you
                        are explicitly waiting before repeated calls of this function

    Returns:
        team_roster (list(dicts)): list of dicts; each dictionary contains the
            following information
        {'person': {'id': int,
                    'fullName': str,
                    'link': str
            },
        'jerseyNumber': str,
        'position': {'code': str
                     'name': str
                     'type': str
                     'abbreviation': str
            }
        }
    """
    if wait:
        # wait a moment to request additional data
        time.sleep(0.25)

    # endpoint to request data from
    endpoint_url = '/teams/{}/roster'.format(team_id)

    if  season:
        # if we want data from a specific season
        endpoint_url += '?expand=team.roster&season={}'.format(season)

    # get team roster
    team_roster = requests.get(base_url + endpoint_url).json()

    # extract player information
    return team_roster['roster']

def get_player_stats(player_id, base_url='https://statsapi.web.nhl.com/api/v1',
                        stat_type='statsSingleSeason', season='20192020', wait=True):
    """
    Queries the NHL API for the stats of a player.

    Parameters:
        player_id (int): nhl api player id number
        base_url (str): base url to the nhl api
        stat_type (str): stats type to request
        season (str): season to request stats from
        wait (bool): specifies if we should pause before requesting the data;
                        should only be False if making a single request or if you
                        are explicitly waiting before repeated calls of this function

    Returns:
        player_stats (dict): dictionary of requested stats
    """
    if wait:
        time.sleep(0.25)

    # endpoint to query
    endpoint_url = '/people/{}/stats?stats={}&season={}'.format(player_id, stat_type, season)

    # request player statistics
    player_stats = requests.get(base_url + endpoint_url).json()
    player_stats = player_stats['stats'][0]

    return player_stats

def update_player_list(base_url='https://statsapi.web.nhl.com/api/v1',
                        save_path='data/basic/', active=True):
    """
    Updates the player dictionaries, which associate players/ids with their
        respective teams

    Parameters:
        base_url (str): base url to the nhl api
        save_path (str): relative path to directory where data will be saved
        active (bool): if True, only updates the active players info

    Returns:
        None

        Creates pickle files for the following:
            player_ids:     [player_ids]
            team_ids:       [team_ids]
            name_to_id:     {player_name: player_id}
            id_to_name:     {player_id: player_name}
            team_to_player: {team_id: [player_ids]}
            player_to_team: {player_id: team_id}

    """
    # get list of every team
    all_teams = get_teams(base_url=base_url, active=active)

    # get team rosters -- list of (roster_dict, team_id) pairs
    team_rosters = [(get_team_roster(team[1], wait=True), team[1])
                        for team in all_teams]

    # create list of player dicts -- dict format like in get_team_roster docstring
    players = [player for team in team_rosters for player in team[0]]

    # create {player: id} and {id: player} dictionaries
    name_to_id = {player['person']['fullName']: player['person']['id'] for player in players}
    id_to_name = {id: fullName for fullName, id in name_to_id.items()}

    # create {team_id: player_ids} and {player_id: team_id} dictionaries
    team_to_player = {team[1]: [player['person']['id'] for player in team[0]]
                        for team in team_rosters}
    player_to_team = {player: team for team in team_to_player.keys()
                        for player in team_to_player[team]}

    # create {team_id: team_name} and {team_name: team_id} dictionaries
    team_id_to_name = {team[1]: team[0] for team in all_teams}
    team_name_to_id = {team[0]: team[1] for team in all_teams}

    # pickle mapping dictionaries
    dicts = [name_to_id, id_to_name, team_to_player, player_to_team,
                team_id_to_name, team_name_to_id]
    dict_names = ['player_name_to_id', 'player_id_to_name', 'team_id_to_players',
                    'player_id_to_team', 'team_id_to_name', 'team_name_to_id']

    for d, n in zip(dicts, dict_names):
        with open(save_path + n, 'wb') as f:
            pickle.dump(d, f)

    # create/pickle player_id and team_id lists
    player_ids = list(player_to_team.keys())
    team_ids = list(team_to_player.keys())
    lists = [player_ids, team_ids]
    list_names = ['player_ids', 'team_ids']

    for l, n in zip(lists, list_names):
        with open(save_path + n, 'wb') as f:
            pickle.dump(l, f)

    return

def update_player_stats(base_url='https://statsapi.web.nhl.com/api/v1',
                        save_path='data/stats/', load_path='data/basic/player_ids',
                        **kwargs):
    """
    Updates player stats data.

    Parameters:
        base_url (str): base url to the nhl api
        save_path (str): rel path to dir where data will be saved
        load_path (str): rel path to dir where player_id data will be loaded from
        **kwargs: keyword arguments to pass to get_player_stats
            season (str)
            stat_type (str):
                'statsSingleSeason' (default), 'homeAndAway', 'winLoss', 'byMonth',
                'byDayofWeek', 'vsDivision', 'vsConference', 'vsTeam', 'gameLog'

    Returns:
        None

        Updates the player stats DataFrame object
    """
    # load player ids
    with open(load_path, 'rb') as f:
        player_ids = pickle.load(f)

    # progressbar to track process
    bar = progressbar.progressbar(player_ids)

    # request player stats
    player_stats = dict()
    for p_id in bar:
        player_stats[p_id] = get_player_stats(p_id, **kwargs)
    # player_stats = {p_id: get_player_stats(p_id, **kwargs) for p_id in player_ids}

    # clean player stats so we can put it into a pandas df
    # generate state labels to fill any empty entries
    stat_labels = ['season']
    for p_id in player_ids:
        if len(player_stats[p_id]['splits']) > 0:
            stat_labels += list(player_stats[p_id]['splits'][0]['stat'].keys())
            break
    # default empty dictionary for players with no data
    no_data = {label: None for label in stat_labels}
    # construct new, flattened, dictionary
    p_stats = dict()
    for p_id in player_ids:
        if len(player_stats[p_id]['splits']) == 0:
            p_stats[p_id] = no_data
        else:
            inner_dict = player_stats[p_id]['splits']['stat']
            outer_dict = {'season': player_stats[p_id]['splits']['season']}
            # unpack the two dictionaries into one
            p_stats[p_id] = {**outer_dict, **inner_dict}

    player_stats_df = pd.DataFrame.from_dict(p_stats, orient='index')

    try:
        # check if we are updating a non-default stat file
        if kwargs['stat_type'] != 'statsSingleSeason':
            save_path += 'player_stats' + kwargs['stat_type']
        else:
            save_path += 'player_statsSingleSeason'
    except KeyError:
        # if updating default stat file
        save_path = save_path + 'player_statsSingleSeason'

    # pickle player_stats_df
    with open(save_path, 'wb') as f:
        pickle.dump(player_stats_df, f)

    return
