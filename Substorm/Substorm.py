import os
import requests
import re
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(console_handler)

# URLs for wordlists
urls = [
    "https://raw.githubusercontent.com/dwyl/english-words/refs/heads/master/words.txt"
]

# Configuration
domain = "cyble.com"
folder_name = "wordlists"
alterx_folder = "alterx_results"
merged_file = os.path.join(folder_name, "MergedList.txt")
alterx_batch_folder = os.path.join(alterx_folder, "batches")
BATCH_SIZE = 50000

# Patterns for domain generation
patterns = [
    "{{word}}.{{domain}}",                # abc.cyble.com
    "{{sub}}.{{word}}.{{domain}}",        # aws.abc.cyble.com
    "{{word}}-{{sub}}.{{domain}}",        # abc-aws.cyble.com
    "{{sub}}-{{word}}.{{domain}}",        # aws-abc.cyble.com
    "{{word}}.{{sub}}.{{domain}}",        # abc.aws.cyble.com
    "{{region}}.{{sub}}.{{domain}}",      # us-east.aws.cyble.com
    "{{word}}{{number}}.{{domain}}"       # abc123.cyble.com
]

# File paths for word lists
words_file = "word.txt"
numbers_file = "number.txt"
regions_file = "region.txt"

# Helper functions
def clean_subdomain(sub):
    """Clean subdomain for use in patterns."""
    return re.sub(r'[^a-z0-9-]', '', sub.lower()).strip('-')

def is_valid_domain(domain):
    """Check if the domain is valid."""
    return re.match(r'^[a-z0-9.-]+\.[a-z]{2,}$', domain) is not None

def save_batch(domains, batch_num):
    """Save a batch of domains to a file"""
    batch_file = os.path.join(alterx_batch_folder, f"batch_{batch_num}.txt")
    try:
        with open(batch_file, "w") as f:
            for domain in domains:
                f.write(domain + "\n")
        logging.info(f"Saved batch {batch_num} with {len(domains)} domains")
    except Exception as e:
        logging.error(f"Error saving batch {batch_num}: {e}")

# Step 1: Download and merge wordlists
if not os.path.exists(merged_file):
    os.makedirs(folder_name, exist_ok=True)
    logging.info("Downloading and merging wordlists...")
    for url in urls:
        file_name = os.path.join(folder_name, os.path.basename(url))
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            with open(file_name, "wb") as file:
                file.write(response.content)
            logging.info(f"Successfully downloaded: {url}")
        except requests.RequestException as e:
            logging.error(f"Failed to download {url}: {e}")

    with open(merged_file, "w") as merged:
        for file_name in os.listdir(folder_name):
            if file_name.endswith(".txt") and file_name != "MergedList.txt":
                file_path = os.path.join(folder_name, file_name)
                with open(file_path, "r") as file:
                    merged.write(file.read())
                    merged.write("\n")
    logging.info(f"Merged wordlists saved to: {merged_file}")
else:
    logging.info("Merged wordlists already exist. Skipping download.")

# Step 2: Load data and sanitize inputs
def load_list_from_file(file_name):
    try:
        with open(file_name, "r") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        logging.error(f"File not found: {file_name}")
        return []

words = load_list_from_file(words_file)
numbers = load_list_from_file(numbers_file)
regions = load_list_from_file(regions_file)

logging.info(f"Loaded words: {len(words)}, numbers: {len(numbers)}, regions: {len(regions)}")

# Step 2: Load filtered subdomains
def load_filtered_subdomains(file_name):
    """Load filtered subdomains from a file."""
    return load_list_from_file(file_name)

# Load filtered subdomains
filtered_subdomains_file = "/Users/kapilgurav/Desktop/Nucclious/wordlists/filtered_domains.txt"
filtered_subdomains = load_filtered_subdomains(filtered_subdomains_file)

# Step 3: Generate subdomains using patterns
os.makedirs(alterx_folder, exist_ok=True)
os.makedirs(alterx_batch_folder, exist_ok=True)

generated_domains = set()  # Use a set to ensure uniqueness
batch_counter = 1
for base_domain in filtered_subdomains:  # Iterate through filtered subdomains
    logging.info(f"Generating domains for base domain: {base_domain}")
    for pattern in patterns:
        for word in words:
            for number in numbers:
                for region in regions:
                    domain_variation = pattern.replace("{{word}}", word) \
                        .replace("{{number}}", number) \
                        .replace("{{region}}", region) \
                        .replace("{{domain}}", base_domain)  # Use base_domain here
                    
                    # Validate and add to the set
                    if is_valid_domain(domain_variation):
                        generated_domains.add(domain_variation)
                    
                    # Save batch
                    if len(generated_domains) >= BATCH_SIZE:
                        save_batch(list(generated_domains), batch_counter)
                        batch_counter += 1
                        generated_domains.clear()

# Save remaining domains
if generated_domains:
    save_batch(list(generated_domains), batch_counter)

logging.info("Domain generation completed!")
