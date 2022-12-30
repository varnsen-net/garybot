import os
import traceback
import time
import csv


# path config
_USER_LOGS_DIR = os.getenv("USER_LOGS_DIR")


def log_msg(nick:str, parsed:list[str]) -> None:
    """Write channel message to file."""
    with open(f"{_USER_LOGS_DIR}/{nick}.csv", "a+", newline="", encoding="utf-8") as log_ref:
        logwriter = csv.writer(log_ref)
        logwriter.writerow(parsed)
    return


def log_error() -> None:
    """Write error message to file."""
    error_timestamp = str(time.asctime())
    with open("./error-log.txt", "a+", encoding="utf-8") as error_log:
        error_log.write(error_timestamp + "\r\n")
        traceback.print_exc(file=error_log)
        error_log.write("\r\n")
    return
