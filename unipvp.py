import requests
import time
import random
import tweepy
import csv
import pickle
from keys import keys # need to have a file with your api keys in it, for security purposes

os_api = 'INSERT OS API KEY HERE' # this should have been in the keys file for security purposes, but never got around to it :P
bearer_token = keys['bearer_token']
headers = {"Authorization": "Bearer {}".format(bearer_token), "X-API-KEY": os_api}
CONSUMER_KEY = keys['consumer_key']
CONSUMER_SECRET = keys['consumer_secret']
ACCESS_TOKEN = keys['access_token']
ACCESS_TOKEN_SECRET = keys['access_token_secret']

# authentication for tweepy to be able to post/ reply on Twitter
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

# Load data
a_file = open("unicorn_stat_data.pkl", "rb") # This is dictionary of all of the Unifriends stats so we don't have to do API calls every time we need info.
uni_dict = pickle.load(a_file)
a_file.close()

tweet_list = []
pvp_queue = []
wallet_list = []
user_dict = {}
player1_unis = []
player2_unis = []


def check_csv():
    """Checks UserInfo.csv for new users to add to the system.""" # This method of doing it isn't required, but it might help with distributing rewards later on.
    print("Checking csv and creating new users as needed")
    with open('UserInfo.csv', newline='') as csvfile:
        user_data = list(csv.reader(csvfile))
    for user in user_data:
        user_handle = user[0]
        user_wallet = user[1]
        if user_wallet not in wallet_list:
            print("New user! Attempting to creat a new profile")
            create_user(user_handle, user_wallet)
            wallet_list.append(user_wallet)
        else:
            print("User exists")


def scan_challenges():
    """Checks Twitter for people who want to fight and has them fight. This is more or less the main gameplay loop."""
    print("Need to search for pvp challenges")
    url = "https://api.twitter.com/2/tweets/search/recent?query=%40UnifriendsPVP%20%23PVP%20has%3Alinks&max_results=100&tweet.fields=id,text,author_id"
    response = requests.request("GET", url, headers=headers)
    res_json = response.json()
    if res_json['meta']['result_count'] != 0:
        for tweet in res_json['data']:
            print(tweet)
            if tweet['id'] not in tweet_list:
                if tweet['author_id'] in user_dict:
                    if tweet['author_id'] not in pvp_queue:
                        pvp_queue.append(tweet['author_id'])
                        user_dict[tweet['author_id']]['last_tweet'] = tweet['id']
                tweet_list.append(tweet['id'])
                if len(pvp_queue) >= 2:
                    print('We about to fight homie...')
                    player1_wallet = user_dict[pvp_queue[0]]['wallet']
                    player2_wallet = user_dict[pvp_queue[1]]['wallet']
                    player1_unis = find_unis(player1_wallet)
                    player2_unis = find_unis(player2_wallet)
                    find_strongest(player1_unis, pvp_queue[0])
                    find_strongest(player2_unis, pvp_queue[1])
                    winner = pvp_fight(pvp_queue[0], pvp_queue[1])
                    if winner == 'p1':
                        user_dict[pvp_queue[0]]['wins'] += 1
                        mutation_check = check_mutation(pvp_queue[0])
                        if mutation_check == True:
                            print("Need to choose mutation type")
                            mutation_type = choose_mutation()
                            if mutation_type == 'Strength':
                                user_dict[pvp_queue[0]]['bonus_str'] += 1
                            elif mutation_type == 'Speed':
                                user_dict[pvp_queue[0]]['bonus_spd'] += 1
                            elif mutation_type == 'Intelligence':
                                user_dict[pvp_queue[0]]['bonus_int'] += 1
                            user_dict[pvp_queue[0]]['mutations'] += 1
                        #announce_winner(pvp_queue[0])
                    elif winner == 'p2':
                        user_dict[pvp_queue[1]]['wins'] += 1
                        mutation_check = check_mutation(pvp_queue[1])
                        if mutation_check == True:
                            print("Need to choose mutation type")
                            mutation_type = choose_mutation()
                            if mutation_type == 'Strength':
                                user_dict[pvp_queue[1]]['bonus_str'] += 1
                            elif mutation_type == 'Speed':
                                user_dict[pvp_queue[1]]['bonus_spd'] += 1
                            elif mutation_type == 'Intelligence':
                                user_dict[pvp_queue[1]]['bonus_int'] += 1
                            user_dict[pvp_queue[1]]['mutations'] += 1
                        #announce_winner(pvp_queue[1])
                    user_dict[pvp_queue[0]]['fights'] += 1
                    user_dict[pvp_queue[1]]['fights'] += 1
                    del (pvp_queue[1])
                    del (pvp_queue[0])

def find_strongest(player_unis, player_id):
    """Figures out which Unifriend is the strongest one in a User's stable and saves that data to their profile for easy access."""
    for uni in player_unis:
        if user_dict[player_id]['strongest_uni'] == None:
            user_dict[player_id]['strongest_uni'] = uni
        else:
            print("Need to compare unis")
            if uni_dict[uni]['total'] > uni_dict[user_dict[player_id]['strongest_uni']]['total']:
                user_dict[player_id]['strongest_uni'] = uni
    print("Done scanning unis... player ready to fight...")

def find_mercs(p1, p2):
    """ Adds a second Unifriend to the fight.""" # Never got around to this one because I didn't know if it was fair for people who only have 1 Uni
    print("Need to find mercenaries")


def check_mutation(winner):
    """ Rolls a random number to see if the winner of a fight will mutate and gain a permanent boost to their stats. This has diminishing returns."""
    print("Need to choose if winner mutates, and what kind of mutation")
    mutate_roll = random.randint(1, user_dict[winner]['mutation_chance'] + user_dict[winner]['mutations'])
    if mutate_roll == 1:
        print("Winner has mutated")
        return True
    else:
        print("Sorry, no mutations")
        return False


def choose_mutation():
    """ Chooses which stat to increase if a mutation happens."""
    print("Choose mutation type")
    mutation_roll = random.randint(1,99)
    print(mutation_roll)
    if mutation_roll <= 33:
        print("Gain strength")
        return 'Strength'
    elif mutation_roll > 33 <= 66:
        print("Gain Speed")
        return 'Speed'
    elif mutation_roll > 66:
        print("Gain Intelligence")
        return 'Intelligence'

def announce_winner(winner):
    """Replies to the Winner's tweet that they won the battle.""" # This might need work because the Loser may not know they lost and are able to fight again.
    print("Announcing winner")
    tweet = user_dict[winner]['last_tweet']
    username = user_dict[winner]['twitter_handle']
    wins = user_dict[winner]['wins']
    stat_update = f"Congrats @{username}, you won the fight! \n" \
                  f"Wins: {wins}"
    api.update_status(status=stat_update, in_reply_to_status_id=tweet,
                      auto_populate_reply_metadata=True)

def pvp_fight(play1, play2):
    """Finds the strongest Unifriend for each combatant, figures out which player goes first, and has them fight."""
    uni1 = user_dict[play1]['strongest_uni']
    uni2 = user_dict[play2]['strongest_uni']
    print("Starting Combat")
    uni1_spd = random.randint(40, uni_dict[uni1]['Spd']) + user_dict[play1]['bonus_spd']
    uni2_spd = random.randint(40, uni_dict[uni2]['Spd']) + user_dict[play2]['bonus_spd']
    p1_str = user_dict[play1]['bonus_str']
    p1_int = user_dict[play1]['bonus_int']
    p2_str = user_dict[play2]['bonus_str']
    p2_int = user_dict[play2]['bonus_int']
    if uni1_spd >= uni2_spd:
        print("Player 1 is faster")
        champion = do_combat('p1', uni1, uni2, p1_str, p1_int, p2_str, p2_int)
    else:
        print("Player 2 is faster")
        champion = do_combat('p2', uni1, uni2, p1_str, p1_int, p2_str, p2_int)
    if champion == 'p1':
        print("Player1 is the Champion")
    elif champion == 'p2':
        print("Player2 is the Champion")
    return champion

def do_combat(fastest, unicorn1, unicorn2, p1str, p1int, p2str, p2int):
    """ Handles the actual fight."""
    p1_life = uni_dict[unicorn1]['Str'] + p1str
    p2_life = uni_dict[unicorn2]['Str'] + p2str
    p1_max_dmg = int(uni_dict[unicorn1]['Int'] / 2) + p1int
    p2_max_dmg = int(uni_dict[unicorn2]['Int'] / 2) + p2int
    while p1_life and p2_life > 0:
        p1_dmg = random.randint(20, p1_max_dmg)
        p2_dmg = random.randint(20, p2_max_dmg)
        if fastest == 'p1':
            p2_life -= p1_dmg
            print(f"Player 2 takes {p1_dmg} damage")
            if p2_life <= 0:
                print('P2 Died...')
                return 'p1'
            p1_life -= p2_dmg + 10
            print(f"Player 1 takes {p2_dmg + 10} damage")
            if p1_life <= 0:
                print('P1 Died...')
                return 'p2'
        elif fastest == 'p2':
            p1_life -= p2_dmg
            print(f"Player 1 takes {p2_dmg} damage")
            if p1_life <= 0:
                print('P1 Died...')
                return 'p2'
            p2_life -= p1_dmg + 10
            print(f"Player 2 takes {p1_dmg + 10} damage")
            if p2_life <= 0:
                print('P2 Died...')
                return 'p1'




def create_user(handle, wallet):
    """Gets a new User's Twitter ID based on their Twitter handle and creates a profile for them."""
    user_id = check_twitter_id(handle)
    if user_id not in user_dict:
        user_dict[user_id] = {'twitter_handle': handle, 'twitter_id': user_id,
                                'wallet': wallet, 'strongest_uni': None, 'wins': 0, 'fights': 0,
                              'mutations': 0, 'crit_chance': 0, 'dodge_chance': 0, 'mutation_chance': 2,
                              'mercenary': None, 'bonus_str': 0, 'bonus_spd': 0, 'bonus_int': 0, 'last_tweet': 0}
    print("User created and twitter id added to active list")


def check_twitter_id(handle):
    """ Checks the Twitter api for the ID that belongs to a handle.""" # doing things based on their ID is easier to manage.
    print("Running check_twitter_id")
    url = f"https://api.twitter.com/2/users/by/username/{handle}?user.fields=id,pinned_tweet_id"
    response = requests.request("GET", url, headers=headers)
    res_json = response.json()
    time.sleep(2)
    twitter_id = res_json['data']['id']
    return twitter_id


def find_unis(wallet):
    """ Scans a User's wallet for a list of Unifriends they own""" # This may be able to be handled through etherscan in order to remove the need for an OS API key
    print("Need to scan and find unicorn stats")
    url = f"https://api.opensea.io/api/v1/assets?owner={wallet}&order_direction=desc&asset_contract_address=0x51369e8c482763089b0b90009c2a79c98244168e&limit=50&include_orders=false"
    response = requests.request("GET", url, headers=headers)
    res_json = response.json()
    uni_list = []
    for asset in res_json['assets']:
        if asset['token_id'] not in uni_list:
            uni_list.append(asset['token_id'])
    return uni_list

# main loop that checks for user data from a csv, checks twitter for people who want to pvp, and has them fight.
while True:
    check_csv()
    scan_challenges()
    print(user_dict)
    print(pvp_queue)
    time.sleep(20)

