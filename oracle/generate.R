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
