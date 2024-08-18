import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time

# Translations dictionary
translations = {
    'en': {
        'title': "Fashion Brand Website Scraper",
        'language': "Language",
        'url_input': "Enter the fashion brand's homepage URL:",
        'start_button': "Start Scraping",
        'url_error': "Please enter a URL.",
        'scraping': "Scraping:",
        'complete': "Scraping complete!",
        'content_header': "Scraped Content",
        'download_button': "Download scraped content",
    },
    'ko': {
        'title': "패션 브랜드 웹사이트 스크레이퍼",
        'language': "언어",
        'url_input': "패션 브랜드의 홈페이지 URL을 입력하세요:",
        'start_button': "스크레이핑 시작",
        'url_error': "URL을 입력해주세요.",
        'scraping': "스크레이핑 중:",
        'complete': "스크레이핑 완료!",
        'content_header': "스크레이핑된 내용",
        'download_button': "스크레이핑된 내용 다운로드",
    }
}

def get_nav_links(soup, base_url):
    nav_links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        full_url = urljoin(base_url, href)
        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            nav_links.append(full_url)
    return list(set(nav_links))

def should_skip_page(url):
    skip_keywords = [
        'shop', 'product', 'category', 'collection',
        'terms', 'conditions', 'privacy', 'policy', 'cookie', 'legal',
        'disclaimer', 'copyright', 'gdpr', 'ccpa', 'returns', 'shipping'
    ]
    return any(keyword in url.lower() for keyword in skip_keywords)

def extract_body_content(soup):
    for elem in soup(['nav', 'header', 'footer', 'script', 'style']):
        elem.decompose()

    main_content = soup.find('main') or soup.find(id=re.compile('^(main|content)')) or soup.find(class_=re.compile('^(main|content)'))
    
    if main_content:
        text_content = main_content.get_text(separator='\n', strip=True)
        alt_texts = [img['alt'] for img in main_content.find_all('img', alt=True)]
    else:
        text_content = soup.body.get_text(separator='\n', strip=True)
        alt_texts = [img['alt'] for img in soup.body.find_all('img', alt=True)]

    return text_content + '\n' + '\n'.join(alt_texts)

def scrape_website(start_url, progress_bar, status_text, lang):
    visited = set()
    to_visit = [start_url]
    content = []

    while to_visit:
        url = to_visit.pop(0)
        if url in visited or should_skip_page(url):
            continue

        visited.add(url)
        status_text.text(f"{translations[lang]['scraping']} {url}")

        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            page_content = extract_body_content(soup)
            content.append(f"--- {url} ---\n{page_content}\n\n")

            nav_links = get_nav_links(soup, url)
            new_links = [link for link in nav_links if link not in visited and not should_skip_page(link)]
            to_visit.extend(new_links)

            progress = len(visited) / (len(visited) + len(to_visit))
            progress_bar.progress(progress)

        except Exception as e:
            st.error(f"Error scraping {url}: {e}")

        time.sleep(0.1)  # To avoid overwhelming the server

    return '\n'.join(content)

def main():
    # Language selector
    lang = st.sidebar.selectbox(
        "Language / 언어",
        options=['en', 'ko'],
        format_func=lambda x: "English" if x == 'en' else "한국어"
    )

    st.title(translations[lang]['title'])

    start_url = st.text_input(translations[lang]['url_input'])
    
    if st.button(translations[lang]['start_button']):
        if not start_url:
            st.error(translations[lang]['url_error'])
            return

        progress_bar = st.progress(0)
        status_text = st.empty()

        content = scrape_website(start_url, progress_bar, status_text, lang)

        st.success(translations[lang]['complete'])
        
        st.subheader(translations[lang]['content_header'])

        # Download button at the top of the results
        st.download_button(
            label=translations[lang]['download_button'],
            data=content,
            file_name="scraped_content.txt",
            mime="text/plain"
        )
        
        # Display the content in a code block
        st.code(content, language="text")

if __name__ == "__main__":
    main()