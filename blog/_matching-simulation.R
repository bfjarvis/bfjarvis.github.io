suppressPackageStartupMessages({
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(matchingR)
  library(mnorm)
})

group_colors <- c(a = "#c73535", b = "#555c60", c = "#287fc4")

scale_beta <- function(n, mean, precision, min_value = 0, max_value = 1) {
  shape1 <- mean * precision
  shape2 <- (1 - mean) * precision
  min_value + (max_value - min_value) * rbeta(n, shape1, shape2)
}

make_people <- function() {
  group_specs <- tibble(
    group = c("a", "b", "c"),
    age_mean = c(0.30, 0.50, 0.68),
    n = c(50, 30, 20)
  ) |>
    expand_grid(tibble(sex = c("man", "woman")))

  group_specs |>
    reframe(
      person = seq_len(n),
      age = scale_beta(n, age_mean, precision = 7, min_value = 18, max_value = 45),
      attractiveness = rnorm(n, mean = 0, sd = 0.35),
      .by = c(group, age_mean, sex)
    ) |>
    select(sex, group, age, attractiveness) |>
    ungroup() |>
    mutate(id = row_number())
}

make_candidate_positions <- function(n) {
  position_sequence <- halton(n = n, base = c(2, 3), start = 1L)

  tibble(
    position_id = seq_len(n),
    x = position_sequence[, 1],
    y = position_sequence[, 2]
  )
}

group_attractors <- tibble(
  group = c("a", "b", "c"),
  group_x = c(0.35, 0.50, 0.65),
  group_y = c(0.35, 0.65, 0.35)
)

youth_attractor <- tibble(
  label = "younger singles",
  x = 0.50,
  y = 0.50
)

assign_positions <- function(people, noise_scale = 1) {
  candidate_positions <- make_candidate_positions(nrow(people))

  spatial_utilities <- people |>
    select(id, group, age) |>
    crossing(candidate_positions) |>
    left_join(group_attractors, by = "group") |>
    mutate(
      youth_x = youth_attractor$x,
      youth_y = youth_attractor$y,
      youth_pull = (45 - age) / (45 - 18),
      group_distance = log(sqrt((x - group_x)^2 + (y - group_y)^2) + 0.01),
      youth_distance = log(sqrt((x - youth_x)^2 + (y - youth_y)^2) + 0.01),
      utility = -1 * group_distance - 2 * youth_pull * youth_distance
    ) |>
    ungroup() |>
    mutate(utility = utility + noise_scale * rnorm(n(), mean = 0, sd = sd(utility))) |>
    mutate(
      preference_rank = min_rank(desc(utility)),
      tie_break = runif(n()),
      .by = id
    ) |>
    arrange(preference_rank, desc(tie_break))

  assigned_people <- integer()
  assigned_locations <- integer()
  assignments <- vector("list", nrow(people))
  n_assigned <- 0L

  for (row_index in seq_len(nrow(spatial_utilities))) {
    option <- spatial_utilities[row_index, ]

    if (option$id %in% assigned_people || option$position_id %in% assigned_locations) {
      next
    }

    n_assigned <- n_assigned + 1L
    assignments[[n_assigned]] <- option |>
      select(id, position_id)

    assigned_people <- c(assigned_people, option$id)
    assigned_locations <- c(assigned_locations, option$position_id)

    if (n_assigned == nrow(people)) {
      break
    }
  }

  people |>
    left_join(bind_rows(assignments), by = "id") |>
    left_join(candidate_positions, by = "position_id") |>
    select(-position_id)
}

simulate_actors_and_locations <- function(seed = 543) {
  set.seed(seed)

  singles <- make_people() |>
    assign_positions()

  list(
    singles = singles,
    men = filter(singles, sex == "man"),
    women = filter(singles, sex == "woman"),
    candidate_positions = make_candidate_positions(nrow(singles)),
    group_attractors = group_attractors,
    youth_attractor = youth_attractor
  )
}

preference_weights <- list(
  same_group = 0.5,
  age_gap = -0.1,
  distance = -1,
  attractiveness = 1,
  noise = 2
)

make_utilities <- function(choosers, candidates, weights = preference_weights) {
  choosers |>
    rename_with(\(x) paste0("chooser_", x)) |>
    mutate(.join_key = 1L) |>
    inner_join(
      candidates |>
        rename_with(\(x) paste0("candidate_", x)) |>
        mutate(.join_key = 1L),
      by = ".join_key",
      relationship = "many-to-many"
    ) |>
    transmute(
      chooser_id = chooser_id,
      candidate_id = candidate_id,
      chooser_group = chooser_group,
      candidate_group = candidate_group,
      same_group = chooser_group == candidate_group,
      age_gap = abs(chooser_age - candidate_age),
      distance = sqrt((chooser_x - candidate_x)^2 + (chooser_y - candidate_y)^2),
      candidate_attractiveness = candidate_attractiveness,
      utility =
        weights$same_group * as.numeric(same_group) +
        weights$age_gap * age_gap +
        weights$distance * log(distance + 0.01) +
        weights$attractiveness * candidate_attractiveness
    ) |>
    group_by(chooser_group) |>
    mutate(utility = utility + weights$noise * rnorm(n(), mean = 0, sd = sd(utility))) |>
    ungroup()
}

make_utility_matrix <- function(utilities, row_ids, column_ids) {
  utility_matrix <- matrix(
    NA_real_,
    nrow = length(row_ids),
    ncol = length(column_ids),
    dimnames = list(row_ids, column_ids)
  )

  utility_matrix[
    cbind(match(utilities$candidate_id, row_ids), match(utilities$chooser_id, column_ids))
  ] <- utilities$utility

  utility_matrix
}

match_partners <- function(men, women) {
  men_to_women <- make_utilities(men, women)
  women_to_men <- make_utilities(women, men)

  man_ids <- men$id
  woman_ids <- women$id

  male_utilities <- make_utility_matrix(
    utilities = men_to_women,
    row_ids = woman_ids,
    column_ids = man_ids
  )

  female_utilities <- make_utility_matrix(
    utilities = women_to_men,
    row_ids = man_ids,
    column_ids = woman_ids
  )

  matching <- galeShapley.marriageMarket(
    proposerUtils = male_utilities,
    reviewerUtils = female_utilities
  )

  matches <- tibble(
    man_id = man_ids,
    woman_id = woman_ids[as.integer(matching$proposals)]
  )

  matched_pairs <- matches |>
    left_join(men |> rename_with(\(x) paste0("man_", x)), by = c("man_id" = "man_id")) |>
    left_join(women |> rename_with(\(x) paste0("woman_", x)), by = c("woman_id" = "woman_id")) |>
    mutate(
      same_group = 1L * (man_group == woman_group),
      age_gap = abs(man_age - woman_age),
      distance = sqrt((man_x - woman_x)^2 + (man_y - woman_y)^2)
    )

  list(
    men_to_women = men_to_women,
    women_to_men = women_to_men,
    male_utilities = male_utilities,
    female_utilities = female_utilities,
    matching = matching,
    matches = matches,
    matched_pairs = matched_pairs
  )
}

all_possible_pairs <- function(men, women) {
  cross_join(men, women, suffix = c("_man", "_woman")) |>
    mutate(
      distance = sqrt((x_man - x_woman)^2 + (y_man - y_woman)^2),
      same_group = 1L * (group_man == group_woman),
      age_gap = abs(age_man - age_woman)
    )
}

make_choice_sets <- function(men, women, matched_pairs) {
  all_possible_pairs(men, women) |>
    transmute(
      chooser_id = id_man,
      candidate_id = id_woman,
      chooser_group = group_man,
      candidate_group = group_woman,
      same_group = 1L * (group_man == group_woman),
      age_gap,
      distance,
      choice = paste(id_man, id_woman) %in% paste(matched_pairs$man_id, matched_pairs$woman_id)
    )
}

group_pair_counts <- function(matched_pairs) {
  matched_pairs |>
    count(man_group, woman_group, name = "n") |>
    complete(man_group, woman_group, fill = list(n = 0)) |>
    mutate(same_group = 1L * (man_group == woman_group))
}
