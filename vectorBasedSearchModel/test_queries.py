# Basic libraries
import os, math
import operator
import pickle

#NLP library used
import nltk
nltk.download('punkt')
nltk.download('stopwords')
from nltk import regexp_tokenize
from nltk.corpus import stopwords
from spellchecker import SpellChecker

# Making the vector space model.
def initializeMem():
	f = open('postingLists','rb')
	global invertedIndex
	invertedIndex = pickle.load(f)
	f.close()
	f = open('docTitles','rb')
	global docSet
	docSet = pickle.load(f)
	f.close()
	global checker
	checker = SpellChecker()

# Using notation lnc.ltc
base = 10
k= 10

def cosineNorm(wt):
	# if(len(wt) == 1):
	# 	return wt
	a = 0
	for i in wt:
		a += i*i
	a = 1/math.sqrt(a)
	wt = [a*x for x in wt]
	return wt

def normalizeDoc(wt,docId):
	for i in range(len(wt)):
		wt[i] = wt[i]*docSet[docId][1]
	return wt

def processQuery(query, NumberOfDocs):
	listOfWords = regexp_tokenize(query.lower(), r'[,.?!"\s–\-]',gaps=True)
	queryDist = nltk.FreqDist(listOfWords)
	popWords = []
	for x in queryDist:
		if x not in invertedIndex:
			popWords.append(x)
	for x in popWords:
		# Title spelling correction
		temp = checker.correction(x)
		if temp in invertedIndex:
			queryDist[temp] = queryDist[x]
		queryDist.pop(x)
	# If query is empty(Contains only stop words or non known words)
	if(queryDist == {}):
		return([],[],[])
	axis = [x for x in queryDist]
	queryWt = [1 + math.log(queryDist[x], base) for x in queryDist]
	idfWt = [math.log(float(NumberOfDocs)/len(invertedIndex[x])) for x in axis]
	queryWt = [queryWt[i]*idfWt[i] for i in range(len(axis))]
	queryWt = cosineNorm(queryWt)
	return (axis,queryWt,queryDist)

def fetchDocuments(axis):
	a = {}
	for word in axis:
		for node in invertedIndex[word]:
			a[node[1]] = True
	return list(a)

def getTermFrequency(word,docId):
	for node in invertedIndex[word]:
		if(node[1] == docId):
			return (1 + math.log(node[0],base))
	return 0

def weightDoc(axis, docId):
	docWt = []
	for idx in range(len(axis)):
		docWt.append(getTermFrequency(axis[idx], docId))
	return docWt

def scoreDoc(qWt, dWt):
	score = 0
	for i in range(len(qWt)):
		score += qWt[i]*dWt[i]
	return score

def jaccardCoefficient(a,b):
	# a and b being Freq Distributions
	intersecCount =0
	for i in a:
		if(i in b):
			intersecCount += 1
	unionCount = len(a.keys())+len(b.keys())-intersecCount
	return intersecCount/unionCount

def sortByKey(pair):
	return pair[0]

def sortByJaccardCoefficient(topResults, queryDist, docSet):
	tempResults = []
	for res in topResults:
		title = regexp_tokenize(docSet[res[0]][0].lower(), r'[,.?!"\s–\-]',gaps=True)
		coeff = jaccardCoefficient(nltk.FreqDist(title), queryDist)
		tempResults.append((coeff,res))

	tempResults.sort(key=sortByKey,reverse=1)
	topResults = [x[1] for x in tempResults]
	return topResults

def searchDocuments(query,limit):
	(axis,queryWt,queryDist) = processQuery(query,len(docSet))
	if(axis == []):
		return axis
	docList = fetchDocuments(axis)
	scores = {}
	for doc in docList:
		docWt = weightDoc(axis, doc)
		docWt = normalizeDoc(docWt,doc)
		scores[doc] = scoreDoc(queryWt, docWt)

	results = sorted(scores.items(),key=operator.itemgetter(1),reverse=1)
	limit = min(len(results), limit)
	topResults = results[:limit]
	
	# Sorting by Jaccard Coefficient
	topResults = sortByJaccardCoefficient(topResults,queryDist,docSet)
	return topResults

def showResults(results,docSet):
	for i in range(len(results)):
		print("["+str(i+1)+"] "+docSet[results[i][0]][0])

initializeMem()
while(1):
	print("Search engine(wiki AA):",end='')
	query = input()
	if(query == 'exit'):
		break
	if(query == ""):
		print("Query can not be empty")
	results = searchDocuments(query, k)
	if results:
		showResults(results,docSet)
	else:
		print("No results Found")