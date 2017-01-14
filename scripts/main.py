#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Julian Schrittwieser"

from Board import Board
from Player import Player
from Game import Game
from Constants import TOKEN
from Constants import ADMIN
from Constants import players

import random
from random import randrange
from time import sleep
import re
import sys
import requests

import telebot
from telebot import types
import logging as log

log.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', filename='../logging.log', level=log.DEBUG)


def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            print(str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text.encode('utf-8'))


bot = telebot.TeleBot(TOKEN)
bot.set_update_listener(listener)
bot.skip_pending = True
games = {}

commands = [  # command description used in the "help" command
                '/help - Gives you information about the available commands',
                '/start - Gives you a short piece of information about Secret Hitler',
                '/symbols - Shows you all possible symbols of the board',
                '/rules - Gives you a link to the official Secret Hitler rules',
                '/newgame - Creates a new game',
                '/join - Joins an existing game',
                '/startgame - Starts an existing game when all players have joined',
                '/cancelgame - Cancels an existing game. All data of the game will be lost',
                '/board - Prints the current board with fascist and liberals tracks, presidential order and election counter'
]

symbols = [
                u"\u25FB\uFE0F" + ' Empty field without special power',
                u"\u2716\uFE0F" + ' Field covered with a card',  # X
                u"\U0001F52E" + ' Presidential Power: Policy Peek', # crystal
                u"\U0001F50E" + ' Presidential Power: Investigate Loyalty', # inspection glass
                u"\U0001F5E1" + ' Presidential Power: Execution', # knife
                u"\U0001F454" + ' Presidential Power: Call Special Election', #tie
                u"\U0001F54A" + ' Liberals win', #dove
                u"\u2620" + ' Fascists win' #skull
]

@bot.message_handler(commands=['symbols'])
def command_info(message):
    cid = message.chat.id
    symbol_text = "The following symbols can appear on the board: \n"
    for i in symbols:
        symbol_text += i + "\n"
    bot.send_message(cid, symbol_text)

@bot.message_handler(commands=['board'])
def command_board(message):
    cid = message.chat.id
    if cid in games.keys():
        if games[cid].board is not None:
            bot.send_message(cid, games[cid].board.print_board())
        else:
            bot.send_message(cid, "There is no running game in this chat. Please start the game with /startgame")
    else:
        bot.send_message(cid, "There is no game in this chat. Create a new game with /newgame")


@bot.message_handler(commands=['start'])
def command_info(message):
    bot.send_message(message.chat.id,
                     "\"Secret Hitler is a social deduction game for 5-10 people about finding and stopping the Secret Hitler."
                     " The majority of players are liberals. If they can learn to trust each other, they have enough "
                     "votes to control the table and win the game. But some players are fascists. They will say whatever "
                     "it takes to get elected, enact their agenda, and blame others for the fallout. The liberals must "
                     "work together to discover the truth before the fascists install their cold-blooded leader and win "
                     "the game.\"\n- official description of Secret Hitler\n\nAdd me to a group and type /newgame to create a game!")
    command_help(message)

@bot.message_handler(commands=['rules'])
def command_rules(message):
    rulesMarkup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Rules", url="http://www.secrethitler.com/assets/Secret_Hitler_Rules.pdf")
    rulesMarkup.add(btn)
    bot.send_message(message.chat.id, "Read the official Secret Hitler rules:", reply_markup=rulesMarkup)

# pings PiBooth, only ADMIN
@bot.message_handler(commands=['ping'])
def command_clear(message):
    cid = message.chat.id
    bot.send_message(cid, 'pong')

# help page
@bot.message_handler(commands=['help'])
def command_help(message):
    cid = message.chat.id
    help_text = "The following commands are available:\n"
    for i in commands:
        help_text += i + "\n"
    bot.send_message(cid, help_text)

@bot.message_handler(commands=['newgame'])
def command_newgame(message):
    global game
    cid = message.chat.id
    if message.chat.type == 'group':
        if cid not in games.keys():
            games[cid] = Game(cid, message.from_user.id)
            bot.send_message(cid,
                             "New game created! Each player has to /join the game.\nThe initiator of this game can /join too and type /startgame when everyone has joined the game!")
        else:
            bot.send_message(cid, "There is currently a game running. If you want to end it please type /cancelgame!")
    else:
        bot.send_message(cid, "You have to add me to a group first and type /newgame there!")


@bot.message_handler(commands=['join'])
def command_join(message):
    group_name = message.chat.title
    cid = message.chat.id
    if message.chat.type == 'group':
        if cid in games.keys():
            game = games[cid]
            uid = message.from_user.id
            fname = message.from_user.first_name
            if uid not in game.playerlist:
                if len(game.playerlist) < 10:
                    player = Player(fname, uid)
                    try:
                        bot.send_message(uid,
                                         "You joined a game in %s. I will soon tell you your secret role." % group_name)
                        game.add_player(uid, player)
                        if len(game.playerlist) > 4:
                            bot.send_message(game.cid,
                                             fname + " has joined the game. Type /startgame if this was the last player and you want to start with %d players!" % len(game.playerlist))
                        else:
                            if len(game.playerlist) == 1:
                                bot.send_message(game.cid, "%s has joined the game. There is currently %d player in the game and you need 5-10 players." % (fname, len(game.playerlist)))
                            else:
                                bot.send_message(game.cid, "%s has joined the game. There are currently %d players in the game and you need 5-10 players."  % (fname, len(game.playerlist)))
                    except Exception:
                        bot.send_message(game.cid,
                                         fname + ", I can\'t send you a private message. Please go to @thesecrethitlerbot and click \"Start\".\nYou then need to send /join again.")
                else:
                    bot.send_message(game.cid,
                                     "You have reached the maximum amount of players. Please start the game with /startgame!")
            else:
                bot.send_message(game.cid, "You already joined the game, %s!" % fname)
        else:
            bot.send_message(cid, "There is no game in this chat. Create a new game with /newgame")
    else:
        bot.send_message(cid, "You have to add me to a group first and type /newgame there!")


@bot.message_handler(commands=['startgame'])
def command_startgame(message):
    log.info('command_startgame called')
    cid = message.chat.id
    if cid in games.keys():
        game = games[cid]
        if message.from_user.id == game.initiator:
            player_number = len(game.playerlist)
            if player_number > 4:
                inform_players(game, game.cid, player_number)
                inform_fascists(game, player_number)
                game.board = Board(player_number, game)
                game.shuffle_player_sequence()
                game.board.state.player_counter = 0
                bot.send_message(game.cid, game.board.print_board())
                #bot.send_message(ADMIN, "Game of Secret Hitler started in group %d" % cid)
                start_round(game)
            else:
                bot.send_message(game.cid, "There are not enough players (min. 5, max. 10). Join the game with /join")
        else:
            bot.send_message(game.cid, "Only the initiator of the game can start the game with /startgame")
    else:
        bot.send_message(message.chat.id, "There is no game in this chat. Create a new game with /newgame")


@bot.message_handler(commands=['cancelgame'])
def command_cancelgame(message):
    cid = message.chat.id
    if cid in games.keys():
        game = games[cid]
        if message.from_user.id == game.initiator:
            end_game(game, 99)
        else:
            bot.send_message(game.cid, "Only the initiator of the game can cancel the game with /cancelgame")
    else:
        bot.send_message(message.chat.id, "There is no game in this chat. Create a new game with /newgame")


##
#
# Beginning of round
#
##

def start_round(game):
    log.info('start_round called')
    if game.board.state.chosen_president is None:
        game.board.state.nominated_president = game.player_sequence[game.board.state.player_counter]
    else:
        game.board.state.nominated_president = game.board.state.chosen_president
        game.board.state.chosen_president = None
    bot.send_message(game.cid,
                     "The next presidential canditate is %s.\n%s, please nominate a Chancellor in our private chat!" % (game.board.state.nominated_president.name, game.board.state.nominated_president.name))
    choose_chancellor(game)
    # --> nominate_chosen_chancellor --> vote --> handle_voting --> count_votes --> voting_aftermath --> draw_policies
    # --> choose_policy --> pass_two_policies --> choose_policy --> enact_policy --> start_round


def choose_chancellor(game):
    log.info('choose_chancellor called')
    chancellorMarkup = types.InlineKeyboardMarkup()
    strcid = str(game.cid)
    pres_uid = 0
    chan_uid = 0
    if game.board.state.president is not None:
        pres_uid = game.board.state.president.uid
    if game.board.state.chancellor is not None:
        chan_uid = game.board.state.chancellor.uid
    for uid in game.playerlist:
        # If there are only five players left in the
        # game, only the last elected Chancellor is
        # ineligible to be Chancellor Candidate; the
        # last President may be nominated.
        if len(game.player_sequence) > 5:
            if uid != game.board.state.nominated_president.uid and game.playerlist[uid].is_dead == False and uid != pres_uid and uid != chan_uid:
                name = game.playerlist[uid].name
                btn = types.InlineKeyboardButton(name, callback_data=strcid + "_chan_" + str(uid))
                chancellorMarkup.add(btn)
        else:
            if uid != game.board.state.nominated_president.uid and game.playerlist[uid].is_dead == False and uid != chan_uid:
                name = game.playerlist[uid].name
                btn = types.InlineKeyboardButton(name, callback_data=strcid + "_chan_" + str(uid))
                chancellorMarkup.add(btn)
    bot.send_message(game.board.state.nominated_president.uid, game.board.print_board())
    bot.send_message(game.board.state.nominated_president.uid, 'Please nominate your chancellor!',
                     reply_markup=chancellorMarkup)


@bot.callback_query_handler(lambda q: re.match("(-[0-9]*)_chan_(.*)", q.data))
def nominate_chosen_chancellor(callback):
    log.info('nominate_chosen_chancellor called')
    regex = re.search("(-[0-9]*)_chan_([0-9]*)", callback.data)
    cid = int(regex.group(1))
    chosen_uid = int(regex.group(2))
    game = games[cid]
    game.board.state.nominated_chancellor = game.playerlist[chosen_uid]
    bot.edit_message_text("You nominated %s as Chancellor!" % game.board.state.nominated_chancellor.name,
                          callback.from_user.id, callback.message.message_id)
    bot.send_message(game.cid,
                     "President %s nominated %s as Chancellor. Please vote now!" % (game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name))
    vote(game)


def vote(game):
    log.info('vote called')
    strcid = str(game.cid)
    voteMarkup = types.InlineKeyboardMarkup()
    jabtn = types.InlineKeyboardButton("Ja", callback_data=strcid + "_Ja")
    neinbtn = types.InlineKeyboardButton("Nein", callback_data=strcid + "_Nein")
    voteMarkup.add(jabtn)
    voteMarkup.add(neinbtn)
    for uid in game.playerlist:
        if not game.playerlist[uid].is_dead:
            if game.playerlist[uid] is not game.board.state.nominated_president:
                # the nominated president already got the board before nominating a chancellor
                bot.send_message(uid, game.board.print_board())
            bot.send_message(uid,
                             "Do you want to elect President %s and Chancellor %s?" % (game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name),
                             reply_markup=voteMarkup)


@bot.callback_query_handler(lambda q: re.match("(-[0-9]*)_(Ja|Nein)", q.data))
def handle_voting(callback):
    log.info('handle_voting called')
    regex = re.search("(-[0-9]*)_(.*)", callback.data)
    cid = int(regex.group(1))
    answer = regex.group(2)
    game = games[cid]
    uid = callback.from_user.id
    bot.edit_message_text("Thank you for your vote: %s to a President %s and a Chancellor %s" % (answer, game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name), uid, callback.message.message_id)
    if game is not None:
        if uid not in game.board.state.last_votes:
            game.board.state.last_votes[uid] = answer
        if len(game.board.state.last_votes) == len(game.player_sequence):
            count_votes(game)
    else:
        bot.send_message(game.cid, "Error. Game should not be None!")


def count_votes(game):
    log.info('count_votes called')
    voting_text = ""
    voting_success = False
    for player in game.player_sequence:
        if game.board.state.last_votes[player.uid] == "Ja":
            voting_text += game.playerlist[player.uid].name + " voted Ja!\n"
        elif game.board.state.last_votes[player.uid] == "Nein":
            voting_text += game.playerlist[player.uid].name + " voted Nein!\n"
    if list(game.board.state.last_votes.values()).count("Ja") > len(
            game.player_sequence) / 2:  # because player_sequence doesnt include dead
        #VOTING WAS SUCCESSFUL
        voting_text += "Hail President %s! Hail Chancellor %s!" % (game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
        game.board.state.chancellor = game.board.state.nominated_chancellor
        game.board.state.president = game.board.state.nominated_president
        game.board.state.nominated_president = None
        game.board.state.nominated_chancellor = None
        voting_success = True
        bot.send_message(game.cid, voting_text)
        voting_aftermath(game, voting_success)
    else:
        voting_text += "The people didn't like the two candidates!"
        game.board.state.nominated_president = None
        game.board.state.nominated_chancellor = None
        game.board.state.failed_votes += 1
        if game.board.state.failed_votes == 3:
            do_anarchy(game)
        else:
            bot.send_message(game.cid, voting_text)
            voting_aftermath(game, voting_success)


def voting_aftermath(game, voting_success):
    log.info('voting_aftermath called')
    game.board.state.last_votes = {}
    if voting_success:
        if game.board.state.fascist_track >= 3 and game.board.state.chancellor.role == "Hitler":
            # fascists win, because Hitler was elected as chancellor after 3 fascist policies
            game.board.state.game_endcode = -2
            end_game(game, game.board.state.game_endcode)
        elif game.board.state.fascist_track >= 3 and game.board.state.chancellor.role != "Hitler" and game.board.state.chancellor not in game.board.state.not_hitlers:
                game.board.state.not_hitlers.append(game.board.state.chancellor)
                draw_policies(game)
        else:
            # voting was successful and Hitler was not nominated as chancellor after 3 fascist policies
            draw_policies(game)
    else:
        bot.send_message(game.cid, game.board.print_board())
        start_next_round(game)


def draw_policies(game):
    log.info('draw_policies called')
    strcid = str(game.cid)
    game.board.state.veto_refused = False
    # shuffle discard pile with rest if rest < 3
    shuffle_policy_pile(game)
    for i in range(3):
        game.board.state.drawn_policies.append(game.board.policies.pop(0))
    choosePolicyMarkup = types.InlineKeyboardMarkup()
    for policy in game.board.state.drawn_policies:
        btn = types.InlineKeyboardButton(policy, callback_data=strcid + "_" + policy)
        choosePolicyMarkup.add(btn)
    bot.send_message(game.board.state.president.uid,
                     "You drew the following 3 policies. Which one do you want to discard?",
                     reply_markup=choosePolicyMarkup)


@bot.callback_query_handler(lambda q: re.match("(-[0-9]*)_(liberal|fascist|veto)", q.data))
def choose_policy(callback):
    log.info('choose_policy called')
    regex = re.search("(-[0-9]*)_(.*)", callback.data)
    cid = int(regex.group(1))
    answer = regex.group(2)
    game = games[cid]
    strcid = str(game.cid)
    uid = callback.from_user.id
    if game is not None:
        if len(game.board.state.drawn_policies) == 3:
            bot.edit_message_text("The policy %s will be discarded!" % answer, uid,
                                  callback.message.message_id)
            # remove policy from drawn cards and add to discard pile, pass the other two policies
            for i in range(3):
                if game.board.state.drawn_policies[i] == answer:
                    game.board.discards.append(game.board.state.drawn_policies.pop(i))
                    break
            pass_two_policies(game)
        elif len(game.board.state.drawn_policies) == 2:
            if answer == "veto":
                bot.edit_message_text("You suggested a Veto to President %s" % game.board.state.president.name, uid,
                                      callback.message.message_id)
                bot.send_message(game.cid,
                                 "Chancellor %s suggested a Veto to President %s." % (game.board.state.chancellor.name, game.board.state.president.name))
                vetoMarkup = types.InlineKeyboardMarkup()
                vetoyes = types.InlineKeyboardButton("Veto! (accept suggestion)", callback_data=strcid + "_yesveto")
                vetono = types.InlineKeyboardButton("No Veto! (refuse suggestion)", callback_data=strcid + "_noveto")
                vetoMarkup.add(vetoyes)
                vetoMarkup.add(vetono)
                bot.send_message(game.board.state.president.uid,
                                 "Chancellor %s suggested a Veto to you. Do you want to veto (discard) these cards?" % game.board.state.chancellor.name,
                                 reply_markup=vetoMarkup)
            else:
                bot.edit_message_text("The policy %s will be enacted!" % answer, uid,
                                      callback.message.message_id)
                # remove policy from drawn cards and enact, discard the other card
                for i in range(2):
                    if game.board.state.drawn_policies[i] == answer:
                        game.board.state.drawn_policies.pop(i)
                        break
                game.board.discards.append(game.board.state.drawn_policies.pop(0))
                assert len(game.board.state.drawn_policies) == 0
                enact_policy(game, answer, False)
        else:
            bot.send_message(game.cid, "Error. drawn_policies should be 3 oder 2, but was " + str(
                len(game.board.state.drawn_policies)))
    else:
        bot.send_message(game.cid, "Error. Game should not be None!")


def pass_two_policies(game):
    choosePolicyMarkup = types.InlineKeyboardMarkup()
    strcid = str(game.cid)
    for policy in game.board.state.drawn_policies:
        btn = types.InlineKeyboardButton(policy, callback_data=strcid + "_" + policy)
        choosePolicyMarkup.add(btn)
    if game.board.state.fascist_track == 5 and not game.board.state.veto_refused:
        btn = types.InlineKeyboardButton("Veto", callback_data=strcid + "_veto")
        choosePolicyMarkup.add(btn)
        bot.send_message(game.board.state.chancellor.uid,
                         "President %s gave you the following 2 policies. Which one do you want to enact? You can also use your Veto power." % game.board.state.president.name,
                         reply_markup=choosePolicyMarkup)
    elif game.board.state.veto_refused:
        bot.send_message(game.board.state.chancellor.uid,
                         "President %s refused your Veto. Now you have to choose. Which one do you want to enact?" % game.board.state.president.name,
                         reply_markup=choosePolicyMarkup)
    elif game.board.state.fascist_track < 5:
        bot.send_message(game.board.state.chancellor.uid,
                         "President %s gave you the following 2 policies. Which one do you want to enact?" % game.board.state.president.name,
                         reply_markup=choosePolicyMarkup)


def enact_policy(game, policy, anarchy):
    log.info('enact_policy called')
    if policy == "liberal":
        game.board.state.liberal_track += 1
    elif policy == "fascist":
        game.board.state.fascist_track += 1
    game.board.state.failed_votes = 0  # reset counter
    if not anarchy:
        bot.send_message(game.cid,
                         "President %s and Chancellor %s enacted a %s policy!" % (game.board.state.president.name, game.board.state.chancellor.name, policy))
    else:
        bot.send_message(game.cid,
                         "The top most policy was enacted: %s" % policy)
    bot.send_message(game.cid, game.board.print_board())
    # end of round
    if game.board.state.liberal_track == 5:
        game.board.state.game_endcode = 1
        end_game(game, game.board.state.game_endcode)  # liberals win with 5 liberal policies
    if game.board.state.fascist_track == 6:
        game.board.state.game_endcode = -1
        end_game(game, game.board.state.game_endcode)  # fascists win with 6 fascist policies

    if not anarchy:
        if policy == "fascist":
            action = game.board.fascist_track_actions[game.board.state.fascist_track - 1]
            if action is None and game.board.state.fascist_track == 6:
                pass
            elif action == None:
                start_next_round(game)
            elif action == "policy":
                bot.send_message(game.cid,
                                 "Presidential Power enabled: Policy Peek " + u"\U0001F52E" + "\nPresident " + game.board.state.president.name + " now knows the next three policies on "
                                                                                                                                                 "the pile.  The President may share "
                                                                                                                                                 "(or lie about!) the results of their "
                                                                                                                                                 "investigation at their discretion.")
                action_policy(game)
            elif action == "kill":
                bot.send_message(game.cid,
                                 "Presidential Power enabled: Execution " + u"\U0001F5E1" + "\nPresident " + game.board.state.president.name + " has to kill one person. You can "
                                                                                                                                               "discuss the decision now but the "
                                                                                                                                               "President has the final say.")
                action_kill(game)
            elif action == "inspect":
                bot.send_message(game.cid,
                                 "Presidential Power enabled: Investigate Loyalty " + u"\U0001F50E" + "\nPresident " + game.board.state.president.name + " may see the party membership of one "
                                                                                                                                                         "player. The President may share "
                                                                                                                                                         "(or lie about!) the results of their "
                                                                                                                                                         "investigation at their discretion.")
                action_inspect(game)
            elif action == "choose":
                bot.send_message(game.cid,
                                 "Presidential Power enabled: Call Special Election " + u"\U0001F454" + "\nPresident " + game.board.state.president.name + " gets to choose the next presidential "
                                                                                                                                                           "candidate. Afterwards the order resumes "
                                                                                                                                                           "back to normal.")
                action_choose(game)
        else:
            start_next_round(game)
    else:
        start_next_round(game)


@bot.callback_query_handler(lambda q: re.match("(-[0-9]*)_(yesveto|noveto)", q.data))
def choose_veto(callback):
    log.info('choose_veto called')
    regex = re.search("(-[0-9]*)_(.*)", callback.data)
    cid = int(regex.group(1))
    answer = regex.group(2)
    game = games[cid]
    uid = callback.from_user.id
    if game is not None:
        if answer == "yesveto":
            bot.edit_message_text("You accepted the Veto!", uid, callback.message.message_id)
            bot.send_message(game.cid,
                             "President %s accepted Chancellor %s's Veto. No policy was enacted but this counts as a failed election." % (game.board.state.president.name, game.board.state.chancellor.name))
            game.board.discards += game.board.state.drawn_policies
            game.board.state.drawn_policies = []
            game.board.state.failed_votes += 1
            if game.board.state.failed_votes == 3:
                do_anarchy(game)
            else:
                bot.send_message(game.cid, game.board.print_board())
                start_next_round(game)
        elif answer == "noveto":
            game.board.state.veto_refused = True
            bot.edit_message_text("You refused the Veto!", uid, callback.message.message_id)
            bot.send_message(game.cid,
                             "President %s refused Chancellor %s's Veto. The Chancellor now has to choose a policy!" % (game.board.state.president.name, game.board.state.chancellor.name))
            pass_two_policies(game)
        else:
            bot.send_message(game.cid,
                             "Error. Callback data can either be \"veto\" or \"noveto\", but not %s" % answer)
    else:
        bot.send_message(game.cid, "Error. Game should not be None!")


def do_anarchy(game):
    log.info('do_anarchy called')
    bot.send_message(game.cid, game.board.print_board())
    bot.send_message(game.cid, "ANARCHY!!")
    top_policy = game.board.policies.pop(0)
    game.board.state.last_votes = {}
    enact_policy(game, top_policy, True)


def action_policy(game):
    log.info('action_policy called')
    topPolicies = ""
    # shuffle discard pile with rest if rest < 3
    shuffle_policy_pile(game)
    for i in range(3):
        topPolicies += game.board.policies[i] + "\n"
    bot.send_message(game.board.state.president.uid,
                     "The top three polices are (top most first):\n%s\nYou may lie about this." % topPolicies)
    start_next_round(game)


def action_kill(game):
    log.info('action_kill called')
    strcid = str(game.cid)
    killMarkup = types.InlineKeyboardMarkup()
    for uid in game.playerlist:
        if uid != game.board.state.president.uid and game.playerlist[uid].is_dead == False:
            name = game.playerlist[uid].name
            btn = types.InlineKeyboardButton(name, callback_data=strcid + "_kill_" + str(uid))
            killMarkup.add(btn)
    bot.send_message(game.board.state.president.uid, game.board.print_board())
    bot.send_message(game.board.state.president.uid,
                     'You have to kill one person. You can discuss your decision with the others. Choose wisely!',
                     reply_markup=killMarkup)


@bot.callback_query_handler(lambda q: re.match("(-[0-9]*)_kill_(.*)", q.data))
def choose_kill(callback):
    log.info('choose_kill called')
    regex = re.search("(-[0-9]*)_kill_(.*)", callback.data)
    cid = int(regex.group(1))
    answer = int(regex.group(2))
    game = games[cid]
    chosen = game.playerlist[answer]
    chosen.is_dead = True
    if game.player_sequence.index(chosen) <= game.board.state.player_counter:
        game.board.state.player_counter -= 1
    game.player_sequence.remove(chosen)
    game.board.state.dead += 1
    bot.edit_message_text("You killed %s!" % chosen.name, callback.from_user.id, callback.message.message_id)
    if chosen.role == "Hitler":
        bot.send_message(game.cid, "President " + game.board.state.president.name + " killed " + chosen.name + ". ")
        end_game(game, 2)
    else:
        bot.send_message(game.cid,
                         "President %s killed %s who was not Hitler. %s, you are dead now and are not allowed to talk anymore!" % (game.board.state.president.name,  chosen.name, chosen.name))
        bot.send_message(game.cid, game.board.print_board())
        start_next_round(game)


def action_choose(game):
    log.info('action_choose called')
    strcid = str(game.cid)
    inspectMarkup = types.InlineKeyboardMarkup()
    for uid in game.playerlist:
        if uid != game.board.state.president.uid and game.playerlist[uid].is_dead == False:
            name = game.playerlist[uid].name
            btn = types.InlineKeyboardButton(name, callback_data=strcid + "_choo_" + str(uid))
            inspectMarkup.add(btn)
    bot.send_message(game.board.state.president.uid, game.board.print_board())
    bot.send_message(game.board.state.president.uid,
                     'You get to choose the next presidential candidate. Afterwards the order resumes back to normal. Choose wisely!',
                     reply_markup=inspectMarkup)


@bot.callback_query_handler(lambda q: re.match("(-[0-9]*)_choo_(.*)", q.data))
def choose_choose(callback):
    log.info('choose_choose called')
    regex = re.search("(-[0-9]*)_choo_(.*)", callback.data)
    cid = int(regex.group(1))
    answer = int(regex.group(2))
    game = games[cid]
    chosen = game.playerlist[answer]
    game.board.state.chosen_president = chosen
    bot.edit_message_text("You chose %s as the next president!" % chosen.name, callback.from_user.id,
                          callback.message.message_id)
    bot.send_message(game.cid,
                     "President %s chose %s as the next president." % (game.board.state.president.name, chosen.name))
    start_next_round(game)


def action_inspect(game):
    log.info('action_inspect called')
    strcid = str(game.cid)
    inspectMarkup = types.InlineKeyboardMarkup()
    for uid in game.playerlist:
        if uid != game.board.state.president.uid and game.playerlist[uid].is_dead == False:
            name = game.playerlist[uid].name
            btn = types.InlineKeyboardButton(name, callback_data=strcid + "_insp_" + str(uid))
            inspectMarkup.add(btn)
    bot.send_message(game.board.state.president.uid, game.board.print_board())
    bot.send_message(game.board.state.president.uid,
                     'You may see the party membership of one player. Which do you want to know? Choose wisely!',
                     reply_markup=inspectMarkup)


@bot.callback_query_handler(lambda q: re.match("(-[0-9]*)_insp_(.*)", q.data))
def choose_inspect(callback):
    log.info('choose_inspect called')
    regex = re.search("(-[0-9]*)_insp_(.*)", callback.data)
    cid = int(regex.group(1))
    answer = int(regex.group(2))
    game = games[cid]
    chosen = game.playerlist[answer]
    bot.edit_message_text("The party membership of %s is %s" % (chosen.name, chosen.party), callback.from_user.id,
                          callback.message.message_id)
    bot.send_message(game.cid, "President %s inspected %s." % (game.board.state.president.name, chosen.name))
    start_next_round(game)


def start_next_round(game):
    log.info('start_next_round called')
    # start next round if there is no winner (or /cancel)
    if game.board.state.game_endcode == 0:
        # start new round
        sleep(3)
        # if there is no special elected president in between
        if game.board.state.chosen_president is None:
            increment_player_counter(game)
        start_round(game)


##
#
# End of round
#
##

def end_game(game, game_endcode):
    log.info('end_game called')
    ##
    # game_endcode:
    #   -2  fascists win by electing Hitler as chancellor
    #   -1  fascists win with 6 fascist policies
    #   0   not ended
    #   1   liberals win with 5 liberal policies
    #   2   liberals win by killing Hitler
    #   99  game cancelled
    #

    if game_endcode == -2:
        bot.send_message(game.cid,
                         "Game over! The fascists win by electing Hitler as Chancellor!\n\n%s" % game.print_roles())
    if game_endcode == -1:
        bot.send_message(game.cid,
                         "Game over! The fascists win by enacting 6 fascist policies!\n\n%s" % game.print_roles())
    if game_endcode == 1:
        bot.send_message(game.cid,
                         "Game over! The liberals win by enacting 5 liberal policies!\n\n%s" % game.print_roles())
    if game_endcode == 2:
        bot.send_message(game.cid,
                         "Game over! The liberals win by killing Hitler!\n\n%s" % game.print_roles())
    if game_endcode == 99:
        if games[game.cid] is not None:
            bot.send_message(game.cid,
                            "Game cancelled!\n\n%s" % game.print_roles())
        else:
            bot.send_message(game.cid, "Game cancelled!")
    del games[game.cid]


def inform_players(game, cid, player_number):
    log.info('inform_players called')
    bot.send_message(cid, "Let's start the game with %d players!\n%s\nGo to your private chat and look at your secret role!" % (player_number, print_player_info(player_number)))
    available_roles = list(players[player_number]["roles"])  # copy not reference because we need it again later
    for uid in game.playerlist:
        random_index = randrange(len(available_roles))
        role = available_roles.pop(random_index)
        party = get_membership(role)
        game.playerlist[uid].role = role
        game.playerlist[uid].party = party
        bot.send_message(uid, "Your secret role is: %s\nYour party membership is: %s" % (role, party))

def print_player_info(player_number):
    if player_number == 5:
        return "There are 3 Liberals, 1 Fascist and Hitler. Hitler knows who the Fascist is."
    elif player_number == 6:
        return "There are 4 Liberals, 1 Fascist and Hitler. Hitler knows who the Fascist is."
    elif player_number == 7:
        return "There are 4 Liberals, 2 Fascist and Hitler. Hitler doesn't know who the Fascists are."
    elif player_number == 8:
        return "There are 5 Liberals, 2 Fascist and Hitler. Hitler doesn't know who the Fascists are."
    elif player_number == 9:
        return "There are 5 Liberals, 3 Fascist and Hitler. Hitler doesn't know who the Fascists are."
    elif player_number == 10:
        return "There are 6 Liberals, 3 Fascist and Hitler. Hitler doesn't know who the Fascists are."

def inform_fascists(game, player_number):
    log.info('inform_fascists called')
    if player_number == 5 or player_number == 6:
        for uid in game.playerlist:
            role = game.playerlist[uid].role
            if role == "Hitler":
                fascists = game.get_fascists()
                if len(fascists) > 1:
                    bot.send_message(uid, "Error. There should be only one Fascist in a 5/6 player game!")
                else:
                    bot.send_message(uid, "Your fellow fascist is: %s" % fascists[0].name)
            elif role == "Fascist":
                hitler = game.get_hitler()
                bot.send_message(uid, "Hitler is: %s" % hitler.name)
            elif role == "Liberal":
                pass
            else:
                bot.send_message(uid, "Error: can\'t handle the role %s" % role)

    else:
        for uid in game.playerlist:
            role = game.playerlist[uid].role
            if role == "Fascist":
                fascists = game.get_fascists()
                if len(fascists) == 1:
                    bot.send_message(uid, "Error: There should be more than one Fascist in a 7/8/9/10 player game!")
                else:
                    fstring = ""
                    for f in fascists:
                        if f.uid != uid:
                            fstring += f.name + ", "
                    fstring = fstring[:-2]
                    bot.send_message(uid, "Your fellow fascists are: %s" % fstring)
                    hitler = game.get_hitler()
                    bot.send_message(uid, "Hitler is: %s" % hitler.name)
            elif role == "Hitler":
                pass
            elif role == "Liberal":
                pass
            else:
                bot.send_message(uid, "Error: can\'t handle the role %s" % role)


def get_membership(role):
    log.info('get_membership called')
    if role == "Fascist" or role == "Hitler":
        return "fascist"
    elif role == "Liberal":
        return "liberal"
    else:
        return None


def increment_player_counter(game):
    log.info('increment_player_counter called')
    if game.board.state.player_counter < len(game.player_sequence) - 1:
        game.board.state.player_counter += 1
    else:
        game.board.state.player_counter = 0


def shuffle_policy_pile(game):
    log.info('shuffle_policy_pile called')
    if len(game.board.policies) < 3:
        game.board.discards += game.board.policies
        game.board.policies = random.sample(game.board.discards, len(game.board.discards))
        game.board.discards = []
        bot.send_message(game.cid, "There were not enough cards left on the policy pile so I shuffled the rest with the discard pile!")

while True:
    try:
        bot.polling(none_stop=True)
    except requests.exceptions.ReadTimeout as e:
        print >> sys.stderr, str(e)
        sleep(5)
    except requests.exceptions.ConnectionError as e:
        print >> sys.stderr, str(e)
        sleep(5)
