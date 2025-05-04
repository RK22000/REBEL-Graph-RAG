import wikipediaapi
import re
from typing import Set, List

class WikipediaScraper:
    def __init__(self, language='en'):
        self.wiki = wikipediaapi.Wikipedia(
            language=language,
            user_agent='REBEL-Graph-RAG/1.0 (https://github.com/yourusername/REBEL-Graph-RAG; your.email@example.com)'
        )
        self.visited_pages: Set[str] = set()
        self.output_file = None

    def clean_text(self, text: str) -> str:
        """Clean the text by removing references and extra whitespace."""
        # Remove references like [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        # Remove multiple newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()

    def get_links(self, page, max_links=None) -> List[str]:
        """Get valid Wikipedia links from a page, optionally limited by max_links."""
        links = []
        for link in page.links.values():
            # Only include links that are valid Wikipedia pages
            if link.namespace == 0:  # Main namespace
                links.append(link.title)
            if max_links and len(links) >= max_links:
                break
        return links

    def scrape_page(self, title: str, current_depth: int, max_depth: int):
        """Recursively scrape Wikipedia pages in a depth-first manner."""
        if current_depth > max_depth or title in self.visited_pages:
            return

        self.visited_pages.add(title)
        page = self.wiki.page(title)

        if not page.exists():
            print(f"Page '{title}' does not exist")
            return

        # Write the page content to the file
        self.output_file.write(f"TITLE: {title}\n")
        self.output_file.write(f"{self.clean_text(page.text)}\n")
        self.output_file.write("----\n")

        # Only follow links if we haven't reached max depth
        if current_depth < max_depth:
            for link_title in self.get_links(page):
                self.scrape_page(link_title, current_depth + 1, max_depth)

    def scrape(self, start_title: str, max_depth: int, max_breadth: int, output_filename: str):
        """Start the scraping process from a given title."""
        with open(output_filename, 'w', encoding='utf-8') as f:
            self.output_file = f
            # First scrape the main page
            main_page = self.wiki.page(start_title)
            if not main_page.exists():
                print(f"Main page '{start_title}' does not exist")
                return

            # Write the main page content
            self.output_file.write(f"TITLE: {start_title}\n")
            self.output_file.write(f"{self.clean_text(main_page.text)}\n")
            self.output_file.write("----\n")

            # Get links from main page limited by max_breadth
            main_links = self.get_links(main_page, max_breadth)
            
            # Scrape each main link up to max_depth
            for link_title in main_links:
                self.scrape_page(link_title, 1, max_depth)

def main():
    # Example usage
    scraper = WikipediaScraper()
    start_topic = input("Enter the Wikipedia topic to start with: ")
    depth = int(input("Enter the maximum depth to scrape (how deep to go into each hyperlink chain): "))
    breadth = int(input("Enter the maximum breadth (how many hyperlinks to explore from the main page): "))
    output_file = f"{start_topic.replace(' ', '_')}_scraped.txt"
    
    print(f"Starting to scrape Wikipedia articles about {start_topic}...")
    scraper.scrape(start_topic, depth, breadth, output_file)
    print(f"Scraping completed! Results saved to {output_file}")

if __name__ == "__main__":
    main() 