import os
import traceback
import time
import csv


# path config
_USER_LOGS_DIR = os.getenv("USER_LOGS_DIR")


def log_msg(message_payload:dict) -> None:
    """Write channel message to file."""
    # the string at [4] is empty because this script used to log the
    # full param string, but that has since changed. TODO fix
    row = [message_payload['ident'],
           message_payload['nick'],
           message_payload['target'],
           message_payload['message'],
           '',
           message_payload['timestamp']]
    path = f"{_USER_LOGS_DIR}/{message_payload['nick']}.csv"
    with open(path, "a+", newline="", encoding="utf-8") as log_ref:
        logwriter = csv.writer(log_ref)
        logwriter.writerow(row)
    return


def log_error() -> None:
    """Write error message to file."""
    error_timestamp = str(time.asctime())
    with open("./error-log.txt", "a+", encoding="utf-8") as error_log:
        error_log.write(error_timestamp + "\r\n")
        traceback.print_exc(file=error_log)
        error_log.write("\r\n")
    return
