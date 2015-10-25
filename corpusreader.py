#!/usr/bin/python
import os
import unicodecsv as csv
import re
import nltk
import json

class Corpus:
    def __init__(self,folder = 'corpus',min_words = 0, max_words = 99999):
        self.folder = folder
        self.min_words = min_words
        self.max_words = max_words
        self.karma_data = None
        
    def iterate(self):    			
        for filename in os.listdir(self.folder):
            if 'submission' in filename:
                get_id = filename.split('_')
                submission_id = get_id[1].replace('.csv', '') 
                submission = Submission(self, submission_id)
                if len(submission.getWords()) >= self.min_words and len(submission.getWords()) <= self.max_words:
                    yield submission

    def summarize(self):
        submissions = 0
        comments = 0
        for submission in self.iterate():
            submissions += 1
            for comment in submission.getComments():
                comments += 1

        print "Submissions: " + str(submissions)
        print "Comments: " + str(comments)


    def getKarmaData(self):
        if not self.karma_data:
            self.karma_data = {}
            with open(self.folder + '/redditors/karma.csv') as csvfile:
                reader = csv.DictReader(csvfile)
                for data in reader:
                    self.karma_data[data['redditor']] = {'comment_karma': int(data['comment_karma']), 'link_karma': int(data['link_karma'])}
        return self.karma_data

class Message:
    def removeUrls(self,text):
        return re.sub(r'https?:\/\/[\/a-zA-Z0-9\.\-_%\?=&]+', '', text, flags=re.MULTILINE)

    def tokenize(self,text):
        text = self.removeUrls(text)
        text = re.sub(r'[\<\>\[\]\(\)\*]', '', text, flags=re.MULTILINE) #Remove mark-up
        return nltk.word_tokenize(text)

    def getWords(self):
        if not hasattr(self, 'words'):
            text = self.body
            text = self.removeUrls(text)
            text = text.replace('\n',' ')
            text = text.split(' ')
            if self.__class__.__name__ == 'Submission':
                #In submissions, the title also belongs to the text
                text = self.title.split(' ') + text
            self.words = []
            for word in text:
                word = word.strip()
                if not word in ['#','/','[',']','}','--',',','-/','+','-','((','))']:
                    if word:
                        self.words.append(word.lower().strip().strip(',.;:?!-#*[]()'))
        return self.words

    def setAttributes(self,attributes):
        for attr,value in attributes.items():
            if attr == 'author':
                value = Redditor(self.corpus,value) #Convert to Redditor
            elif attr == 'score' or attr == 'num_comments' or attr == 'created_utc' or attr == 'collected_utc':
                value = int(value) #Convert to integer
            elif attr == 'score_hidden' or attr == 'is_root':
                value = value == '1' #Convert to boolean
            setattr(self, attr, value)

    def getPosTags(self):
        if not hasattr(self, 'pos_tags'):

            #Get pos tags from cache if possible
            cachefilename = self.corpus.folder + '/cache/pos_tags_' + self.__class__.__name__ + '_' + self.id + '.json'
            if os.path.isfile(cachefilename):
                with open(cachefilename) as cachefile:
                    content = cachefile.read()
                    return json.loads(content)

            tags = nltk.pos_tag(self.tokenize(self.body))
            if self.__class__.__name__ == 'Submission':
                #In submissions, the title also belongs to the text
                title_tags = nltk.pos_tag(self.tokenize(self.title))
                tags = title_tags + tags
            self.pos_tags = [tag for word,tag in tags]

            #Write pos tags to cache
            with open(cachefilename, 'w') as cachefile:
                cachefile.write(json.dumps(self.pos_tags))
        return self.pos_tags

    def getNGram(self,n=2):
        tags = self.getPosTags()
        ngram = []
        for i in range(0,len(tags)+1-n):
            ngram.append(tuple(tags[i+j] for j in range(0,n)))
        return ngram

class Submission(Message):
    def __init__(self,corpus,id):
        self.corpus = corpus
        self.submission_csv = self.corpus.folder + '/submission_' + id + '.csv'
        self.comments_csv = self.corpus.folder + '/comments_' + id + '.csv'
        self.comments = None
        self.other_comments = [] #Contains comments that are not analyzed, but might still be useful for other info

        with open(self.submission_csv) as csvfile:
            reader = csv.DictReader(csvfile)
            self.setAttributes(list(reader)[0])

    def getComments(self):
        if not self.comments:
            self.comments = []
            with open(self.comments_csv) as csvfile:
                reader = csv.DictReader(csvfile)
                for data in reader:
                    comment = Comment(data,self,None)
                    if comment.author.exists and len(comment.getWords()) >= self.corpus.min_words and len(comment.getWords()) <= self.corpus.max_words:
                        self.comments.append(comment)
                    else:
                        self.other_comments.append(comment)
        return self.comments


class Comment(Message):
    def __init__(self,data,submission=None,redditor=None):
        if submission:
            self.corpus = submission.corpus
        else:
            self.corpus = redditor.corpus

        self.submission = submission
        self.redditor = redditor
        self.setAttributes(data)
        self.parent = None

    def getRelativeScore(self):
        if self.submission.score:
            return self.score / self.submission.score
        else:
            return self.score

    def getParent(self):
        if not self.parent:
            if self.is_root:
                #Comment is in the root, so the parent is the submission
                self.parent = self.submission
            else:
                #Find the parent comment in the submission object
                parent_id = self.parent_id.split('_')[1]
                for comment in self.submission.getComments():
                    if comment.id == parent_id:
                        self.parent = comment
                        break
                for comment in self.submission.other_comments:
                    if comment.id == parent_id:
                        self.parent = comment
                        break
        return self.parent

    def getDepth(self):
        obj = self
        depth = 0
        while obj.is_root == False:
            depth += 1
            obj = obj.getParent()
            if not obj:
                return None #Could be the case that one of the parents got deleted.
            
        return depth


class Redditor:
    def __init__(self,corpus,name):
        self.corpus = corpus
        self.name = name
        self.comments = None
        self.words = None
        self.ngram = None
        self.comments_csv = self.corpus.folder + '/redditors/redditor_' + self.name + '.csv'
        if os.path.isfile(self.comments_csv):
            self.exists = True
        else:
            self.exists = False

    def getComments(self):
        if not self.comments:
            self.comments = []
            with open(self.comments_csv) as csvfile:
                reader = csv.DictReader(csvfile)
                for data in reader:
                    self.comments.append(Comment(data,None,self))
        return self.comments
        
    def getWords(self):
        if not self.words:
            self.words = []
            for comment in self.getComments():
                self.words += comment.getWords()
        return self.words

    def getNGram(self,n=2):
        if not self.ngram:
            self.ngram = []
            for comment in self.getComments():
                self.ngram += comment.getNGram(n)
        return self.ngram

    def getCommentKarma(self):
        try:
            return self.corpus.getKarmaData()[self.name]['comment_karma']
        except KeyError:
            return None

    def getLinkKarma(self):
        try:
            return self.corpus.getKarmaData()[self.name]['link_karma']
        except KeyError:
            return None

