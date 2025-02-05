import Telegram_Manager
import Command_Centre
from time import sleep, ctime
import atexit

print(ctime() + " - Starting Script")

def receiver_loop(Octavius_Receiver):
    #enter endless loop awaiting messages
    while True:
        #get message contents
        text = Octavius_Receiver.get_response()
        #if message contents is not empty, pass to command centre for handling
        if text != "":
            Command_Centre.handle(text, Octavius_Receiver)

        sleep(2)



def exiting():
    print(ctime() + " - Exiting")



if __name__ == '__main__':

    #Initialise system and wait for internet connection to be established
    print(ctime() + " - Initialising")
    atexit.register(exiting)
    previousmessage = ''

    #Generate telegram receiver object to handle comms. If excption is raised, try again
    Octavius_Receiver = None
    while Octavius_Receiver is None:
        #sleep(10)
        try:
            Octavius_Receiver = Telegram_Manager.generate_receiver()
            if Octavius_Receiver == None:
                raise Exception

        except Exception as E:
            print(ctime() + " - Error Initialising - ")
            print(str(E))
            print(ctime() + " - Retrying in 10 seconds")

    #once connection established, attempt to send a message
    print(ctime() + " - Initialisation Complete, Connecting to URL")
    connected = Octavius_Receiver.send_message("I am online...")

    attempts = 0
    #if message fails to send, re-try for 24 hours, then reboot
    if connected is False:
        print(ctime() + " - Re-trying…")
        while connected is False:
            connected = Octavius_Receiver.send_message("I am online...")
            attempts += 1
            sleep(10)
            print(ctime() + " - Re-trying…")
            if attempts > 6:
                sleep(50)
                if attempts > 66:
                    sleep(3540)
                    if attempts > 84:
                        Command_Centre.reboot()

    #if connections are fine, enter receiver loop and await messages
    receiver_loop(Octavius_Receiver)

