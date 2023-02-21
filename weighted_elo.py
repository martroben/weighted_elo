#################
# Load packages #
#################

import csv
import math
from statistics import mean
from collections import OrderedDict


#############
# Functions #
#############

def p_normal(x: float) -> float:
    """
    CDF of normal with standard deviation of std_dev_coefficient * sqrt(2).
    sqrt(2) comes from assuming that standard deviations of two players are equal,
    and we want to find the standard deviation of player 1 score - player 2 score.
    https://stackoverflow.com/questions/809362/how-to-calculate-cumulative-normal-distribution

    :param x: The variable. Usually difference in player scores in elo.
    :return: Value of the normal CDF at x.
    """
    global std_dev_coefficient
    standardized_x = x / (math.sqrt(2) * std_dev_coefficient)
    p = 1/2 * (1 + math.erf(standardized_x / math.sqrt(2)))
    return p


def p_logistic(x: float) -> float:
    """
    Calculates values of the logistic probability function
    aka CDF of Verhulst distribution.
    Uses the exponent base from log_base global variable
    and parameter from std_dev_coefficient global variables.

    :param x: The variable. Usually difference in player scores in elo.
    :return: Value of the logistic function at x.
    """
    global log_base
    global std_dev_coefficient
    p = 1 / (1 + log_base**(-x / std_dev_coefficient))
    return p


def get_expected_score_multiplayer(player: str, ratings: dict) -> float:
    """
    Get the expected score of a multiplayer game for a particular player
    based on all participants' current ratings

    :param player: name/indicator of the player to get the expected score for
    :param ratings: {player name: elo rating}
    :return: expected score for the input player
    """

    # Score differences for every match up combination
    score_differences_by_match_up = [ratings[player] - ratings[opponent]
                                     for opponent in ratings.keys() if opponent != player]

    expected_scores_by_match_up = [p_function(score_difference)
                                   for score_difference in score_differences_by_match_up]

    # Divide the score by the number of games so that they would sum to 1
    expected_score = sum(expected_scores_by_match_up) / math.comb(len(ratings), 2)
    return expected_score


def get_actual_scores_multiplayer(ranks: dict) -> dict:
    """
    Turns achieved ranks of a multiplayer game to multiplayer results.
    Results add up to 1 with the lowest value (loser) getting zero.

    :param ranks: {name: rank}. Winner has the lowest rank.
    :return: {name: multiplayer score}
    """
    # Order ranks to match up right keys and values later
    ordered_ranks = OrderedDict(sorted(ranks.items(), key=lambda x: x[1]))
    rank_vector = [i for i in ordered_ranks.values()]

    # Vector that indicates whether element n and n+1 are the same in rank vector
    ties_vector = [rank_vector[i] == rank_vector[i+1] for i in range(len(rank_vector) - 1)]

    # Get positions of elements with same scores
    pos = 0
    ties_intervals = []
    while pos < len(ties_vector):
        if ties_vector[pos]:
            slice_start = pos
            while pos < (len(ties_vector) - 1) and ties_vector[pos + 1]:
                pos += 1
            ties_intervals.append((slice_start, pos + 2))
        pos += 1

    # Create a vector of scores / multiplayer tournament outcomes
    scores_raw = list(reversed(range(len(rank_vector))))
    for interval in ties_intervals:
        draw_result = mean(scores_raw[slice(*interval)])
        scores_raw[slice(*interval)] = [draw_result for i in range(*interval)]

    # Normalize to sum to 1
    scores_normalized = [i / sum(scores_raw) for i in scores_raw]

    scores = dict(zip(ordered_ranks.keys(), scores_normalized))
    return scores


def get_rating_changes_multiplayer(ratings: dict, ranks: dict, game_points_coef: float) -> dict:
    """
    Get elo rating changes of a multiplayer game by initial ratings and outcome (player ranks) of the game.
    If there are only 2 players, returns standard 2-player elo result

    :param ratings: Player elo ratings. {player: rating}
    :param ranks: Ranks from the multiplayer game (lowest = winner). {player: rank}
    :param game_points_coef: Amount of points divided per game.
    :return: A dict with player names and resulting elo rating changes for each.
    """

    players = ranks.keys()
    initial_ratings = {player: ratings[player] for player in players}
    expected_scores = {player: get_expected_score_multiplayer(player, initial_ratings) for player in players}
    actual_scores = get_actual_scores_multiplayer(ranks)
    rating_changes_raw = {player: game_points_coef * (actual_scores[player] - expected_scores[player])
                          for player in players}

    # Rating changes are multiplied by the number of players in the multiplayer game - 1:
    # this is to take into account that winning a 20-person tournament is more impressive than 5-person tournament.
    rating_changes = {player: (len(players) - 1) * rating_changes_raw[player] for player in players}

    return rating_changes


def weight_function(weight: float, change: float = 0) -> float:
    """
    Function to modify weight according to weight value or weighted change value.

    :param weight: raw weight
    :param change: (Elo score) change that the weight is to be applied to.
    :return: Modified weight (to fit elo scoring).
    """
    # Currently a placeholder. Returns the input value (linear weighting).
    return weight


#############################
# Inputs & global variables #
#############################

csv_path = "/media/mart/Data/martroben/Projects/Python/weighted_elo/maxdiff_kaalutud.csv"

# Base of the logistic function (if p_function is logistic)
# sqrt(10) in traditional chess elo
log_base = math.sqrt(10)

# Coefficient to determine what kind of rating difference is impressive (has big effect on ratings)
# Represent the standard deviation of game outcomes
# C = 200 in traditional chess elo
std_dev_coefficient = 200

# Coefficient to determine how many rating points are awarded per game
# K = 32 in traditional chess elo
game_points_coefficient = 32

# Probability function to be used
# p_normal or p_logistic
# p_function = p_logistic in current chess elo
p_function = p_logistic

# Starting elo score for all unique poll reply options
elo_starting_score = 0


########################
# Import & format data #
########################

# Import and format csv
with open(csv_path) as data:
    reader = csv.DictReader(data)
    data_formatted = [{"i": row[""],
                       "best": row["best"],
                       "worst": row["worst"],
                       "all_options": [row["option1"], row["option2"], row["option3"], row["option4"], row["option5"]],
                       "weight": float(row["kaalud"])}
                      for row in reader]

# Drop rows where best or worst selections are not in presented options
defective_observation_indices = [row["i"] for row in data_formatted
                                 if row["best"] not in row["all_options"]
                                 or row["worst"] not in row["all_options"]]

data_cleaned = [row for row in data_formatted if row["i"] not in defective_observation_indices]

# Append a dictionary with ranks to each row (poll reply)
for row in data_cleaned:
    row["tied"] = [option for option in row["all_options"]
                   if option != row["best"]
                   and option != row["worst"]]

    row["ranks"] = {row["best"]: 1,
                    row["worst"]: len(row["all_options"]) + 1,
                    **{i: 2 for i in row["tied"]}}


###################
# Get elo ratings #
###################

# Get all unique reply options used in the poll
elo_ratings_initial = {}
for row in data_cleaned:
    for option in row["all_options"]:
        if option not in elo_ratings_initial:
            elo_ratings_initial[option] = elo_starting_score

# Get weighted elo ratings
elo_ratings = {key: value for key, value in elo_ratings_initial.items()}
for data_row in data_cleaned:
    rating_changes = get_rating_changes_multiplayer(elo_ratings, data_row["ranks"], game_points_coefficient)
    rating_changes_weighted = {option: weight_function(data_row["weight"], change) * change
                               for option, change in rating_changes.items()}
    for option in rating_changes_weighted.keys():
        elo_ratings[option] = elo_ratings[option] + rating_changes_weighted[option]

# Format output string
elo_ratings_sorted = dict(sorted(elo_ratings.items(), key=lambda x: x[1]))
elo_ratings_out = {key: round(value, 2) for key, value in elo_ratings_sorted.items()}
elo_ratings_out_string = "\n".join("{}: {}".format(key, value) for key, value in elo_ratings_out.items())
print(elo_ratings_out_string)


##################################
# Validate with mulitelo package #
##################################

# Validate results using the multielo package (should give the same results)
# pip install git+https://github.com/djcunningham0/multielo.git
from multielo import MultiElo

elo = MultiElo()
elo_ratings_multielo = {key: value for key, value in elo_ratings_initial.items()}

for row in data_cleaned:
    current_ratings = [elo_ratings_multielo[option] for option in row["ranks"].keys()]
    ranks = [rank for rank in row["ranks"].values()]
    new_ratings = elo.get_new_ratings(current_ratings, result_order=ranks)
    rating_changes = [i[1] - i[0] for i in zip(current_ratings, new_ratings)]
    rating_changes_weighted = [row["weight"] * rating_change for rating_change in rating_changes]
    new_ratings_weighted = [i[0] + i[1] for i in zip(current_ratings, rating_changes_weighted)]
    new_ratings_named = dict(zip(row["ranks"].keys(), new_ratings_weighted))
    for option, new_rating in new_ratings_named.items():
        elo_ratings_multielo[option] = new_rating

print(dict(sorted(elo_ratings_multielo.items(), key=lambda x: x[1])))


#####################################################
# Test linear approximation of weighing (tentative) #
#####################################################

# Iteratively applied elo ratings look logarithmic,
# therefore deviations from linear weighing are biggest at highest weights.

# Integer weights can be tested against the "true" weights:
# Eg. to get the result with true weight 2, apply elo rating function 2 times.

# 1. Test the theoretical maximum rating differences in using the different systems
# 2. Find the maximum rating change differences per single game/observation

test_ranks = {"winner": 1, "tie1": 2, "tie2": 2, "tie3": 2, "loser": 5}
option_max_occurrence = int(len(data_cleaned) / len(elo_ratings))
option_max_weight = 2      # Only integer values

# 1. Test how ratings may differ in linear weighing system vs true weighing system
# LINEAR:
sys_linear_ratings = {key: elo_starting_score for key in test_ranks.keys()}
sys_linear_winner_ratings = [sys_linear_ratings["winner"]]

for i in range(option_max_occurrence):
    sys_linear_rating_changes = get_rating_changes_multiplayer(sys_linear_ratings, test_ranks, game_points_coefficient)
    sys_linear_rating_changes_weighted = {option: option_max_weight * change
                                          for option, change in sys_linear_rating_changes.items()}
    for option in sys_linear_rating_changes_weighted.keys():
        sys_linear_ratings[option] = sys_linear_ratings[option] + sys_linear_rating_changes_weighted[option]

    sys_linear_winner_ratings.append(sys_linear_ratings["winner"])

# TRUE:
sys_true_ratings = {key: elo_starting_score for key in test_ranks.keys()}
sys_true_winner_ratings = [sys_true_ratings["winner"]]

for i in range(option_max_occurrence * option_max_weight):
    sys_true_rating_changes = get_rating_changes_multiplayer(sys_true_ratings, test_ranks, game_points_coefficient)
    for option in sys_true_rating_changes.keys():
        sys_true_ratings[option] = sys_true_ratings[option] + sys_true_rating_changes[option]

    if (i-1) % option_max_weight == 0:
        sys_true_winner_ratings.append(sys_true_ratings["winner"])

# DIFFERENCES:
weighing_system_differences = [i[1] - i[0] for i in zip(sys_true_winner_ratings, sys_linear_winner_ratings)]

# What is the maximum rating difference when using linear weights vs true weights?
max(weighing_system_differences)

# At how many consecutive wins is the difference greatest?
weighing_system_differences.index(max(weighing_system_differences)) + 1


# 2. Test rating changes brought on by a single observation: different starting ratings, linear vs true weights.
start_rating_differences = []
for option, score in elo_ratings.items():
    start_rating_differences += [abs(score - score2) for option2, score2 in elo_ratings.items() if option2 != option]
possible_rating_differences = list(range(int(max(start_rating_differences) + 1)))

# LINEAR:
obs_linear_rating_changes = []
for rating_difference in possible_rating_differences:
    obs_linear_rating_change = get_rating_changes_multiplayer(
        ratings={"winner": rating_difference, "loser": 0},
        ranks={"winner": 1, "loser": 2},
        game_points_coef=game_points_coefficient)
    obs_linear_rating_changes += [obs_linear_rating_change["winner"] * option_max_weight]

# TRUE:
obs_true_rating_changes = []
for rating_difference in possible_rating_differences:
    ratings = {"winner": rating_difference, "loser": 0}
    # Apply rating function option_max_weight times and get the total change
    for i in range(option_max_weight):
        rating_changes = get_rating_changes_multiplayer(ratings, {"winner": 1, "loser": 2}, game_points_coefficient)
        for key, value in rating_changes.items():
            ratings[key] = ratings[key] + value
    obs_true_rating_changes += [ratings["winner"] - rating_difference]

# DIFFERENCES:
# Differences in single observation when applying linear vs true weighing system to different start rating differences
per_observation_rating_change_differences = [i[1] - i[0] for i in zip(obs_true_rating_changes, obs_linear_rating_changes)]

# Maximum difference in changes of ratings produced by a single observation:
# different starting rating differences, linear vs true weighing
max(per_observation_rating_change_differences)

# Initial rating difference that produces the greatest difference
per_observation_rating_change_differences.index(max(per_observation_rating_change_differences))


##############
# Literature #
##############

# Arpad E. Elo: "The Rating of Chessplayers - Past & Present"
# https://www.gwern.net/docs/statistics/comparison/1978-elo-theratingofchessplayerspastandpresent.pdf

# Danny Cunningham: "Developing a Generalized Elo Rating System for Multiplayer Games" (Towards Data Science)
# https://towardsdatascience.com/developing-a-generalized-elo-rating-system-for-multiplayer-games-b9b495e87802

# Python MultiElo package:
# https://github.com/djcunningham0/multielo
