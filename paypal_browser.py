import contextlib
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import time
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from dotenv import load_dotenv
from pyotp import TOTP

load_dotenv(verbose=True, override=True)

# import sys
# sys.path.append('../')

from scraper import get_driver
from captcha_bypass import CaptchaBypass
from otp_bypass import TextBypass
# from common.aws_connection import connect_to_dynamodb

class PayPalBrowser(object):

    def __init__(self, email_user, email_pass, auth_secret, driver=None):
        self.email_user_id = email_user
        self.email_pass_id = email_pass
        self.auth_secret = auth_secret
        self.driver = driver or get_driver()
        self.driver.implicitly_wait(10)

    def authenticator(self):
        totp = TOTP(self.auth_secret)
        token = totp.now()
        for x in range(6):
            self.driver.find_element('id', f'ci-otpCode-{x}').send_keys(token[x])
        self.driver.find_element('xpath', '//button[@data-nemo="twofactorSubmit"]').click()

    def login(self):

        wait = WebDriverWait(self.driver, 60)

        self.driver.get('https://www.paypal.com/signin')

        time.sleep(2)

        if self.driver.find_elements('id', 'acceptAllButton'):
            self.driver.find_element('id', 'acceptAllButton').click()

        self.driver.find_element('id', 'email').clear()
        self.driver.find_element('id', 'email').send_keys(self.email_user_id)

        if self.driver.find_elements('id', 'btnNext'):
            self.driver.find_element('id', 'btnNext').click()
            time.sleep(2)

        # TODO: Programmatically get sitekey
        """
        API error ERROR_INVALID_KEY_TYPE: Passed sitekey is from another Recaptcha type.Try solve it as V2, V2 - invisible or V3. task
        finished with error: ERROR_INVALID_KEY_TYPE
        """
        sitekey_clean = '6LdCCOUUAAAAAHTE-Snr6hi4HJGtJk_d1_ce-gWB'

        g_response = CaptchaBypass(sitekey_clean, self.driver.current_url).bypass()

        self.driver.switch_to.frame(self.driver.find_element('xpath',
                                                   '//*[@id="grcv3enterpriseframe"]'))
        self.driver.execute_script(
            'var element=document.getElementById("g-recaptcha-response-100000"); element.style.display="";')
        self.driver.execute_script("""document.getElementById("g-recaptcha-response-100000").innerHTML = arguments[0]""",
                              g_response)
        self.driver.execute_script(
            'var element=document.getElementById("g-recaptcha-response-100000"); element.style.display="none";')
        self.driver.switch_to.default_content()

        element = wait.until(EC.presence_of_element_located((By.ID, "password")))
        # user_field_element = WebDriverWait(driver,10).until(lambda driver: driver.find_element('id', "email"))
        element.send_keys(self.email_pass_id)
        self.driver.find_element('id', 'btnLogin').click()

        self.otp_bypass()

        # wait.until(EC.presence_of_element_located((By.ID, "ci-otpCode-0")))
        # self.authenticator()

        wait.until(lambda driver: self.driver.current_url == 'https://www.paypal.com/myaccount/summary')

        return self.driver

    def otp_bypass(self):
        radio_btn = self.driver.find_element('css selector', "input[id='sms-challenge-option']")
        self.driver.execute_script("arguments[0].click();", radio_btn)
        self.driver.find_element('class name', 'challenge-submit-button').click()

        ## Read messages from imessage doesn't work on MacOS Sonoma
        code = TextBypass().check_code("PayPal: ", 'paypal')

        if self.driver.find_elements('id', 'ci-answer-0'):
            self.driver.find_element('id', 'ci-answer-0').send_keys(code)
        elif self.driver.find_elements('id', 'ci-otpCode-0'):
            self.driver.find_element('id', 'ci-otpCode-0').send_keys(code)

        self.driver.find_element('id', 'securityCodeSubmit').click()

    def make_payments(self, lis: list, recipient: str, card='Debit ••••xxxx'):
        """
        lis: list of payment amounts
        recipient: email address of recipient
        card: last four digits of card
        """
        self.driver.get('https://www.paypal.com/myaccount/transfer/homepage/pay')
        time.sleep(2)

        if 'paypal.com/myaccount' not in self.driver.current_url:
            self.login()

        wait = WebDriverWait(self.driver, 60)

        # Payments page
        for amount in lis:
            for attempt in range(2):  # Attempt twice if declined
                # try:
                    # amount = "115.00"
                    self.driver.get('https://www.paypal.com/myaccount/transfer/homepage/pay')
                    time.sleep(2)
                    wait.until(lambda driver: self.driver.find_element('id', 'fn-sendRecipient')).send_keys(recipient)
                    self.driver.find_element('id', 'fn-sendRecipient').send_keys(Keys.RETURN)
                    time.sleep(2)

                    # Send page
                    # amount = '1.00'
                    wait.until(lambda driver: self.driver.find_element('id', 'fn-amount')).send_keys(amount)

                    # driver.find_element('id', 'fn-amount')
                    self.driver.find_element('xpath', '//button[contains(text(), "Next")]').click()
                    time.sleep(5)

                    if self.driver.find_elements('id', 'challenge-heading'):
                        try:
                            self.otp_bypass()
                            element = WebDriverWait(self.driver, 30).until(lambda driver: self.driver.find_element('id', "fn-amount"))
                        except Exception as e:
                            print("fn-amount not found")
                            print(f"{e}")
                            self.driver.refresh()
                            code = TextBypass().check_code("PayPal: ", 'paypal')
                            if self.driver.find_elements('id', 'ci-answer-0'):
                                self.driver.find_element('id', 'ci-answer-0').send_keys(code)
                            elif self.driver.find_elements('id', 'ci-otpCode-0'):
                                self.driver.find_element('id', 'ci-otpCode-0').send_keys(code)
                            self.driver.find_element('id', 'securityCodeSubmit').click()

                    element = WebDriverWait(self.driver, 30).until(lambda driver: driver.find_element('id', "fn-amount"))
                    # Checking amount match
                    if element.get_attribute("value") != amount:
                        print(f'Amount mismatch, Expected: {amount} vs Actual: {element.get_attribute("value")}')
                        continue
                        # driver.close()
                        # driver.quit()
                        # quit()

                    time.sleep(3)
                    # Make payment
                    if card in self.driver.page_source:
                        self.driver.find_element('xpath', '//button[contains(text(), "Send")]').click()
                    else:
                        element = WebDriverWait(self.driver, 30).until(
                            lambda driver: self.driver.find_element('id', "selectedFundingOptionYourePayingWith"))
                        element.click()

                        time.sleep(5)

                        try:
                            WebDriverWait(self.driver, 30).until(
                                lambda driver: self.driver.find_element('xpath', '//button[contains(text(), "Show more")]')).click()
                        except TimeoutException:
                            print("No 'Show more' button")

                        try:
                            self.driver.find_element('xpath', f'//div[contains(text(), "{card}")]').click()
                        except ElementClickInterceptedException:
                            print(f"{card} click failed")
                            continue

                        self.driver.find_element('xpath', '//button[contains(text(), "Next")]').click()
                        time.sleep(2)
                        # element = WebDriverWait(self.driver, 10).until(
                        #     lambda driver: self.driver.find_element('xpath', '//button[contains(text(), "Send Money Now")]'))
                        element = WebDriverWait(self.driver, 10).until(
                            lambda driver: self.driver.find_element('xpath', '//button[contains(text(), "Send")]'))
                        element.click()

                    time.sleep(5)
                    # If declined
                    if self.driver.find_elements('xpath',
                                            '//div[@data-nemo="error-message-common"]') or 'success' not in self.driver.current_url:  # TODO: Find out successful payment url
                        print(f'Payment declined £{amount} - attempt: {attempt + 1}/2')
                        time.sleep(60)
                    else:
                        print(f'Payment successful £{amount}')
                        break
                # except Exception as e:
                #     print(e)
                #     continue

    def withdrawal(self):

        account = 'Barclays Bank'

        wait = WebDriverWait(self.driver, 30)

        time.sleep(2)
        if 'paypal.com/myaccount' not in self.driver.current_url:
            self.login()

        self.driver.get('https://www.paypal.com/myaccount/money/')

        if float(self.driver.find_element('class name', 'balanceDetails-amount').text.replace('£', '')) > 0.00:

            banks = self.driver.find_elements('class name', 'fiList-item_testTreatment')
            accounts = [bank.text.split('\n')[0] for bank in banks if 'Current account' in bank.text]
            accounts = [x for x in accounts if not x.startswith('M')]

            self.driver.get('https://www.paypal.com/myaccount/money/balances/withdraw/balance')
            # self.driver.find_element('id', 'GBPRadioBtn').click()
            # self.driver.find_element('name', 'selectBalanceNext').click()

            self.driver.find_element('name', 'changefi').click()

            # checkpoints = connect_to_dynamodb('checkpoints')
            # previous_account = checkpoints.get_item(Key={'checkpoint_id': 'bank'})['Item']['code']
            # account = accounts[accounts.index(previous_account) + 1] if accounts.index(previous_account) != len(accounts) - 1 else accounts[0]
            # checkpoints.put_item(Item={"checkpoint_id": "bank", 'code': account})

            self.driver.find_element('xpath', f"//*[contains(text(), '{account}')]").click()
            self.driver.find_element('xpath', '//button[contains(text(), "Next")]').click()

            self.driver.find_element('name', 'submit').click()

            # wait.until(lambda driver: self.driver.find_element('xpath', '//button[contains(text(), "Next")]')).click() # Currently just transfers whole balance

            if self.driver.find_elements('id', 'challenge-heading'):
                try:
                    self.otp_bypass()
                    # element = WebDriverWait(self.driver, 30).until(
                    #     lambda driver: self.driver.find_element('id', "fn-amount"))
                except Exception as e:
                    print(f"{e}")
                    self.driver.refresh()
                    code = TextBypass().check_code("PayPal: ", 'paypal')
                    if self.driver.find_elements('id', 'ci-answer-0'):
                        self.driver.find_element('id', 'ci-answer-0').send_keys(code)
                    elif self.driver.find_elements('id', 'ci-otpCode-0'):
                        self.driver.find_element('id', 'ci-otpCode-0').send_keys(code)
                    self.driver.find_element('id', 'securityCodeSubmit').click()

            time.sleep(5)

            if self.driver.find_element('xpath', '//button[contains(text(), "Next")]'):
                self.driver.find_element('xpath', '//button[contains(text(), "Next")]').click()

            amount = wait.until(lambda driver: self.driver.find_element('class name', 'withdrawReview-amount')).text

            wait.until(EC.presence_of_element_located((By.NAME, 'submit|standard'))).click()
            wait.until(EC.presence_of_element_located((By.ID, "done"))).click()

            return account, amount

    def close(self):
        self.driver.close()
        self.driver.quit()

if __name__ == '__main__':

    EMAIL = os.getenv('MAIN_USER')
    PASS = os.getenv('MAIN_PASS')
    AUTH = os.getenv('AUTH_SECRET')

    withdrawal_browser = PayPalBrowser(EMAIL, PASS, AUTH)
    withdrawal_browser.login()
    withdrawal_browser.make_payments(['100.00', '50.00', '17.35','25.00', '14.00'], os.getenv('MAIN_USER'), card='Debit ••••xxxx')

    wait = WebDriverWait(withdrawal_browser.driver, 30)

    withdrawal_browser.withdrawal()
    withdrawal_browser.close()
