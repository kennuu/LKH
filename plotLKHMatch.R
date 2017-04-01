library(dplyr)
library(ggplot2)
library(tidyr)
library(stringr)
library(rjson)

# data <- readRDS("kuntavaalit2017/koko-2017.rds") %>%
#   # tibble::rownames_to_column() %>%
#   filter(X2017_kuntanro == 91) %>%
#   select(-contains("UUTTA")) %>%
# 
# write.csv(data, "kuntavaalit2012/vaalikone_Helsinki_2017.csv", row.names = FALSE)

year <- 2012

cont <- TRUE
while (cont==TRUE){
  data <- read.csv(paste0("kuntavaalit",year,"/results_latest.csv"))
  valt_puolueet <- unique(filter(data, electedInformation=="ELECTED")$abbr)
  
  version <- fromJSON(file=paste0("kuntavaalit",year,"/version_latest.json"))
  
  lastElected <- data %>%
    filter(electedInformation=="ELECTED") %>%
    select(comparativeIndex) %>%
    min()
  lastReserve <- data %>%
    filter(electedInformation=="ON_SUBSTITUTE_PLACE") %>%
    select(comparativeIndex) %>%
    min()
  ggplot(filter(data, abbr %in% valt_puolueet), aes(x=LKH_match, y=comparativeIndex)) + geom_point(aes(color=abbr)) + 
    scale_y_log10() + geom_smooth(method="lm") + ggtitle(paste0("Laskentatilanne: ", version$calculationStatusPercent, 
                                                                "%", ", ", version$created)) +
    geom_hline(yintercept = lastElected, colour = 'green') + geom_hline(yintercept = lastReserve, colour = 'red')
  
  ggsave(paste0("kuntavaalit",year,"/LKH_match.png"))
  print(paste0("plotting the results for version ", version$mainVersion))
  Sys.sleep(120)
}
