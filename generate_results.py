#!/usr/bin/python
import corpusreader
from scipy.stats.stats import pearsonr #Import function to calculate Pearson correlation coefficient
from helpers import *
import unicodecsv as csv
import pprint
pp = pprint.PrettyPrinter(indent=4)

def get_alignment_content(utterance1,utterance2):

    if not len(utterance1.getWords()):
        #Fail if no words
        return None

    if not len(utterance2.getWords()):
        #Fail if no words
        return None

    if not len(utterance2.author.getWords()):
        #Fail if we don't have author comments
        return None

    alignments = []
    for word in list_unique(utterance1.getWords()):
        amount = utterance2.getWords().count(word)
        base_frequency = utterance2.author.getWords().count(word) / float(len(utterance2.author.getWords()))
        expected_amount = base_frequency * len(utterance2.getWords())
        alignments.append(amount - expected_amount)

    average = sum(alignments)/float(len(alignments))

    weight = len(utterance1.getWords())/float(len(utterance2.getWords()))

    return average * weight

def get_alignment_syntax(utterance1,utterance2,n):

    if not len(utterance1.getNGram(n)):
        #N-gram can be empty, if amount of words < n
        return None

    if not len(utterance2.getNGram(n)):
        #N-gram can be empty, if amount of words < n
        return None

    if not len(utterance2.author.getNGram(n)):
        #N-gram can be empty if author only writes really short comments or there are not enough of them
        return None

    alignments = []
    for sequence in list_unique(utterance1.getNGram(n)):
        amount = utterance2.getNGram(n).count(sequence)
        base_frequency = utterance2.author.getNGram(n).count(sequence) / float(len(utterance2.author.getNGram(n)))
        expected_amount = base_frequency * len(utterance2.getNGram(n))
        alignments.append(amount - expected_amount)

    average = sum(alignments)/float(len(alignments))

    weight = len(utterance1.getNGram(n))/float(len(utterance2.getNGram(n)))

    return average * weight

def feature_alignment_binary(utterance1,utterance2,feature):

    if not len(utterance2.author.getComments()):
        return None

    feature_in_utterance1 = contains_feature(utterance1.getWords(),feature)
    

    count_feature_speaker2 = 0
    for comment in utterance2.author.getComments():
        count_feature_speaker2 += int(contains_feature(comment.getWords(),feature))
    prob_feature_speaker2 = count_feature_speaker2 / float(len(utterance2.author.getComments()))


    if not feature_in_utterance1:
        return None
    else:
        prob_feature_both_utterances = int(coordination(utterance1,utterance2,feature))
        conditional_probability = prob_feature_both_utterances

    return conditional_probability - prob_feature_speaker2

def feature_alignment(utterance1,utterance2,feature):

    if not len(utterance2.author.getComments()):
        return None

    feature_in_utterance1 = contains_feature(utterance1.getWords(),feature)

    count_feature_speaker2 = 0
    comment_length = 0
    for comment in utterance2.author.getComments():
        comment_length += len(comment.getWords())
        count_feature_speaker2 += int(count_feature(comment.getWords(),feature))
        
    if comment_length == 0:
        return None
    else:
        prob_feature_speaker2 = count_feature_speaker2 / float(comment_length)

    
    if not feature_in_utterance1:
        return None
    else:
        if (len(utterance2.getWords())) != 0:
            prob_feature_both_utterances = count_feature(utterance2.getWords(),feature) / float(len(utterance2.getWords()))
            conditional_probability = prob_feature_both_utterances
        else:
            conditional_probability = 0


    return conditional_probability - prob_feature_speaker2

def get_alignment_features_binary(utterance1,utterance2):
    alignments = []
    for name,feature in features.items():
        alignment = feature_alignment_binary(utterance1,utterance2,feature)
        if alignment is not None:
            alignments.append(alignment)

    if not len(alignments):
        return None
    else:
        return sum(alignments)/len(alignments)

def contains_feature(words,feature):
    for word in words:
        for f in feature:
            if word == f:
                return True
    return False

def count_feature(comment,feature):
    counter = 0
    for word in comment:
        for f in feature:
            if word == f:
                counter += 1
    return counter

def coordination(utterance1,utterance2,feature):
    found_utterance1 = False
    found_utterance2 = False

    words = utterance1.getWords()
    for word in words:
        if word in feature:
            for f in feature:
                if word == f:
                    found_utterance1 = True
                    break
        if found_utterance1:
            break
    
    if found_utterance1:
        words = utterance2.getWords()
        for word in words:
            if word in feature:
                for f in feature:
                    if word == f:
                        found_utterance2 = True
                        break
            if found_utterance2:
                break
    return found_utterance2





features = {}
class_names = ['articles','prepositions','auxiliary verbs','impersonal pronouns','adverbs','conjunctions','personal pronouns','quantifiers']
for class_name in class_names:
    with open('features/' + class_name + '.txt') as f:
        features[class_name] = [unicode(x.strip(),'utf-8') for x in f.readlines()]


corpus = corpusreader.Corpus('corpus C')

def alignment_all_features():
    comment_alignments = []
    comment_scores = []
    comment_scores_relative = []

    for submission in corpus.iterate():

        for comment in submission.getComments():
            parent = comment.getParent()
            if parent:
                comment_alignment = alignment(submission,comment)
                if comment_alignment is not None:
                    comment_alignments.append(comment_alignment)
                    comment_scores.append(comment.score)
                    comment_scores_relative.append(comment.getRelativeScore())
                    
    print 'Correlation with score: ',pearsonr(comment_alignments,comment_scores)
    print 'Correlation with relative score: ',pearsonr(comment_alignments,comment_scores_relative)
    
def alignment_per_feature():
    for name,feature in features.items():
        print name
        comment_alignments = []
        comment_scores = []
        comment_scores_relative = []

        for submission in corpus.iterate():
            for comment in submission.getComments():
                parent = comment.getParent()
                if parent:
                    comment_alignment = feature_alignment(submission,comment,feature)
                    if comment_alignment is not None:
                        comment_alignments.append(comment_alignment)
                        comment_scores.append(comment.score)
                        comment_scores_relative.append(comment.getRelativeScore())
        print 'Correlation with score: ',pearsonr(comment_alignments,comment_scores)
        print 'Correlation with relative score: ',pearsonr(comment_alignments,comment_scores_relative)

def correlation_length():

    correlation = Correlation('Length','Score','Relative score')
    
    comment_scores_relative = []
    for submission in corpus.iterate():
        for comment in submission.getComments():
            correlation.addData(
                len(comment.getWords()),
                comment.score,
                comment.getRelativeScore()
            )
    print correlation

def correlation_comment_karma():
    comment_karmas = []
    comment_scores = []
    comment_scores_relative = []
    for submission in corpus.iterate():
        for comment in submission.getComments():
            if comment.author.getCommentKarma():
                comment_karmas.append(comment.author.getCommentKarma())
                comment_scores.append(comment.score)
                comment_scores_relative.append(comment.getRelativeScore())
    print 'Correlation with score: ',pearsonr(comment_karmas,comment_scores)
    print 'Correlation with relative score: ',pearsonr(comment_karmas,comment_scores_relative)


def correlation_timing():

    correlation = Correlation('Timing','Score','Relative score')
    
    for submission in corpus.iterate():
        for comment in submission.getComments():
            parent = comment.getParent()
            if parent:
                correlation.addData(
                    comment.created_utc - submission.created_utc,
                    comment.score,
                    comment.getRelativeScore()
                )
    print correlation


def correlation_age():

    correlation = Correlation('Age','Score','Relative score')
    
    for submission in corpus.iterate():
        for comment in submission.getComments():
            parent = comment.getParent()
            if parent:
                correlation.addData(
                    comment.collected_utc - comment.created_utc,
                    comment.score,
                    comment.getRelativeScore()
                )
    print correlation

def correlation_depth():

    correlation = Correlation('Depth','Score','Relative score')
    
    for submission in corpus.iterate():
        for comment in submission.getComments():
            depth = comment.getDepth()
            if depth:
                correlation.addData(
                    depth,
                    comment.score,
                    comment.getRelativeScore()
                )
    print correlation

def correlation_submission_rating():
    correlation = Correlation('Submission rating','Score','Relative score')
    
    for submission in corpus.iterate():
        for comment in submission.getComments():
            correlation.addData(
                submission.score,
                comment.score,
                comment.getRelativeScore()
            )
    print correlation


i = 0
for submission in corpus.iterate():
    with open(submission.corpus.folder + '/analysis/' + submission.id + '.csv','w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['comment_id','score','depth','length','time_since_submission','time_since_parent','parent_score','age','karma','submission_score','urls','alignment_content','alignment_syntax_3','alignment_syntax_4','alignment_features_binary','alignment_features_frequency'])
        writer.writeheader()
        for comment in submission.getComments():
            i += 1
            print i
            parent = comment.getParent()

            depth = comment.getDepth()
            length = len(comment.getWords())
            time_since_submission = comment.created_utc - submission.created_utc
            if parent:
                time_since_parent = comment.created_utc - parent.created_utc
                parent_score = parent.score
            else:
                time_since_parent = None
                parent_score = None

            age = comment.collected_utc - comment.created_utc
            karma = comment.author.getCommentKarma()
            submission_score = submission.score
            urls = len(getURLs(comment.body))
            alignment_content = get_alignment_content(submission,comment)
            alignment_syntax_3 = get_alignment_syntax(submission,comment,3)
            alignment_syntax_4 = get_alignment_syntax(submission,comment,4)
            alignment_features_binary = get_alignment_features_binary(submission,comment)
            alignment_features_frequency = feature_alignment(submission,comment,features['prepositions'])

            row = {
                'comment_id': comment.id,
                'score': comment.score,
                'depth': depth,
                'length': length,
                'time_since_submission': time_since_submission,
                'time_since_parent': time_since_parent,
                'parent_score': parent_score,
                'age': age,
                'karma': karma,
                'submission_score': submission_score,
                'urls': urls,
                'alignment_content': alignment_content,
                'alignment_syntax_3': alignment_syntax_3,
                'alignment_syntax_4': alignment_syntax_4,
                'alignment_features_binary': alignment_features_binary,
                'alignment_features_frequency': alignment_features_frequency
            }
            pp.pprint(row)
            writer.writerow(row)
