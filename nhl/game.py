# game.py

from nhl import api
import pandas as pd

class Game:

    def __init__(self, game_id=None, initData=True):
        """
        Class providing a high level object-oriented approach to working with game data.

        Parameters
        ----------
        game_id : str or int (default : None)
            Integer or string of the unique game id (gamePk) for the desired game.
            If None, the self.game_id attribute must be set manually later

        initData : bool (default : True)
            If False, init will not call self.getLiveData().

        Attributes
        ----------
        self.game_id : str
            NHL API's game id (gamePk) associated with this game.

        self.live_data : list of dicts
            Live feed data for the game. By default, this data is collected at instantiation.

        """
        self._base_url = 'https://statsapi.web.nhl.com/api/v1'

        # if integer was passed, convert to string
        if game_id is not None:
            game_id = str(game_id)

        self.game_id = game_id

        if initData:
            self.live_data = self.getLiveData()
        else:
            self.live_data = list()





    def getLiveData(self, diffPatch=False, overwrite=False):
        """
        Method to request live* game data. Note that the game doesn't have to be
        *actually* live - it will just request the archived live feed data if it isn't.

        Parameters
        ----------
        diffPatch : bool or str ("yyyymmdd_hhmmss"; default : False)
            If specified, will only return the feed events since "yyyymmdd_hhmmss".

            When diffPatch is set to True, the self._last_live_pull attribute will
            be used pull everything since the last time it pulled.

            If a string of the form "yyyymmdd_hhmmss" is passed, then all data since
            the specified timestamp will be pulled.

        overwrite : bool (default : False)
            Whether to overwrite previous data.

            If True, this will overwrite any previously pulled data.

            If False, this will append the requested data to any existing data.

        Attributes
        ----------
        self.live_data : list of dicts
            All the ugly data returned by nhl.api.getLiveData
        """
        if diffPatch is True:
            raise NotImplementedError("This is actually really tricky to figure out updating; just pull it all...")
            # set diffPatch to correspond to the most recent pull
            diffPatch = self._last_live_pull

        # request data
        self.live_data = api.getLiveData(self.game_id, diffPatch=diffPatch, base_url=self._base_url)

        # if diffPatch was specified, append new data
        if diffPatch:
            raise NotImplementedError("This is actually really tricky to figure out updating; just pull it all...")

        return self.live_data

    def shotData(self, include_goals=True):
        """
        Method for retrieving shots on goal data for the game.

        NOTE: this function automatically flips the coordinate for events
        during the second period (and even numbered OT periods).

        Returns
        -------
        shots : pd.DataFrame


        """
        # DataFrame column structure
        cols = ['player', 'shotType', 'scored', 'coords', 'period', 'periodTime',
                'goalie', 'playerTeam']

        _data = []

        # find all the shots
        for event in self.live_data['plays']['allPlays']:
            # most shots don't go in; we only change this if it did
            scored = False
            # check if it is a shot
            if event['result']['eventTypeId'] in ['SHOT', 'GOAL']:
                # check if this shot was actually a goal
                if event['result']['eventTypeId'] == 'GOAL':
                    scored = True

                # get relevant data
                try:
                    shotType = event['result']['secondaryType']
                except KeyError:
                    print(event)
                    shotType = None
                coords = tuple(event['coordinates'].values())
                period = event['about']['period']
                periodTime = event['about']['periodTime']
                playerTeam = event['team']['triCode']

                # find who the player (shooter/scorer) and goalie were
                for p in event['players']:
                    # finding skater
                    if p['playerType'] in ['Shooter', 'Scorer']:
                        player = p['player']['fullName']
                    # finding goalie
                    if p['playerType'] == 'Goalie':
                        goalie = p['player']['fullName']

                # flip the coordinates if it is an even period number
                if period%2 == 1:
                    coords = (-coords[0], -coords[1])

                # append to list that will become the dataframe
                vals = [player, shotType, scored, coords, period, periodTime, goalie, playerTeam]
                _data.append(vals)

        return pd.DataFrame(_data, columns=cols)
