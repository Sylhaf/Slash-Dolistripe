
from asyncio.windows_events import NULL
from time import sleep
from app_logging import logger_name, init as init_logging
import logging
logger = logging.getLogger(logger_name)
import requests,json
import datetime
import argparse


init_logging()

logger.debug(__name__)


logger.info("")
logger.info("")
logger.info("")
logger.info("-------         welcome to Slash-Dolistripe        -------")

# Method to read config file settings
logger.info(" --- -------------------------------------------------------------------------------- ---")
logger.info(" --- ---------------------------------- ARG PHASE ----------------------------------- ---")
logger.info(" --- -------------------------------------------------------------------------------- ---")


parser = argparse.ArgumentParser()
parser.add_argument("-v","--verbosity", help="increase output verbosity",action="store_true")
parser.add_argument("-d","--dry", help="perform a dry run",action="store_true")
parser.add_argument("-m","--mail", help="send invoice per mail to client",action="store_true")
parser.add_argument("-p","--planned", help="trigger planned work to ",action="store_true")

args = parser.parse_args()
if args.verbosity:
    logger.info("Args : Debug Verbose Enabled")
    logger.setLevel(logging.DEBUG)
else :
    logger.setLevel(logging.INFO)

args = parser.parse_args()
if args.dry:
    logger.info("Args : Dry Run Enabled")

args = parser.parse_args()
if args.mail:
    logger.info("Args : send invoice per Mails Enabled")


logger.info(" --- -------------------------------------------------------------------------------- ---")
logger.info(" --- ---------------------------------- CONF PHASE ---------------------------------- ---")
logger.info(" --- -------------------------------------------------------------------------------- ---")
logger.info("Reading Reference ConfIguration File")
import configparser
config = configparser.ConfigParser()
config.optionxform = str # to make the read Case Sensitive 
config.read('references.conf')

references_dict = config["list"]
stripe_api_key = config["credentials"]["stripe_api_key"]
dolibarr_username = config["credentials"]["dolibarr_username"]
dolibarr_password = config["credentials"]["dolibarr_password"]

if args.planned :
    dolibarr_planned_work_key = config["credentials"]["planned_work_key"]
    dolibarr_planned_work_cron_job_id = config["credentials"]["cron_job_id"]

contact_mail = None

if config.has_option("credentials", "contact_mail") :
    contact_mail = config["credentials"]["contact_mail"]

logger.debug("contact mail in configuration is : " + contact_mail)

logger.debug("Reading Stripe subscriptions references with CRM link to  subscription contract")
for reference in  references_dict:
    logger.debug("link reference found : " + reference  + " -> " + references_dict[reference])



logger.info(" --- -------------------------------------------------------------------------------- ---")
logger.info(" --- --------------------------------- STRIPE PHASE --------------------------------- ---")
logger.info(" --- -------------------------------------------------------------------------------- ---")

logger.info("testing connection to stripe...")
import requests
from requests.structures import CaseInsensitiveDict

headers = CaseInsensitiveDict()
headers["Accept"] = "application/json"
headers["Authorization"] = "Bearer "+ stripe_api_key

logger.debug("retrieving balance for test")
r = requests.get("https://api.stripe.com/v1/balance", headers=headers)
json_content = json.loads(r.text)
logger.debug(json.dumps(json_content, indent=4 , ensure_ascii=False))
assert r.status_code == 200
logger.info("Stripe OK")


logger.info("----------- Validating Stripe references and retrieving data -----------")

class crm_linked_invoice : 
    url    : str
    date   : datetime
    amount : float
    unpaid : bool = False

class invoice_link :

    stripe_subscription_reference : str
    contract_number               : int

    stripe_customer_ref    : str
    stripe_customer_name   : str
    stripe_customer_mail   : str
    stripe_paid_amount     : float
    stripe_epoch_date      : int
    stripe_invoice_url     : str
    stripe_invoice_number  : str


    crm_contract_activated     : bool = False
    crm_needs_new_invoice      : bool = False
    crm_needs_update           : bool = False
    crm_target_invoice         : crm_linked_invoice
    


invoice_links = set()


for reference in  references_dict:

    logger.info("retrieving Subscription data of " + reference)
    url = "https://api.stripe.com/v1/subscriptions/" + reference
    logger.debug("testing url : '" + url + "'")
    r = requests.get(url, headers=headers)
 
    assert r.status_code == 200
    subscription_json_data = json.loads(r.text)
    logger.debug("Subscription Data found : ")
    logger.debug(json.dumps(subscription_json_data, indent=4 , ensure_ascii=False))

    if subscription_json_data["status"] != "active" :
        logger.info("subscription not active, going to next")
        continue

    #retrieving customer data 
    latest_invoice_reference = subscription_json_data["latest_invoice"]
    logger.debug("latest invoice reference found : " + latest_invoice_reference)
    url = "https://api.stripe.com/v1/invoices/" + latest_invoice_reference
    r = requests.get(url, headers=headers)
    assert r.status_code == 200

    latest_invoice_json_data = json.loads(r.text)
    logger.debug("latest invoice Data found : ")
    logger.debug(json.dumps(latest_invoice_json_data, indent=4, ensure_ascii=False))

    #TODO verfiy invoice status to "paid"

    link = invoice_link()


    link.stripe_subscription_reference = reference
    link.contract_number        = references_dict[reference]
    link.stripe_paid_amount     = float(float(latest_invoice_json_data["amount_paid"]) / 100 )
    link.stripe_epoch_date      = latest_invoice_json_data["created"]
    link.stripe_customer_name   = latest_invoice_json_data["customer_name"]
    link.stripe_customer_mail   = latest_invoice_json_data["customer_email"]
    link.stripe_invoice_url     = latest_invoice_json_data["hosted_invoice_url"]
    link.stripe_invoice_number  = latest_invoice_json_data["number"]


    logger.info("latest invoice customer info : " + link.stripe_customer_name + " - " + link.stripe_customer_mail)
    logger.info("latest invoice paid amount   : " + str(link.stripe_paid_amount) + latest_invoice_json_data["currency"])
    logger.info("latest invoice payment date  : " + str(datetime.datetime.fromtimestamp(int(link.stripe_epoch_date))))
    logger.info("latest invoice url : " + link.stripe_invoice_url )

    # subscription reference - dolibarr contract reference - name - mail - amount - date of payment. 




    invoice_links.add(link)


    logger.info(" ----------- Subscription Data OK")
    

logger.info("Stripe Phase OK")


logger.info(" --- -------------------------------------------------------------------------------- ---")
logger.info(" --- -------------------------------- READ CRM PHASE -------------------------------- ---")
logger.info(" --- -------------------------------------------------------------------------------- ---")

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import logging
from selenium.webdriver.remote.remote_connection import LOGGER
LOGGER.setLevel(logging.CRITICAL)


logger.info("CRM Login")
driver = webdriver.Edge()
driver.get("https://crm.slashthd.fr/index.php")
assert "Identifiant" in driver.title


driver.find_element(By.NAME,"username").send_keys(str(dolibarr_username))
pass_field = driver.find_element(By.NAME,"password")
pass_field.send_keys(str(dolibarr_password))
pass_field.send_keys(Keys.RETURN)
logger.info(driver.title)
assert "Accueil" in driver.title

logger.info("login successful")

current_date = datetime.datetime.now()

if args.planned : 
    logger.info("preparation phase : trigger planned work in CRM")
    work_url = "https://crm.slashthd.fr/public/cron/cron_run_jobs_by_url.php?securitykey=" + \
        dolibarr_planned_work_key + "&userlogin=" + dolibarr_username + "&id=" + str(dolibarr_planned_work_cron_job_id)
    driver.get(work_url)
    logger.info("temporization 1 sec....")
    sleep(1)

# iterating over links63
logger.info("iterating over invoice links")
link : invoice_link
for link in invoice_links :
    link.crm_contract_activated == False
    logger.debug("treating contract : " + link.contract_number)
    driver.get("https://crm.slashthd.fr/contrat/card.php?id=" + str(link.contract_number))
    logger.debug("testing if services are activated")
    #iterating service 


    contract_lines = driver.find_elements(By.XPATH,"//div[contains(@id,'contrat-lines-container')]/div")
    logger.info(str(len(contract_lines)) + " service line found")
    for line in contract_lines : 
        service_name   = line.find_element(By.CLASS_NAME,"classfortooltip").text
        service_status = line.find_element(By.CLASS_NAME,"badge-status").text

        logger.info(service_name)
        logger.info(service_status)

        if "En service" in service_status :
            logger.debug("crm contract have at least one service activated")
            link.crm_contract_activated = True


    if link.crm_contract_activated == False:
        logger.info("the contract with  number " + link.contract_number + " have all services disabled, SKIPPING CONTRACT")
        continue

    contract_links_table = driver.find_element(By.XPATH,'//table[@data-block="showLinkedObject"]')
    contract_links_elements = driver.find_elements(By.XPATH,'//tr[@data-element="facture"]')
   
    link.crm_needs_new_invoice = True

    if len(contract_links_elements) == 0  or contract_links_elements == None:
         link.crm_needs_new_invoice = False
    
    if not link.crm_contract_activated : 
        link.crm_needs_new_invoice = False

    for element in contract_links_elements : 

        current_invoice = crm_linked_invoice()
        current_invoice.url = element.find_element(By.CLASS_NAME, "linkedcol-name").find_element(By.TAG_NAME,"a").get_attribute("href")
        current_invoice.amount = float(element.find_element(By.CLASS_NAME, "linkedcol-amount").text.replace(',', "."))
        current_invoice.date = datetime.datetime.strptime(element.find_element(By.CLASS_NAME, "linkedcol-date").text, '%d/%m/%Y')

        if element.find_element(By.CLASS_NAME, "linkedcol-statut").find_element(By.TAG_NAME,"span").get_attribute("title") == "Impayée" : 
            logger.debug("invoice is unpaid")
            current_invoice.unpaid = True
    
        logger.info("-----")
        logger.info("CRM linked invoice for customer : " + link.stripe_customer_name + " - " + link.stripe_customer_mail)
        logger.info("CRM linked invoice url : " + current_invoice.url)
        logger.info("CRM linked invoice date : " + str(current_invoice.amount))
        logger.info("CRM linked invoice amount : " + str(current_invoice.date))
        logger.info("CRM linked invoice unpaid ?  : " + str(current_invoice.unpaid))
        logger.info("-----")
    

        stripe_date  = datetime.datetime.fromtimestamp(link.stripe_epoch_date)

        #checking if new invoice is needed for the month
        if current_invoice.date.year == current_date.year :
            if current_invoice.date.month == current_date.month :
                logger.debug("invoice link does not need a new invoice for this month")
                link.crm_needs_new_invoice = False #TODO check all month since last invoice

        #checking if invoice is eligible to update
        if current_invoice.date.year == stripe_date.year :
            if current_invoice.date.month == stripe_date.month :
                if current_invoice.date.day <= stripe_date.day :

                    if current_invoice.unpaid : 
                        
                        if link.stripe_paid_amount == current_invoice.amount :

                            logger.info("Current crm invoice is unpaid, and corresponding to same month and amount as stripe payment")
                            logger.info(" ## Target invoice FOUND !  ##")
                            link.crm_needs_update = True
                            link.crm_target_invoice = current_invoice
            


logger.info(" --- -------------------------------------------------------------------------------- ---")
logger.info(" --- -------------------------------- SUMMARY PHASE --------------------------------- ---")
logger.info(" --- -------------------------------------------------------------------------------- ---")

logger.info("summary of actions")

if len(invoice_links) == 0 :
    logger.info("## no action pending detected ##")

action = False

link : invoice_link
for link in invoice_links :

    if link.crm_contract_activated : 
        if link.crm_needs_update :
            action = True
            logger.info(" ## ------------------------------- ##")
            logger.info("@@ INVOICE UPDATE PENDING : ")
            logger.info("stripe invoice customer info : " + link.stripe_customer_name + " - " + link.stripe_customer_mail)
            logger.info("stripe invoice paid amount   : " + str(link.stripe_paid_amount) + " " + latest_invoice_json_data["currency"])
            logger.info("stripe invoice payment date  : " + str(datetime.datetime.fromtimestamp(int(link.stripe_epoch_date))))
            logger.info("CRM linked invoice url : " + link.crm_target_invoice.url)
            logger.info("CRM linked invoice date : " + str(link.crm_target_invoice.amount))
            logger.info("CRM linked invoice amount : " + str(link.crm_target_invoice.date))
            logger.info("CRM linked invoice unpaid ?  : " + str(link.crm_target_invoice.unpaid))
            logger.info(" ## ------------------------------- ##")
        
        if link.crm_needs_new_invoice :
            Action = True
            logger.info(" ## ------------------------------- ##")
            logger.info("New Invoice Generation Pending")
            logger.info("invoice customer info : " + link.stripe_customer_name + " - " + link.stripe_customer_mail)
            date_string = format(current_date,'01/%m/%Y')
            logger.info("planned date : " + date_string)
            logger.info(" ## ------------------------------- ##")
        
if not action :
    logger.info("## no action pending detected ##")


if args.dry:
    driver.close()
    logger.info("dry run enabled, exiting here...")
    exit(0)


logger.info(" --- -------------------------------------------------------------------------------- ---")
logger.info(" --- -------------------------------- ACTION PHASE ---------------------------------- ---")
logger.info(" --- -------------------------------------------------------------------------------- ---")


for link in invoice_links :

    if link.crm_contract_activated : 
        if link.crm_needs_update :

            logger.info(" ## ------ Creating Payment ------ ##")
            logger.info("stripe invoice customer info : " + link.stripe_customer_name + " - " + link.stripe_customer_mail)
            logger.info("stripe invoice paid amount   : " + str(link.stripe_paid_amount) + " " + latest_invoice_json_data["currency"])
            logger.info("stripe invoice payment date  : " + str(datetime.datetime.fromtimestamp(int(link.stripe_epoch_date))))
            logger.info("CRM linked invoice url : " + link.crm_target_invoice.url)
            logger.info("CRM linked invoice date : " + str(link.crm_target_invoice.amount))
            logger.info("CRM linked invoice amount : " + str(link.crm_target_invoice.date))
            logger.info("CRM linked invoice unpaid ?  : " + str(link.crm_target_invoice.unpaid))

 

            driver.get(link.crm_target_invoice.url)
            pay_url = driver.find_element(By.XPATH, "//*[text()='Saisir règlement']").get_attribute("href")
            driver.get(pay_url)
            stripe_payment_date = datetime.datetime.fromtimestamp(int(link.stripe_epoch_date))
            date_string = format(stripe_payment_date,'{%d/%m/%Y}')
            driver.find_element(By.ID, "re").send_keys(date_string)
            driver.find_element(By.NAME, "comment").send_keys("Payment treated by automation - Slash-DoliStripe \n stripe invoice URL : " + link.stripe_invoice_url )
            driver.find_element(By.CLASS_NAME,'AutoFillAmout').click()
            driver.find_element(By.NAME, "num_paiement").send_keys(link.stripe_invoice_number)
            driver.find_element(By.XPATH,'//input[@value="Payer"]').click()
            driver.find_element(By.XPATH,'//input[@value="Valider"]').click()

            if args.mail:
                logger.info("sending email to client...")
                driver.find_element(By.XPATH, "//*[text()='Envoyer email']").click()
                driver.find_element(By.ID, "sendto").send_keys(link.stripe_customer_mail)
                if contact_mail is not None : 
                    driver.find_element(By.ID, "sendtocc").send_keys(contact_mail)
                driver.find_element(By.ID, "sendmail").click()
                


logger.info(" --- -------------------------------------------------------------------------------- ---")
logger.info(" --- -------------------------------- CLEANING PHASE -------------------------------- ---")
logger.info(" --- -------------------------------------------------------------------------------- ---")


driver.close()
exit(0)