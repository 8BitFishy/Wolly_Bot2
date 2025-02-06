from time import ctime, sleep
from os import walk, system
from Telegram_Manager import directory

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    TRANSMIT_PIN = 24
    GPIO.setup(TRANSMIT_PIN, GPIO.OUT)
except:
    print(ctime() + " - No gpiozero module found")

if system == "Linux":
    directory = __file__.strip("Telegram_Manager.py").strip(":")
else:
    directory = __file__.rpartition("\\")[0] + "\\"
directory += "RF_Binary_Codes/Plugs-"

binary_codes = []

for i in range(2):
    if i == 0:
        plug = 'Black'
    else:
        plug = "White"
    for file in walk(f"{directory}{plug}"):
        filelist = list(file[2])
        for file in filelist:
            with open(f"{directory}{plug}/{file}") as f:
                code = []
                for k in range(5):
                    line = next(f).strip()
                    data, value = line.rsplit(" - ")
                    if k == 0:
                        value = int(value)
                    else:
                        value = float(value)

                    code.append(value)
                binary_codes.append([plug.lower(), int(file[0]), file[2:5].rstrip('_').lower(), code])




def Code_Picker(Octavius_Receiver, target, action, number=None):

    binary_codes = Generate_Code_List()
    if target == 'all':
        print(ctime() + f" - Action - All plugs set to {action}")
        Octavius_Receiver.send_message(f"Turning all plugs {action}")
        for i in range(len(binary_codes)):
            if binary_codes[i][2] == action:
                transmit_code(binary_codes[i][3])
                # sleep(0.2)

    else:
        number = int(number)
        print(ctime() + f" - Action - Turn {target} plug {number} {action}")
        Octavius_Receiver.send_message(f"Turning {target} plug {number} {action}")
        for i in range(len(binary_codes)):
            if binary_codes[i][0] == target and binary_codes[i][1] == number and binary_codes[i][2] == action:
                try:
                    transmit_code(binary_codes[i][3])
                    print(ctime() + f" - {target} plug {number} turned {action}")
                    Octavius_Receiver.send_message(f"{target} plug {number} turned {action}")
                except:
                    print(ctime() + f" - Failed to send code")
                    Octavius_Receiver.send_message(f"Failed to send code")
                    
                return
    return


def transmit_code(binary_code):
    NUM_ATTEMPTS = 30
    # Transmit a chosen code string using the GPIO transmitter

    code = str(binary_code[0])
    print(ctime() + f" - Action - transmitting code {code}")

    for t in range(NUM_ATTEMPTS):
        for i in code:
            if i == '1':
                GPIO.output(TRANSMIT_PIN, 1)
                sleep(binary_code[2])
                GPIO.output(TRANSMIT_PIN, 0)
                sleep(binary_code[4] - binary_code[2])
            elif i == '0':
                GPIO.output(TRANSMIT_PIN, 1)
                sleep(binary_code[3])
                GPIO.output(TRANSMIT_PIN, 0)
                sleep(binary_code[3] - binary_code[2])
            else:
                continue
        GPIO.output(TRANSMIT_PIN, 0)
        sleep(binary_code[1])
    GPIO.cleanup()
    return


def Generate_Code_List():

    return binary_codes
