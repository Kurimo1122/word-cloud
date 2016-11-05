# coding:utf-8
import io
import os
from os import path
import numpy as np
import logging
import tweepy
from flask import Flask, session, redirect, render_template, request, send_file
from igo.Tagger import Tagger
from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image


# Consumer Key
CONSUMER_KEY = os.environ['CONSUMER_KEY']

# Consumer Secret
CONSUMER_SECRET = os.environ['CONSUMER_SECRET']

# CALLBACK_URL (Will be redirected after authentication)
CALLBACK_URL = 'https://twitter-word-cloud-toshi.herokuapp.com'
#CALLBACK_URL = 'http://localhost:5000' # local environment

logging.warn('app start!')

# Start Flask
app = Flask(__name__)

# Set key to use session of flask
app.secret_key = os.environ['SECRET_KEY']

# Set root page
@app.route('/')
def index():
    timeline = user_timeline()

    # preparation for calculating sentiment score
    nouns, verbs, adjs, advs = [], [], [], []
    nounswords, verbswords, adjswords, advswords = [], [], [], []
    nounspoint, verbspoint, adjspoint, advspoint = [], [], [], []
    posinega_score = 0
    score = 0
    number = 0

    #preparation for keitaiso kaiseki 
    text_list = []
    wakati_list = []
    user_image = ""
    text_all = ""
    
    # open sentiment table and save each hinshi to each list
    nounswords, nounspoint, verbswords, verbspoint, 
    adjswords, adjspoint, advswords, advspoint = save_hinshi_list(
        nounswords, verbswords, adjswords, advswords, 
        nounspoint, verbspoint, adjspoint, advspoint)
    
    if timeline == False:
        pass
    else:
        user_image = timeline[0].user.profile_image_url
        
        #get analyzed tweets text
        wakati_text = get_tweet_keitaiso_kaiseki(timeline, text_list, text_all)

        #caluculate sentiment score and meishi list
        posinega_score, wakati_list = get_sentiment_score_and_meishi_list(wakati_text, wakati_list, nouns, verbs, adjs, advs, 
            nounswords, verbswords, adjswords, advswords, 
            nounspoint, verbspoint, adjspoint, advspoint, 
            posinega_score, score, number):

        # send wakati_all to word_cloud route
        wakati_all = " ".join(wakati_list)
        session['wakati_all'] = wakati_all
    
    return render_template('index.html', timeline=timeline, user_image=user_image, posinega_score = posinega_score)

#show word cloud
@app.route('/word_cloud/<user_id>', methods=['GET', 'POST'])
def word_cloud(user_id):
    # Set font path
    fpath = "Fonts/NotoSansCJKjp-Medium.otf"
    d = path.dirname(__file__)
    #Set mask image 
    alice_mask = np.array(Image.open(path.join(d, "alice_mask.png")))

    wakati_all = "テスト中 "
    wakati_all += session.get('wakati_all')

    stop_words = [
        u'こと', u'そう', u'はず', u'みたい', u'それ',
        u'よう', u'こと', u'これ', u'ため', u'せい', 
        u'どころ'
    ]

    #generate wordcloud
    wordcloud = WordCloud(
        background_color = 'white',
        max_font_size = 40,
        relative_scaling = .5,
        font_path = fpath,
        stopwords = set(stop_words),
        mask = alice_mask,
        ).generate(wakati_all)
           
    fig = plt.figure()
    plt.imshow(wordcloud)
    plt.axis("off")
    
    #show image
    img = io.BytesIO()
    fig.savefig(img)
    img.seek(0)
    response = send_file(img, mimetype='image/png')
    return response


# Set auth page
@app.route('/twitter_auth', methods=['GET'])
def twitter_auth():
    # Authentication using OAuth by tweepy
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET, CALLBACK_URL)
        
    try:
        # Get the redirect_url
        redirect_url = auth.get_authorization_url()
        
        # Save the request_token which will be used after authentication
        session['request_token'] = auth.request_token
    
    except (tweepy.TweepError, e):
        logging.error(str(e))
    
    return redirect(redirect_url)

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
    f = io.open('pn_ja.dic.txt', 'r', encoding="Shift-JIS")
    for line in f:
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
    f.close()

    return nounswords, nounspoint, verbswords, verbspoint, adjswords, adjspoint, advswords, advspoint

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

def get_sentiment_score_and_meishi_list(wakati_text, wakati_list, nouns, verbs, adjs, advs, 
    nounswords, verbswords, adjswords, advswords, 
    nounspoint, verbspoint, adjspoint, advspoint,
    posinega_score, score, number):

    for word in wakati_text:
        if '名詞' in word.feature:
            wakati_list.append(word.surface)
            nouns.append(word.surface)
        if '動詞' in word.feature:
            verbs.append(word.surface)
        if '形容詞' in word.feature:
            adjs.append(word.surface)
        if '副詞' in word.feature:
            advs.append(word.surface)

    score = number = 0
    score_n, number_n = analyze(nouns, nounswords, nounspoint, score, number)
    score_v, number_v = analyze(verbs, verbswords, verbspoint, score, number)
    score_j, number_j = analyze(adjs, adjswords, adjspoint, score, number)
    score_v, number_v = analyze(advs, advswords, advspoint, score, number)
    score += score_n + score_v + score_j + score_v
    number += number_n + number_v + number_j + number_v
    
    if number > 0:
        posinega_score = score / number

    return posinega_score, meishi_list

#analyze function to calculate the sentiment score
def analyze(hinshi, words, point, score, number):
    global score, number
    for i in hinshi:
        cnt = 0
        for j in words:
            if i == j:
                score += float(point[cnt])
                number += 1
            cnt += 1
    return score, number
