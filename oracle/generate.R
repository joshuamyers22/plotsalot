options(
  repos = c(CRAN = "https://cloud.r-project.org"),
  digits = 17,
  warn = 2
)

expected_revision <- Sys.getenv("GGSTATSPLOT_REVISION")
package_metadata <- utils::packageDescription("ggstatsplot")
installed_revision <- package_metadata$RemoteSha

if (!identical(installed_revision, expected_revision)) {
  stop(
    "ggstatsplot revision mismatch: expected ", expected_revision,
    ", installed ", installed_revision
  )
}

input_dir <- "/work/oracle/fixtures/input"
output_dir <- "/work/oracle/fixtures/r-output"
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

fixture_names <- c("normal", "null-containing", "small-sample")
normalized <- vector("list", length(fixture_names))

for (index in seq_along(fixture_names)) {
  fixture_name <- fixture_names[[index]]
  input_path <- file.path(input_dir, paste0(fixture_name, ".csv"))
  input <- utils::read.csv(input_path, na.strings = c("", "NA"))
  values <- input$value
  analyzed <- values[!is.na(values)]
  test_value <- unique(input$test_value)
  conf_level <- unique(input$conf_level)

  if (length(test_value) != 1L || length(conf_level) != 1L) {
    stop("fixture parameters must be constant: ", fixture_name)
  }

  plot <- ggstatsplot::gghistostats(
    data = input,
    x = value,
    type = "parametric",
    test.value = test_value,
    alternative = "two.sided",
    conf.level = conf_level,
    bf.message = FALSE,
    centrality.plotting = FALSE
  )
  extracted <- ggstatsplot::extract_stats(plot)$subtitle_data
  if (is.null(extracted) || nrow(extracted) != 1L) {
    stop("ggstatsplot did not retain one subtitle result row: ", fixture_name)
  }
  dput(
    extracted,
    file = file.path(output_dir, paste0(fixture_name, "-ggstatsplot.R")),
    control = c("keepNA", "keepInteger", "niceNames")
  )

  test <- stats::t.test(
    analyzed,
    mu = test_value,
    alternative = "two.sided",
    conf.level = conf_level
  )
  normalized[[index]] <- data.frame(
    fixture = fixture_name,
    input_rows = length(values),
    analyzed_rows = extracted$n.obs[[1L]],
    dropped_null_rows = sum(is.na(values)),
    test_value = test_value,
    conf_level = conf_level,
    mean = mean(analyzed),
    standard_deviation = stats::sd(analyzed),
    statistic = extracted$statistic[[1L]],
    df = extracted$df.error[[1L]],
    p_value = extracted$p.value[[1L]],
    interval_low = unname(test$conf.int[[1L]]),
    interval_high = unname(test$conf.int[[2L]]),
    cohen_d = (mean(analyzed) - test_value) / stats::sd(analyzed),
    upstream_effect_name = extracted$effectsize[[1L]],
    upstream_effect_estimate = extracted$estimate[[1L]],
    upstream_effect_interval_low = extracted$conf.low[[1L]],
    upstream_effect_interval_high = extracted$conf.high[[1L]],
    upstream_effect_interval_method = extracted$conf.method[[1L]],
    stringsAsFactors = FALSE
  )
}

utils::write.csv(
  do.call(rbind, normalized),
  file.path(output_dir, "normalized-results.csv"),
  row.names = FALSE,
  na = "NA"
)

boundary_names <- c("non-finite", "degenerate")
boundary_results <- lapply(boundary_names, function(fixture_name) {
  input_path <- file.path(input_dir, paste0(fixture_name, ".csv"))
  input <- utils::read.csv(input_path, na.strings = c("", "NA"))
  outcome <- tryCatch(
    {
      suppressWarnings(
        ggstatsplot::gghistostats(
          data = input,
          x = value,
          type = "parametric",
          test.value = unique(input$test_value),
          alternative = "two.sided",
          conf.level = unique(input$conf_level),
          bf.message = FALSE,
          centrality.plotting = FALSE
        )
      )
      list(status = "accepted", condition_class = NA_character_)
    },
    error = function(condition) {
      list(status = "rejected", condition_class = class(condition)[[1L]])
    }
  )
  data.frame(
    fixture = fixture_name,
    status = outcome$status,
    condition_class = outcome$condition_class,
    stringsAsFactors = FALSE
  )
})
utils::write.csv(
  do.call(rbind, boundary_results),
  file.path(output_dir, "boundary-results.csv"),
  row.names = FALSE,
  na = "NA"
)

# M2 labeled-dot fixture -------------------------------------------------------

dot_input <- utils::read.csv(
  file.path(input_dir, "m2-dot.csv"),
  na.strings = c("", "NA")
)
dot_plot <- ggstatsplot::ggdotplotstats(
  data = dot_input,
  x = value,
  y = label,
  type = "parametric",
  test.value = 0,
  alternative = "two.sided",
  conf.level = 0.95,
  bf.message = FALSE,
  centrality.plotting = FALSE
)
dput(
  ggstatsplot::extract_stats(dot_plot),
  file = file.path(output_dir, "m2-dot-ggstatsplot.R"),
  control = c("keepNA", "keepInteger", "niceNames")
)

dot_complete <- dot_input[stats::complete.cases(dot_input), , drop = FALSE]
dot_labels <- unique(dot_complete$label)
dot_rows <- lapply(dot_labels, function(label) {
  values <- dot_complete$value[dot_complete$label == label]
  interval <- stats::t.test(values, conf.level = 0.95)$conf.int
  data.frame(
    record = "label",
    label = label,
    input_rows = sum(dot_input$label == label, na.rm = TRUE),
    analyzed_rows = length(values),
    dropped_null_rows = sum(dot_input$label == label & is.na(dot_input$value), na.rm = TRUE),
    mean = mean(values),
    standard_deviation = stats::sd(values),
    statistic = NA_real_,
    df = length(values) - 1L,
    p_value = NA_real_,
    interval_low = unname(interval[[1L]]),
    interval_high = unname(interval[[2L]]),
    stringsAsFactors = FALSE
  )
})
dot_overall_test <- stats::t.test(dot_complete$value, mu = 0, conf.level = 0.95)
dot_overall <- data.frame(
  record = "overall",
  label = NA_character_,
  input_rows = nrow(dot_input),
  analyzed_rows = nrow(dot_complete),
  dropped_null_rows = nrow(dot_input) - nrow(dot_complete),
  mean = mean(dot_complete$value),
  standard_deviation = stats::sd(dot_complete$value),
  statistic = unname(dot_overall_test$statistic),
  df = unname(dot_overall_test$parameter),
  p_value = dot_overall_test$p.value,
  interval_low = unname(dot_overall_test$conf.int[[1L]]),
  interval_high = unname(dot_overall_test$conf.int[[2L]]),
  stringsAsFactors = FALSE
)
utils::write.csv(
  do.call(rbind, c(list(dot_overall), dot_rows)),
  file.path(output_dir, "m2-dot-results.csv"),
  row.names = FALSE,
  na = "NA"
)

# M2 Pearson scatter and matrix fixture ---------------------------------------

correlation_input <- utils::read.csv(
  file.path(input_dir, "m2-correlation.csv"),
  na.strings = c("", "NA")
)
scatter_plot <- ggstatsplot::ggscatterstats(
  data = correlation_input,
  x = x,
  y = y,
  type = "parametric",
  conf.level = 0.95,
  bf.message = FALSE,
  marginal = FALSE
)
dput(
  ggstatsplot::extract_stats(scatter_plot),
  file = file.path(output_dir, "m2-scatter-ggstatsplot.R"),
  control = c("keepNA", "keepInteger", "niceNames")
)
matrix_plot <- ggstatsplot::ggcorrmat(
  data = correlation_input,
  cor.vars = c(x, y, z),
  type = "parametric",
  conf.level = 0.95,
  p.adjust.method = "holm"
)
dput(
  ggstatsplot::extract_stats(matrix_plot),
  file = file.path(output_dir, "m2-corrmat-ggstatsplot.R"),
  control = c("keepNA", "keepInteger", "niceNames")
)

correlation_columns <- c("x", "y", "z")
pair_indices <- utils::combn(seq_along(correlation_columns), 2L)
correlation_rows <- lapply(seq_len(ncol(pair_indices)), function(index) {
  left <- correlation_columns[[pair_indices[1L, index]]]
  right <- correlation_columns[[pair_indices[2L, index]]]
  complete <- stats::complete.cases(correlation_input[, c(left, right)])
  test <- stats::cor.test(
    correlation_input[[left]][complete],
    correlation_input[[right]][complete],
    method = "pearson",
    alternative = "two.sided",
    conf.level = 0.95
  )
  data.frame(
    x = left,
    y = right,
    n_obs = sum(complete),
    estimate = unname(test$estimate),
    statistic = unname(test$statistic),
    df = unname(test$parameter),
    p_value = test$p.value,
    interval_low = unname(test$conf.int[[1L]]),
    interval_high = unname(test$conf.int[[2L]]),
    stringsAsFactors = FALSE
  )
})
correlation_results <- do.call(rbind, correlation_rows)
correlation_results$adjusted_p_value <- stats::p.adjust(
  correlation_results$p_value,
  method = "holm"
)
utils::write.csv(
  correlation_results,
  file.path(output_dir, "m2-correlation-results.csv"),
  row.names = FALSE,
  na = "NA"
)

# M3 independent comparison fixture ------------------------------------------

between_input <- utils::read.csv(file.path(input_dir, "m3-between.csv"))
between_input$group <- factor(between_input$group, levels = sort(unique(between_input$group)))
between_plot <- ggstatsplot::ggbetweenstats(
  data = between_input,
  x = group,
  y = value,
  type = "parametric",
  pairwise.display = "all",
  p.adjust.method = "holm",
  bf.message = FALSE,
  centrality.plotting = FALSE
)
dput(
  ggstatsplot::extract_stats(between_plot),
  file = file.path(output_dir, "m3-between-ggstatsplot.R"),
  control = c("keepNA", "keepInteger", "niceNames")
)

between_omnibus <- stats::oneway.test(
  value ~ group,
  data = between_input,
  var.equal = FALSE
)
between_pairs <- utils::combn(levels(between_input$group), 2L, simplify = FALSE)
between_pair_rows <- lapply(between_pairs, function(pair) {
  left <- between_input$value[between_input$group == pair[[1L]]]
  right <- between_input$value[between_input$group == pair[[2L]]]
  test <- stats::t.test(left, right, var.equal = FALSE, conf.level = 0.95)
  data.frame(
    record = "pairwise",
    left = pair[[1L]],
    right = pair[[2L]],
    statistic = unname(test$statistic),
    df1 = NA_real_,
    df2 = unname(test$parameter),
    p_value = test$p.value,
    estimate = mean(left) - mean(right),
    interval_low = unname(test$conf.int[[1L]]),
    interval_high = unname(test$conf.int[[2L]]),
    stringsAsFactors = FALSE
  )
})
between_pairs_df <- do.call(rbind, between_pair_rows)
between_pairs_df$adjusted_p_value <- stats::p.adjust(
  between_pairs_df$p_value,
  method = "holm"
)
between_omnibus_row <- data.frame(
  record = "omnibus",
  left = NA_character_,
  right = NA_character_,
  statistic = unname(between_omnibus$statistic),
  df1 = unname(between_omnibus$parameter[[1L]]),
  df2 = unname(between_omnibus$parameter[[2L]]),
  p_value = between_omnibus$p.value,
  estimate = NA_real_,
  interval_low = NA_real_,
  interval_high = NA_real_,
  adjusted_p_value = NA_real_,
  stringsAsFactors = FALSE
)
utils::write.csv(
  rbind(between_omnibus_row, between_pairs_df),
  file.path(output_dir, "m3-between-results.csv"),
  row.names = FALSE,
  na = "NA"
)

# M3 repeated comparison fixture ---------------------------------------------

within_input <- utils::read.csv(file.path(input_dir, "m3-within.csv"))
within_input$condition <- factor(
  within_input$condition,
  levels = sort(unique(within_input$condition))
)
within_plot <- ggstatsplot::ggwithinstats(
  data = within_input,
  x = condition,
  y = value,
  subject.id = subject,
  type = "parametric",
  pairwise.display = "all",
  p.adjust.method = "holm",
  bf.message = FALSE,
  centrality.plotting = FALSE
)
dput(
  ggstatsplot::extract_stats(within_plot),
  file = file.path(output_dir, "m3-within-ggstatsplot.R"),
  control = c("keepNA", "keepInteger", "niceNames")
)

within_wide <- stats::reshape(
  within_input,
  idvar = "subject",
  timevar = "condition",
  direction = "wide"
)
within_matrix <- as.matrix(
  within_wide[, paste0("value.", levels(within_input$condition)), drop = FALSE]
)
n_subjects <- nrow(within_matrix)
n_conditions <- ncol(within_matrix)
grand_mean <- mean(within_matrix)
ss_condition <- n_subjects * sum((colMeans(within_matrix) - grand_mean)^2)
ss_subject <- n_conditions * sum((rowMeans(within_matrix) - grand_mean)^2)
ss_total <- sum((within_matrix - grand_mean)^2)
ss_error <- ss_total - ss_condition - ss_subject
within_df1 <- n_conditions - 1L
within_df2 <- (n_subjects - 1L) * (n_conditions - 1L)
within_f <- (ss_condition / within_df1) / (ss_error / within_df2)
within_covariance <- stats::cov(within_matrix)
centering <- diag(n_conditions) - matrix(1 / n_conditions, n_conditions, n_conditions)
projected <- centering %*% within_covariance %*% centering
epsilon <- sum(diag(projected))^2 / (
  (n_conditions - 1L) * sum(diag(projected %*% projected))
)
epsilon <- min(1, max(1 / (n_conditions - 1L), epsilon))
within_uncorrected_p <- stats::pf(within_f, within_df1, within_df2, lower.tail = FALSE)
within_corrected_df1 <- epsilon * within_df1
within_corrected_df2 <- epsilon * within_df2
within_corrected_p <- stats::pf(
  within_f,
  within_corrected_df1,
  within_corrected_df2,
  lower.tail = FALSE
)
within_pairs <- utils::combn(levels(within_input$condition), 2L, simplify = FALSE)
within_pair_rows <- lapply(within_pairs, function(pair) {
  left <- within_matrix[, paste0("value.", pair[[1L]])]
  right <- within_matrix[, paste0("value.", pair[[2L]])]
  test <- stats::t.test(left, right, paired = TRUE, conf.level = 0.95)
  data.frame(
    record = "pairwise",
    left = pair[[1L]],
    right = pair[[2L]],
    statistic = unname(test$statistic),
    df1 = NA_real_,
    df2 = unname(test$parameter),
    p_value = test$p.value,
    estimate = mean(left - right),
    interval_low = unname(test$conf.int[[1L]]),
    interval_high = unname(test$conf.int[[2L]]),
    epsilon = NA_real_,
    uncorrected_p_value = NA_real_,
    adjusted_p_value = NA_real_,
    stringsAsFactors = FALSE
  )
})
within_pairs_df <- do.call(rbind, within_pair_rows)
within_pairs_df$adjusted_p_value <- stats::p.adjust(
  within_pairs_df$p_value,
  method = "holm"
)
within_omnibus_row <- data.frame(
  record = "omnibus",
  left = NA_character_,
  right = NA_character_,
  statistic = within_f,
  df1 = within_corrected_df1,
  df2 = within_corrected_df2,
  p_value = within_corrected_p,
  estimate = NA_real_,
  interval_low = NA_real_,
  interval_high = NA_real_,
  epsilon = epsilon,
  uncorrected_p_value = within_uncorrected_p,
  adjusted_p_value = NA_real_,
  stringsAsFactors = FALSE
)
utils::write.csv(
  rbind(within_omnibus_row, within_pairs_df),
  file.path(output_dir, "m3-within-results.csv"),
  row.names = FALSE,
  na = "NA"
)

# M4 categorical fixtures ----------------------------------------------------

categorical_names <- c("m4-one-way", "m4-independent", "m4-paired")
for (fixture_name in categorical_names) {
  categorical_input <- utils::read.csv(file.path(input_dir, paste0(fixture_name, ".csv")))
  categorical_input$x <- factor(
    categorical_input$x,
    levels = sort(unique(categorical_input$x))
  )
  if ("y" %in% names(categorical_input)) {
    categorical_input$y <- factor(
      categorical_input$y,
      levels = sort(unique(categorical_input$y))
    )
  }
  paired_value <- identical(fixture_name, "m4-paired")
  if ("y" %in% names(categorical_input)) {
    bar_plot <- ggstatsplot::ggbarstats(
      data = categorical_input,
      x = x,
      y = y,
      counts = n,
      type = "parametric",
      paired = paired_value,
      pairwise.display = "all",
      p.adjust.method = "holm",
      proportion.test = !paired_value,
      bf.message = FALSE
    )
    pie_plot <- ggstatsplot::ggpiestats(
      data = categorical_input,
      x = x,
      y = y,
      counts = n,
      type = "parametric",
      paired = paired_value,
      pairwise.display = "all",
      p.adjust.method = "holm",
      proportion.test = !paired_value,
      bf.message = FALSE
    )
  } else {
    bar_plot <- ggstatsplot::ggbarstats(
      data = categorical_input,
      x = x,
      counts = n,
      type = "parametric",
      pairwise.display = "all",
      p.adjust.method = "holm",
      proportion.test = TRUE,
      bf.message = FALSE
    )
    pie_plot <- ggstatsplot::ggpiestats(
      data = categorical_input,
      x = x,
      counts = n,
      type = "parametric",
      pairwise.display = "all",
      p.adjust.method = "holm",
      proportion.test = TRUE,
      bf.message = FALSE
    )
  }
  dput(
    ggstatsplot::extract_stats(bar_plot),
    file = file.path(output_dir, paste0(fixture_name, "-bar-ggstatsplot.R")),
    control = c("keepNA", "keepInteger", "niceNames")
  )
  dput(
    ggstatsplot::extract_stats(pie_plot),
    file = file.path(output_dir, paste0(fixture_name, "-pie-ggstatsplot.R")),
    control = c("keepNA", "keepInteger", "niceNames")
  )
}

categorical_raw <- utils::read.csv(file.path(input_dir, "m4-raw.csv"))
categorical_raw$x <- factor(categorical_raw$x, levels = sort(unique(categorical_raw$x)))
categorical_raw$y <- factor(categorical_raw$y, levels = sort(unique(categorical_raw$y)))
raw_bar_plot <- ggstatsplot::ggbarstats(
  data = categorical_raw,
  x = x,
  y = y,
  type = "parametric",
  pairwise.display = "all",
  p.adjust.method = "holm",
  proportion.test = TRUE,
  bf.message = FALSE
)
raw_pie_plot <- ggstatsplot::ggpiestats(
  data = categorical_raw,
  x = x,
  y = y,
  type = "parametric",
  pairwise.display = "all",
  p.adjust.method = "holm",
  proportion.test = TRUE,
  bf.message = FALSE
)
dput(
  ggstatsplot::extract_stats(raw_bar_plot),
  file = file.path(output_dir, "m4-raw-bar-ggstatsplot.R"),
  control = c("keepNA", "keepInteger", "niceNames")
)
dput(
  ggstatsplot::extract_stats(raw_pie_plot),
  file = file.path(output_dir, "m4-raw-pie-ggstatsplot.R"),
  control = c("keepNA", "keepInteger", "niceNames")
)

categorical_grouped <- utils::read.csv(file.path(input_dir, "m4-grouped.csv"))
categorical_grouped$x <- factor(
  categorical_grouped$x,
  levels = sort(unique(categorical_grouped$x))
)
categorical_grouped$y <- factor(
  categorical_grouped$y,
  levels = sort(unique(categorical_grouped$y))
)
grouped_bar_plot <- ggstatsplot::grouped_ggbarstats(
  data = categorical_grouped,
  x = x,
  y = y,
  counts = n,
  grouping.var = group,
  type = "parametric",
  pairwise.display = "all",
  p.adjust.method = "holm",
  proportion.test = TRUE,
  bf.message = FALSE
)
grouped_pie_plot <- ggstatsplot::grouped_ggpiestats(
  data = categorical_grouped,
  x = x,
  y = y,
  counts = n,
  grouping.var = group,
  type = "parametric",
  pairwise.display = "all",
  p.adjust.method = "holm",
  proportion.test = TRUE,
  bf.message = FALSE
)
dput(
  ggstatsplot::extract_stats(grouped_bar_plot),
  file = file.path(output_dir, "m4-grouped-bar-ggstatsplot.R"),
  control = c("keepNA", "keepInteger", "niceNames")
)
dput(
  ggstatsplot::extract_stats(grouped_pie_plot),
  file = file.path(output_dir, "m4-grouped-pie-ggstatsplot.R"),
  control = c("keepNA", "keepInteger", "niceNames")
)

one_way_input <- utils::read.csv(file.path(input_dir, "m4-one-way.csv"))
noncentral_effect_interval <- function(
  statistic,
  df,
  n,
  scale,
  maximum,
  conf_level = 0.95
) {
  alpha <- 1 - conf_level
  solve_ncp <- function(target) {
    upper <- max(1, statistic + df)
    while (stats::pchisq(statistic, df, ncp = upper) > target) {
      upper <- upper * 2
      if (upper > 1e12) stop("noncentral interval root was not bracketed")
    }
    stats::uniroot(
      function(value) stats::pchisq(statistic, df, ncp = value) - target,
      interval = c(0, upper),
      tol = 1e-14
    )$root
  }
  cdf0 <- stats::pchisq(statistic, df)
  lower_ncp <- if (cdf0 <= 1 - alpha / 2) 0 else solve_ncp(1 - alpha / 2)
  lower <- min(maximum, sqrt(lower_ncp / (n * scale)))
  upper <- if (cdf0 <= alpha / 2) {
    maximum
  } else {
    min(maximum, sqrt(solve_ncp(alpha / 2) / (n * scale)))
  }
  c(lower, upper)
}

one_way_test <- stats::chisq.test(one_way_input$n, correct = FALSE)
one_way_interval <- noncentral_effect_interval(
  unname(one_way_test$statistic),
  unname(one_way_test$parameter),
  sum(one_way_input$n),
  1,
  sqrt(length(one_way_input$n) - 1)
)
one_way_row <- data.frame(
  fixture = "m4-one-way",
  family = "omnibus",
  left = NA_character_,
  right = NA_character_,
  statistic = unname(one_way_test$statistic),
  df = unname(one_way_test$parameter),
  p_value = one_way_test$p.value,
  adjusted_p_value = NA_real_,
  effect = sqrt(unname(one_way_test$statistic) / sum(one_way_input$n)),
  interval_low = one_way_interval[[1L]],
  interval_high = one_way_interval[[2L]],
  stringsAsFactors = FALSE
)

independent_input <- utils::read.csv(file.path(input_dir, "m4-independent.csv"))
independent_input$x <- factor(independent_input$x, levels = sort(unique(independent_input$x)))
independent_input$y <- factor(independent_input$y, levels = sort(unique(independent_input$y)))
independent_table <- stats::xtabs(n ~ x + y, data = independent_input)
independent_test <- stats::chisq.test(independent_table, correct = FALSE)
independent_scale <- min(dim(independent_table) - 1L)
independent_interval <- noncentral_effect_interval(
  unname(independent_test$statistic),
  unname(independent_test$parameter),
  sum(independent_table),
  independent_scale,
  1
)
independent_row <- data.frame(
  fixture = "m4-independent",
  family = "omnibus",
  left = NA_character_,
  right = NA_character_,
  statistic = unname(independent_test$statistic),
  df = unname(independent_test$parameter),
  p_value = independent_test$p.value,
  adjusted_p_value = NA_real_,
  effect = sqrt(
    unname(independent_test$statistic) /
      (sum(independent_table) * independent_scale)
  ),
  interval_low = independent_interval[[1L]],
  interval_high = independent_interval[[2L]],
  stringsAsFactors = FALSE
)

pair_indices <- utils::combn(rownames(independent_table), 2L, simplify = FALSE)
pair_rows <- lapply(pair_indices, function(pair) {
  pair_table <- independent_table[pair, , drop = FALSE]
  pair_test <- stats::chisq.test(pair_table, correct = FALSE)
  pair_interval <- noncentral_effect_interval(
    unname(pair_test$statistic),
    unname(pair_test$parameter),
    sum(pair_table),
    min(dim(pair_table) - 1L),
    1
  )
  data.frame(
    fixture = "m4-independent",
    family = "pairwise",
    left = pair[[1L]],
    right = pair[[2L]],
    statistic = unname(pair_test$statistic),
    df = unname(pair_test$parameter),
    p_value = pair_test$p.value,
    adjusted_p_value = NA_real_,
    effect = sqrt(
      unname(pair_test$statistic) /
        (sum(pair_table) * min(dim(pair_table) - 1L))
    ),
    interval_low = pair_interval[[1L]],
    interval_high = pair_interval[[2L]],
    stringsAsFactors = FALSE
  )
})
pair_rows <- do.call(rbind, pair_rows)
pair_rows$adjusted_p_value <- stats::p.adjust(pair_rows$p_value, method = "holm")

stratum_rows <- lapply(colnames(independent_table), function(level) {
  stratum_test <- stats::chisq.test(independent_table[, level], correct = FALSE)
  stratum_interval <- noncentral_effect_interval(
    unname(stratum_test$statistic),
    unname(stratum_test$parameter),
    sum(independent_table[, level]),
    1,
    sqrt(nrow(independent_table) - 1)
  )
  data.frame(
    fixture = "m4-independent",
    family = "stratum",
    left = level,
    right = NA_character_,
    statistic = unname(stratum_test$statistic),
    df = unname(stratum_test$parameter),
    p_value = stratum_test$p.value,
    adjusted_p_value = NA_real_,
    effect = sqrt(unname(stratum_test$statistic) / sum(independent_table[, level])),
    interval_low = stratum_interval[[1L]],
    interval_high = stratum_interval[[2L]],
    stringsAsFactors = FALSE
  )
})
stratum_rows <- do.call(rbind, stratum_rows)
stratum_rows$adjusted_p_value <- stats::p.adjust(
  stratum_rows$p_value,
  method = "holm"
)

paired_input <- utils::read.csv(file.path(input_dir, "m4-paired.csv"))
paired_table <- stats::xtabs(n ~ x + y, data = paired_input)
discordant <- paired_table[1L, 2L] + paired_table[2L, 1L]
paired_test <- stats::binom.test(
  paired_table[1L, 2L],
  discordant,
  p = 0.5,
  alternative = "two.sided"
)
paired_interval <- unname(paired_test$conf.int) - 0.5
paired_row <- data.frame(
  fixture = "m4-paired",
  family = "omnibus",
  left = NA_character_,
  right = NA_character_,
  statistic = paired_table[1L, 2L],
  df = 0,
  p_value = paired_test$p.value,
  adjusted_p_value = NA_real_,
  effect = paired_table[1L, 2L] / discordant - 0.5,
  interval_low = paired_interval[[1L]],
  interval_high = paired_interval[[2L]],
  stringsAsFactors = FALSE
)

utils::write.csv(
  rbind(one_way_row, independent_row, pair_rows, stratum_rows, paired_row),
  file.path(output_dir, "m4-categorical-results.csv"),
  row.names = FALSE,
  na = "NA"
)

# M5A coefficient and fitted-model fixtures ---------------------------------

coefficient_input <- utils::read.csv(file.path(input_dir, "m5a-coefficients.csv"))
coefficient_tidy <- data.frame(
  term = coefficient_input$term,
  estimate = coefficient_input$estimate,
  std.error = coefficient_input$standard_error,
  statistic = coefficient_input$statistic,
  p.value = coefficient_input$p_value,
  conf.low = coefficient_input$conf_low,
  conf.high = coefficient_input$conf_high,
  stringsAsFactors = FALSE
)
coefficient_plot <- ggstatsplot::ggcoefstats(
  coefficient_tidy,
  conf.int = TRUE,
  conf.level = 0.95,
  stats.labels = FALSE
)
dput(
  ggstatsplot::extract_stats(coefficient_plot),
  file = file.path(output_dir, "m5a-coefficients-ggstatsplot.R"),
  control = c("keepNA", "keepInteger", "niceNames")
)

ols_input <- utils::read.csv(file.path(input_dir, "m5a-ols.csv"))
ols_fit <- stats::lm(y ~ x, data = ols_input)
ols_plot <- ggstatsplot::ggcoefstats(
  ols_fit,
  conf.int = TRUE,
  conf.level = 0.95,
  stats.labels = FALSE
)
dput(
  ggstatsplot::extract_stats(ols_plot),
  file = file.path(output_dir, "m5a-ols-ggstatsplot.R"),
  control = c("keepNA", "keepInteger", "niceNames")
)
ols_coefficients <- summary(ols_fit)$coefficients
ols_intervals <- stats::confint(ols_fit, level = 0.95)
utils::write.csv(
  data.frame(
    term = c("const", "x1"),
    estimate = unname(ols_coefficients[, "Estimate"]),
    standard_error = unname(ols_coefficients[, "Std. Error"]),
    statistic = unname(ols_coefficients[, "t value"]),
    df = stats::df.residual(ols_fit),
    p_value = unname(ols_coefficients[, "Pr(>|t|)"]),
    interval_low = unname(ols_intervals[, 1L]),
    interval_high = unname(ols_intervals[, 2L]),
    stringsAsFactors = FALSE
  ),
  file.path(output_dir, "m5a-ols-results.csv"),
  row.names = FALSE,
  na = "NA"
)
utils::write.csv(
  data.frame(
    nobs = stats::nobs(ols_fit),
    df_model = length(stats::coef(ols_fit)) - 1L,
    df_resid = stats::df.residual(ols_fit),
    rank = ols_fit$rank,
    stringsAsFactors = FALSE
  ),
  file.path(output_dir, "m5a-ols-summary.csv"),
  row.names = FALSE,
  na = "NA"
)

# M5B frequentist random-effects meta-analysis fixture -----------------------

meta_input <- utils::read.csv(file.path(input_dir, "m5b-meta.csv"))
meta_tidy <- data.frame(
  term = meta_input$term,
  estimate = meta_input$estimate,
  std.error = meta_input$standard_error,
  check.names = FALSE,
  stringsAsFactors = FALSE
)
meta_plot <- ggstatsplot::ggcoefstats(
  meta_tidy,
  conf.int = FALSE,
  meta.analytic.effect = TRUE,
  meta.type = "parametric",
  bf.message = FALSE,
  stats.labels = FALSE
)
dput(
  ggstatsplot::extract_stats(meta_plot),
  file = file.path(output_dir, "m5b-meta-ggstatsplot.R"),
  control = c("keepNA", "keepInteger", "niceNames")
)

meta_fit <- metafor::rma(
  yi = meta_tidy$estimate,
  sei = meta_tidy$std.error,
  method = "REML",
  test = "z"
)
meta_fit_adhoc <- metafor::rma(
  yi = meta_tidy$estimate,
  sei = meta_tidy$std.error,
  method = "REML",
  test = "adhoc"
)
meta_variances <- meta_tidy$std.error^2
meta_scale <- max(abs(meta_tidy$estimate), meta_tidy$std.error)
meta_scaled_estimates <- meta_tidy$estimate / meta_scale
meta_scaled_variances <- (meta_tidy$std.error / meta_scale)^2
meta_reml_score <- function(tau_squared) {
  weights <- 1 / (meta_scaled_variances + tau_squared)
  total <- sum(weights)
  pooled <- sum(weights * meta_scaled_estimates) / total
  sum(weights^2 * (meta_scaled_estimates - pooled)^2) -
    total + sum(weights^2) / total
}
meta_score_at_zero <- meta_reml_score(0)
if (meta_score_at_zero <= 0) {
  meta_tau_squared <- 0
} else {
  meta_upper <- max(1, stats::var(meta_scaled_estimates), meta_scaled_variances)
  while (meta_reml_score(meta_upper) >= 0) meta_upper <- meta_upper * 2
  meta_tau_squared <- stats::uniroot(
    meta_reml_score,
    interval = c(0, meta_upper),
    tol = .Machine$double.eps,
    maxiter = 1000L
  )$root * meta_scale^2
}
meta_weights <- 1 / (meta_variances + meta_tau_squared)
meta_normalized_weights <- meta_weights / sum(meta_weights)
meta_pooled <- sum(meta_normalized_weights * meta_tidy$estimate)
meta_df <- nrow(meta_tidy) - 1L
meta_q_hk <- sum(meta_weights * (meta_tidy$estimate - meta_pooled)^2) / meta_df
meta_q_star <- max(1, meta_q_hk)
meta_adjusted_variance <- meta_q_star / sum(meta_weights)
meta_adjusted_se <- sqrt(meta_adjusted_variance)
meta_statistic <- meta_pooled / meta_adjusted_se
meta_p_value <- 2 * stats::pt(abs(meta_statistic), meta_df, lower.tail = FALSE)
meta_t_critical <- stats::qt(0.975, meta_df)
meta_ci <- meta_pooled + c(-1, 1) * meta_t_critical * meta_adjusted_se
meta_prediction <- meta_pooled + c(-1, 1) * meta_t_critical * sqrt(
  meta_tau_squared + meta_adjusted_variance
)
meta_fixed_weights <- 1 / meta_variances
meta_fixed_mean <- sum(meta_fixed_weights * meta_tidy$estimate) / sum(meta_fixed_weights)
meta_q <- sum(meta_fixed_weights * (meta_tidy$estimate - meta_fixed_mean)^2)
meta_i_squared <- if (meta_q > 0) max(0, (meta_q - meta_df) / meta_q) else 0

meta_summary <- data.frame(
  fixture = "m5b-meta",
  studies = nrow(meta_tidy),
  tau_squared = meta_tau_squared,
  tau = sqrt(meta_tau_squared),
  pooled_estimate = meta_pooled,
  conventional_variance = 1 / sum(meta_weights),
  q_hk = meta_q_hk,
  q_star = meta_q_star,
  adjusted_variance = meta_adjusted_variance,
  pooled_standard_error = meta_adjusted_se,
  pooled_statistic = meta_statistic,
  pooled_df = meta_df,
  pooled_p_value = meta_p_value,
  pooled_interval_low = meta_ci[[1L]],
  pooled_interval_high = meta_ci[[2L]],
  prediction_interval_low = meta_prediction[[1L]],
  prediction_interval_high = meta_prediction[[2L]],
  q = meta_q,
  q_df = meta_df,
  q_p_value = stats::pchisq(meta_q, meta_df, lower.tail = FALSE),
  q_reference_mean = meta_fixed_mean,
  i_squared = meta_i_squared,
  metafor_tau_squared = unname(meta_fit$tau2),
  upstream_test = "z",
  upstream_pooled_estimate = unname(meta_fit$b[[1L]]),
  upstream_standard_error = unname(meta_fit$se[[1L]]),
  upstream_p_value = unname(meta_fit$pval[[1L]]),
  upstream_interval_low = unname(meta_fit$ci.lb[[1L]]),
  upstream_interval_high = unname(meta_fit$ci.ub[[1L]]),
  metafor_adhoc_estimate = unname(meta_fit_adhoc$b[[1L]]),
  metafor_adhoc_standard_error = unname(meta_fit_adhoc$se[[1L]]),
  metafor_adhoc_statistic = unname(meta_fit_adhoc$zval[[1L]]),
  metafor_adhoc_df = unname(meta_fit_adhoc$ddf[[1L]]),
  metafor_adhoc_p_value = unname(meta_fit_adhoc$pval[[1L]]),
  metafor_adhoc_interval_low = unname(meta_fit_adhoc$ci.lb[[1L]]),
  metafor_adhoc_interval_high = unname(meta_fit_adhoc$ci.ub[[1L]]),
  stringsAsFactors = FALSE
)
utils::write.csv(
  meta_summary,
  file.path(output_dir, "m5b-meta-results.csv"),
  row.names = FALSE,
  na = "NA"
)

meta_z <- meta_tidy$estimate / meta_tidy$std.error
meta_study_results <- data.frame(
  term = meta_tidy$term,
  estimate = meta_tidy$estimate,
  standard_error = meta_tidy$std.error,
  statistic = meta_z,
  p_value = 2 * stats::pnorm(abs(meta_z), lower.tail = FALSE),
  interval_low = meta_tidy$estimate - stats::qnorm(0.975) * meta_tidy$std.error,
  interval_high = meta_tidy$estimate + stats::qnorm(0.975) * meta_tidy$std.error,
  sampling_variance = meta_variances,
  random_effects_weight = meta_weights,
  normalized_weight = meta_normalized_weights,
  weighted_contribution = meta_normalized_weights * meta_tidy$estimate,
  stringsAsFactors = FALSE
)
utils::write.csv(
  meta_study_results,
  file.path(output_dir, "m5b-meta-study-results.csv"),
  row.names = FALSE,
  na = "NA"
)

# M6A approved robust-method fixtures ----------------------------------------

# These normalized calculations independently implement the approved M6A
# formulas in base R. The retained ggstatsplot objects are compatibility
# evidence only: M6A deliberately adapts upstream interval, reference-df, and
# repeated-comparison behavior documented in docs/M6_STATISTICAL_METHODS.md.

m6a_kernel <- function(values, trim = 0.2) {
  ordered <- sort(values)
  n <- length(ordered)
  g <- floor(trim * n)
  h <- n - (2L * g)
  lower <- ordered[[g + 1L]]
  upper <- ordered[[n - g]]
  winsorized <- pmin(pmax(values, lower), upper)
  winsorized_variance <- stats::var(winsorized)
  list(
    n = n,
    g = g,
    h = h,
    lower = lower,
    upper = upper,
    theta = mean(ordered[(g + 1L):(n - g)]),
    winsorized = winsorized,
    winsorized_variance = winsorized_variance,
    q = (n - 1) * winsorized_variance / (h * (h - 1))
  )
}

m6a_dump_upstream <- function(filename, expression) {
  set.seed(20260914)
  value <- tryCatch(
    expression,
    error = function(condition) structure(
      list(message = conditionMessage(condition)),
      class = "plotsalot_upstream_error"
    )
  )
  dput(
    value,
    file = file.path(output_dir, filename),
    control = c("keepNA", "keepInteger", "niceNames")
  )
}

m6a_hist <- utils::read.csv(file.path(input_dir, "m6a-hist.csv"))
m6a_dump_upstream(
  "m6a-hist-ggstatsplot.R",
  ggstatsplot::extract_stats(ggstatsplot::gghistostats(
    data = m6a_hist,
    x = value,
    type = "robust",
    test.value = 3,
    conf.level = 0.95,
    tr = 0.2,
    bf.message = FALSE,
    centrality.plotting = FALSE
  ))
)
m6a_hist_kernel <- m6a_kernel(m6a_hist$value)
m6a_hist_se <- sqrt(m6a_hist_kernel$q)
m6a_hist_statistic <- (m6a_hist_kernel$theta - 3) / m6a_hist_se
m6a_hist_critical <- stats::qt(0.975, m6a_hist_kernel$h - 1L)
utils::write.csv(
  data.frame(
    n = m6a_hist_kernel$n,
    g = m6a_hist_kernel$g,
    h = m6a_hist_kernel$h,
    lower_bound = m6a_hist_kernel$lower,
    upper_bound = m6a_hist_kernel$upper,
    trimmed_mean = m6a_hist_kernel$theta,
    winsorized_variance = m6a_hist_kernel$winsorized_variance,
    q = m6a_hist_kernel$q,
    statistic = m6a_hist_statistic,
    df = m6a_hist_kernel$h - 1L,
    p_value = 2 * stats::pt(abs(m6a_hist_statistic), m6a_hist_kernel$h - 1L, lower.tail = FALSE),
    interval_low = m6a_hist_kernel$theta - m6a_hist_critical * m6a_hist_se,
    interval_high = m6a_hist_kernel$theta + m6a_hist_critical * m6a_hist_se,
    raw_effect = m6a_hist_kernel$theta - 3
  ),
  file.path(output_dir, "m6a-hist-results.csv"),
  row.names = FALSE
)

m6a_correlation <- utils::read.csv(file.path(input_dir, "m6a-correlation.csv"))
m6a_dump_upstream(
  "m6a-scatter-ggstatsplot.R",
  ggstatsplot::extract_stats(ggstatsplot::ggscatterstats(
    data = m6a_correlation,
    x = x,
    y = y,
    type = "robust",
    conf.level = 0.95,
    tr = 0.2,
    bf.message = FALSE,
    marginal = FALSE
  ))
)
m6a_x <- m6a_kernel(m6a_correlation$x)
m6a_y <- m6a_kernel(m6a_correlation$y)
m6a_covariance <- stats::cov(m6a_x$winsorized, m6a_y$winsorized)
m6a_r <- m6a_covariance / sqrt(
  m6a_x$winsorized_variance * m6a_y$winsorized_variance
)
m6a_r_statistic <- m6a_r * sqrt((m6a_x$n - 2) / (1 - m6a_r^2))
utils::write.csv(
  data.frame(
    n = m6a_x$n,
    g = m6a_x$g,
    h = m6a_x$h,
    x_lower_bound = m6a_x$lower,
    x_upper_bound = m6a_x$upper,
    y_lower_bound = m6a_y$lower,
    y_upper_bound = m6a_y$upper,
    x_winsorized_variance = m6a_x$winsorized_variance,
    y_winsorized_variance = m6a_y$winsorized_variance,
    winsorized_covariance = m6a_covariance,
    estimate = m6a_r,
    statistic = m6a_r_statistic,
    df = m6a_x$h - 2L,
    p_value = 2 * stats::pt(abs(m6a_r_statistic), m6a_x$h - 2L, lower.tail = FALSE)
  ),
  file.path(output_dir, "m6a-correlation-results.csv"),
  row.names = FALSE
)

m6a_yuen <- function(left, right) {
  left_kernel <- m6a_kernel(left)
  right_kernel <- m6a_kernel(right)
  estimate <- left_kernel$theta - right_kernel$theta
  standard_error <- sqrt(left_kernel$q + right_kernel$q)
  df <- (left_kernel$q + right_kernel$q)^2 / (
    left_kernel$q^2 / (left_kernel$h - 1L) +
      right_kernel$q^2 / (right_kernel$h - 1L)
  )
  statistic <- estimate / standard_error
  critical <- stats::qt(0.975, df)
  data.frame(
    estimate = estimate,
    standard_error = standard_error,
    statistic = statistic,
    df = df,
    p_value = 2 * stats::pt(abs(statistic), df, lower.tail = FALSE),
    interval_low = estimate - critical * standard_error,
    interval_high = estimate + critical * standard_error
  )
}

m6a_between <- utils::read.csv(file.path(input_dir, "m6a-between.csv"))
m6a_between$group <- factor(m6a_between$group, levels = c("a", "b", "c"))
m6a_dump_upstream(
  "m6a-between-ggstatsplot.R",
  ggstatsplot::extract_stats(ggstatsplot::ggbetweenstats(
    data = m6a_between,
    x = group,
    y = value,
    type = "robust",
    pairwise.display = "all",
    p.adjust.method = "holm",
    conf.level = 0.95,
    tr = 0.2,
    bf.message = FALSE,
    centrality.plotting = FALSE
  ))
)
m6a_between_levels <- levels(m6a_between$group)
m6a_between_kernels <- lapply(m6a_between_levels, function(level) {
  m6a_kernel(m6a_between$value[m6a_between$group == level])
})
m6a_between_q <- vapply(m6a_between_kernels, function(kernel) kernel$q, numeric(1L))
m6a_between_theta <- vapply(
  m6a_between_kernels,
  function(kernel) kernel$theta,
  numeric(1L)
)
m6a_between_h <- vapply(m6a_between_kernels, function(kernel) kernel$h, numeric(1L))
m6a_between_w <- 1 / m6a_between_q
m6a_between_u <- sum(m6a_between_w)
m6a_between_center <- sum(m6a_between_w * m6a_between_theta) / m6a_between_u
m6a_between_j <- length(m6a_between_levels)
m6a_between_a <- sum(
  m6a_between_w * (m6a_between_theta - m6a_between_center)^2
) / (m6a_between_j - 1L)
m6a_between_c <- sum(
  (1 - (m6a_between_w / m6a_between_u))^2 / (m6a_between_h - 1L)
) / (m6a_between_j^2 - 1L)
m6a_between_f <- m6a_between_a / (
  1 + 2 * (m6a_between_j - 2L) * m6a_between_c
)
m6a_between_df2 <- 1 / (3 * m6a_between_c)
m6a_between_pairs <- utils::combn(m6a_between_levels, 2L, simplify = FALSE)
m6a_between_rows <- lapply(m6a_between_pairs, function(pair) {
  result <- m6a_yuen(
    m6a_between$value[m6a_between$group == pair[[1L]]],
    m6a_between$value[m6a_between$group == pair[[2L]]]
  )
  cbind(record = "pairwise", left = pair[[1L]], right = pair[[2L]], result)
})
m6a_between_rows <- do.call(rbind, m6a_between_rows)
m6a_between_rows$adjusted_p_value <- stats::p.adjust(
  m6a_between_rows$p_value,
  method = "holm"
)
m6a_between_omnibus <- data.frame(
  record = "omnibus",
  left = NA_character_,
  right = NA_character_,
  estimate = NA_real_,
  standard_error = NA_real_,
  statistic = m6a_between_f,
  df = m6a_between_df2,
  p_value = stats::pf(
    m6a_between_f,
    m6a_between_j - 1L,
    m6a_between_df2,
    lower.tail = FALSE
  ),
  interval_low = NA_real_,
  interval_high = NA_real_,
  adjusted_p_value = NA_real_
)
utils::write.csv(
  rbind(m6a_between_omnibus, m6a_between_rows),
  file.path(output_dir, "m6a-between-results.csv"),
  row.names = FALSE,
  na = "NA"
)

m6a_within <- utils::read.csv(file.path(input_dir, "m6a-within.csv"))
m6a_within$condition <- factor(m6a_within$condition, levels = c("a", "b", "c"))
m6a_dump_upstream(
  "m6a-within-ggstatsplot.R",
  ggstatsplot::extract_stats(ggstatsplot::ggwithinstats(
    data = m6a_within,
    x = condition,
    y = value,
    type = "robust",
    subject.id = subject,
    pairwise.display = "all",
    p.adjust.method = "holm",
    conf.level = 0.95,
    tr = 0.2,
    bf.message = FALSE,
    centrality.plotting = FALSE,
    centrality.path = FALSE,
    point.path = FALSE
  ))
)
m6a_within_wide <- reshape(
  m6a_within,
  idvar = "subject",
  timevar = "condition",
  direction = "wide"
)
m6a_within_wide <- m6a_within_wide[order(m6a_within_wide$subject), ]
m6a_within_matrix <- as.matrix(m6a_within_wide[, paste0("value.", c("a", "b", "c"))])
m6a_within_n <- nrow(m6a_within_matrix)
m6a_within_j <- ncol(m6a_within_matrix)
m6a_within_kernels <- lapply(seq_len(m6a_within_j), function(index) {
  m6a_kernel(m6a_within_matrix[, index])
})
m6a_within_h <- m6a_within_kernels[[1L]]$h
m6a_within_theta <- vapply(
  m6a_within_kernels,
  function(kernel) kernel$theta,
  numeric(1L)
)
m6a_within_winsorized <- do.call(
  cbind,
  lapply(m6a_within_kernels, function(kernel) kernel$winsorized)
)
m6a_within_qc <- m6a_within_h * sum(
  (m6a_within_theta - mean(m6a_within_theta))^2
)
m6a_within_residual <- sweep(
  m6a_within_winsorized,
  1L,
  rowMeans(m6a_within_winsorized),
  "-"
)
m6a_within_residual <- sweep(
  m6a_within_residual,
  2L,
  colMeans(m6a_within_residual),
  "-"
)
m6a_within_qe <- sum(m6a_within_residual^2)
m6a_within_f <- m6a_within_qc / (m6a_within_qe / (m6a_within_h - 1L))
m6a_within_v <- stats::cov(m6a_within_winsorized)
m6a_within_v_bar <- mean(m6a_within_v)
m6a_within_v_diag <- mean(diag(m6a_within_v))
m6a_within_v_j <- rowMeans(m6a_within_v)
m6a_within_a <- m6a_within_j^2 * (
  m6a_within_v_diag - m6a_within_v_bar
)^2 / (m6a_within_j - 1L)
m6a_within_b <- sum(m6a_within_v^2) -
  2 * m6a_within_j * sum(m6a_within_v_j^2) +
  m6a_within_j^2 * m6a_within_v_bar^2
m6a_within_e_hat <- m6a_within_a / m6a_within_b
m6a_within_e_raw <- (
  m6a_within_n * (m6a_within_j - 1L) * m6a_within_e_hat - 2
) / (
  (m6a_within_j - 1L) *
    (m6a_within_n - 1L - (m6a_within_j - 1L) * m6a_within_e_hat)
)
m6a_within_epsilon <- max(
  1 / (m6a_within_j - 1L),
  min(1, m6a_within_e_raw)
)
m6a_within_df1 <- (m6a_within_j - 1L) * m6a_within_epsilon
m6a_within_df2 <- (m6a_within_j - 1L) * m6a_within_epsilon *
  (m6a_within_h - 1L)
m6a_within_omnibus <- data.frame(
  record = "omnibus",
  left = NA_character_,
  right = NA_character_,
  estimate = NA_real_,
  standard_error = NA_real_,
  statistic = m6a_within_f,
  df1 = m6a_within_df1,
  df2 = m6a_within_df2,
  p_value = stats::pf(m6a_within_f, m6a_within_df1, m6a_within_df2, lower.tail = FALSE),
  interval_low = NA_real_,
  interval_high = NA_real_,
  adjusted_p_value = NA_real_,
  epsilon = m6a_within_epsilon,
  epsilon_hat = m6a_within_e_hat,
  epsilon_raw = m6a_within_e_raw,
  covariance_a = m6a_within_a,
  covariance_b = m6a_within_b,
  qc = m6a_within_qc,
  qe = m6a_within_qe
)
m6a_within_pairs <- utils::combn(c("a", "b", "c"), 2L, simplify = FALSE)
m6a_within_rows <- lapply(m6a_within_pairs, function(pair) {
  difference <- m6a_within_matrix[, match(pair[[1L]], c("a", "b", "c"))] -
    m6a_within_matrix[, match(pair[[2L]], c("a", "b", "c"))]
  kernel <- m6a_kernel(difference)
  standard_error <- sqrt(kernel$q)
  statistic <- kernel$theta / standard_error
  df <- kernel$h - 1L
  critical <- stats::qt(0.975, df)
  data.frame(
    record = "pairwise",
    left = pair[[1L]],
    right = pair[[2L]],
    estimate = kernel$theta,
    standard_error = standard_error,
    statistic = statistic,
    df1 = NA_real_,
    df2 = df,
    p_value = 2 * stats::pt(abs(statistic), df, lower.tail = FALSE),
    interval_low = kernel$theta - critical * standard_error,
    interval_high = kernel$theta + critical * standard_error,
    adjusted_p_value = NA_real_,
    epsilon = NA_real_,
    epsilon_hat = NA_real_,
    epsilon_raw = NA_real_,
    covariance_a = NA_real_,
    covariance_b = NA_real_,
    qc = NA_real_,
    qe = NA_real_
  )
})
m6a_within_rows <- do.call(rbind, m6a_within_rows)
m6a_within_rows$adjusted_p_value <- stats::p.adjust(
  m6a_within_rows$p_value,
  method = "holm"
)
utils::write.csv(
  rbind(m6a_within_omnibus, m6a_within_rows),
  file.path(output_dir, "m6a-within-results.csv"),
  row.names = FALSE,
  na = "NA"
)

installed <- as.data.frame(utils::installed.packages()[, c("Package", "Version")])
installed <- installed[order(installed$Package), , drop = FALSE]
utils::write.csv(
  installed,
  file.path(output_dir, "installed-packages.csv"),
  row.names = FALSE
)

session <- capture.output(utils::sessionInfo())
writeLines(session, file.path(output_dir, "session-info.txt"), useBytes = TRUE)

if (!file.exists("/work/oracle/renv.lock")) {
  stop("the retained renv lockfile is required")
}
