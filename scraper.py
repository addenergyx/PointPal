import undetected_chromedriver as uc
# from selenium.common.exceptions import WebDriverException
# import re
from webdriver_manager.chrome import ChromeDriverManager
import chromedriver_autoinstaller

def get_driver(headless=False):
    # Configure ChromeOptions
    uc_options = uc.ChromeOptions()
    # uc_options.add_argument("--start-maximized")
    # uc_options.add_argument("--disable-popup-blocking") # block location popup

    if headless:
        uc_options.add_argument('--headless')

    # Configure ChromeDriverManager
    # chrome_driver_path = ChromeDriverManager().install()

    '''using undetected_chromedriver set executable_path to chromedriver path'''
    print('Using undetected_chromedriver...')


    # Create and return the Chrome driver instance
    # https://github.com/ultrafunkamsterdam/undetected-chromedriver/issues/1491
    # return uc.Chrome(executable_path=chrome_driver_path, options=uc_options, use_subprocess=True)
    # uc.TARGET_VERSION = 85
    # return uc.Chrome(driver_executable_path='/Users/david/Library/CloudStorage/OneDrive-Personal/GitHub/Automated-Scripts/chromedriver_mac_arm64/chromedriver', options=uc_options, use_subprocess=True)
    # return uc.Chrome(options=uc_options, use_subprocess=True, version_main=118)
    return uc.Chrome(use_subprocess=True)

# def get_driver(version_main=113, headless=False):
#     uc_options = uc.ChromeOptions()
#     uc_options.add_argument("--start-maximized")
#     uc_options.add_argument("--disable-popup-blocking") # block location popup
#
#     if headless:
#         uc_options.add_argument('--headless')
#
#     return uc.Chrome(version_main=version_main, options=uc_options, use_subprocess=True)

# def get_driver(version_main=101, headless=False):
#     uc_options = uc.ChromeOptions()
#     uc_options.add_argument("--start-maximized")
#     uc_options.add_argument("--disable-popup-blocking") # block location popup
#
#     try:
#         driver = uc.Chrome(options=uc_options, use_subprocess=True)  # Works on windows
#     except WebDriverException as e:
#         print('Failed: ' + str(e))
#
#         pattern = '^Current browser version is\s(\d+)'
#
#         a = re.search(pattern, str(e), re.MULTILINE)
#
#         print('Attemping again with chrome version ' + a.group(1))
#
#         # Try again with suggested version
#         uc_options = uc.ChromeOptions()
#         uc_options.add_argument("--start-maximized")
#         driver = uc.Chrome(version_main=a.group(1), options=uc_options)
#
#     return driver
