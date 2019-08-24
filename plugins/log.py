"""Log Plugin

Logs all input and output for recordkeeping purposes.
"""

import time
from pyaib.plugins import observe, plugin_class
from helpers import parse
from pprint import pprint
from helpers.database import DB
from helpers.config import CONFIG

@plugin_class('log')
class Log:
    def __init__(self, irc_c, config):
        print("Log Plugin Loaded!")

    # @observe('IRC_RAW_MSG')
    # def print_everything(self, irc_c, msg):
    #     print(msg)

    @observe('IRC_MSG_PRIVMSG','IRC_MSG_JOIN','IRC_MSG_PART','IRC_MSG_NICK')
    def log(self, irc_c, msg):
        print("OBSERVING",msg.kind)
        chname = "private" if msg.channel is None else msg.channel
        if msg.kind == 'PRIVMSG':
            print("[{}] {} <{}> {}".format(
                time.strftime("%H:%M:%S"),
                parse.nickColor(chname),
                parse.nickColor(msg.nick),
                msg.message))
        elif msg.kind == 'NICK':
            print("[{}] {} changed their name to {}".format(
                time.strftime("%H:%M:%S"),
                parse.nickColor(msg.nick),
                parse.nickColor(msg.args)))
        else:
            print("[{}] {} {} {}".format(
                time.strftime("%H:%M:%S"),
                parse.nickColor(msg.nick),
                "joined" if msg.kind == 'JOIN' else "left",
                parse.nickColor(chname)))
        try:
            DB.log_message(msg)
        except:
            irc_c.RAW("PRIVMSG #tars A logging error has occurred.")
            raise

    @observe('IRC_RAW_SEND')
    def debug(self, irc_c, msg):
        msg = parse.output(msg)
        if not msg:
            return
        print("[{}] --> {}: {}".format(
            time.strftime('%H:%M:%S'),
            parse.nickColor(msg['channel']),
            msg['message']
        ))
        if "IDENTIFY" in msg['message']: return
        msg = {'channel': msg['channel']
                          if msg['channel'].startswith('#')
                          else None,
               'sender': CONFIG.nick,
               'kind': "PRIVMSG",
               'message': msg['message'],
               'nick': CONFIG.nick,
               'timestamp': int(time.time())}
        try:
            DB.log_message(msg)
        except:
            irc_c.RAW("PRIVMSG #tars A logging error has occurred.")
            raise
