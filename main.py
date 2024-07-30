from requests_html import HTMLSession
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import concurrent.futures

session = HTMLSession()

def scrape_page(url, depth=0, max_depth=2, visited=None):
    if visited is None:
        visited = set()
    
    if depth > max_depth or url in visited:
        return set()

    print(f"Scraping page: {url} (Depth: {depth})")
    visited.add(url)
    
    try:
        response = session.get(url)
        response.html.render(timeout=30, sleep=1)
    except Exception as e:
        print(f"Error rendering JavaScript for {url}: {e}")
        return set()

    soup = BeautifulSoup(response.html.html, "html.parser")
    emails = set()
    links = set()

    # Find emails
    email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    emails.update(set(re.findall(email_pattern, soup.get_text())))

    # Find links
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(url, href)
        parsed_url = urlparse(full_url)
        if parsed_url.netloc == urlparse(url).netloc:
            links.add(full_url)

    # Recursively scrape subpages
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(scrape_page, link, depth + 1, max_depth, visited): link for link in links}
        for future in concurrent.futures.as_completed(future_to_url):
            emails.update(future.result())

    return emails

def scrape_email_from_website(url, max_depth=2):
    print(f"Starting email scraping from: {url}")
    emails = scrape_page(url, max_depth=max_depth)
    print(f"Total unique emails found: {len(emails)}")
    return list(emails)

def print_emails(emails):
    if not emails:
        print("No emails found.")
        return

    # Count emails by domain
    email_dict = {}
    for email in emails:
        domain = email.split('@')[-1]
        if domain not in email_dict:
            email_dict[domain] = []
        email_dict[domain].append(email)

    # Print the total count
    print(f"\nTotal unique emails found: {len(emails)}\n")

    # Print emails grouped by domain
    for domain, email_list in sorted(email_dict.items()):
        print(f"Domain: {domain} - {len(email_list)} email(s)")
        for email in sorted(email_list):
            print(f"  - {email}")

# Main execution
url = "url" # Enter the URL you want to scrape
max_depth = 6  # You can adjust this value to control how deep the scraper goes
result = scrape_email_from_website(url, max_depth)
print_emails(result)