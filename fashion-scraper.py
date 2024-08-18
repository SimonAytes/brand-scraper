import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time

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

def scrape_website(start_url, progress_bar, status_text):
    visited = set()
    to_visit = [start_url]
    content = []

    while to_visit:
        url = to_visit.pop(0)
        if url in visited or should_skip_page(url):
            continue

        visited.add(url)
        status_text.text(f"Scraping: {url}")

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
    st.title("Fashion Brand Website Scraper")

    start_url = st.text_input("Enter the fashion brand's homepage URL:")
    
    if st.button("Start Scraping"):
        if not start_url:
            st.error("Please enter a URL.")
            return

        progress_bar = st.progress(0)
        status_text = st.empty()

        content = scrape_website(start_url, progress_bar, status_text)

        st.success("Scraping complete!")
        
        st.subheader("Scraped Content")

        # Download button at the top of the results
        st.download_button(
            label="Download scraped content",
            data=content,
            file_name="scraped_content.txt",
            mime="text/plain"
        )
        
        # Display the content in a code block
        st.code(content, language="text")

if __name__ == "__main__":
    main()