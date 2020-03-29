"""parse.py

Provides functions for parsing and formatting stuff into other stuff.
"""

import argparse
import re
import shlex

from helpers.config import CONFIG
from helpers.error import CommandError, ArgumentMessage

def parse_commands(irc_c, message):
    """Takes a message object and returns a list of parsed commands."""
    submessages = [m.strip() for m in message.message.split("&&")]
    return [ParsedCommand(irc_c, message, m) for m in submessages]

class ParsedCommand():
    """Object representing a single command"""
    def __init__(self, irc_c, msg, message):
        """msg is the pyaib message object
        message is the text of the message"""
        self.sender = msg.sender # nick of issuing user
        self.channel = msg.raw_channel # channel to which message was sent
        self.raw = str(message) # the original message
        self.ping = False # was the bot pinged?
        self.command = None # if command, then the command name
        self.message = None # message text excluding ping and command name
        self.args = {} # argparse Namespace object
        self.force = False # whether to bypass defer
        self.context = irc_c

        # Was someone pinged?
        pattern = re.compile(r"""
            ^                          # Start of message
            ([A-Z0-9\\\[\]\^_-{\|}]+)  # Ping, including allowed chars
            [,:]+                      # Colon or comma to denote ping
            \s*                        # Whitespace between ping and message
            (.*)                       # Message body
            $                          # End of message
        """, (re.IGNORECASE, re.VERBOSE))
        match = pattern.search(self.raw)
        if match:
            # Remove ping from the message
            self.message = match.group(2).strip()
            ping = match.group(1).strip()
            if ping.lower() == CONFIG.nick.lower():
                self.ping = True
        else:
            # nobody was pinged
            self.message = self.raw

        # What was the command?
        pattern = r"""
            ^                  # Start of command
            (?P<signal>        # Punctuation to denote command (signal)
                [!\.]{{{},2}}  # Amount of required signal depends on ping
            )                  # End signal group
            (?P<cmd>           # Command name
                [^!\.\s]+      # Any character but not signal or whitespace
            )                  # End command name group
            (?P<rest>.*)       # Rest of the command (arguments)
            $"""
        if self.ping:
            # If the bot was pinged, do not require a signal
            pattern = pattern.format(0)
        else:
            # If the bot was not pinged, require a signal
            pattern = pattern.format(1)
        pattern = re.compile(pattern, re.VERBOSE)
        match = pattern.search(self.message)
        if match:
            # Remove command from the message
            self.command = match.group('cmd').strip().lower()
            self.message = match.group('rest').strip()
            # if >1 punctuation used, override defer
            if len(match.group('signal')) > 1:
                self.force = True

    def __contains__(self, arg):
        """Allows cmd.hasarg via the `in` operator"""
        return arg in self.args

    def __getitem__(self, arg):
        """Allows cmd.getarg via the [] operator"""
        return self.args['arg']

    def expandargs(self, arglist):
        parser = ArgumentParser(prog=arglist.pop(0),
                                formatter_class=HelpFormatter)
        # arglist is a list of arguments like ["--longname", "--ln", "-l"]

        # TODO TODO TODO
        # Regardless of input make the nargs * and then manually validate
        # afterwards with more verbose error messages
        # TODO TODO TODO
        # XXX old parser woz ere
        # remove apostrophes because they'll fuck with shlex
        self.message = self.message.replace("'", "<<APOS>>")
        self.message = self.message.replace('\\"', "<<QUOT>>") # explicit \"
        try:
            self.message = shlex.split(self.message, posix=False)
            # posix=False does not remove quotes
            for i,word in enumerate(self.message):
                if word.startswith('"') and word.endswith('"'):
                    self.message[i] = word[1:-1]
        except ValueError:
            # raised if shlex detects fucked up quotemarks
            # self.message = self.message.split()
            raise CommandError("Unmatched quotemark. Use \\\" to escape a "
                               "literal quotemark.")
        self.message = [w.replace("<<APOS>>", "'") for w in self.message]
        self.message = [w.replace("<<QUOT>>", '"') for w in self.message]
        try:
            self.args = parser.parse_args(self.message)
        except ArgumentMessage as e:
            raise CommandError(str(e))
        # now validate the args against the nargs that were actually provided
        for arg in arglist:
            argname = (arg[2][2:], arg[-1][1:])
            print(self.args, argname)
            value = getattr(self.args, argname[0])
            err_start = "When using the {} option (--{}{}), {{}}".format(
                argname[0], argname[0],
                "/-{}".format(argname[1]) if len(argname[1]) == 1 else "")
            if arg[1] == '*':
                # all good!
                pass
            elif arg[1] == '+' and len(value) <= 1:
                raise CommandError(err_start.format(
                    "at least one argument should be specified"))
            elif arg[1] is None:
                if len(value) != 1:
                    raise CommandError(err_start.format(
                        "exactly one argument should be specified"))
                setattr(self.args, argname[0], value[0])
            elif arg[1] is 0 and len(value) != 0:
                raise CommandError(err_start.format(
                    "no arguments should be specified"))
            elif isinstance(arg[1], (int, float)) and len(value) != arg[1]:
                raise CommandError(err_start.format(
                    "exactly {} arguments should be specified".format(arg[1])))
            else:
                raise CommandError(err_start.format(
                    "the correct number of arguments must be provided"))

        print(vars(self.args))

# Parse a nick to its IRCCloud colour
def nickColor(string, html=False):
    length = 27
    colours =      [180,220,216,209,208,
                     46, 11,143,113, 77,
                    108, 71, 79, 37, 80,
                     14, 39,117, 75, 69,
                    146,205,170,213,177,
                     13,217]
    html_colours = ['#b22222','#d2691e','#ff9166','#fa8072','#ff8c00',
                    '#228b22','#808000','#b7b05d','#8ebd2e','#2ebd2e',
                    '#82b482','#37a467','#57c8a1','#1da199','#579193',
                    '#008b8b','#00bfff','#4682b4','#1e90ff','#4169e1',
                    '#6a5acd','#7b68ee','#9400d3','#8b008b','#ba55d3',
                    '#ff00ff','#ff1493']

    def t(x):
        x &= 0xFFFFFFFF
        if x > 0x7FFFFFFF:
            x -= 0x100000000
        return float(x)

    bytes = string.lower()
    bytes = re.sub(r"^#", "", bytes)
    bytes = re.sub(r"[`_]+$", "", bytes)
    bytes = re.sub(r"\|.*$", "", bytes)
    bytes = bytes.encode('utf-16-le')
    hash = 0.0
    for i in range(0, len(bytes), 2):
        char_code = bytes[i] + 256*bytes[i+1]
        hash = char_code + t(int(hash) << 6) + t(int(hash) << 16) - hash
    index = int(hash % length if hash >= 0 else abs(hash % length - length))
    index = index % length
    if html:
        return html_colours[index]
    else:
        return "\x1b[38;5;{}m{}\x1b[0m".format(colours[index], string)

def output(output):
    """Takes an output message from plugins/log.py"""
    output = str(output)
    pattern = r"(?P<kind>[A-Z]+) (?P<ch>\S+) :(?P<message>.*)"
    match = re.match(pattern, output)
    if not match:
        return None
    msg = {}
    #if match.group('ch')[0] == '#':
    #    msg['channel'] = match.group('ch')
    #else:
    #    msg['channel'] = "private"
    #    msg['nick'] = match.group('ch')
    msg['channel'] = match.group('ch')
    msg['message'] = match.group('message')
    return msg
