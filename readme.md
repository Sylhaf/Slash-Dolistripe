

This project is meant to have a link between Stripe Subscriptions and Dolibar contract with reccuring invoice. 

I use it for my association who is an internet provider : Slash - [https://slashthd.fr](https://slashthd.fr)

The main goal of this script is to mark the dolibarr invoice as "paid" when the Stripe automatic payment occurs.

thanks [https://www.mistergeek.net](https://www.mistergeek.net) for the visibility. 

Manual : 

1. get a dolibarr account that can read/write invoices/contracts/clients and get an read Stripe API KEY, put both in a reference.conf file.  an exemple of conf is in the file references_example.conf.
2. Create your contract associated to your client in dolibarr and get his ID in its URL : https://dolibarr_instance.com/contrat/card.php?id=13 -> here the ID is 13
3. you have to wait the first payment of your client in Stripe, when it's done get the subscription ID, it looks like something like that : 
sub_1Lsdhjqsdlkqh2367sdhqjTx

put the two reference in the reference.conf

the script is using selenium and request. 

Console Option of the Script : 

usage: main.py [-h] [-v] [-d] [-m] [-p]

options:
  -h, --help       show this help message and exit
  -v, --verbosity  increase output verbosity
  -d, --dry        perform a dry run
  -m, --mail       send invoice per mail to client (to add copy mail to a mail check contact mail in refenrence example file)
  -p, --planned    trigger planned work to
  
  
  In order of execution the script will : 
  
  
  1. verify connection to Stripe
  2. Test All Stripe Subscription référence and gather Data about it ( last payment) 
  3. Connect to dolibarr via Selenium to Gather contracts last invoices data and their status.
  4. make a summary in console of what action will be perfomed
  5. perform actions : mark corresponding invoices as "paid" and if option is activated send a mail to the client registered in dolibarr. (it uses the Stripe Mail) 
