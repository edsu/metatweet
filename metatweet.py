#!/usr/bin/env python

import os
import json
import time

from collections import OrderedDict
from tweepy import OAuthHandler, Stream, API
from tweepy.streaming import StreamListener


def main():

    # get credentials
    e = os.environ.get
    consumer_key = e("CONSUMER_KEY")
    consumer_secret = e("CONSUMER_SECRET")
    access_token = e("ACCESS_TOKEN")
    access_token_secret = e("ACCESS_TOKEN_SECRET")
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    # start the stream
    listener = Listener(auth)
    stream = Stream(auth, listener)

    while True:
        try:
            stream.sample()
        except Exception as e:
            print(e)
            time.sleep(5) 


class Listener(StreamListener):

    def __init__(self, auth):
        self.blueprint = None
        self.api = API(auth)

    def on_status(self, status):
        tweet = status._json
        if not self.blueprint:
            self.blueprint = json.load(open("blueprint.json"))
        else:
            new_blueprint = blueprint(tweet)
            diff = compare(self.blueprint, new_blueprint)

            if diff["added"] or diff["changed"]:
                for path, json_type in diff["added"]:
                    self.send_tweet("added: %s(%s)" % (path, json_type), tweet)
                    self.blueprint[path] = json_type
                for path, json_type in diff["changed"]:
                    self.send_tweet("changed: %s(%s)" % (path, json_type), tweet)
                    self.blueprint[path] = json_type

                # save current blueprint to disk
                json.dump(
                    self.blueprint, 
                    open("blueprint.json", "w"),
                    indent=2, 
                    sort_keys=True)
            else: 
                import sys
                sys.stdout.write(".")
                sys.stdout.flush()

    def on_error(self, status):
        pass

    def send_tweet(self, msg, tweet):
        tweet_url = "https://twitter.com/%s/status/%s" % (tweet["user"]["screen_name"], tweet["id_str"])
        try:
            self.api.update_status(msg + " in " + tweet_url)
        except Exception as e:
            print(e)
        time.sleep(5)


def compare(old_bp, new_bp):
    """
    compare will compare two blueprints and return any changes between them
    """

    if new_bp == old_bp:
        return None

    result = {"added": [], "removed": [], "changed": []}

    for path, json_type in new_bp.items():
        if path not in old_bp:
            result["added"].append([path, json_type])
        elif old_bp[path] != json_type:
            result["changed"].append([path, json_type])

    for path, json_type in old_bp.items():
        if path not in new_bp:
            result["removed"].append([path, json_type])

    return result


def blueprint(x, prefix=""):
    """
    blueprint examines an object and generates a blueprint for it, which
    loosely resembles a list of jq paths and their values.
    """
    bp = OrderedDict()

    pytype = type(x)
    if x is None:
        # hard to compare nulls so they are not recorded
        pass
    elif pytype == str:
        bp[prefix] = "string"
    elif pytype in (int, float):
        bp[prefix] = "number"
    elif pytype == bool:
        bp[prefix] = "boolean"
    elif pytype == dict:
        if prefix:
            bp[prefix] = "object"
        for k, v in x.items():
            bp.update(blueprint(v, prefix + "." + k)) 
    elif pytype == list:
        if prefix:
            bp[prefix] = "array"
        if (len(x) > 0):
            bp.update(blueprint(x[0], prefix + "[]"))

    return bp


if __name__ == '__main__':
    main()

