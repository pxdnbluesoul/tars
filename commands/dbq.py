"""dbq.py

Database Query commands for checking the database.
"""

import string
from pprint import pprint
from datetime import datetime
from helpers.error import CommandError
from helpers.parse import nickColor
from helpers.database import DB
from helpers.defer import defer

class query:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        cmd.expandargs(["table tables t",
                        "user users u"])
        # No argument given - show the db structure
        if len(cmd.args) == 1:
            msg.reply("https://raw.githubusercontent.com/"
                      "rossjrw/tars/master/database.png")
            return
        # Table - print a list of tables, or a given table
        if 'table' in cmd:
            if len(cmd['table']) > 0:
                # print a specific table
                msg.reply("Printing contents of table {} to console."
                          .format(cmd['table'][0]))
                DB.print_one_table(cmd['table'][0])
            else:
                # print a list of all tables
                tables = DB.get_all_tables()
                msg.reply("Printed a list of tables to console. {} total."
                          .format(len(tables)))
                print(" ".join(tables))
        # Users - print a list of users, or from a given channel
        if 'user' in cmd:
            users = DB.get_all_users()
            if len(users) == 0:
                msg.reply("There are no users.")
            else:
                msg.reply("Printed a list of users to console. {} total."
                          .format(len(users)))
                print(" ".join([nickColor(u) for u in users]))
        if 'id' in cmd:
            # we want to find the id of something
            if len(cmd.args['root']) != 2:
                search = msg.sender
            else:
                search = cmd.args['root'][1]
            id,type = DB.get_generic_id(search)
            if id:
                if type == 'user' and search == msg.sender:
                    msg.reply("{}, your ID is {}.".format(msg.sender, id))
                elif search == "TARS":
                    msg.reply("My ID is {}.".format(id))
                else:
                    msg.reply("{}'s ID is {}.".format(search, id))
            else:
                if type == 'channel':
                    msg.reply("I don't know the channel '{}'."
                             .format(search))
                else:
                    msg.reply("I don't know anything called '{}'."
                              .format(search))
        if 'alias' in cmd:
            search = cmd.args['root'][1] if len(cmd.args['root']) > 1 \
                                         else msg.sender
            aliases = DB.get_aliases(search)
            # should be None or a list of lists
            if aliases is None:
                msg.reply("I don't know anyone with the alias '{}'."
                          .format(search))
            else:
                msg.reply("I know {} users with the alias '{}'."
                          .format(len(aliases), search))
                for i,group in enumerate(aliases):
                    msg.reply("\x02{}.\x0F {}"
                              .format(i+1, ", ".join(group)))
        if 'occ' in cmd:
            if len(cmd.args['root']) < 2:
                raise CommandError("Specify a channel to get the occupants of")
            msg.reply("Printing occupants of {} to console"
                      .format(cmd.args['root'][1]))
            users = DB.get_occupants(cmd.args['root'][1], True)
            if isinstance(users[0], int):
                pprint(users)
            else:
                pprint([nickColor(user) for user in users])
        if 'sql' in cmd:
            if not defer.controller(cmd):
                raise CommandError("I'm afriad I can't let you do that.")
            try:
                DB.print_selection(" ".join(cmd['sql']))
                msg.reply("Printing that selection to console")
            except:
                msg.reply("There was a problem with the selection")
                raise
