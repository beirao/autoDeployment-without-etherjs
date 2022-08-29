from nis import match
import requests
from dotenv import load_dotenv
import os
import json
from datetime import datetime,timedelta

def timeIntervaleGenerator5Days():
    def normalizeDate(date) : 
        return "0"+ str(date) if date < 10  else str(date)
 
    now = datetime.now() + timedelta(days=1)
    nowPlus5 = now + timedelta(days=2)

    return f"dateTo={nowPlus5.year}-{normalizeDate(nowPlus5.month)}-{normalizeDate(nowPlus5.day)}&dateFrom={now.year}-{normalizeDate(now.month)}-{normalizeDate(now.day)}"

def jsonMatchNormalization(res) :
    # [(match_id, date, status, league_id, league_string, home_id, home_string, away_id, away_string, isDeployed)]
    matchsData = []
    res = json.loads(res.text)

    for i in range(res['resultSet']['count']) :
        match_id =      res['matches'][i]['id']
        date =          res['matches'][i]['utcDate']
        status =        res['matches'][i]['status']
        league_id =     res['matches'][i]['competition']['id']
        league_string = res['matches'][i]['competition']['name'] 
        home_id =       res['matches'][i]['homeTeam']['id'] 
        home_string =   res['matches'][i]['homeTeam']['name'] 
        home_logo =     res['matches'][i]['homeTeam']['crest'] 
        away_id =       res['matches'][i]['awayTeam']['id'] 
        away_string =   res['matches'][i]['awayTeam']['name']
        away_logo =     res['matches'][i]['awayTeam']['crest'] 
        isDeployed = 0
        address = "0x"
        
        # date to timestamp
        match_timestamp = datetime.timestamp(datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ'))
        
        matchsData.append((match_id, match_timestamp, status, league_id, league_string, home_id, home_string, home_logo, away_id, away_string, away_logo, isDeployed, address))
    return matchsData

def requestMatchPlanning() :
    try : 
        load_dotenv()
        url = f"https://api.football-data.org/v4/matches?{timeIntervaleGenerator5Days()}"
        res = requests.request("GET", url, headers={ "X-Auth-Token":os.getenv('FOOT_API_KEY')}, data={})
        return jsonMatchNormalization(res)
    except Exception as e :
        print("Error :",e)
   
if __name__ == "__main__":
    print(requestMatchPlanning())