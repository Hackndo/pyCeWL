# PyCeWL

A Python implementation of CeWL (Custom Word List generator) for creating targeted wordlists from websites.
Written by Claude

## Purpose

PyCeWL crawls a website and extracts words to generate custom wordlists. This is useful for security testing, password cracking, or analyzing website content. Words are sorted by frequency of occurrence.

## Installation

```bash
pip install requests beautifulsoup4
```

## Basic Usage

```bash
# Basic crawl with default settings
python pycewl.py https://example.com

# Specify crawl depth and minimum word length
python pycewl.py -d 3 -m 5 https://example.com

# Save output to file
python pycewl.py -w wordlist.txt https://example.com

# Show word occurrence counts
python pycewl.py -c https://example.com

# Extract emails
python pycewl.py -e emails.txt https://example.com
```

## Options

```
-d, --depth              Crawling depth (default: 2)
-m, --min-word-length    Minimum word length (default: 3)
-x, --max-word-length    Maximum word length
-w, --write              Write output to file
-c, --count              Show occurrence count for each word
-n, --with-numbers       Accept words containing digits
-e, --email              Extract and save emails to file
--email-only             Extract only emails, skip words
--no-meta                Do not include metadata from meta tags
-a, --auth               HTTP Basic auth (format: user:pass)
-u, --user-agent         Custom User-Agent string
```

## Features

- Recursive web crawling with configurable depth
- Extracts words including accented characters
- Case-insensitive word extraction (all lowercase)
- Email address extraction
- Metadata extraction from HTML meta tags
- HTTP Basic authentication support
- Results sorted by frequency (most common first)

## Examples

```bash
# Deep crawl with longer words
python pycewl.py -d 4 -m 6 -w passwords.txt https://target.com

# Extract both words and emails
python pycewl.py -w words.txt -e emails.txt https://target.com

# Crawl authenticated area
python pycewl.py -a admin:password123 https://target.com/admin

# Get word frequency analysis
python pycewl.py -c -w analysis.txt https://target.com
```

## Notes

- Only crawls pages within the same domain
- Progress information is printed to stderr
- Words are always normalized to lowercase
- Supports Unicode characters (accents, special letters)
