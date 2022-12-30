#!/usr/bin/python3
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

        # we are still connected. yay!
        ident, nick, target, message, command, word_count, word_list = parser.parse(raw_msg)

        if comms.received_exit_code(target, nick, message):
            comms.disconnect()
            break
        if comms.message_is_valid(target, word_count, nick, command):
            # the string at [4] is empty because this script used to log the
            # full param string, but that has since changed. TODO fix
            parsed = [ident, nick, target, message, '', timestamp]
            logger.log_msg(nick, parsed)
            handler.handler(nick, message, word_list)
            # try:
                # # auto-replies
                # autoreplies.autoResponses(msg, irc)

                # # arb replies
                # if msg.message.startswith(irc.botnick):
                    # threading.Thread(target=irc.runAndSend, args=(chanfcn_dict['.arb'], msg, irc)).start()

                # # call channel-specific functions
                # trigger = msg.word_list[0]
                # if trigger in chanfcn_keys:
                    # threading.Thread(target=irc.runAndSend, args=(chanfcn_dict[trigger], msg, irc)).start()
            # except:
                # irc.logError()
                # irc.sendMsg("gary, there's been an error.", irc.adminnick)


main()

