import json
import requests
import urllib
from time import time, ctime, sleep
from platform import system

if system() == "Linux":
    directory = __file__.strip("Telegram_Manager.py").strip(":")
else:
    directory = __file__.rpartition("\\")[0] + "\\"

filename = 'telegramID.txt'
with open(f'{directory}{filename}') as f:
    IDS = f.read().splitlines()

chat_id = str(IDS[0])
TOKEN = str(IDS[1])
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

class Message_Receiver:
    def __init__(self, text):
        self.text = text
        self.last_update_id = None

    def get_updates(self, offset=None):
        url = URL + "getUpdates?timeout=100"
        if offset:
            url += "&offset={}".format(offset)
        js = self.get_json_from_url(url)
        return js

    def get_json_from_url(self, url):
        content = self.get_url(url)
        js = json.loads(content)
        return js

    def get_url(self, url):
        response = requests.get(url)
        content = response.content.decode("utf8")
        return content

    def send_message(self, text):

        try:
            print(ctime() + " - Sending Message - " + text)
            text = urllib.parse.quote_plus(text)
            url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
            self.get_url(url)
            return True

        except Exception as e:
            print(f"{ctime()} - Error reaching URL, cannot send message")
            print(e)
            return False

    
    def get_response(self):
        #clear message text variable
        self.text = ""

        try:
            #get most recent message as js
            updates = self.get_updates(self.last_update_id)

            #if content available
            if len(updates["result"]) is not None:
                #and content is longer than 0
                if len(updates["result"]) > 0:

                    #only take notice of last message if multiple messages available
                    if len(updates["result"]) > 1:
                        del updates["result"][:-1]

                    #update last update id
                    self.last_update_id = int(updates["result"][0]["update_id"]) + 1
                    print(ctime() + " - Received Update")

                    #get current datetime and datetime of last message
                    date_time = int(str(time()).split(".")[0])
                    time_since_message = updates["result"][0]["message"]["date"] - date_time

                    #if message is less than 20 seconds old, update text variable
                    if abs(time_since_message) < 20:
                        self.text = updates["result"][0]["message"]["text"]
                        print(ctime() + ' - Update Text - "' + self.text + '"')

                    #otherwise, message has timed out
                    else:
                        print(ctime() + " - Message timed out")

            #return text variable
            return self.text

        except Exception as e:
            print("Caught exception")
            try:
                #409 error means you are running multiple versions of this bot, please suspend one
                if str(updates["error_code"]) == str(409):
                    print("Is 409 error")
                    exit()

            except:
                pass
            print(f"{ctime()} - Error reaching URL, cannot get updates")
            print(e)
            self.text = ''
            sleep(5)
            return self.text

def generate_receiver():
    Octavius_Receiver = Message_Receiver("")
    return Octavius_Receiver
