#!/usr/bin/env python3
"""
PyCeWL - Custom Word List Generator
Python implementation of https://github.com/digininja/CeWL
Written with Claude
"""

import argparse
import re
import sys
from urllib.parse import urljoin, urlparse
from collections import Counter
import requests
from bs4 import BeautifulSoup
from typing import Set, List


class PyCeWL:
    def __init__(self, url: str, depth: int = 2, min_word_length: int = 3, 
                 max_word_length: int = None, lowercase: bool = False,
                 with_numbers: bool = False, email_file: str = None,
                 meta: bool = True, auth: tuple = None, user_agent: str = None):
        self.start_url = url
        self.depth = depth
        self.min_word_length = min_word_length
        self.max_word_length = max_word_length
        self.lowercase = lowercase
        self.with_numbers = with_numbers
        self.email_file = email_file
        self.meta = meta
        self.auth = auth
        
        self.visited_urls: Set[str] = set()
        self.words: Counter = Counter()
        self.emails: Set[str] = set()
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if auth:
            self.session.auth = auth
    
    def is_valid_url(self, url: str) -> bool:
        """Check if the URL belongs to the same domain"""
        parsed_start = urlparse(self.start_url)
        parsed_url = urlparse(url)
        return parsed_start.netloc == parsed_url.netloc
    
    def extract_words(self, text: str) -> List[str]:
        """Extract words from text (including accented characters)"""
        if self.with_numbers:
            # Unicode characters for letters (including accents) + digits
            pattern = r'\b[\w\u00C0-\u024F]+\b'
        else:
            # Unicode characters for letters only (including accents)
            pattern = r'\b[a-zA-ZÀ-ÿ]+\b'
        
        words = re.findall(pattern, text, re.UNICODE)
        
        # Filter by length and normalize to lowercase (case insensitive)
        filtered_words = []
        for word in words:
            word_len = len(word)
            if word_len >= self.min_word_length:
                if self.max_word_length is None or word_len <= self.max_word_length:
                    # Always normalize to lowercase
                    filtered_words.append(word.lower())
        
        return filtered_words
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)
    
    def crawl(self, url: str, current_depth: int = 0):
        """Recursively crawl a website"""
        if current_depth > self.depth or url in self.visited_urls:
            return
        
        if not self.is_valid_url(url):
            return
        
        self.visited_urls.add(url)
        
        try:
            print(f"[*] Crawling: {url} (depth: {current_depth})", file=sys.stderr)
            response = self.session.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text()
            
            # Extract words (already lowercase for case insensitivity)
            words = self.extract_words(text)
            self.words.update(words)
            
            # Extract emails if requested
            if self.email_file:
                emails = self.extract_emails(text)
                self.emails.update(emails)
            
            # Extract metadata if requested
            if self.meta:
                meta_tags = soup.find_all('meta')
                for tag in meta_tags:
                    content = tag.get('content', '')
                    if content:
                        words = self.extract_words(content)
                        self.words.update(words)
            
            # Extract links and continue crawling
            if current_depth < self.depth:
                for link in soup.find_all('a', href=True):
                    next_url = urljoin(url, link['href'])
                    # Clean anchors and query parameters if needed
                    next_url = next_url.split('#')[0]
                    self.crawl(next_url, current_depth + 1)
        
        except requests.RequestException as e:
            print(f"[!] Error crawling {url}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"[!] Unexpected error: {e}", file=sys.stderr)
    
    def run(self):
        """Start crawling and return results"""
        print(f"[*] Starting crawl of {self.start_url}", file=sys.stderr)
        print(f"[*] Depth: {self.depth}", file=sys.stderr)
        self.crawl(self.start_url)
        print(f"\n[*] Crawling complete. URLs visited: {len(self.visited_urls)}", file=sys.stderr)
        print(f"[*] Unique words found: {len(self.words)}", file=sys.stderr)
        return self.words, self.emails


def main():
    parser = argparse.ArgumentParser(
        description='PyCeWL - Custom Word List Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  python pycewl.py -d 2 -m 5 https://example.com
  python pycewl.py -d 1 -m 4 -w wordlist.txt https://example.com
  python pycewl.py --lowercase -e emails.txt https://example.com
        """
    )
    
    parser.add_argument('url', help='URL of the website to crawl')
    parser.add_argument('-d', '--depth', type=int, default=2,
                        help='Crawling depth (default: 2)')
    parser.add_argument('-m', '--min-word-length', type=int, default=3,
                        help='Minimum word length (default: 3)')
    parser.add_argument('-x', '--max-word-length', type=int, default=None,
                        help='Maximum word length')
    parser.add_argument('-w', '--write', metavar='FILE',
                        help='Write output to a file')
    parser.add_argument('--lowercase', action='store_true',
                        help='(Kept for compatibility - words are always lowercase)')
    parser.add_argument('-n', '--with-numbers', action='store_true',
                        help='Accept words containing digits')
    parser.add_argument('-e', '--email', metavar='FILE',
                        help='Extract emails and save them to a file')
    parser.add_argument('--email-only', action='store_true',
                        help='Extract only emails')
    parser.add_argument('-c', '--count', action='store_true',
                        help='Show occurrence count for each word')
    parser.add_argument('--no-meta', action='store_true',
                        help='Do not include metadata')
    parser.add_argument('-a', '--auth', metavar='USER:PASS',
                        help='HTTP Basic authentication (format: user:pass)')
    parser.add_argument('-u', '--user-agent', metavar='AGENT',
                        help='Custom User-Agent')
    
    args = parser.parse_args()
    
    # Handle authentication
    auth = None
    if args.auth:
        try:
            username, password = args.auth.split(':', 1)
            auth = (username, password)
        except ValueError:
            print("[!] Invalid authentication format. Use USER:PASS", file=sys.stderr)
            sys.exit(1)
    
    # Create PyCeWL instance
    cewl = PyCeWL(
        url=args.url,
        depth=args.depth,
        min_word_length=args.min_word_length,
        max_word_length=args.max_word_length,
        lowercase=args.lowercase,
        with_numbers=args.with_numbers,
        email_file=args.email,
        meta=not args.no_meta,
        auth=auth,
        user_agent=args.user_agent
    )
    
    # Start crawling
    try:
        words, emails = cewl.run()
        
        # Save emails if requested
        if args.email and emails:
            with open(args.email, 'w', encoding='utf-8') as f:
                for email in sorted(emails):
                    f.write(f"{email}\n")
            print(f"[*] {len(emails)} emails saved to {args.email}", file=sys.stderr)
        
        # If email-only mode, exit here
        if args.email_only:
            sys.exit(0)
        
        # Sort words by occurrence (most frequent first)
        if args.count:
            sorted_words = words.most_common()
        else:
            # Sort by decreasing frequency, then alphabetically for ties
            sorted_words = sorted(words.items(), key=lambda x: (-x[1], x[0]))
        
        # Output
        output_lines = []
        for word, count in sorted_words:
            if args.count:
                output_lines.append(f"{word}, {count}")
            else:
                output_lines.append(word)
        
        # Write to file or stdout
        if args.write:
            with open(args.write, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_lines) + '\n')
            print(f"[*] {len(words)} words saved to {args.write}", file=sys.stderr)
        else:
            print('\n'.join(output_lines))
    
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
