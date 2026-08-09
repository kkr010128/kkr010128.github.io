"""
import urllib.request

#데이터 읽기
response = urllib.request.urlopen("https://www.kakao.com/")
data = response.read()

#읽어온 데이터의 인코딩 설정
encoding = response.info().get_content_charset()
html = data.decode(encoding)

#화면 출력
print(html)
"""


"""
#URL에 한글이 포함된 경우
import urllib.request
response = urllib.request.urlopen("https://search.hani.co.kr/search?command=query&media=common&searchword=사이버가수아담&x=0&y=0&_ga=2.225940573.611667888.1689238630-1387075702.1689238630")
data = response.read()

#읽어온 데이터의 인코딩 설정
encoding = response.info().get_content_charset()
html = data.decode(encoding)

#화면 출력
print(html)
"""


"""
#URL에 한글이 포함된 경우
import urllib.request
from urllib.parse import quote

keyword = quote("사이버가수아담")
response = urllib.request.urlopen("https://search.hani.co.kr/search?command=query&media=common&searchword=" + keyword + "&x=0&y=0&_ga=2.225940573.611667888.1689238630-1387075702.1689238630")
data = response.read()

#읽어온 데이터의 인코딩 설정
encoding = response.info().get_content_charset()
html = data.decode(encoding)

#화면 출력
print(html)
"""


"""
import requests

# GET
resp = requests.get('http://httpbin.org/get')
print(resp.text)

# POST
dic = {"id": "ggangpae1", "name": "박문석", "age": 40}
resp = requests.post('http://httpbin.org/post', data=dic)
print(resp.text)

resp = requests.put('http://httpbin.org/put')
print(resp.text)

resp = requests.delete('http://httpbin.org/delete')
print(resp.text)
"""

"""
import requests
res = requests.get('https://www.python.org/')
# resp.raise_for_status()

if (res.status_code == requests.codes.ok):
    html = res.text
    print(html)
"""


"""
import requests
try:
    res = requests.get('https://www.naver.com') # 네이버 홈
    print(res.encoding)
    res = requests.get('http://www.tjoeun.co.kr/') # 더조은 홈페이지
    print(res.encoding)
except Exception as e:
    print("예외발생:", e)
"""


"""
import requests

imgurl = 'http://www.onlifezone.com/files/attach/images/962811/376/321/005/2.jpg'
imgname = 'data/' + imgurl.split('/')[-1]
try:
    res = requests.get(imgurl)
    with open(imgname, 'wb') as h:
        img = res.content
        h.write(img)
except Exception as e:
    print(e)
"""


"""
import requests
import json
url = 'https://dapi.kakao.com/v2/local/search/category.json?category_group_code=PM9&rect=126.95,37.55,127.0,37.60'
headers = {'Authorization': 'KakaoAK {}'.format('c454c0e64688ce2bde2dfff9cceced87')}
data = requests.post(url, headers=headers)
result = json.loads(data.text) #파싱한 결과
#print(result)
documents = result['documents']
for data in documents:
    print(format(data['place_name'], '30s'), end='\t')
    print(format(data['address_name'], '30s'))
"""

"""
import requests, bs4

try:
    resp = requests.get('http://finance.daum.net/')
    resp.raise_for_status()

    html = resp.text
    bs = bs4.BeautifulSoup(html, 'html.parser')

except Exception as e:
    print("예외 발생:", e)

else:
    print(bs.body.span.get_text())
"""


"""
import requests, bs4
from urllib.parse import quote
import re

try:
    # wikipedia 에서 기계_학습 검색 결과 가져오기
    keyword = '기계_학습'
    keyword = quote(keyword)
    resp = requests.get('https://ko.wikipedia.org/wiki/' + keyword)
    resp.raise_for_status()

    html = resp.text
    # 텍스트를 DOM으로 만들기
    bs = bs4.BeautifulSoup(html, 'html.parser')
except Exception as e:
    print("예외 발생1:", e)
else:
    #a 태그 전부 가져오기
    for link in bs.findAll('a'):
        #속성에 href 가 있는 경우
        if 'href' in link.attrs:
            #href 안의 내용 중 /wiki/가 포함된 것만 골라내기
            href = link.attrs['href']
            p = re.compile('^(/wiki/)')
            if p.search(href) != None:
                print(href)
"""


"""
#네이버 주식에서 타이틀 가져오기
import requests, bs4

try:
    resp = requests.get('https://finance.naver.com/')
    resp.raise_for_status()

    resp.encoding = 'euc-kr'
    html = resp.text
    bs = bs4.BeautifulSoup(html, 'html.parser')
    tags = bs.select('span > a')  # Top 뉴스
    title = tags[0].getText()
    print(title)
except Exception as e:
    print("예외 발생:", e)
"""


"""
#네이버 팟 캐스트에서 타이틀 가져오기
import requests, bs4
try:
    res = requests.get('https://tv.naver.com/r/category/drama')
    res.raise_for_status()

    html = res.text
    bs = bs4.BeautifulSoup(html, 'html.parser')
    tags = bs.select('strong span')
    for title in tags:
        print(title.getText())
except Exception as e:
    print("예외 발생:", e)
"""


"""
#온도, 습도 출력
import requests                  # 웹 페이지의 HTML을 가져오는 모듈
from bs4 import BeautifulSoup    # HTML을 파싱하는 모듈

# 웹 페이지를 가져온 뒤 BeautifulSoup 객체로 만듦
response = requests.get('http://www.weather.go.kr/weather/observation/currentweather.jsp')

soup = BeautifulSoup(response.content, 'html.parser')

table = soup.select('#weather_table > tbody')

loc = []
temp =[]
hum=[]


# 데이터를 저장할 리스트 생성
for tr in table[0].find_all('tr'):      # 모든 <tr> 태그를 찾아서 반복(각 지점의 데이터를 가져옴)
    tds = list(tr.find_all('td'))    # 모든 <td> 태그를 찾아서 리스트로 만듦
    for td in tds:                   # <td> 태그 리스트 반복(각 날씨 값을 가져옴)
        if td.find('a'):             # <td> 안에 <a> 태그가 있으면(지점인지 확인)
            loc.append(td.find('a').text)    # <a> 태그 안에서 지점을 가져옴
            temp.append(tds[5].text)    # <td> 태그 리스트의 여섯 번째(인덱스 5)에서 기온을 가져옴
            hum.append(tds[9].text)       # <td> 태그 리스트의 열 번째(인덱스 9)에서 습도를 가져옴
print('도시 이름:', loc[0:5])
print('현재 온도:', temp[0:5])
print('습도:', hum[0:5])
print()
print()

cities = ['서울', '인천', '대전', '대구', '광주', '부산', '울산', '창원']
temperatures = []
humidities = []
for city in cities:
    j = 0
    for c in loc:
        if city == c:
            temperatures.append(temp[j])
            humidities.append(hum[j])
            break
        j = j + 1

print('도시 이름:', cities)
print('현재 온도:', temperatures)
print('습도:', humidities)
"""


"""
import requests
import bs4
url = 'https://dapi.kakao.com/v2/local/search/category.xml?category_group_code=PM9&rect=127.0561466,37.5058277,127.0602340,37.5142554'
headers = {'Authorization': 'KakaoAK {}'.format('c454c0e64688ce2bde2dfff9cceced87')}
response = requests.post(url, headers=headers)
#print(response.text)

#파싱 객체 생성
xml = bs4.BeautifulSoup(response.text, "html.parser")
place_names = xml.find_all('place_name')
address_names = xml.find_all('address_name')

i = 0
for place_name in place_names:
    address_name = address_names[i]
    print(format(place_name.getText(), '30s'), end='\t')
    print(format(address_name.getText(), '30s'))
    i = i + 1
    
"""

"""
#크롬 실행
from selenium import webdriver
import os
os.environ['webdriver.chrome.driver'] = '/Users/adam/Downloads/chrome-mac-arm64/Google\ Chrome\ for\ Testing.app'
driver = webdriver.Chrome()
while(True):
    	pass
"""


"""
#html 가져오기
from selenium import webdriver
import os
os.environ['webdriver.chrome.driver'] = '/Users/adam/Downloads/chrome-mac-arm64/Google\ Chrome\ for\ Testing.app'
driver = webdriver.Chrome()
driver.get("https://pt.masanggames.co.kr/")
print(driver.page_source)
while(True):
    	pass
"""


"""
#다음 카페 로그인 페이지로 이동
from selenium import webdriver
import os
os.environ['webdriver.chrome.driver'] = '/Users/adam/Downloads/chrome-mac-arm64/Google\ Chrome\ for\ Testing.app'
driver = webdriver.Chrome()
driver.implicitly_wait(5)

#다음 카페 페이지로 이동 - 로그인 되어 있지 않으므로 로그인 페이지로 이동
driver.get('https://accounts.kakao.com/login/?continue=https%3A%2F%2Flogins.daum.net%2Faccounts%2Fksso.do%3Frescue%3Dtrue%26url%3Dhttps%253A%252F%252Fwww.daum.net%252F&login_type=simple#login')
driver.implicitly_wait(5)

while(True):
    	pass
"""


"""
#다음 카페 로그인
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import time

os.environ['webdriver.chrome.driver'] = '/Users/adam/Downloads/chrome-mac-arm64/Google\ Chrome\ for\ Testing.app'
driver = webdriver.Chrome()
driver.implicitly_wait(5)

#다음 카페 페이지로 이동 - 로그인 되어 있지 않으므로 로그인 페이지로 이동
driver.get('https://accounts.kakao.com/login/?continue=https%3A%2F%2Flogins.daum.net%2Faccounts%2Fksso.do%3Frescue%3Dtrue%26url%3Dhttps%253A%252F%252Fwww.daum.net%252F&login_type=simple#login')
driver.implicitly_wait(5)

#아이디 와 비밀번호 입력받기
userid = input("아이디:")
userpw = input("비밀번호:")
time.sleep(3)

#입력받은 내용을 삽입하기
driver.find_element(By.XPATH, '//*[@id="loginId--1"]').send_keys(userid)
driver.find_element(By.XPATH, '//*[@id="password--2"]').send_keys(userpw)

#버튼
btn = driver.find_element(By.XPATH, '//*[@id="mainContent"]/div/div/form/div[4]/button[1]')
btn.click()

while(True):
    	pass
"""


"""
#다음 카페 목록 페이지로 이동
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import time

os.environ['webdriver.chrome.driver'] = '/Users/adam/Downloads/chrome-mac-arm64/Google\ Chrome\ for\ Testing.app'
driver = webdriver.Chrome()
driver.implicitly_wait(5)

#다음 카페 페이지로 이동 - 로그인 되어 있지 않으므로 로그인 페이지로 이동
driver.get('https://accounts.kakao.com/login/?continue=https%3A%2F%2Flogins.daum.net%2Faccounts%2Fksso.do%3Frescue%3Dtrue%26url%3Dhttps%253A%252F%252Fwww.daum.net%252F&login_type=simple#login')
driver.implicitly_wait(5)

#아이디 와 비밀번호 입력받기
userid = input("아이디:")
userpw = input("비밀번호:")
time.sleep(3)

#입력받은 내용을 삽입하기
driver.find_element(By.XPATH, '//*[@id="loginId--1"]').send_keys(userid)
driver.find_element(By.XPATH, '//*[@id="password--2"]').send_keys(userpw)

#버튼
btn = driver.find_element(By.XPATH, '//*[@id="mainContent"]/div/div/form/div[4]/button[1]')
btn.click()

time.sleep(3)
driver.get('http://top.cafe.daum.net/_c21_/my_cafe')

time.sleep(3)
driver.find_element(By.XPATH, '//*[@id="mArticle"]/div/div[1]/div/div[2]/ul/li/a').click()

while(True):
    	pass
"""


"""
#다음 카페 목록 페이지로 이동
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import time

os.environ['webdriver.chrome.driver'] = '/Users/adam/Downloads/chrome-mac-arm64/Google\ Chrome\ for\ Testing.app'
driver = webdriver.Chrome()
driver.implicitly_wait(5)

#다음 카페 페이지로 이동 - 로그인 되어 있지 않으므로 로그인 페이지로 이동
driver.get('https://accounts.kakao.com/login/?continue=https%3A%2F%2Flogins.daum.net%2Faccounts%2Fksso.do%3Frescue%3Dtrue%26url%3Dhttps%253A%252F%252Fwww.daum.net%252F&login_type=simple#login')
driver.implicitly_wait(5)

#아이디 와 비밀번호 입력받기
userid = input("아이디:")
userpw = input("비밀번호:")
time.sleep(3)

#입력받은 내용을 삽입하기
driver.find_element(By.XPATH, '//*[@id="loginId--1"]').send_keys(userid)
driver.find_element(By.XPATH, '//*[@id="password--2"]').send_keys(userpw)

#버튼
btn = driver.find_element(By.XPATH, '//*[@id="mainContent"]/div/div/form/div[4]/button[1]')
btn.click()

time.sleep(3)
driver.get('http://top.cafe.daum.net/_c21_/my_cafe')

time.sleep(3)
driver.find_element(By.XPATH, '//*[@id="mArticle"]/div/div[1]/div/div[2]/ul/li/a').click()

# 메모 작성
time.sleep(3)
driver.get('http://cafe.daum.net/samhak7/_memo')

time.sleep(3)
driver.switch_to.frame('down')
driver.find_element(By.XPATH, '//*[@id="primaryContent"]/div/div[1]/div[2]/div/div/div[1]/textarea').send_keys(
	'모두들 안녕 매크로 연습이야')

time.sleep(3)
driver.find_element(By.XPATH, '//*[@id="primaryContent"]/div/div[1]/div[2]/div/div/div[2]/div[2]/div/button').click()

time.sleep(3)
driver.get('http://top.cafe.daum.net/_c21_/my_cafe')

time.sleep(3)
driver.find_element(By.XPATH,
	'//*[@id="mArticle"]/div/div[2]/div[2]/ul/li[1]/div[1]/a/div[2]/div/div/div[1]/strong').click()

while(True):
    	pass
"""


"""
#크롬 브라우저를 구동하지 않고 데이터 가져오기
from selenium import webdriver
import os

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1920x1080')
options.add_argument("disable-gpu")
# 혹은 options.add_argument("--disable-gpu")

# Chrome의 경우 | 아까 받은 chromedriver의 위치를 지정
os.environ['webdriver.chrome.driver'] = '/Users/adam/Downloads/chrome-mac-arm64/Google\ Chrome\ for\ Testing.app'
driver = webdriver.Chrome(options=options)
driver.get('https://www.naver.com')
html = driver.page_source
print(html)
"""


"""
#네이버 자동 로그인
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import time

# Chrome의 경우 | 아까 받은 chromedriver의 위치를 지정
os.environ['webdriver.chrome.driver'] = '/Users/adam/Downloads/chrome-mac-arm64/Google\ Chrome\ for\ Testing.app'
driver = webdriver.Chrome()
driver.get('https://nid.naver.com/nidlogin.login')
time.sleep(3)

userid = input("아이디:")
userpw = input("비밀번호:")

driver.execute_script("document.getElementsByName('id')[0].value=\'" + userid + "\'")
driver.execute_script("document.getElementsByName('pw')[0].value=\'" + userpw + "\'")
driver.find_element(By.XPATH, '//*[@id="log.login"]').click()
while(True):
    	pass
"""


"""
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import time
from selenium.webdriver.common.keys import Keys
import bs4

os.environ['webdriver.chrome.driver'] = '/Users/adam/Downloads/chrome-mac-arm64/Google\ Chrome\ for\ Testing.app'
driver = webdriver.Chrome()

driver.get('https://www.youtube.com/results?search_query=%EB%A7%88%EB%A7%88%EB%AC%B4')
time.sleep(5)
body = driver.find_element(By.TAG_NAME, 'body')  # 스크롤하기 위해 소스 추출
num_of_pagedowns = 10
# 10번 밑으로 내리는 것
while num_of_pagedowns:
	body.send_keys(Keys.PAGE_DOWN)
	time.sleep(2)
	num_of_pagedowns -= 1

html = bs4.BeautifulSoup(driver.page_source, 'html.parser')
print(html)
"""
