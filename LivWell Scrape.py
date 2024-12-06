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


def get_strain_recommendations(user_preference: str, analyzed_strains: List[Dict]) -> str:
    """Get personalized strain recommendations based on user preferences"""

    prompt = f"""Given this list of cannabis strains and their analyses, recommend the best options for someone who says: "{user_preference}"

Here are the strains to consider:

{format_strains_for_prompt(analyzed_strains)}

Please provide:
1. Top 2-3 recommended strains with brief explanations why
2. Any relevant warnings or considerations
3. Suggested usage tips"""

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
        return f"Error getting recommendations: {str(e)}"


def format_strains_for_prompt(strains: List[Dict]) -> str:
    """Format strain data for the recommendation prompt"""
    formatted_strains = ""
    for strain in strains:
        formatted_strains += f"\nStrain: {strain['strain_name']}\n"
        formatted_strains += f"THC: {strain['thc_percentage']}\n"
        formatted_strains += f"Analysis: {strain['analysis']}\n"
        formatted_strains += "-" * 30 + "\n"
    return formatted_strains


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

                    strain_info = parse_strain_info(thc_info)
                    if not strain_info:
                        continue

                    print(f"\nAnalyzing: {strain_info['strain_name']} ({strain_info['thc_percentage']})")

                    analysis = get_strain_analysis(
                        strain_info['strain_name'],
                        strain_info['thc_percentage']
                    )

                    strain_data = {
                        **strain_info,
                        'analysis': analysis
                    }

                    all_strains.append(strain_data)

                    print("-" * 30)
                    print(analysis)
                    print("-" * 30)

                    time.sleep(1)

                except Exception as e:
                    print(f"Error processing strain: {e}")
                    continue

        except Exception as e:
            print(f"Error on page {page}: {e}")
            continue

    return all_strains


def interactive_recommendations(analyzed_strains: List[Dict]):
    """Interactive recommendation system for users"""
    print("\nWelcome to the Strain Recommendation System!")
    print("Tell me what you're looking for in a cannabis experience.")
    print("Examples:")
    print("- 'I want something to help with creativity'")
    print("- 'Looking for a relaxing indica for evening use'")
    print("- 'Need something for anxiety that won't make me too sleepy'")
    print("\nType 'quit' to exit")

    while True:
        user_input = input("\nWhat are you looking for? ").strip()

        if user_input.lower() == 'quit':
            break

        if not user_input:
            print("Please provide some preferences to get recommendations.")
            continue

        print("\nAnalyzing your preferences...")
        recommendations = get_strain_recommendations(user_input, analyzed_strains)
        print("\nRecommendations:")
        print("-" * 50)
        print(recommendations)
        print("-" * 50)


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

    # Save results to file
    try:
        with open('strain_analysis.txt', 'w') as f:
            for strain in analyzed_strains:
                f.write(f"\n{'=' * 50}\n")
                f.write(f"Strain: {strain['strain_name']}\n")
                f.write(f"THC: {strain['thc_percentage']}\n")
                f.write(f"Analysis:\n{strain['analysis']}\n")
    except Exception as e:
        print(f"Error saving results: {e}")

    # Start interactive recommendation system
    interactive_recommendations(analyzed_strains)
