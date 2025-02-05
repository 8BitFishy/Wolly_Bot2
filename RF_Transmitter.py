import time
import os

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    TRANSMIT_PIN = 24
    GPIO.setup(TRANSMIT_PIN, GPIO.OUT)
except:
    print(time.ctime() + "No gpiozero module found")


def Code_Picker(target, action, number=None):
    
    binary_codes = Generate_Code_List()
    
    if target == 'all':
        for i in range(len(binary_codes)):
            if binary_codes[i][2] == action:
                transmit_code(binary_codes[i][3])
                # time.sleep(0.2)

    else:
        for i in range(len(binary_codes)):
            if binary_codes[i][0] == target and binary_codes[i][1] == number and binary_codes[i][2] == action:
                try:
                    transmit_code(binary_codes[i][3])
                except:
                    pass
    return


def transmit_code(binary_code):
    NUM_ATTEMPTS = 30
    # Transmit a chosen code string using the GPIO transmitter

    code = str(binary_code[0])
    for t in range(NUM_ATTEMPTS):
        for i in code:
            if i == '1':
                GPIO.output(TRANSMIT_PIN, 1)
                time.sleep(binary_code[2])
                GPIO.output(TRANSMIT_PIN, 0)
                time.sleep(binary_code[4] - binary_code[2])
            elif i == '0':
                GPIO.output(TRANSMIT_PIN, 1)
                time.sleep(binary_code[3])
                GPIO.output(TRANSMIT_PIN, 0)
                time.sleep(binary_code[3] - binary_code[2])
            else:
                continue
        GPIO.output(TRANSMIT_PIN, 0)
        time.sleep(binary_code[1])
    GPIO.cleanup()
    return


def Generate_Code_List():
    binary_codes = []
    dir = __file__.strip("Telegram_Manager.py").strip(":") + "RF_Binary_Codes/Plugs-"

    for i in range(2):
        if i == 0:
            plug = 'Black'
        else:
            plug = "White"

        for file in os.walk(f"{dir}{plug}"):
            filelist = list(file[2])

            for file in filelist:
                with open(f"{dir}{plug}/{file}") as f:
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

    return binary_codes
