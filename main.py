from requests_html import HTMLSession
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from requests_html import HTMLSession
import re

session = HTMLSession()

session = HTMLSession()

def scrape_buttons_in_website(url):
    print(f"Scraping buttons from: {url}")
    try:
        response = session.get(url)
        response.html.render(timeout=30)  # Increase timeout to 30 seconds
    except Exception as e:
        print(f"Error rendering JavaScript for {url}: {e}")
        return []

    soup = BeautifulSoup(response.html.html, "html.parser")
    matches = set()  # Use a set to avoid duplicates

    # Find all <a> tags
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]

        # Construct the full URL
        full_url = urljoin(url, href)

        # Parse the URL
        parsed_url = urlparse(full_url)

        # Check if the URL is from the same domain
        if parsed_url.netloc == urlparse(url).netloc:
            matches.add(full_url)
            print(f"Found internal link: {full_url}")
        else:
            print(f"Found external link: {full_url}")

    # Find all buttons with onclick events
    for button in soup.find_all("button"):
        onclick = button.get("onclick")
        if onclick:
            # Extract URL from onclick attribute (if present)
            match = re.search(r"window\.location\.href='([^']*)'", onclick)
            if match:
                full_url = urljoin(url, match.group(1))
                matches.add(full_url)
                print(f"Found button link: {full_url}")

    # Find all elements with data-href attribute
    for elem in soup.find_all(attrs={"data-href": True}):
        href = elem["data-href"]
        full_url = urljoin(url, href)
        matches.add(full_url)
        print(f"Found data-href link: {full_url}")

    print(f"Total unique links found: {len(matches)}")
    return list(matches)


def scrape_email_from_website(url):
    print(f"Starting email scraping from: {url}")
    matches = scrape_buttons_in_website(url)
    emails = set()

    # Iterate through the links and scrape emails
    for link in matches:
        print(f"Processing link: {link}")
        try:
            response = session.get(link)
            soup = BeautifulSoup(response.content, "html.parser")
            email_pattern = re.compile(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            )
            found_emails = set(re.findall(email_pattern, soup.get_text()))
            emails.update(found_emails)

            if found_emails:
                print(f"Found emails: {found_emails}")
            else:
                print("No emails found on this page.")

        except Exception as e:
            print(f"Error while processing {link}: {e}")
            continue

    print(f"Total unique emails found: {len(emails)}")
    return list(emails)

# Main execution
url = "url to scrape"
result = scrape_email_from_website(url)
print("Final list of emails:")
print(result)
