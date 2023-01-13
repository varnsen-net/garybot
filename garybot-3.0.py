import time
import dotenv

# import environment variables
dotenv.load_dotenv()

# local modules 
import pyrc.comms as comms
import pyrc.parser as parser
import pyrc.logger as logger
import pyrc.handler as handler


def main():

    # make it dirty
    comms.connect_to_server()

    # my programming skills are VERY highly regarded 
    while True:

        raw_msg = comms.listen_for_msg()
        timestamp = time.time()
        # print(raw_msg, '\n')

        # stay connected to the server/channel
        comms.reconnect_if_disconnected(raw_msg)
        comms.rejoin_if_kicked(raw_msg)
        comms.ping_pong(raw_msg)

        # we are still connected. hella fresh. 
        message_payload = parser.parse(raw_msg, timestamp)

        if comms.received_exit_code(message_payload):
            comms.disconnect()
            break
        if comms.message_is_valid(message_payload):
            logger.log_msg(message_payload)
            handler.handler(message_payload)


main()

