import os
from dotenv import load_dotenv
import random
import boto3
import time
from datetime import datetime

# from plutus_tracker.plutus_browser import PlutusBrowser
# from plutus_tracker import balance
# from paypal_browser import PayPalBrowser

load_dotenv('.env', verbose=True, override=True)

NOTIFICATION_TOKEN = os.getenv('NOTIFICATION_TOKEN')

# import sys
# sys.path.append('../')

from push_notifications import push_notification
# from paydown_service.klarna_browser import KlarnaBrowser
from paypal_browser import PayPalBrowser

print('Starting points service...')

email_user = os.getenv('ALT_EMAIL')
email_pass = os.getenv('ALT_PASS')
main_user = os.getenv('MAIN_USER')
main_pass = os.getenv('MAIN_PASS')
AUTH_SECRET = os.getenv('AUTH_SECRET')
PHONE_NUM = os.getenv('PHONE_NUM')
EMAIL = os.getenv('EMAIL')
PASS = os.getenv('PASS')
AUTH = os.getenv('AUTH')

# push_notification(NOTIFICATION_TOKEN, "Paypal Payments", 'Getting Klarna purchasing power...')
#
# klarna = KlarnaBrowser(PHONE_NUM, email_user, email_pass)
# purchasing_power = klarna.get_purchasing_power()
# klarna.close()
#
# push_notification(NOTIFICATION_TOKEN, "Paypal Payments", 'Auto payments starting in one minute. Ensure Curve card is set to Klarna')

def randomise_payment_amounts(purchasing_power):
    # purchasing_power = 524

    n = random.randrange(3, 7)

    if purchasing_power > n:

        purchasing_power -= n * 2

        if datetime.now().weekday() < 5:
            purchasing_power -= 17

        lis = constrained_sum_sample_pos(n, purchasing_power)

        max_value = 120

        # Warning!! If a list comprehension is too complicated they are likely to become... incomprehensible!
        while max(lis) > max_value:
            [(lis.extend(constrained_sum_sample_pos(2, num)), lis.remove(num)) for num in lis if num > max_value]

        # Fixing single digit decimals .1 becomes .01
        lis2 = [random.randrange(99) for _ in range(len(lis))]
        lis2 = [f"0{x}" if len(str(x)) == 1 else x for x in lis2]

        return [f"{x}.{y}" for x, y in zip(lis, lis2)]

    return [f"{purchasing_power}.00"]

browser = PayPalBrowser(main_user, main_pass, AUTH_SECRET)
browser.login()

time.sleep(60)

balance = 1000
lis = randomise_payment_amounts(balance)

print(lis)
# lis = ['25.00', '25.00', '26.31', '50.00', '50.00', '17.35', '41.00', '76.00']
# make_payments(['655.00'], driver)
# make_payments(lis, driver)
# make_payments(lis, driver, card='Debit ••••xxxx')
# lis = ['4.00', '28.75', '28.75', '15.00']
browser.make_payments(lis, EMAIL, card='Debit ••••xxxx') # Get your card name from PayPal
browser.close()

push_notification(NOTIFICATION_TOKEN, "Paypal Payments", 'Starting withdrawal process')

withdrawal_browser = PayPalBrowser(EMAIL, PASS, AUTH)
bank, amount = withdrawal_browser.withdrawal()
withdrawal_browser.close()

push_notification(NOTIFICATION_TOKEN, "Paypal Payments", f'Withdrawal Complete. {amount} transferred to {bank}')

def constrained_sum_sample_pos(n, total):
    """Return a randomly chosen list of n positive integers summing to total.
    Each such list is equally likely to occur."""

    dividers = sorted(random.sample(range(1, total), n - 1))
    return [a - b for a, b in zip(dividers + [total], [0] + dividers)]




