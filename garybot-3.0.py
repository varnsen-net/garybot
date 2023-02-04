import time
import dotenv

# import environment variables
dotenv.load_dotenv()

# local modules 
import pyrc.startup
import pyrc.comms as comms
import pyrc.parser as parser
import pyrc.logger as logger
import pyrc.handler as handler


def main():

    # make it dirty
    client = comms.irc_client()
    client.connect_to_server()
    client.join_channel()

    # my programming skills are VERY highly regarded 
    while True:

        # listen and log
        raw_msg = client.listen_for_msg()
        timestamp = time.time()

        # stay connected to the server/channel
        client.reconnect_if_disconnected(raw_msg)
        client.rejoin_if_kicked(raw_msg)
        client.ping_pong(raw_msg)

        # we are still connected. hella fresh. 
        message_payload = parser.parse(raw_msg, timestamp)

        if client.received_exit_code(message_payload):
            client.close_existing_socket()
            break
        if client.message_is_valid(message_payload):
            logger.log_msg(message_payload)
            handler.handler(message_payload, client)


main()

