#!/usr/bin/python
from scipy.stats.stats import pearsonr
import re

class Correlation:
    def __init__(self,*arg):
        self.vars = []
        self.values = []
        for i in arg:
            self.vars.append(i)
            self.values.append([])

    def addData(self,*arg):
        for i in range(0,len(arg)):
            self.values[i].append(arg[i])

    def __str__(self):
        output = ''
        for i in range(0,len(self.values)):
            for j in range(0,len(self.values)):
                if i < j:
                    output += 'Correlation ' + self.vars[i] + ' & ' + self.vars[j] + ':\n' + str(pearsonr(self.values[i],self.values[j])) + '\n'
            
        return output

def list_unique(original_list):
    new_list = []
    for l in original_list:
        if l not in new_list:
            new_list.append(l)
    return new_list

def getURLs(text):
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    return urls