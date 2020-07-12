"""docstring"""

# pylint: disable =

import json
import csv
import time
import configparser
import urllib.request as request
import praw
from praw.models import Comment, Submission


def url_to_json(url, json_filename, user_agent):
    """
    Args:
        url: url of JSON data from reddit
        json_filename: the name of the file to be created
        user_agent: lets servers identify the requesting user agent, can be set to anything
    Returns:
        creates json file
    """

    hdr = {'User-agent': user_agent}
    req = request.Request(url, headers=hdr)
    response = request.urlopen(req)
    source = response.read()
    data = json.loads(source)

    json_file = open(json_filename, "w")
    json_file.write(json.dumps(data))

def json_to_csv(json_filename, csv_filename):
    """
    Args:
        json_filename: the name of the file to be read
        json_filename: the name of the file to be created
    Returns:
        creates csv file
    """
    json_file = open(json_filename, "r", encoding="utf-8")
    json_data = json.load(json_file)

    csv_file = open(csv_filename, "w", encoding="utf-8")

    csv_fieldnames = ['position', 'name', 'title', 'created_utc',
                      'author', 'subreddit', 'permalink']
    csv_writer = csv.DictWriter(csv_file, fieldnames=csv_fieldnames)
    csv_writer.writeheader()

    # print(json_data["data"]["children"][0]["data"]["name"])
    for pos, post in enumerate(json_data["data"]["children"]):
        json_dict = {}
        json_dict["position"] = pos + 1
        for field in csv_fieldnames[1:]:
            json_dict[field] = post["data"][field]
        csv_writer.writerow(json_dict)

def csv_to_dictlist(csv_filename):
    """
    Args:
        csv_filename: the name of the file to be read
    Returns:
        a list of dictionaries for every entry
    """
    csv_file = open(csv_filename, "r", encoding="utf-8")
    csv_dict = [{k: v for k, v in row.items()}
                for row in csv.DictReader(csv_file, skipinitialspace=True)]
    return csv_dict

def dictlist_to_csv(dictlist, csv_filename):
    """
    Args:
        dictlist: a list of dictionaries for every entry
        csv_filename: the name of the file to be created
    Returns:
        creates csv file
    """
    csv_file = open(csv_filename, "w+", encoding="utf-8")
    csv_fieldnames = dictlist[0].keys()
    csv_writer = csv.DictWriter(csv_file, fieldnames=csv_fieldnames)
    csv_writer.writeheader()

    for row in dictlist:
        csv_writer.writerow(row)

def csv_formatted_output(csv_filename, txt_filename):
    """
    Args:
        csv_filename: the name of the file to be read
        txt_filename: the name of the file to be created
    Returns:
        creates txt file
    """
    output = open(txt_filename, "w", encoding="utf-8")
    mydict = csv_to_dictlist(csv_filename)

    for row in mydict:
        line = ""
        line = line + "**to /r/" + row.get("subreddit") + " by /u/" + row.get("author") + "**\n\n"
        output.write(line)

        line = ""
        line = line + "**" + row.get("title") + "**\n\n"
        output.write(line)

        line = ""
        line = line + "[**Comments**](" + row.get("permalink") + ")\n\n"
        output.write(line)

        line = "\n\n\n---\n\n"
        output.write(line)

def frontpage_to_txt(url, user_agent):
    """
    Args:
        url: url of JSON data from reddit
        user_agent: lets servers identify the requesting user agent
    Returns:
        creates json, csv, txt files
    """

    timestamp = int(time.time())
    ts_json_filename = "data/fpage" + str(timestamp) + ".json"
    ts_csv_filename = "data/fpage" + str(timestamp) + ".csv"
    ts_txt_filename = "data/fpage" + str(timestamp) + ".txt"

    url_to_json(url, ts_json_filename, user_agent)
    json_to_csv(ts_json_filename, ts_csv_filename)
    csv_formatted_output(ts_csv_filename, ts_txt_filename)

def saved_to_csv(reddit, limit=100, unsave=False):
    """
    Args:
        reddit: praw.Reddit object
        limit: maximum number of saved posts to look through
        unsave: if True then unsaves posts from account
    Returns:
        creates csv of saved posts
    """

    savedcontent = reddit.user.me().saved(limit=limit)

    new_dictlist = []
    for item in savedcontent:
        new_dict = {}
        if isinstance(item, Comment):
            if len(item.body) <= 280:
                subtype = "short"
            else:
                subtype = "long"

            new_dict = {
                "type": "comment",
                "subtype": subtype,
                "subreddit": item.subreddit,
                "title": item.body[:140].replace("\n", " "),
                "permalink": "https://www.reddit.com"+item.permalink,
            }
            if unsave:
                item.unsave()

        elif isinstance(item, Submission):
            if item.is_self:
                subtype = "text"
            else:
                subtype = "link"

            new_dict = {
                "type": "post",
                "subtype": subtype,
                "subreddit": item.subreddit,
                "title": item.title[:140],
                "permalink": "https://www.reddit.com"+item.permalink,
            }
            if unsave:
                item.unsave()
        new_dictlist.append(new_dict)

    timestamp = int(time.time())
    ts_save_filename = "data/saved" + str(timestamp) + ".csv"
    dictlist_to_csv(new_dictlist, ts_save_filename)


print("Before you continue, ensure you have updated config.ini")
print("What do you want to do?")
print("1. frontpage_to_txt")
print("2. saved_to_csv")
choice = input("> ")

if choice == "1":
    read_config = configparser.ConfigParser()
    read_config.read("config.ini")

    url = read_config.get("frontpage_to_txt", "url")
    user_agent = read_config.get("frontpage_to_txt", "user_agent")

    frontpage_to_txt(url, user_agent)

elif choice == "2":
    read_config = configparser.ConfigParser()
    read_config.read("config.ini")

    client_id = read_config.get("saved_to_csv", "client_id")
    client_secret = read_config.get("saved_to_csv", "client_secret")
    user_agent = read_config.get("saved_to_csv", "user_agent")
    username = read_config.get("saved_to_csv", "username")
    password = read_config.get("saved_to_csv", "password")
    limit = int(read_config.get("saved_to_csv", "limit"))
    unsave = read_config.get("saved_to_csv", "unsave")
    if unsave == "True":
        unsave = True
    elif unsave == "False":
        unsave = False

    reddit = praw.Reddit(client_id=client_id,
                         client_secret=client_secret,
                         user_agent=user_agent,
                         username=username,
                         password=password)

    saved_to_csv(reddit, limit, unsave)
