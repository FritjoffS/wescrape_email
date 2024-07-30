from requests_html import HTMLSession
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import concurrent.futures

session = HTMLSession()

def is_login_page(url, soup):
    login_keywords = ['login', 'signin', 'logon', 'auth', 'account', 'user', 'password']
    url_lower = url.lower()
    if any(keyword in url_lower for keyword in login_keywords):
        return True

    title = soup.title.string if soup.title else ''
    if any(keyword in title.lower() for keyword in login_keywords):
        return True

    for form in soup.find_all('form', action=True):
        action = form['action'].lower()
        if any(keyword in action for keyword in login_keywords):
            return True

    return False

def scrape_page(url, depth=0, max_depth=2, visited=None):
    if visited is None:
        visited = set()
    
    if depth > max_depth or url in visited:
        return set(), set()

    print(f"Scraping page: {url} (Depth: {depth})")
    visited.add(url)
    
    try:
        response = session.get(url)
        response.html.render(timeout=30, sleep=1)
    except Exception as e:
        print(f"Error rendering JavaScript for {url}: {e}")
        return set(), set()

    soup = BeautifulSoup(response.html.html, "html.parser")
    emails = set()
    links = set()
    login_pages = set()

    # Find emails
    email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    emails.update(set(re.findall(email_pattern, soup.get_text())))

    # Check if the current page is a login page
    if is_login_page(url, soup):
        login_pages.add(url)
        print(f"Found login page: {url}")

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
            sub_emails, sub_login_pages = future.result()
            emails.update(sub_emails)
            login_pages.update(sub_login_pages)

    return emails, login_pages

def scrape_email_and_login_from_website(url, max_depth=2):
    print(f"Starting email and login page scraping from: {url}")
    emails, login_pages = scrape_page(url, max_depth=max_depth)
    print(f"Total unique emails found: {len(emails)}")
    print(f"Total unique login pages found: {len(login_pages)}")
    return list(emails), list(login_pages)

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

def print_login_pages(login_pages):
    if not login_pages:
        print("No login pages found.")
        return

    print(f"\nTotal unique login pages found: {len(login_pages)}\n")
    for page in sorted(login_pages):
        print(f"  - {page}")

# Main execution
if __name__ == "__main__":
    url = input("Please enter the URL to scrape: ")
    
    while True:
        try:
            max_depth = int(input("Enter the maximum depth for scraping (1-5): "))
            if 1 <= max_depth <= 5:
                break
            else:
                print("Please enter a number between 1 and 5.")
        except ValueError:
            print("Please enter a valid integer.")

    emails, login_pages = scrape_email_and_login_from_website(url, max_depth)
    print_emails(emails)
    print_login_pages(login_pages)