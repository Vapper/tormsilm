library(purrr)
library(httr2)
library(stringr)
library(dplyr)
library(tidyr)
library(stringr)
library(fs)

library(listviewer)



data_dir <- dir_create("data")

# collect news records for 2023 -------------------------------------------
req_base <- 
  request("https://arhiiv.err.ee/api/v1/contentSeries/audio/uudised") |> 
  req_body_form(year = 2023)
reqs <- map(1:12, \(month) req_body_form(req_base, month = month)) 
resps <- req_perform_parallel(reqs, progress = TRUE)

if (FALSE){
  resps[[1]] |> 
    resp_body_string() |> 
    jsonedit()
}
 
if (FALSE){
  resps[[1]] |> 
    resp_body_json() |>
    pluck("seriesList", "contents")
}

cont <- 
  map(resps, \(x) resp_body_json(x) |> pluck("seriesList", "contents")) |> 
  do.call(what = c)

readr::write_rds(cont, data_dir / "err_news_summary_lst.rds")
jsonlite::write_json(cont, data_dir / "err_news_summary.json")

cont_df <- 
  cont |> 
  bind_rows()

readr::write_csv(cont_df, data_dir / "err_news_summary.csv")


# -------------------------------------------------------------------------
# check LLM classification results
if (FALSE) {
  cont_df <- readr::read_csv(data_dir / "err_news_summary.csv")
  cont_llm_flt_df <- readr::read_csv(data_dir / "err_news_summary_google_ai_filter.csv")
  
  semi_join(cont_df, cont_llm_flt_df, by = "url") |> View()
  left_join(cont_llm_flt_df, cont_df, by = "url") |> View()
  
  missed_match <- anti_join(cont_llm_flt_df, cont_df)
  
  cont_df |> 
    filter(url %in% missed_match$url) |> 
    select(date, url)
}

# fetch trascriptions -----------------------------------------------------
# batches of 100 to save intermittent results. 
cont_split <- split(cont, ceiling(seq_along(cont)/100))
resp_list <- vector(mode = "list", length = length(cont_split))

for (idx in 3:30) {
  message(idx)
  resp_list[[idx]] <- 
    cont_split[[idx]] |> 
    map(pluck, "url") |> 
    map(\(x) str_c("https://arhiiv.err.ee/api/v1/transcription/audio/", x)) |> 
    map(request) |> 
    map(req_body_form, phrase = "", page = 1) |> 
    req_perform_sequential(on_error = "continue")
}

readr::write_rds(resp_list, data_dir / "resp_list_complete.rds")

resp_list_c <- 
  resp_list |> 
  do.call(what = c)

transcript_flat <- 
  resp_list_c |> 
  map_chr(\(x) resp_body_json(x) |> 
    pluck(1, "data") |> 
    map("content") |> 
    str_c(collapse = "\n")
  )

readr::write_rds(transcript_flat, data_dir / "transcript_flat.rds")


# concat news content -----------------------------------------------------

transcr_df <- 
  cont_df |> 
  select(date, heading, lead, url) |> 
  bind_cols(transcript = transcript_flat)

readr::write_rds(transcr_df, data_dir / "transcr_df.rds")

transcr_df |> 
  mutate(heading = str_remove(heading, "^UUDISED.\\s+")) |> 
  mutate(date = as.Date(date)) |> 
  unite(text, heading, lead, transcript, sep = "\n") |> 
  select(date, url, text) |> 
  jsonlite::write_json(data_dir / "err_viker_uudised_2023_transcript.json")


