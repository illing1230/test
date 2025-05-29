#!/usr/bin/env python3
"""
Simple Wikipedia Tool for Langflow
"""

import wikipedia
import json
from typing import Dict, Any, List


class WikipediaTool:
    def __init__(self):
        self.name = "Wikipedia Tool"
        self.description = "Search and retrieve Wikipedia articles"
    
    def search(self, query: str, results: int = 5) -> str:
        """Search Wikipedia articles."""
        try:
            search_results = wikipedia.search(query, results=results)
            if not search_results:
                return f"No results found for query: {query}"
            
            result_text = f"Wikipedia search results for '{query}':\n\n"
            for i, title in enumerate(search_results, 1):
                result_text += f"{i}. {title}\n"
            
            return result_text
        except wikipedia.exceptions.DisambiguationError as e:
            suggestions = e.options[:5]
            result_text = f"Multiple articles found for '{query}'. Did you mean:\n\n"
            for i, suggestion in enumerate(suggestions, 1):
                result_text += f"{i}. {suggestion}\n"
            return result_text
        except Exception as e:
            return f"Error searching Wikipedia: {str(e)}"
    
    def get_summary(self, title: str, sentences: int = 3) -> str:
        """Get Wikipedia article summary."""
        try:
            summary = wikipedia.summary(title, sentences=sentences)
            return f"Summary of '{title}':\n\n{summary}"
        except wikipedia.exceptions.DisambiguationError as e:
            suggestions = e.options[:3]
            result_text = f"Multiple articles found for '{title}'. Did you mean:\n"
            for suggestion in suggestions:
                result_text += f"- {suggestion}\n"
            return result_text
        except wikipedia.exceptions.PageError:
            return f"No Wikipedia page found for '{title}'"
        except Exception as e:
            return f"Error getting summary: {str(e)}"
    
    def get_content(self, title: str) -> str:
        """Get full Wikipedia article content."""
        try:
            page = wikipedia.page(title)
            content = f"Title: {page.title}\n"
            content += f"URL: {page.url}\n\n"
            content += f"Content:\n{page.content}"
            return content
        except wikipedia.exceptions.DisambiguationError as e:
            suggestions = e.options[:3]
            result_text = f"Multiple articles found for '{title}'. Did you mean:\n"
            for suggestion in suggestions:
                result_text += f"- {suggestion}\n"
            return result_text
        except wikipedia.exceptions.PageError:
            return f"No Wikipedia page found for '{title}'"
        except Exception as e:
            return f"Error getting content: {str(e)}"
    
    def get_page_info(self, title: str) -> str:
        """Get detailed Wikipedia page information."""
        try:
            page = wikipedia.page(title)
            
            info = f"Title: {page.title}\n"
            info += f"URL: {page.url}\n"
            info += f"Page ID: {page.pageid}\n"
            info += f"Categories: {', '.join(page.categories[:10])}\n"
            info += f"Links count: {len(page.links)}\n"
            info += f"References count: {len(page.references)}\n"
            
            if page.images:
                info += f"Images: {len(page.images)} found\n"
                info += f"First image: {page.images[0] if page.images else 'None'}\n"
            
            return info
        except wikipedia.exceptions.DisambiguationError as e:
            suggestions = e.options[:3]
            result_text = f"Multiple articles found for '{title}'. Did you mean:\n"
            for suggestion in suggestions:
                result_text += f"- {suggestion}\n"
            return result_text
        except wikipedia.exceptions.PageError:
            return f"No Wikipedia page found for '{title}'"
        except Exception as e:
            return f"Error getting page info: {str(e)}"


# Test the tool
if __name__ == "__main__":
    wiki = WikipediaTool()
    print("Testing Wikipedia Tool:")
    print("-" * 50)
    
    # Test search
    print("Search Results:")
    print(wiki.search("artificial intelligence", 3))
    print("\n" + "-" * 50)
    
    # Test summary
    print("Summary:")
    print(wiki.get_summary("Python (programming language)", 2))