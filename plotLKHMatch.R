library(dplyr)
library(ggplot2)
library(tidyr)
library(stringr)
library(rjson)
library(ggExtra)
library(gridExtra)
# data <- readRDS("kuntavaalit2017/koko-2017.rds") %>%
#   # tibble::rownames_to_column() %>%
#   filter(X2017_kuntanro == 91) %>%
#   select(-contains("UUTTA")) %>%
# 
# write.csv(data, "kuntavaalit2012/vaalikone_Helsinki_2017.csv", row.names = FALSE)

year <- 2017

cont <- TRUE

# TODO: colouring that suits the parties
# TODO: only time, not date
# TODO: 
puolue_colors = list(KD="dodgerblue2", KESK="darkolivegreen1", KOK="cadetblue3", PS="goldenrod1", RKP="dodgerblue1",
                     SDP="firebrick1", SKP="darkred", VAS="firebrick4", VIHR="chartreuse3", OTHER="black")
# puolue_colors = c("dodgerblue2", "darkolivegreen1", "cadetblue3", "goldenrod1", "dodgerblue1", 
#                      "firebrick1", "darkred", "firebrick4", "chartreuse3", "green", "green", "green", "green", "green")

while (cont==TRUE){
  data <- read.csv(paste0("kuntavaalit", year, "/results_latest.csv"))
  valt_puolueet <- unique((data %>%
    filter(electedInformation=="ELECTED") %>%
    droplevels())$abbr) %>%
    sort()
  data <- data %>%
    filter(abbr %in% valt_puolueet) %>%
    droplevels()
  valt_puolue_colors <- c()
  for (p in valt_puolueet){
    if (p %in% names(puolue_colors)){
      valt_puolue_colors <- c(valt_puolue_colors, puolue_colors[[p]])
    }
    else{
      valt_puolue_colors <- c(valt_puolue_colors, "black")
    }
  }

  version <- fromJSON(file=paste0("kuntavaalit",year,"/version_latest.json"))
  
  lastElected <- data %>%
    filter(electedInformation=="ELECTED") %>%
    select(comparativeIndex) %>%
    min()
  lastReserve <- data %>%
    filter(electedInformation=="ON_SUBSTITUTE_PLACE") %>%
    select(comparativeIndex) %>%
    min()

  # FIXME: remove na
  # LKHaverage <- data %>%
  # filter(electedInformation=="ELECTED") %>%
  #   select(LKH_match) %>%
  #   mean()
  #FIXME 

  # ggplot(filter(data, electedInformation=="ELECTED"), aes(x=LKH_match)) + geom_density() + 
  #   scale_fill_continuous(low="firebrick1", high="chartreuse") +
  #   ggtitle(paste0("Laskentatilanne: ", version$calculationStatusPercent, 
  #                  "%", ", ", version$created))
  
    
  hist_plot <- ggplot(filter(data, electedInformation=="ELECTED"), aes(x=LKH_match)) + geom_histogram(breaks=seq(-7,7,2), aes(fill=..x..)) + 
    scale_fill_continuous(low="firebrick1", high="chartreuse") + scale_x_continuous(limits = c(-8, 8))
  
  score_plot <- ggplot(data, aes(x=LKH_match, y=comparativeIndex, label=sukunimi)) + scale_y_log10() +
    # scale_y_log10(limits=c(lastReserve,max(data$comparativeIndex)), breaks = c(round(lastReserve), round(lastElected), 10000), 
    #               label=c(paste("viim. varap. vl", round(lastReserve)), 
    #                                    paste("viim. valittu", round(lastElected)), "10 000")) +
    # # geom_smooth(method = "glm") +
    ggtitle(paste0("Laskentatilanne: ", version$calculationStatusPercent, 
                                                                "%", ", ", version$created)) +
    geom_hline(yintercept = lastElected, colour = 'green') + 
    # geom_hline(yintercept = lastReserve, colour = 'red') +
    # geom_vline(xintercept = LKHaverage, colour = 'green') +
    geom_text(data=subset(data, electedInformation=="ELECTED" ), aes(color=abbr), ) + labs(x="LKH", y="vertailuluku") +
    # geom_point(data=subset(data, electedInformation=="NOT_ELECTED"), aes(color=abbr)) + 
    scale_color_manual(values=valt_puolue_colors) + scale_x_continuous(limits = c(-8, 8))

    # ggExtra::ggMarginal(p, margins = "x", type = "histogram", binwidth=3, fill="electedInformation")             
  ggs <- arrangeGrob(score_plot, hist_plot, ncol = 1, nrow = 2, heights = c(2, 1))
  ggsave(paste0("kuntavaalit",year,"/LKH_match.png"), ggs, width = 16, height = 12)
  print(paste0("plotting the results for version ", version$mainVersion))
  Sys.sleep(200)
}
