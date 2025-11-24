import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re

class WebScraperBot:
    def __init__(self, url, depth, read_documents_flag='no'):
        print("Connected to bot")
        self.url = url
        self.read_documents_flag = read_documents_flag
        self.document_text = []
        self.text_content = []
        self.visited_links = set()
        self.depth = depth

    def fetch_page(self, url):
        print('fetching url: ',url)
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            print("page fetched")
            return response.content
        except (requests.RequestException, requests.HTTPError) as e:
            print(f"Failed to fetch {url}: {e}")
            return None

    def scrape_page(self, url):
        content = self.fetch_page(url)
        print('scraping url: ',url)
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            title = soup.title.get_text() if soup.title else ""
            metadata = self.extract_metadata(soup)
            text_content = f"""
            Webpage Link: {url}, 
            Webpage Title: {title},
            Metadata: {metadata},
            {soup.get_text()} 
            """ 
            self.text_content.append(text_content)

    def get_internal_links(self, url, depth):
        print('\n','Getting internal links in url:',url)
        if depth <= 0:
            return []
        internal_links = []
        content = self.fetch_page(url)
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            for link in soup.find_all('a', href=True):
                link_url = urljoin(url, link['href'])
                if link_url not in self.visited_links and urlparse(link_url).netloc == urlparse(url).netloc:
                    self.visited_links.add(link_url)
                    internal_links.append(link_url)
                    self.scrape_page(link_url)
                    internal_links.extend(self.get_internal_links(link_url, depth - 1))
        # print("internal links found:",internal_links)
        return internal_links

    def get_external_links(self, url, depth):
        if depth <= 0:
            return []
        external_links = []
        content = self.fetch_page(url)
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            for link in soup.find_all('a', href=True):
                link_url = urljoin(url, link['href'])
                if link_url not in self.visited_links and urlparse(link_url).netloc != urlparse(url).netloc:
                    self.visited_links.add(link_url)
                    external_links.append(link_url)
                    self.scrape_page(link_url)
                    external_links.extend(self.get_external_links(link_url, depth - 1))
        return external_links

    def extract_metadata(self, soup):
        title = soup.title.get_text() if soup.title else ""
        meta_description = soup.find('meta', attrs={'name': 'description'})['content'] if soup.find('meta', attrs={'name': 'description'}) else ""
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})['content'] if soup.find('meta', attrs={'name': 'keywords'}) else ""
        return {
            'title': title,
            'description': meta_description,
            'keywords': meta_keywords
        }

    def merge_hyphenated_words(self, text: str) -> str:
        return re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    def fix_newlines(self, text: str) -> str:
        return re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    def remove_multiple_newlines(self, text: str) -> str:
        return re.sub(r"\n{2,}", "\n", text)

    def run_bot(self, follow_external, follow_internal):
        print('running')
        external_links = []
        internal_links = []
        if follow_internal:
            internal_links = self.get_internal_links(self.url, self.depth)
        if follow_external:
            external_links = self.get_external_links(self.url, self.depth)
        if not follow_external and not follow_internal:
            self.scrape_page(self.url)

        clean_list=[]
        for x in self.text_content:
            # clean_text = self.remove_multiple_newlines(x)
            # clean_text = self.fix_newlines(clean_text)
            clean_list.append(self.merge_hyphenated_words(x))

        return clean_list, external_links, internal_links

if __name__ == "__main__":
    url = "https://help.pythonanywhere.com/pages/"  
    depth = 1  
    read_documents_flag = 'no'
    follow_external = False
    follow_internal = True

    bot = WebScraperBot(url, depth, read_documents_flag)
    text_content, external_links, internal_links = bot.run_bot(follow_external, follow_internal)
    # print(internal_links)

    # if read_documents_flag:
    #     document_text = result[3]
    #     print("Document text:")
    #     for doc_text in document_text:
    #         print(doc_text)
