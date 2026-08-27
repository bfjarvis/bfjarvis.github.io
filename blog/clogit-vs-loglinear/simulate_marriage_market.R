# A wrapper and associated functions for building a simulated marriage market and matches.
#
# Main function:
# - simulate_marriage_market:
#    returns:
#     - data.frame of singles and their attributes
#     - data.frame of matched pairs
#     - data.frame containing utilities of all possible pairs
#     - list of input parameters.

# Functions called by main:
#  - rbeta_scaled : scaled draws from beta dist w/ specified min, max, and mean
#  - make_locations: create a grid
#  - make_actors: create agents with sex, group membership and randomly drawn ages.
#  - d2: calculate Euclidean distance between pairs of coordinates.
#  - locate_actors: assign agents to locations in a grid, with age and group clustering
#  - make_union_utilities: combinations of actors with match utility = f(age,group,proximity)
#  - make_unions: generate matches based on utilities using Gale-Shapley algorithm

library(dplyr)
library(tidyr)
library(matchingR)

rbeta_scaled <- function(n, mean, precision, min_value = 0, max_value = 1) {
  scaled_mean <- (mean - min_value) / (max_value - min_value)
  shape1 <- scaled_mean * precision
  shape2 <- (1 - scaled_mean) * precision
  min_value + (max_value - min_value) * rbeta(n, shape1, shape2)
}

make_locations <- function(n, relax = 1.2) {
  dim <- ceiling(relax * sqrt(n))
  expand_grid(
    x = (seq_len(dim) - .5) / dim,
    y = (seq_len(dim) - .5) / dim
  ) |>
    arrange(x, y) |>
    mutate(id_location = row_number()) |>
    select(id_location, x, y)
}

make_actors <- function(
  n,
  groups,
  group_shares,
  age_mean,
  age_min,
  age_max,
  age_concentration
) {
  G <- length(groups)
  group_shares <- group_shares / sum(group_shares)
  group_counts <- as.integer(n * group_shares)
  group_counts[G] <- n - sum(group_counts[-G])

  tibble(group = groups, age_mean, group_counts) |>
    reframe(
      age = rbeta_scaled(
        group_counts,
        age_mean,
        precision = age_concentration,
        min_value = age_min,
        max_value = age_max
      ),
      .by = c(group, age_mean)
    ) |>
    mutate(id = row_number()) |>
    group_by(group) |>
    mutate(sex = if_else(as.logical(row_number() %% 2), "man", "woman")) |>
    select(id, sex, group, age)
}

d2 <- function(x1, y1, x2, y2) {
  sqrt((x1 - x2)^2 + (y1 - y2)^2)
}

locate_actors <- function(
  actors,
  locations,
  poles,
  params
) {
  utilities <- actors |>
    select(id, group, age) |>
    crossing(locations) |>
    left_join(poles, by = c("group" = "pole")) |>
    mutate(
      x_youth = poles[poles$pole == "youth", ]$x_pole,
      y_youth = poles[poles$pole == "youth", ]$y_pole,
      scale_youth = (mean(age) - age) / sd(age),
      group_distance = log(d2(x, y, x_pole, y_pole) + 0.01),
      youth_distance = log(d2(x, y, x_youth, y_youth) + 0.01),
      utility = params$group *
        group_distance +
        params$youth * scale_youth * youth_distance
    ) |>
    ungroup() |>
    mutate(
      utility = utility +
        params$noise * rnorm(n(), mean = 0, sd = sd(utility))
    ) |>
    arrange(desc(utility))

  assigned_actors <- integer()
  assigned_locations <- integer()
  assignments <- vector("list", nrow(actors))
  n_assigned <- 0L

  for (r in seq_len(nrow(utilities))) {
    option <- utilities[r, ]
    if (
      option$id %in%
        assigned_actors ||
        option$id_location %in% assigned_locations
    ) {
      next
    }
    n_assigned <- n_assigned + 1L
    assignments[[n_assigned]] <- option |>
      select(id, id_location)
    assigned_actors <- c(assigned_actors, option$id)
    assigned_locations <- c(assigned_locations, option$id_location)
    if (n_assigned == nrow(actors)) {
      break
    }
  }

  actors |>
    select(id, sex, group, age) |>
    left_join(bind_rows(assignments), by = "id") |>
    left_join(locations, by = "id_location") |>
    select(-id_location)
}

rank_char <- function(x) {
  match(x, sort(unique(x), decreasing = TRUE))
}

make_union_utilities <- function(singles, params) {
  cross_join(
    singles |> filter(sex == "man") |> rename_with(\(x) paste0(x, "_man")),
    singles |> filter(sex == "woman") |> rename_with(\(x) paste0(x, "_woman"))
  ) |>
    mutate(
      age_gap = abs(age_man - age_woman),
      distance = d2(x_man, y_man, x_woman, y_woman),
      same_group = 1L * (group_man == group_woman),
      utility = params$same_group *
        same_group +
        params$rank_group * (rank_char(group_man) + rank_char(group_woman)) +
        params$age_gap * age_gap +
        params$distance * log(distance + 0.01),
      utility = utility + params$noise * rnorm(n(), mean = 0, sd = sd(utility))
    ) |>
    ungroup() |>
    arrange(id_man, id_woman)
}


make_unions <- function(union_utils) {
  utility_matrix <- xtabs(utility ~ id_woman + id_man, data = union_utils)

  unions <- matchingR::galeShapley.marriageMarket(
    proposerUtils = utility_matrix,
    reviewerUtils = t(utility_matrix)
  )

  tibble(
    id_man = as.integer(colnames(utility_matrix)),
    id_woman = as.integer(rownames(utility_matrix)[as.integer(
      unions$proposals
    )]),
    matched = TRUE
  )
}

simulate_marriage_market <- function(
  seed = 543,
  n = 1000,
  groups = c("a", "b", "c"),
  group_shares = c(60, 30, 10),
  age_mean = c(35, 30, 25),
  age_min = 18,
  age_max = 45,
  age_concentration = 2,
  location_relax = 1.2,
  location_poles = tibble(
    pole = c("a", "b", "c", "youth"),
    x_pole = c(0.5, 0.25, 0.75, 0.5),
    y_pole = c(0.75, 0.25, 0.25, 0.5)
  ),
  location_params = list(group = -1, youth = -1, noise = 3),
  partner_params = list(
    same_group = 1,
    rank_group = 0.5,
    age_gap = -0.1,
    distance = -1,
    noise = 0.5
  )
) {
  set.seed(seed)

  actors <- make_actors(
    n = n,
    groups = groups,
    group_shares = group_shares,
    age_mean = age_mean,
    age_min = age_min,
    age_max = age_max,
    age_concentration = age_concentration
  )
  locations <- make_locations(n, relax = location_relax)
  singles <- locate_actors(
    actors = actors,
    locations = locations,
    poles = location_poles,
    params = location_params
  )

  union_utils <- make_union_utilities(singles, params = partner_params)
  matches <- make_unions(union_utils)

  list(
    singles = singles,
    matches = matches |>
      select(id_man, id_woman),
    utilities = union_utils |>
      select(id_man, id_woman, utility),
    parameters = list(
      location = location_params,
      partner = partner_params,
      seed = seed,
      n = n,
      groups = groups,
      group_shares = group_shares,
      age_mean = age_mean,
      age_min = age_min,
      age_max = age_max,
      age_concentration = age_concentration,
      location_relax = location_relax,
      location_poles = location_poles
    )
  )
}
