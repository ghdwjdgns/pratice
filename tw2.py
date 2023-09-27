from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import mysql.connector

# MySQL 연결 설정
db_config = {
    'host': '127.0.0.1',       # MySQL 호스트 주소
    'user': 'root',   # MySQL 사용자 이름
    'password': '1234',  # MySQL 비밀번호
    'database': 'sport'       # MySQL 데이터베이스 이름
}

# MySQL 연결
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# 크롤링할 페이지 수
total_pages = 5

# MySQL 테이블 생성 쿼리
create_table_query = '''
CREATE TABLE IF NOT EXISTS news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    content TEXT,
    url VARCHAR(255),
    news_content TEXT
)
'''

cursor.execute(create_table_query)
conn.commit()

options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])
driver = webdriver.Chrome(options=options)

# WebDriverWait를 사용하여 페이지 로딩 대기 시간 설정
wait = WebDriverWait(driver, 10)

# 페이지 수 설정 (예를 들어, 3 페이지까지 크롤링하려면 range(1, 4)로 설정)
for page_number in range(1, total_pages + 1):
    # 페이지 URL 생성
    page_url = f'https://sports.news.naver.com/kfootball/news/index?isphoto=N&date=20230926&page={page_number}'
    driver.get(page_url)
    
    # 명시적 대기 시간 설정
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#_newsList > ul > li')))

    # 페이지 소스 가져오기
    page_source = driver.page_source

    # BeautifulSoup를 사용하여 HTML 파싱
    soup = BeautifulSoup(page_source, 'html.parser')

    # CSS 선택자를 사용하여 뉴스 아이템 추출
    news_list = soup.select('#_newsList > ul > li')

    # 뉴스 제목, 내용, URL, 뉴스 내용 크롤링 및 MySQL에 저장
    for news_item in news_list:
        try:
            title_element = news_item.select_one('div > a > span')
            content_element = news_item.select_one('div > p')
            if title_element and content_element:
                title = title_element.text.strip()
                content = content_element.text.strip()

                # 뉴스 아이템의 URL 가져오기
                news_url = news_item.select_one('div > a')['href']
                news_url = news_url.replace("/kfootball/news/read?", "https://sports.news.naver.com/news?")

                # 뉴스 아이템 페이지로 이동
                driver.get(news_url)

                # 명시적 대기 시간 설정
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.content_area > div.news_end')))

                # 내용 크롤링
                news_page_source = driver.page_source
                news_soup = BeautifulSoup(news_page_source, 'html.parser')

                # 특정 요소 제외
                reporter_area = news_soup.select_one('#newsEndContents > div.reporter_area')
                if reporter_area:
                    reporter_area.extract()

                copyright = news_soup.select_one('#newsEndContents > div.copyright')
                if copyright:
                    copyright.extract()

                guide = news_soup.select_one('#_article_section_guide')
                if guide:
                     guide.extract()

                promotion = news_soup.select_one('#newsEndContents > div.promotion')
                if promotion:
                    promotion.extract()

                # 내용 추출
                news_content_element = news_soup.select_one('div.content_area > div.news_end')
                if news_content_element:
                    news_content = news_content_element.text.strip()

                # MySQL에 데이터 삽입
                insert_query = '''
                INSERT INTO news (title, content, url, news_content) 
                VALUES (%s, %s, %s, %s)
                '''
                data = (title, content, news_url, news_content)
                cursor.execute(insert_query, data)
                conn.commit()
                
                print(f"제목 : {title}")
                print("--------------------------------------")
                print(f"내용 : {content}")
                print("--------------------------------------")
                print(f"URL : {news_url}")
                print("--------------------------------------")
                print(f"뉴스 내용 : {news_content}")
                print("--------------------------------------")
                print()
        except AttributeError as e:
            print(f"오류 발생: {e}")

# MySQL 연결 해제
cursor.close()
conn.close()

# 드라이버 종료
driver.quit()
