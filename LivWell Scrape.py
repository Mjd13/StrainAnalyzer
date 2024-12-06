import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, List, Optional


def get_strain_analysis(strain_name: str, thc_percentage: str) -> Dict:
    """Get strain analysis from Ollama"""

    prompt = f"""Please analyze the cannabis strain {strain_name} and provide:
1. General Profile:
   * THC content: {thc_percentage}
   * Strain family (Indica/Sativa/Hybrid)
2. Primary Effects:
   * Mental effects (mood, creativity, focus)
   * Physical sensations
   * Duration/onset expectations"""

    try:
        response = requests.post('http://localhost:11434/api/generate',
                                 json={
                                     'model': 'mistral',
                                     'prompt': prompt,
                                     'stream': False
                                 })
        response.raise_for_status()
        return response.json()['response']
    except Exception as e:
        return f"Error getting analysis: {str(e)}"


def parse_strain_info(thc_info: str) -> Optional[Dict]:
    """Parse strain name and THC percentage from the info string"""
    if 'THC:' not in thc_info:
        return None

    parts = thc_info.split('THC:')
    strain_name = parts[0].strip()
    thc_percentage = parts[1].strip()

    return {
        'strain_name': strain_name,
        'thc_percentage': thc_percentage
    }


def scrape_and_analyze_strains(base_url: str, headers: Dict) -> List[Dict]:
    """Scrape strains and get AI analysis for each"""

    print("Starting strain analysis...")
    print("=" * 50)

    all_strains = []

    for page in range(1, 3):
        try:
            response = requests.get(base_url.format(page), headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            product_listings = soup.find_all("div", class_="product-card-content")

            if not product_listings:
                print(f"No products found on page {page}")
                continue

            for product_listing in product_listings:
                try:
                    product_batch_div = product_listing.find("div", class_="product-batch")
                    if not product_batch_div:
                        continue

                    thc_info_span = product_batch_div.find("span")
                    if not thc_info_span:
                        continue

                    thc_info = thc_info_span.text.strip()
                    if not thc_info:
                        continue

                    # Parse strain info
                    strain_info = parse_strain_info(thc_info)
                    if not strain_info:
                        continue

                    print(f"\nAnalyzing: {strain_info['strain_name']} ({strain_info['thc_percentage']})")

                    # Get AI analysis
                    analysis = get_strain_analysis(
                        strain_info['strain_name'],
                        strain_info['thc_percentage']
                    )

                    # Store complete information
                    strain_data = {
                        **strain_info,
                        'analysis': analysis
                    }

                    all_strains.append(strain_data)

                    # Print analysis
                    print("-" * 30)
                    print(analysis)
                    print("-" * 30)

                    # Rate limit to be nice to the APIs
                    time.sleep(1)

                except Exception as e:
                    print(f"Error processing strain: {e}")
                    continue

        except Exception as e:
            print(f"Error on page {page}: {e}")
            continue

    return all_strains


# Main execution
if __name__ == "__main__":
    base_url = "https://livwell.com/order_ahead/pre-weighed-flower?page={}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

    analyzed_strains = scrape_and_analyze_strains(base_url, headers)

    print("\nAnalysis Complete!")
    print(f"Total strains analyzed: {len(analyzed_strains)}")

    # Optionally save results to a file
    try:
        with open('strain_analysis.txt', 'w') as f:
            for strain in analyzed_strains:
                f.write(f"\n{'=' * 50}\n")
                f.write(f"Strain: {strain['strain_name']}\n")
                f.write(f"THC: {strain['thc_percentage']}\n")
                f.write(f"Analysis:\n{strain['analysis']}\n")
    except Exception as e:
        print(f"Error saving results: {e}")