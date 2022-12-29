import time
import pyrc.comms as comms

def reason_will_prevail():
    comms.send_message('REASON WILL PREVAIL')
    return 


def timer():
    time.sleep(1)
    comms.send_message('3')
    time.sleep(1)
    comms.send_message('2')
    time.sleep(1)
    comms.send_message('1')
    time.sleep(1)
    comms.send_message('Go!')
    return


def throw_error():
    return 1/0


def parrot(message:str, nick:str):
    comms.send_message(message)
    comms.send_message(message, target=nick)
    return
