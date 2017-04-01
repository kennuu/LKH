# -*- coding: utf-8 -*-

import numpy as np
import re
import codecs
import pandas
import urllib2
import json
import time
import glob
from sklearn import preprocessing
from sklearn.preprocessing import Imputer

wait_time = 10  # wait time in seconds before trying to fetch new data from S3
year = 2012
fields = ['caid', 'abbr', 'firstname', 'lastname', 'electedInformation', 'comparativeIndex']

def elected(x):
    try:
        return x['electedInformation'] == 'ELECTED'
    except (KeyError, TypeError):
        return False

def checkIfNewResults(year):
    latestVersion_url = 'https://vaalit-test.yle.fi/content/kv' + str(year) + '/latestVersion.json'

    print('retrieving the latest version information from ' + latestVersion_url)
    try:
        latest_url = urllib2.urlopen(latestVersion_url)
        latestVersion = json.loads(latest_url.read())
        calculationStatusPercent = latestVersion['calculationStatusPercent']
        if calculationStatusPercent == 0:
            print('no votes reported yet')
        else:
            print('votes calculated: ' + str(calculationStatusPercent))
        latestVersionNumber = latestVersion['mainVersion']

        print('the latest data is version ' + str(latestVersionNumber))
        try:
            with codecs.open('kuntavaalit' + str(year) + '/version_latest.json', 'r') as f:
                latestLocalVersion = json.load(f)
        except:
            pass
            print("no local versions")
            return True, latestVersion
    except:
        pass
        print('cannot get a new version: ' + latestVersion_url + ' does not answer')
        return False, -1

    if latestLocalVersion['mainVersion'] == latestVersionNumber:
        print
        "no new version"
        return False, []
    else:
        return True, latestVersion


def readElectionResults(fields, year, latestVersionNumber):
    candidates = []
    try:
        pollingresult = 'https://vaalit-test.yle.fi/content/kv' + str(year) + '/' + str(
            latestVersionNumber) + '/electorates/1/municipalities/91/partyAndCandidateResults.json'

        print('retrieving the latest candidate data from ' + pollingresult)
        # try to read the candidate data from the local file system first
        try:
            response = urllib2.urlopen(pollingresult)
            results = json.loads(response.read())
        except:
            print('cannot fetch the candidate data')

        candidates = results['candidateResults']
        print('found results for ' + str(len(candidates)) + ' candidates')
        # candidates_elected = filter(elected, candidates)
    except:
        pass

    try:
        candidate_data = [[x[y].encode('utf8') if isinstance(x[y], unicode) else x[y] for y in fields] for x in candidates]
    except:
        pass
        print('something went wrong: could not get the candidate data')
        for x in candidates:
            print x
        candidate_data = []

    columns_finnish = fields[:]
    columns_finnish[2]='etunimi'
    columns_finnish[3] = 'sukunimi'

    return pandas.DataFrame(candidate_data, columns=columns_finnish)

def processOpinions(year):
    #opinions_to_num = {u't<U+00E4>ysin eri mielt<U+00E4>': 0,
    #                   u'jokseenkin eri mielt<U+00E4>': 1,
    #                    u'ohita kysymys': float('nan'), 'NaN': float('nan'),
    #                   u'jokseenkin samaa mielt<U+00E4>': 3,
    #                   u't<U+00E4>ysin samaa mielt<U+00E4>': 4}
    opinions_to_num = {'täysin eri mieltä': 0,
                       'jokseenkin eri mieltä': 1,
                       'ohita kysymys': float('nan'), 'NaN': float('nan'),
                       'jokseenkin samaa mieltä': 3,
                       'täysin samaa mieltä': 4}

    with codecs.open('kuntavaalit' + str(year) + '/candidate_answer_data_' + str(year   ) + '.csv', 'r',
                 encoding='utf-8') as csvfile:
        opinion_data = pandas.read_csv(csvfile, delimiter=";")
    questions = opinion_data.filter(regex='\|') \
            .select(lambda x: not re.search('.*Valitse.*', x), axis=1)
    for opinion in opinions_to_num:
        questions = questions.replace(opinion, opinions_to_num[opinion])
    questions = questions.fillna(questions.mean())
    questions_col = questions.columns.values
    questions = pandas.DataFrame(preprocessing.scale(questions), columns=questions_col)
    # scale & impute

    identity = opinion_data.filter(regex='etunimi|sukunimi')
    #    .replace('\<U\+00E4\>', 'ä', regex=True) \
    #    .replace('\<U\+00F6\>', 'ö', regex=True) \
    #    .replace('\<U\+00D6\>', 'Ö', regex=True) \
    #    .replace('\<U\+00C5\>', 'Ö', regex=True) \
    #    .replace('\<U\+00D8\>', 'Ø', regex=True)
    candidate_opinions = pandas.concat([identity, questions], axis=1)
    return candidate_opinions

def readTargetVector(year):
    with codecs.open('kuntavaalit' + str(year) + '/target_vector_new.csv', 'r',
                     encoding='utf-8') as csvfile:
        target_vector = pandas.read_csv(csvfile, delimiter=";")
    target_vector = pandas.DataFrame(
        np.array(target_vector['target_vec']).reshape(1,len(target_vector)), columns=target_vector['kysymykset'])
        # reshape needed because pandas thoughts numpy vector as nx1
    return target_vector

def matchCandidateswithTarget(opinions, target):
    matched_columns = pandas.concat([opinions, target], join='outer')
    opinions = np.array(matched_columns.filter(regex='\|'))
    target = opinions[-1,]
    match = np.dot(opinions[:-1,], target)
    candidate_matches = pandas.DataFrame(list(zip(matched_columns['sukunimi'].tolist(),
                                          matched_columns['etunimi'].tolist(),
                                          match.tolist())), columns=['sukunimi', 'etunimi', 'LKH_match'])
    return candidate_matches.sort_values(by='LKH_match')



# main
cont = True
saved_version = -1
candidate_opinions = processOpinions(year)
target_vector = readTargetVector(year)

candidate_matches = matchCandidateswithTarget(candidate_opinions, target_vector)

while(cont):
    (newResultsExist, versionData) = checkIfNewResults(year)
    if newResultsExist:
        polling_results = readElectionResults(fields, year, versionData['mainVersion'])
        versionNumber = versionData['mainVersion']
        if not polling_results.empty:
            polling_results = pandas.merge(polling_results, candidate_matches, how='outer', on=['etunimi', 'sukunimi'])
            polling_results.to_csv('kuntavaalit' + str(year) + '/results_latest.csv', encoding='utf8')
            with codecs.open('kuntavaalit' + str(year) + '/version_latest.json', 'w', encoding='utf-8') as f:
                json.dump(versionData, f)
    # cont = False

    print('waiting')

    time.sleep(wait_time)
