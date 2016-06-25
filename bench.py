__author__ = "Adam Kabbeke"

#A short script to parse transaction data

import urllib 
import json
import datetime
import collections as co
import string
import re

class Transaction:
	"""
	A wrapper class for transactions

	"""
	def __init__(self, transactionInfo):
		self.date = datetime.datetime.strptime(transactionInfo['Date'], "%Y-%m-%d").date()
		self.ammount = float(transactionInfo['Amount'])
		self.company = transactionInfo['Company'].lower()
		self.ledger = transactionInfo['Ledger']
		self.ccNumber = ''
		self.isValid = True

		self.sanityCheck()

		self.keywords = reduce(lambda x,y: x.replace(y, ''), string.punctuation, self.ledger).lower().split()
		self.company = ' '.join(self.company.split()).capitalize()

	def sanityCheck(self):
		"""
		Removes creditcard info and purchase info from the company name
		Also checks if the purchase info is correct

		"""
		ccNumber = re.search( r'#*x+[0-9]{4,4}', self.company, re.M|re.I)
		if ccNumber:
			self.ccNumber = ccNumber.group()
			self.company = self.company.replace(self.ccNumber, '')

		ammountInName = re.search( r'[0-9]+\.[0-9]{2,2}', self.company, re.M|re.I)
		if ammountInName:
			ammount = ammountInName.group()
			self.isValid = float(ammount) == self.ammount
			self.company = self.company.replace(ammount+' usd', '')

	def __str__(self):
		returnString =  'Ledger:  %s \n'%self.ledger
		returnString += 'Company: %s \n'%self.company
		returnString += 'Date:    %s \n'%self.date
		returnString += 'Ammount: $%.2f \n'%self.ammount
		returnString += 'Valid:   %s \n'%self.isValid
		return returnString

class User:
	"""
	A wrapper for users with utility functions
	"""
	def __init__(self, name):
		self.name = name
		self.ballance = 0
		self.transactions = []
		self.invalid = []

	def addTransaction(self, transaction):
		"""
		Adds a transaction to the user's list of tansactions 
		"""
		if not self.checkDuplicate(transaction) and transaction.isValid:
			self.transactions += [transaction]
			self.ballance += transaction.ammount
		else:
			print 'Invalid transaction: ', self.name, transaction.ledger, transaction.ammount
			self.invalid = [transaction]

	def checkDuplicate(self, newTransaction):
		"""
		Checks if the transaction is duplicate of an existing transaction
		"""
		for oldTransaction in self.transactions:
			if newTransaction.__dict__ == oldTransaction.__dict__:
				return True
		return False

	def getTransactionCategories(self):
		"""
		Creates a transaction list for keywords
		"""
		categories = co.defaultdict(list)
		for transaction in self.transactions:
			for word in transaction.keywords:
				categories[word.lower()] += [transaction]
		return categories

	def getTransactionsByKeyword(self, keyword):
		"""
		Returns all  transactions associated with a keyword
		"""
		categories = self.getTransactionCategories()
		if keyword in categories:
			return categories[keyword]
		else:
			return None

	def printTransactionsByCategory(self, keyword):
		"""
		prints out transactions matching a keyword
		"""
		print 'Transactions for "%s" with keyword: "%s" \n'%(self.name, keyword)
		category = self.getTransactionsByKeyword(keyword)
		if category:
			self.printTransactions(category)
		else:
			print 'No transactions found matching keyword: %s \n'%keyword

	def printTransactions(self, transactions):
		"""
		prints out a list of transactions and a ballance
		"""
		ballance = 0
		for transaction in transactions:
			ballance += transaction.ammount
			print transaction

		print 'Transactions ballance: $%.2f \n'%ballance

	def ballanceOnDate(self, date):
		"""
		Returns the users ballance on a specified date
		"""
		return sum([x.ammount for x in self.transactions if x.date<date])

class TransactionManager:
	"""
	Retrives and parses user transaction data
	"""
	def __init__(self):
		self.tranactionsList = []
		self.users = {}
		self.getTransactions()
		self.parseTransactions()

	def getJsonData(self, url):
		"""
		Pulls json data from a remote source
		"""
		try:
			response = urllib.urlopen(url)
			pageData = json.loads(response.read())
			return pageData
		except:
			return None

	def getTransactions(self):
		"""
		Pulls all transactions form the web interface

		Note: Pulls the first page twice so could be cleaner
		"""

		firstPageData = self.getJsonData("http://resttest.bench.co/transactions/1.json")
		tansactionsCount = 0
		pageIndex = 1

		while tansactionsCount < firstPageData['totalCount']:
			pageData = self.getJsonData("http://resttest.bench.co/transactions/%i.json"%pageIndex)
			if pageData:
				for transactionData in pageData['transactions']:
					self.tranactionsList += [Transaction(transactionData)]
				tansactionsCount += len(pageData['transactions'])
			pageIndex += 1

	def parseTransactions(self):
		"""
		parses the transaction data
		"""
		for transaction in self.tranactionsList:
			if not transaction.company in self.users:
				self.users[transaction.company] = User(transaction.company)
			self.users[transaction.company].addTransaction(transaction)

if __name__ == '__main__':

	t = TransactionManager()

	for username in t.users:
		print username, t.users[username].ballanceOnDate(datetime.datetime.now().date())

	for username in t.users:
		t.users[username].printTransactionsByCategory('meals')
	
