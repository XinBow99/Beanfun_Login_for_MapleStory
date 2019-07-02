#引用所需檔案
#pip3 install htmlparser
#pip3 install datetime
#pip3 install getpass
#pip3 install Crypto
#pip3 install pycryptodome
import re
import datetime
import requests
import getpass
import os
from Crypto.Cipher import DES
import html.parser as htmlparser
#停止SSL報錯
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
#get login key
def getLogin_page(url):
    getTime = str(round(float(str(datetime.datetime.now()).replace('-','').replace(' ','').replace(':','')),3))
    print('[Step_1]認證時間: '+getTime)
    login_url = "https://tw.beanfun.com/beanfun_block/bflogin/default.aspx?service_code=999999&service_region=T0"
    first_page = url.get(login_url,verify = False)
    print('[Step_1]Parsing...')
    r = re.compile('var strSessionKey = (.*?);')
    strSessionKey = r.search(str(first_page.text)).group(1).replace('"','')
    print('[Step_1]done!')
    return strSessionKey
#check login
def login_pages(skey,url,ac,pw):
    login_url = 'https://tw.newlogin.beanfun.com/login/id-pass_form.aspx?skey=%s'%(skey)
    beanfun_login_page = url.get(login_url)
    print('[Step_2]please wait...')
    print('[Step_2]Parsing...')
    client = {
        '__EVENTTARGET':'',
        '__EVENTARGUMENT':'',
        '__VIEWSTATE':re.search(r'id="__VIEWSTATE" value="(.*?)"',beanfun_login_page.text).group(1),
        '__VIEWSTATEGENERATOR':re.search(r'id="__VIEWSTATEGENERATOR" value="(.*?)"',beanfun_login_page.text).group(1),
        '__EVENTVALIDATION':re.search(r'id="__EVENTVALIDATION" value="(.*?)"',beanfun_login_page.text).group(1),
        't_AccountID':ac,
        't_Password':pw,
        'CodeTextBox':'',
        'LBD_VCID_c_login_idpass_form_samplecaptcha':re.search(r'id="LBD_VCID_c_login_idpass_form_samplecaptcha" value="(.*?)"',beanfun_login_page.text).group(1),
        'btn_login':'登入'
    }
    beanfun_login_page = url.post(login_url,data = client)

    auth_key = re.search(r'AuthKey.value = "(.*?)";',beanfun_login_page.text).group(1)
    final_page_url = 'https://tw.newlogin.beanfun.com/login/final_step.aspx?akey=' + auth_key
    final_page = url.get(final_page_url)

    data = {
            'SessionKey': skey,
            'AuthKey': auth_key
        }
    return_url = 'https://tw.beanfun.com/beanfun_block/bflogin/return.aspx'
    beanfun_main_page = url.post(return_url, data=data)

    url.get('https://tw.beanfun.com')
    web_token = url.cookies['bfWebToken']
    print('[Step_2]done!')
    return web_token
#get MapleStory account 
def getMSAccount(service,reg,web_token,url):
    game_zone_url = 'https://tw.beanfun.com/beanfun_block/auth.aspx?channel=game_zone&page_and_query=game_start.aspx%3Fservice_code_and_region%3D{}_{}&web_token={}'
    game_zone_url = game_zone_url.format(service,reg,web_token,url)#%3F
    account = url.get(game_zone_url)
    account_parse = re.findall(r'div id="(.*?)" sn="(.*?)" name="(.*?)"',account.text)
    account_list = []
    print('[GET]Parsing...')
    for account in account_parse:
        if "+" in account[0]:
            continue
        account_list.append(account)
    print('[GET]Done!')
    return account_list
#Select account
def Select_Account(accounts):
    for index,ac in enumerate(accounts):
        print('--[' + str(index + 1) +']名稱：' + htmlparser.unescape(ac[2]) + '｜帳號：'+ac[0])
    select_index = input('[Select]輸入你想選擇的帳號順序編號: ')
    return int(select_index) -1
#OTP Password
def OTP(account,service,reg,url,web_token):
    getTime = int(round(float(str(datetime.datetime.now()).replace('-','').replace(' ','').replace(':','')),0))
    game_start = 'https://tw.beanfun.com/beanfun_block/game_zone/game_start_step2.aspx?service_code=%s&service_region=%s&sotp=%s&dt=%d'
    game_start = game_start%(service,reg,account[1],getTime)
    game_start_result = url.get(game_start)

    GetResultByLongPollingkey = re.search(r'GetResultByLongPolling&key=(.*?)"', game_start_result.text).group(1)
    ServiceAccountCreateTime = re.search(r'ServiceAccountCreateTime: "(.*?)"', game_start_result.text).group(1)

    secretCode = url.get('https://tw.newlogin.beanfun.com/generic_handlers/get_cookies.ashx')
    S_Code = re.search(r"m_strSecretCode = '(.*?)';",secretCode.text).group(1)
    
    OTP_Data = {
        'service_account_id':account[0],
        'service_code':service,
        'service_create_time':ServiceAccountCreateTime,
        'service_display_name':account[2],
        'service_region':reg,
        'service_sotp':account[1]
    }
    OTP_Url = 'https://tw.beanfun.com/beanfun_block/generic_handlers/record_service_start.ashx'
    OTP_Result = url.post(OTP_Url,data=OTP_Data)
    OTP_Url = 'https://tw.beanfun.com/generic_handlers/get_result.ashx?meth=GetResultByLongPolling&key=' + GetResultByLongPollingkey
    OTP_Result = url.get(OTP_Url)
    OTP_Url = 'http://tw.beanfun.com/beanfun_block/generic_handlers/get_webstart_otp.ashx?SN={}&WebToken={}&SecretCode={}' \
            + '&ppppp=1F552AEAFF976018F942B13690C990F60ED01510DDF89165F1658CCE7BC21DBA&ServiceCode={}' \
            + '&ServiceRegion={}&ServiceAccount={}&CreateTime={}&d={}'
    OTP_Url = OTP_Url.format(
            GetResultByLongPollingkey, 
            web_token, 
            S_Code, 
            service, 
            reg,
            account[0],
            ServiceAccountCreateTime.replace(' ', '%20'), 
            int(2500129.999999997))
    OTP_Result = url.get(OTP_Url)
    print('[OTP]Get OTP: '+ OTP_Result.text)
    status = OTP_Result.text[0]
    if status != '1':
            print('[Error] Need to restart...')
            return -1
    Password = OTP_Result.text[2: 10]
    Bf = OTP_Result.text[10:]
    Real_OTP = decrypt(Password, Bf)
    return Real_OTP
def decrypt(key, text):
    bytes_key = key.encode('ascii')
    bytes_text = bytes.fromhex(text)
    des = DES.new(bytes_key, DES.MODE_ECB)
    decrypted = des.decrypt(bytes_text)[:10].decode()
    return decrypted
#check relogin
def check_relogin():
    #Relogig Beanfun 1
    #Get Account 2
    #Get OTP PassWord 3
    print("[####################]")
    result = input('[Info]請選擇操作\n[1]重新登入Beanfun\n[2]取得楓之谷帳號\n[3]取得目前帳號的密碼\n[0]退出阿骨登入\n[Answer]')
    return result
#Main action
def R_Gu_Login():
    #初始化
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
    beanfun_login_base = requests.Session()#Url
    beanfun_login_base.headers.update({'User-Agent':user_agent})
    #get login key to login
    print('初始化成功...')
    print('[Step_1]取得金鑰')
    skey = getLogin_page(beanfun_login_base)
    #print('[Step_1]The login key is: ' + skey)
    print('[Info]請輸入Beanfun帳號密碼')
    ac = input('[Info]UserName: ')
    pw = getpass.getpass("[Info]Password: ")
    web_token = login_pages(skey,beanfun_login_base,ac,pw)
    #getMS
    service = "610074"
    reg = "T9"
    print('[GET]取得楓之谷帳號')
    account = getMSAccount(service,reg,web_token,beanfun_login_base)
    print('[Select]選擇你想登入的帳號吧！')
    Selected_Ac = account[Select_Account(account)]
    print('[OTP]Get PassWord')
    real = OTP(Selected_Ac,service,reg,beanfun_login_base,web_token)
    print("[####################]")
    print("[Complete]Account and Password is:")
    print("[Account ]" + Selected_Ac[0])
    print("[Password]" + real)
    Check_result = check_relogin()
    while Check_result != "0":
        os.system("cls") # windows
        os.system("clear") # linux & mac
        show_R_GU()
        if Check_result == "1":
            R_Gu_Login()
        elif Check_result == "2":
            print('[GET]取得楓之谷帳號')
            account = getMSAccount(service,reg,web_token,beanfun_login_base)
            print('[Select]選擇你想登入的帳號吧！')
            Selected_Ac = account[Select_Account(account)]
            print('[OTP]Get PassWord')
            real = OTP(Selected_Ac,service,reg,beanfun_login_base,web_token)
            print("[####################]")
            print("[Complete]Account and Password is:")
            print("[Account ]" + Selected_Ac[0])
            print("[Password]" + real)
        elif Check_result == "3":
            print('[OTP]Get PassWord')
            real = OTP(Selected_Ac,service,reg,beanfun_login_base,web_token)
            print("[####################]")
            print("[Complete]Account and Password is:")
            print(Selected_Ac[0])
            print(real)
        Check_result = check_relogin()
#R_GU_LOGO
def show_R_GU():
    print('＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃')
    print('＃Welcome to 阿骨Login')
    print('＃Powered By Python')
    print('＃Version 0.1')
    print('＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃')
#check main 
if __name__ == "__main__":
    show_R_GU()
    R_Gu_Login()
