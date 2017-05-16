#!/usr/bin/env python

import os

from collections import OrderedDict
from tweepy import OAuthHandler, Stream
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
    listener = Listener()
    stream = Stream(auth, listener)
    stream.sample()



class Listener(StreamListener):
    blueprint = None

    def on_status(self, status):
        tweet = status._json
        if not self.blueprint:
            self.blueprint = blueprint(tweet)
            print("setting first blueprint")
        else:
            new_blueprint = blueprint(tweet)
            diff = compare(self.blueprint, new_blueprint)
            if diff:
                print("added:", len(diff["added"]))
                print("removed:", len(diff["removed"]))
                print("changed:", len(diff["changed"]))
                print()
                self.blueprint = new_blueprint
            else: 
                import sys
                sys.stdout.write(".")
                sys.stdout.flush()

    def on_error(self, status):
        print(status)


def compare(old_bp, new_bp):
    if new_bp == old_bp:
        return None

    result = {"added": [], "removed": [], "changed": []}

    for path, json_type in new_bp.items():
        if path not in old_bp:
            result["added"].append("%s(%s)" % (path, json_type))
        elif old_bp[path] != json_type:
            result["changed"].append("%s(%s)" % (path, json_type))

    for path, json_type in old_bp.items():
        if path not in new_bp:
            result["removed"].append("%s(%s)" % (path, json_type))

    return result

def blueprint(x, prefix=""):
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

