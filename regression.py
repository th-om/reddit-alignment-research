#!/usr/bin/python
import os
import pprint
import csv
pp = pprint.PrettyPrinter(indent=4)
import numpy as np
import statsmodels.api as sm
from random import shuffle
from helpers import *

class RegressionModel:
    def __init__(self,corpus):
        self.use_vars = [
            'depth',
            'length',
            'time_since_submission',
            'time_since_parent',
            'parent_score',
            'age',
            'karma',
            'submission_score',
            'urls',
            'alignment_content',
            'alignment_syntax_3',
            'alignment_features_binary',
            'alignment_features_frequency'
        ]
        self.corpus = corpus
        self.folder = self.corpus + '/analysis'
        self.data = {}
        self.scores = []
        self.excluded_amount = 0

    def setVars(self,use_vars):
        self.use_vars = use_vars

    def pairwiseCorrelation(self):
        self.loadData()
        correlation = Correlation(
            'depth',
            'length',
            'time_since_submission',
            'time_since_parent',
            'parent_score',
            'age',
            'karma',
            'submission_score',
            'urls',
            'alignment_content',
            'alignment_syntax_3',
            'alignment_features_binary',
            'alignment_features_frequency'
        )
        
        for i in range(0,len(self.data['depth'])):
            correlation.addData(
                self.data['depth'][i],
                self.data['length'][i],
                self.data['time_since_submission'][i],
                self.data['time_since_parent'][i],
                self.data['parent_score'][i],
                self.data['age'][i],
                self.data['karma'][i],
                self.data['submission_score'][i],
                self.data['urls'][i],
                self.data['alignment_content'][i],
                self.data['alignment_syntax_3'][i],
                self.data['alignment_features_binary'][i],
                self.data['alignment_features_frequency'][i]
            )
        print correlation

    def standardize(self,values):
        mean = np.average(values)
        std = np.std(values)
        for i in range(0,len(values)):
            values[i] = (values[i] - mean) / std
        return values


    def loadData(self):
        #Empty data
        self.scores = []
        self.data = {}
        self.excluded_amount = 0
        for var in self.use_vars:
            self.data[var] = []

        #Load the data
        for filename in os.listdir(self.folder):
            if '.csv' in filename:
                submission_id = filename.replace('.csv', '') 
                with open(self.folder + '/' + filename) as csvfile:
                    reader = csv.DictReader(csvfile)
                    
                    for item in reader:
                        if not self.isExcluded(item):
                            self.scores.append(int(item['score']))
                            for var in self.use_vars:
                                if 'alignment' in var:
                                    self.data[var].append(float(item[var]))
                                else:
                                    self.data[var].append(int(item[var]))
                                
    
    def isExcluded(self,item):
        for var in self.use_vars:
            if item[var] == '':
                self.excluded_amount += 1
                return True

        if item['alignment_syntax_3'] == '':
            self.excluded_amount += 1
            return True
        return False

    def reg_m(self,y, x):
        ones = np.ones(len(x[0]))
        X = sm.add_constant(np.column_stack((x[0], ones)))
        for ele in x[1:]:
            X = sm.add_constant(np.column_stack((ele, X)))
        results = sm.OLS(y, X).fit()
        return results


    def run(self):
        self.loadData()
        y = self.scores
        print sum(self.scores)/float(len(self.scores))
        x = []
        for i in range(0,len(self.use_vars)):
            print  'x' + str(i+1) + ': ' + self.use_vars[i]
            x.append(self.standardize(self.data[self.use_vars[i]]))

        x = list(reversed(x)) #The variables have to be inserted in reverse
        print 'Excluded: ' + str(self.excluded_amount)
        print self.reg_m(y, x).summary()


regressionModel = RegressionModel('corpus C')
regressionModel.pairwiseCorrelation()

regressionModel.setVars([
    #'age',
    'parent_score',
    'depth',
    'time_since_parent',
    'submission_score',
    'karma',
    'length',
    #'time_since_submission',
    'urls',
    'alignment_content',
    #'alignment_syntax_3',
    #'alignment_features_binary',
    #'alignment_features_frequency',    
])

regressionModel.run()
