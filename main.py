from datetime import datetime
from nis import match
import sqlite3 as db
from deployBet import deployBet
from request import requestMatchPlanning
import numpy as np
import yaml


# Créer TABLE 
# cursor.execute("CREATE TABLE 'match' ('match_id'	INTEGER NOT NULL UNIQUE,'home_id'	INTEGER,'home_string'	TEXT NOT NULL,'away_id'	INTEGER NOT NULL,'away_string'	TEXT NOT NULL,PRIMARY KEY('match_id'))")

# Inserer element dans TABLE
# cursor.execute("INSERT INTO match (match_id, home_id, home_string, away_id, away_string) VALUES ('2', '4', 'OL', '3', 'lille' );")
# connection.commit();

# Access element in TABLE 
# req = cursor.execute('SELECT * FROM match WHERE match_id = ?', (2,))

# req = cursor.execute('DELETE FROM match WHERE match_id = 3')


def dataBaseUpdate(rmpArray, connection, cursor) :
    for match_api in rmpArray :
        match_data = cursor.execute('SELECT * FROM match WHERE match_id = ?', (match_api[0],)).fetchone()

        if(match_data == None and (match_api[2] == "SCHEDULED" or match_api[2] == "TIMED")) :
            req = f"INSERT INTO match VALUES {tuple(match_api)};"
            cursor.execute(req)
            print("DB updated, match ID: ", match_api[0])

    connection.commit()

def deployContract(connection, cursor) : 
    with open("config.yaml", "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    # look at undeployed contract
    req = cursor.execute('SELECT * FROM match WHERE isDeployed = ?', (0,))
    deployementNeeded  = req.fetchall()
    # deploy contracts
    for i in deployementNeeded :
        if (    i[4] in config["listBetLeague"] 
            and (i[2] == "SCHEDULED" or i[2] == "TIMED") 
            and (datetime.timestamp(datetime.now()) < i[1] - config["minimumTimeBeforeDeployement"])) :
 
            try :
                print(f"Deploying : match ID {i[0]} league {i[4]}")
                contractAddress = deployBet(i[0],i[1])
                req = f"UPDATE match SET address = '{contractAddress}' WHERE match_id = {i[0]}"
                cursor.execute(req)

                # update data base at isDeployed = 1            
                req = f"UPDATE match SET isDeployed = 1 WHERE match_id = {i[0]}"
                cursor.execute(req)
                
            except Exception as e :
                print("Error main :",e)

    connection.commit()
    print("All deployed !")



# rmpArray element : 
# (417226, '2022-08-31T19:00:00Z', 'TIMED', 2015, 'Ligue 1', 
# 511, 'Toulouse FC', 'https://crests.football-data.org/511.png', 
# 524, 'Paris Saint-Germain FC', 'https://crests.football-data.org/524.png', 
# 0)]
def main() :
    try : 
        connection = db.connect("../bdd_match.db")
        cursor = connection.cursor()
        rmpArray = np.array(requestMatchPlanning())
        dataBaseUpdate(rmpArray, connection, cursor)
        deployContract(connection, cursor)

        # req = cursor.execute('SELECT * FROM match')
        # print(req.fetchall())

    except Exception as e :
        print("Error :",e)

    finally :
        connection.close()


if __name__ == "__main__":
    connection = db.connect("bdd_match.db")
    cursor = connection.cursor()
    cursor.execute('DELETE FROM match')
    connection.commit();    
    connection.close()

    main()