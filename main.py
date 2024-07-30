from requests_html import HTMLSession
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import concurrent.futures

session = HTMLSession()


def scrape_buttons_in_website(url):
    print(f"Scraping buttons from: {url}")
    try:
        response = session.get(url)
        response.html.render(timeout=30, sleep=1)
    except Exception as e:
        print(f"Error rendering JavaScript for {url}: {e}")
        return []

    soup = BeautifulSoup(response.html.html, "html.parser")
    matches = set()

    # Find all <a> tags
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(url, href)
        parsed_url = urlparse(full_url)
        if parsed_url.netloc == urlparse(url).netloc:
            matches.add(full_url)
            print(f"Found internal link: {full_url}")
        else:
            print(f"Found external link: {full_url}")

    # Find all buttons with onclick events
    for button in soup.find_all(["button", "input", "a"]):
        onclick = button.get("onclick")
        if onclick:
            match = re.search(
                r"(?:window\.location\.href|location\.href)\s*=\s*['\"]([^'\"]+)['\"]",
                onclick,
            )
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

    # Find links in JavaScript
    scripts = soup.find_all("script")
    for script in scripts:
        if script.string:
            urls = re.findall(r'(?:url|href):\s*["\']([^"\']+)["\']', script.string)
            for url in urls:
                full_url = urljoin(url, url)
                matches.add(full_url)
                print(f"Found JavaScript link: {full_url}")

    print(f"Total unique links found: {len(matches)}")
    return list(matches)


def scrape_email_from_page(link):
    print(f"Processing link: {link}")
    try:
        response = session.get(link)
        soup = BeautifulSoup(response.content, "html.parser")
        email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )
        found_emails = set(re.findall(email_pattern, soup.get_text()))

        # Look for obfuscated emails
        scripts = soup.find_all("script")
        for script in scripts:
            if script.string:
                obfuscated_emails = re.findall(
                    r"[\w\.-]+\s*@\s*[\w\.-]+\s*\.\s*[\w]{2,}", script.string
                )
                found_emails.update(
                    set("".join(email.split()) for email in obfuscated_emails)
                )

        if found_emails:
            print(f"Found emails: {found_emails}")
        else:
            print("No emails found on this page.")
        return found_emails
    except Exception as e:
        print(f"Error while processing {link}: {e}")
        return set()


def scrape_email_from_website(url):
    print(f"Starting email scraping from: {url}")
    matches = scrape_buttons_in_website(url)
    emails = set()

    # Use ThreadPoolExecutor for parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {
            executor.submit(scrape_email_from_page, link): link for link in matches
        }
        for future in concurrent.futures.as_completed(future_to_url):
            emails.update(future.result())

    print(f"Total unique emails found: {len(emails)}")
    return list(emails) if emails else []


def print_emails(emails):
    if not emails:
        print("No emails found.")
        return

    # Count emails by domain
    email_dict = {}
    for email in emails:
        domain = email.split("@")[-1]
        if domain not in email_dict:
            email_dict[domain] = []
        email_dict[domain].append(email)

    # Print the total count
    print(f"\nTotal unique emails found: {len(emails)}\n")

    # Print emails grouped by domain
    for domain, email_list in email_dict.items():
        print(f"Domain: {domain} - {len(email_list)} email(s)")
        for email in email_list:
            print(f"  - {email}")


# Main execution
url = "url_to_scrape"
result = scrape_email_from_website(url)
print_emails(result)
