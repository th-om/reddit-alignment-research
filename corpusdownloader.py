#!/usr/bin/python
import os
import praw
import unicodecsv as csv
import time


class CorpusDownloader:

    def __init__(self,subreddit='PoliticalDiscussion',num_submissions = 10, min_comments = 10):
        self.praw = praw.Reddit(user_agent='computational_pragmatics_project_tests',log_requests=1)
        self.subreddit = subreddit
        self.num_submissions = num_submissions
        self.min_comments = min_comments
        self.count_submissions = 0
        self.count_comments = 0
        self.count_redditors = 0

    def getSubmissions(self):
        #Loop through submissions until we have enough
        submissions = self.praw.get_subreddit(self.subreddit).get_new(limit=None)
        for submission in submissions:        
            if submission.selftext and submission.num_comments > self.min_comments:
                days_ago = (time.time() - submission.created_utc) / 86400.0
                if days_ago >= 7: #Only collect submissions of at least 7 days old
                    self.saveSubmission(submission)
                    self.getRedditorComments(submission.author)
                    if self.count_submissions == self.num_submissions:
                        break

    def getRedditorComments(self,redditor):
        #Get latest 10 comments from this Redditor
        if redditor: #Could be empty in case message was deleted

            #Get Redditor comments only if we don't have them yet
            filename = 'redditors/redditor_' + str(redditor) + '.csv'
            if not os.path.isfile('corpus/' + filename):
                try:
                    comments = redditor.get_comments('new','all',limit=10)
                    self.saveComments(comments,filename,True)
                    #Save karma data to csv file
                
                    with open('corpus/redditors/karma.csv', 'a') as csvfile:
                        csvfile.write(redditor.name + ',' + str(redditor.link_karma) + ',' + str(redditor.comment_karma) + '\n')
                except praw.errors.NotFound:
                    print "Error: Comments and/or Karma could not be found for this Redditor"

    def saveSubmission(self,submission):
        #Save submission data to csv
        with open('corpus/submission_' + submission.id + '.csv', 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['id', 'title','num_comments','author','body','score','permalink','subreddit','created_utc','collected_utc'])
            writer.writeheader()
            writer.writerow({
                'id': submission.id,
                'title': submission.title,
                'num_comments': submission.num_comments,
                'author': submission.author,
                'body': submission.selftext,
                'score': submission.score,
                'permalink': submission.permalink,
                'subreddit': submission.subreddit,
                'created_utc': int(submission.created_utc),
                'collected_utc': int(time.time())
            })

        submission.replace_more_comments(limit=None, threshold=0)
        flat_comments = praw.helpers.flatten_tree(submission.comments)
        self.saveComments(flat_comments,'comments_' + submission.id + '.csv')

        self.count_submissions += 1
        self.log()
    
    def saveComments(self,comments,filename,is_redditor=False):
        #Save comments on submission to csv
        with open('corpus/' + filename, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['id', 'is_root','parent_id','author','body','score','score_hidden','created_utc','collected_utc'])
            writer.writeheader()
            for comment in comments:
                writer.writerow({
                    'id': comment.id,
                    'is_root': int(comment.is_root),
                    'parent_id': comment.parent_id,
                    'author': comment.author,
                    'body': comment.body,
                    'score': comment.score,
                    'score_hidden': int(comment.score_hidden),
                    'created_utc': int(comment.created_utc),
                    'collected_utc': int(time.time())
                })
                if not is_redditor:
                    self.getRedditorComments(comment.author)
                    self.count_comments += 1
        if is_redditor:
            self.count_redditors += 1
            self.log()

    def log(self):
        print "Collected:" + str(self.count_submissions) + ' submissions, ' + str(self.count_comments) + ' comments, ' + str(self.count_redditors) + ' redditors'

    def run(self):
        #Prepare corpus dirs
        if not os.path.isdir('corpus/redditors'):
            os.makedirs('corpus/redditors')

        #Prepare csv file for Redditor karma data
        with open('corpus/redditors/karma.csv', 'w') as csvfile:
            csvfile.write('redditor,link_karma,comment_karma\n')

        #Start collecting data
        self.getSubmissions()



corpusDownloader = CorpusDownloader('PoliticalDiscussion',num_submissions = 1000)
corpusDownloader.run()