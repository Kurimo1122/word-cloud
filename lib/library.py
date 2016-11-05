# Function to get user_timeline
def user_timeline():
    # Check request_token and oauth_verifier
    token = session.pop('request_token', None)
    verifier = request.args.get('oauth_verifier')
    
    if token is None or verifier is None:
        return False # if the authentication has not yet been done.
    
    # OAuth authentication using tweepy
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET, CALLBACK_URL)
    
    # Get access token, Access token secret
    auth.request_token = token
    try:
        auth.get_access_token(verifier)
    except (tweepy.TweepError, e):
        logging.error(str(e))
        return {}

    # Access to Twitter API using tweepy
    api = tweepy.API(auth)
    
    # Get tweets (max: 100 tweets) list
    return api.user_timeline(count=100)

# open sentiment table and save each hinshi to each list
def save_hinshi_list(nounswords, verbswords, adjswords, advswords, 
    nounspoint, verbspoint, adjspoint, advspoint):
    with open('pn_ja.dic.txt', 'r', encoding="Shift-JIS") as f:
    it = (line for line in f)
    while True:
        try:
            line = next(it)
        except StopIteration:
            break
        line = line.rstrip()
        x = line.split(':')
        if abs(float(x[3])) > 0:
            if x[2] == '名詞':
                nounswords.append(x[0])
                nounspoint.append(x[3])
            if x[2] == '動詞':
                verbswords.append(x[0])
                verbspoint.append(x[3])
            if x[2] == '形容詞':
                adjswords.append(x[0])
                adjspoint.append(x[3])
            if x[2] == '副詞':
                advswords.append(x[0])
                advspoint.append(x[3])

#get analyzed tweets text
def get_tweet_keitaiso_kaiseki(timeline, text_list, text_all):
    for status in timeline:
        text = status.text
        if 'RT' in text:
            pass
        elif '@' in text:
            pass
        else:
            text_list.append(text)

    text_all += "".join(text_list)
    
    # keitaiso kaiseki
    tagger = Tagger()
    wakati_text = tagger.parse(text_all)

    return wakati_text
