#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import numpy as np
import pandas as pd
import json
import requests
import time
class halo():
    def __init__(self,location=''):
        """
        This class manages data for the users as it gathers more of them
        
        """
        self.data = self.fromfile(location)
        # Makes it easier for me to determine which is which
        self.gamemodes = {'4a2cedcc90984728886f60649896278d':"3v3",
                          '379f9ee592ec45d9b5e59f30236cab00':"2v2",
                          '548d864e8666430e91408dd2ad8fbfcd':'1v1'}
        # Key for website
        micro_key = ""
        self.header = {"Ocp-Apim-Subscription-Key": micro_key}
    
    def gamertags(self,nasort = False):
        """
        Outputs all the usernames that have been collected so far.
        
        Parameters
            nasort (Boolean): Outputs everything with an nan value
        
        Return:
            (List): List of usernames
        
        """
        data = self.data
        if nasort:
            data = self.data[self.data.isnull().any(axis=1)]
        
        return data['usernames']

    def getRanks(self,players):
        """
        Collects the MMR and rank for each player and stores it into the main table
        
        Parameters
            players (List of Strings): Up to 6 players that will get collected for
        
        Return:
            (List): All of the rank data for those players
        
        
        """
        # I don't know what to output here
        output = list()
        
        #Adding all the usernames into a single string
        player = ''
        for itm in players:
            player +='{},'.format(itm)
        player = player[:-1]

        # Loops through the gamemodes
        #The keys for the dictionary are the ID's that the API uses
        for itm in self.gamemodes.keys():
            # The request
            website = 'https://www.haloapi.com/stats/hw2/playlist/{0}/rating?players={1}'.format(itm,player)
            requestRaw = requests.get(website,headers= self.header)
            time.sleep(1)
            requestDict = json.JSONDecoder().decode(requestRaw.text)
            
            # Loops through each player and adds the data into the proper column
            for item in requestDict['Results']:
                name = item['Id']
                mask = np.where(self.gamertags() == name)[0]
                # Doesn't let you put dictionaries into a spot
                self.data.at[mask,self.gamemodes[itm]] = [item['Result']]
                
            output.append(requestDict)
        return output
    def get_matches(self,seed):
        """
        Gathers match ID from a given username
        
        Parameters
            seed (String): The given username to collect data for
        
        Return:
            (List): List of ID values for games
        
        """
        # Gathering Match ID's

        # Previous matches
        match_overview = "https://www.haloapi.com/stats/hw2/players/{}/matches".format(seed)
        #Pulls last 20 matches from player
        overview = requests.get(match_overview,headers= header)
        
        # Decodes website output into dict
        temp = json.JSONDecoder().decode(overview.text)
        
        # Loops through each game and pulls out the ID for the game
        ids = list()
        for itm in temp['Results']:
            ids.append(itm["MatchId"])
        return ids
    
    def get_usernames(self, seed):
        """
        Obtains all users that recently played with the given user.
        Sorts out the ones that I've already collected and adds new ones to the
        internal variable
        
        Parameters
            seed (String): The given username to collect data for
        
        Return:
            (List): List of usernames that were added to the internal variable
        
        """
        # Gathering Match ID's
        ids = self.get_matches(seed)
        
        # Output 
        usernames = list()
        
        # Check most recent game against saved most recent game
        mask = np.where(self.data['usernames'] == seed)[0]
        savedMatch = self.data.at[mask[0],'LastMatch']
        # If match matches most recent game then skip player 
        if savedMatch == ids[0]:
            return usernames
        else:
            # Add most recent game to seed if it doesn't match currently saved
            mask = np.where(self.gamertags() == seed)[0]
            self.data.at[mask,'LastMatch'] = ids[0]
        
        
        for i,itm in enumerate(ids):
            #Get match results
            matchId = itm
            if savedMatch == itm and i!=0:
                # Add most recent game to seed if it doesn't match currently saved
                mask = np.where(self.gamertags() == seed)[0]
                self.data.at[mask[0],'LastMatch'] = ids[0]
                # End the loop
                return usernames
            match_details = "https://www.haloapi.com/stats/hw2/matches/{}".format(matchId)
            specific = requests.get(match_details,headers= header)
            r = json.JSONDecoder().decode(specific.text)

            # This will put all the players in a list
            players = r['Players']

            # Each player is assigned a key from 1-number of players
            for key in players.keys():
                # Making sure the player is a human and not a computer
                if players[key]['IsHuman']:
                    # Pulling the gamertag name out of the data
                    username = players[key]['HumanPlayerId']['Gamertag']
                    # Only add it if I haven't seen it yet.
                    # Small playerbase means you'll regularly play against the same people
                    if not((self.gamertags() == username).any()):
                        usernames.append(username)
                        self.data = self.data.append({
                            'usernames': username,
                            'LastMatch' : np.nan
                        }, ignore_index=True)
            if i==(len(ids)-1):
                # Add most recent game to seed if it doesn't match currently saved
                mask = np.where(self.gamertags() == seed)[0]
                self.data.at[mask[0],'LastMatch'] = ids[0]
            # 10 requests every 10 seconds or it'll fail        
            time.sleep(1)

        return usernames
    
    def getLastPlayed(self,player):
        """
        Determines the date of the last match this player played
        
        Parameters
            player (String): The given username to collect data for
        
        Return:
            (String): Date last game was played
        """
        match_overview = "https://www.haloapi.com/stats/hw2/players/{}/matches".format(player)
        #Pulls last 20 matches from player
        overview = requests.get(match_overview,headers= header)
        time.sleep(1)
        # Decodes website output into dict
        temp = json.JSONDecoder().decode(overview.text)
        # Easiest one. Outputs date
        output = temp['Results'][0]['MatchStartDate']['ISO8601Date']
        # Place the date into the data
        mask = np.where(self.gamertags() == player)[0]
        self.data.at[mask,'LastPlayed'] = output
        
        return output
    
    def createfile(self,name):
        data = self.data.sort_values(by='usernames',ignore_index=True)
        data.to_csv(name,index=False)
        return True
    def fromfile(self,name):
        return pd.read_csv(name)
    

