
pverhulst <- function(x, base, coefficient) {
  1 / (1 + base^(-x / coefficient))
}

dverhulst <- function(x, base, coefficient) {
  log(base) * base^(-x / coefficient) / (1 + base^(-x / coefficient))^2 / coefficient
}

log_base <<- sqrt(10)
coefficient <<- 200
max_points <<- 32

curve(pverhulst(x, sqrt(10), 200), from = -1000, to = 1000)

pverhulst(32, sqrt(10), 200)

elo <- function(player_rating, opponent_rating, result) {
  stopifnot(result %in% c(0, 0.5, 1))
  
  rating_difference <- player_rating - opponent_rating
  expected_result <- pverhulst(rating_difference, .GlobalEnv$log_base, .GlobalEnv$coefficient)
  updated_player_rating <- player_rating + .GlobalEnv$max_points * (result - expected_result)
  return (updated_player_rating)
}

elo(0, 0, 1)
elo(16, -16, 1)
elo(30.5305, -30.5305, 1)
elo(43.74714, -43.74714, 1)
elo(55.80095, -55.80095, 1)
elo(66.83125, -66.83125, 1)
elo(76.96257, -76.96257, 1)
elo(86.3041, -86.3041, 1)
elo(94.95047, -94.95047, 1)
elo(102.9832, -102.9832, 1)


player_score <- c(2000)
opponent_score <- c(2000)
for (i in 1:10000) {
  player_score <- c(player_score, elo(player_score[length(player_score)], opponent_score[length(opponent_score)], 1))
  opponent_score <- c(opponent_score, elo(opponent_score[length(opponent_score)], player_score[length(player_score)], 0))
}

plot(player_score)

