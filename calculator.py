from selenium import webdriver
from selenium.webdriver.common import action_chains, keys
import time
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pprint

import config

def money_string_to_int(money_string):
	split_money = money_string.split('.')
	money = 0
	for i in reversed(range(len(split_money))):
		money = int(split_money[i])*pow(1000,len(split_money) - 1 - i) + money
	return money

def find(driver):
    #~ element = driver.find_element_by_class_name("notice-transfer")
    element = driver.find_elements_by_xpath('//*[@ng-switch-when="transfer"]')
    if element:
        return element
    else:
        return False

try:
	config.email
	config.password
	config.driver_location
	#~ config.teams_balance
except:
	print("Insert your driver location, teams intial balance, email and password first in config.py")
	exit()

#get driver and go to webpage
driver = webdriver.Chrome(config.driver_location) # initiate a driver, in this case Chrome
driver.get('http://app.biwenger.com/login')
driver.execute_script("document.querySelector('.btn.success').click()")
time.sleep(1)

#authenticate
username_field = driver.find_element_by_xpath('//*[@type="email"]') # get the username field
password_field = driver.find_element_by_xpath('//*[@ng-model="password"]') # get the password field
username_field.send_keys(config.email) # enter in your username
password_field.send_keys(config.password) # enter in your password
password_field.submit() # submit it
time.sleep(1)

#go to settings to get league settings
driver.get('http://app.biwenger.com/settings')
time.sleep(1)

#go to equipos section
driver.execute_script("document.querySelectorAll('ul.tabs>li>a')[1].click()")
time.sleep(1)

#get initial amount of money
value = int(driver.find_element_by_xpath("//select[@ng-model='league.settings.newSeason']").
find_element_by_xpath(".//option[@selected='selected']").get_attribute("value")[-1])

if(value != 1 and value != 3):
	print("Not allowed")
	exit()
elif(value==1):
	initial_amount = 20000000
elif(value==3):
	initial_amount = 40000000

#go to main menu before starting to scrap
driver.get('http://app.biwenger.com/')
time.sleep(1)
alert = driver.switch_to_alert()
alert.accept()
driver.get('http://app.biwenger.com/')
time.sleep(1)

# Balance of money of each team
teams_balance = {}


#scrap comuniame/biwenger
while True:

	try:
		secs = 4 # seconds
		element = WebDriverWait(driver, secs).until(find)
	except:
		break

	transfers_transfer = driver.find_elements_by_xpath('//*[@ng-switch-when="transfer"]')
	transfers_market = driver.find_elements_by_xpath('//*[@ng-switch-when="market"]')

	end_round_elems = driver.find_elements_by_class_name("notice-roundFinished");

	#money for end rounds
	for round_elem in end_round_elems:
		player_positions = round_elem.find_elements_by_tag_name("li")
		for player_position in player_positions:
			user = player_position.find_element_by_class_name("user").get_attribute("innerHTML").split("</span>")[1]
			try:
				money_string = player_position.find_element_by_xpath(".//span[@title=\"Dinero abonado\"]")
				.get_attribute("innerHTML").split("</i> ")[1].split("&")[0]
				try:
					teams_balance[user] += money_string_to_int(money_string)
				except:
					teams_balance[user] = initial_amount + money_string_to_int(money_string)
			except:
				pass

	#transfers
	for transfer in transfers_transfer:

		cards = transfer.find_elements_by_class_name("card")
		for card in cards:
			is_between_users = re.search(r'Cambia.*class=\"user.*class=\"user', card.get_attribute('innerHTML'))
			if(is_between_users != None):
				users = card.find_elements_by_class_name('user')
				user1 = users[0].get_attribute('innerHTML').split("</span>")[1]
				user2 = users[1].get_attribute('innerHTML').split("</span>")[1]
				money_string = card.find_elements_by_xpath(".//strong[@ng-bind=\"::transfer.amount|money\"]")[0]
				.get_attribute("innerHTML").split("&")[0]
				try:
					teams_balance[user1] -= money_string_to_int(money_string)
				except:
					teams_balance[user1] = initial_amount - money_string_to_int(money_string)
				try:
					teams_balance[user2] += money_string_to_int(money_string)
				except:
					teams_balance[user2] = initial_amount + money_string_to_int(money_string)

			else:
				user = card.find_element_by_class_name('user').get_attribute('innerHTML').split("</span>")[1]
				money_string = card.find_elements_by_xpath(".//strong[@ng-bind=\"::transfer.amount|money\"]")[0]
				.get_attribute("innerHTML").split("&")[0]
				is_a_buy = re.search('Cambia por', card.get_attribute('innerHTML'))
				is_a_sell = re.search('Vendido por', card.get_attribute('innerHTML'))
				if(is_a_sell != None):
					try:
						teams_balance[user] += money_string_to_int(money_string)
					except:
						teams_balance[user] = initial_amount + money_string_to_int(money_string)

				elif(is_a_buy != None):
					try:
						teams_balance[user] -= money_string_to_int(money_string)
					except:
						teams_balance[user] = initial_amount - money_string_to_int(money_string)
				else:
					print("Error")

	#market
	for transfer in transfers_market:

		cards = transfer.find_elements_by_class_name("card")
		for card in cards:
			user = card.find_element_by_class_name('user').get_attribute('innerHTML').split("</span>")[1]
			money_string = card.find_elements_by_xpath(".//strong[@ng-bind=\"::transfer.amount|money\"]")[0]
			.get_attribute("innerHTML").split("&")[0]
			try:
				teams_balance[user] -= money_string_to_int(money_string)
			except:
				teams_balance[user] = initial_amount - money_string_to_int(money_string)


	#go to next page
	if (driver.find_element_by_class_name("pagination").find_elements_by_tag_name("li")[7]
	.get_attribute("class") == "disabled"):
		break
	else:
		driver.execute_script("document.querySelectorAll('ul.pagination>li>a')[7].click()")
		time.sleep(2)


pprint.pprint(teams_balance)
