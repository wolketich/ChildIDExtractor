#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Child Info Extractor - Extract child IDs and names from ChildPaths HTML

Extracts child information from HTML snippets and exports to CSV or Excel.

Author: wolketich
Last updated: 2025-04-29
"""

import re
import logging
import sys
import csv
import os
from datetime import datetime
from typing import List, Dict, Optional, Union
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('child_extractor')

class ChildInfoExtractor:
    """Extract child information from ChildPaths HTML snippets."""
    
    def __init__(self, debug: bool = False):
        self.html_content = ""
        self.debug = debug
        self.child_id_pattern = re.compile(r'/child/([^/]+)')
        self.all_children = []
        
    def _sanitize_text(self, text: Optional[str]) -> str:
        """Clean up text - handling whitespace, non-breaking spaces, etc."""
        if not text:
            return ""
        return ' '.join(text.replace('\xa0', ' ').split())
    
    def _extract_child_id(self, href: str) -> Optional[str]:
        """Pull the child ID from a URL."""
        if not href:
            return None
            
        match = self.child_id_pattern.search(href)
        return match.group(1) if match else None
    
    def _find_child_name(self, anchor_tag) -> str:
        """Extract child name from the anchor tag structure."""
        # First try the expected structure
        name_div = anchor_tag.find('div', {'class': ['col-lg-8', 'col-xs-8']})
        
        if name_div:
            return self._sanitize_text(name_div.text)
            
        # If that didn't work, try a few common variations
        alt_name_div = anchor_tag.find('div', text=re.compile(r'\w+'))
        if alt_name_div:
            return self._sanitize_text(alt_name_div.text)
            
        # Last resort: just get all text from the anchor
        all_text = self._sanitize_text(anchor_tag.text)
        if all_text:
            return all_text
            
        return "Unknown"
    
    def extract(self, html_content: str) -> List[Dict[str, str]]:
        """
        Parse HTML and extract all child information.
        
        Args:
            html_content: HTML string to parse
            
        Returns:
            List of dictionaries with child information (id and name)
        """
        self.html_content = html_content
        
        if not self.html_content:
            logger.warning("No HTML content provided to extract")
            return []
            
        try:
            soup = BeautifulSoup(self.html_content, 'html.parser')
        except Exception as e:
            logger.error(f"Failed to parse HTML: {e}")
            return []
        
        children = []
        child_links = soup.find_all('a', href=re.compile(r'/child/'))
        
        if not child_links and self.debug:
            logger.debug("No child links found - might be using unexpected HTML structure")
            all_links = soup.find_all('a')
            for link in all_links:
                logger.debug(f"Found link: {link.get('href')}")
        
        for idx, a_tag in enumerate(child_links):
            try:
                href = a_tag.get('href', '')
                child_id = self._extract_child_id(href)
                
                if not child_id:
                    logger.warning(f"Could not extract child ID from link: {href}")
                    continue
                
                child_name = self._find_child_name(a_tag)
                
                if not child_name or child_name == "Unknown":
                    logger.warning(f"Could not extract name for child ID: {child_id}")
                    parent_row = a_tag.find_parent('div', {'class': 'row'})
                    if parent_row:
                        all_text = self._sanitize_text(parent_row.text)
                        for common_text in ["overview", "profile", "details"]:
                            all_text = all_text.replace(common_text, "")
                        if all_text:
                            child_name = all_text
                
                children.append({
                    'id': child_id,
                    'name': child_name,
                    'extraction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
            except Exception as e:
                logger.error(f"Error processing child #{idx+1}: {e}")
                continue
        
        if not children:
            logger.warning("No children information extracted from the provided HTML")
            
        # Add to our cumulative collection of children
        self.all_children.extend(children)
        return children
    
    def export_to_csv(self, filename: str = None) -> str:
        """
        Export all extracted children to CSV file
        
        Args:
            filename: Optional filename to use for the CSV
            
        Returns:
            Path to the created CSV file
        """
        if not self.all_children:
            logger.warning("No children to export")
            return ""
            
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"child_data_{timestamp}.csv"
            
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'name', 'extraction_time']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for child in self.all_children:
                    writer.writerow(child)
                    
            logger.info(f"Successfully exported {len(self.all_children)} children to {filename}")
            return os.path.abspath(filename)
            
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            return ""
    
    def export_to_excel(self, filename: str = None) -> str:
        """
        Export all extracted children to Excel file
        
        Args:
            filename: Optional filename to use for the Excel file
            
        Returns:
            Path to the created Excel file
        """
        if not self.all_children:
            logger.warning("No children to export")
            return ""
            
        try:
            # Only import pandas when needed
            import pandas as pd
        except ImportError:
            logger.error("pandas is required for Excel export. Please install it with: pip install pandas openpyxl")
            return ""
            
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"child_data_{timestamp}.xlsx"
            
        try:
            df = pd.DataFrame(self.all_children)
            df.to_excel(filename, index=False, engine='openpyxl')
            
            logger.info(f"Successfully exported {len(self.all_children)} children to {filename}")
            return os.path.abspath(filename)
            
        except Exception as e:
            logger.error(f"Failed to export to Excel: {e}")
            return ""


def main():
    """Interactive command-line interface for the extractor."""
    print("\n" + "="*60)
    print("  ChildPaths Information Extractor")
    print("  Author: wolketich | Last Updated: 2025-04-29")
    print("="*60 + "\n")
    
    print("This tool extracts child IDs and names from ChildPaths HTML snippets.")
    print("You can paste HTML content multiple times and export the results.")
    print("\nNote: For Excel export, you need pandas and openpyxl installed.")
    print("      Install with: pip install pandas openpyxl\n")
    
    extractor = ChildInfoExtractor(debug=True)
    
    while True:
        print("\n" + "-"*60)
        print("Paste the HTML content below (type 'DONE' on a new line when finished):")
        print("-"*60)
        
        # Collect multiline input until user types DONE
        html_lines = []
        while True:
            line = input()
            if line.strip().upper() == 'DONE':
                break
            html_lines.append(line)
        
        html_content = "\n".join(html_lines)
        
        if not html_content.strip():
            print("\nNo HTML content provided.")
        else:
            print("\nProcessing HTML content...")
            children = extractor.extract(html_content)
            
            if children:
                print(f"\nExtracted {len(children)} children:")
                for idx, child in enumerate(children):
                    print(f"  {idx+1}. {child['name']} (ID: {child['id']})")
            else:
                print("\nNo children found in the provided HTML.")
                print("Please check that the HTML contains the expected structure.")
        
        print(f"\nTotal children collected so far: {len(extractor.all_children)}")
        
        # Ask if the user wants to add more HTML, export, or quit
        action = input("\nWhat would you like to do next? (add/export/quit): ").strip().lower()
        
        if action == 'add':
            continue
        elif action == 'export':
            if not extractor.all_children:
                print("No children to export. Please add some HTML content first.")
                continue
            
            export_format = input("Export as CSV or Excel? (csv/excel): ").strip().lower()
            
            if export_format == 'csv':
                default_filename = f"child_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filename = input(f"Enter filename (default: {default_filename}): ").strip()
                filename = filename or default_filename
                
                filepath = extractor.export_to_csv(filename)
                if filepath:
                    print(f"Data exported to: {filepath}")
            
            elif export_format == 'excel':
                default_filename = f"child_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                filename = input(f"Enter filename (default: {default_filename}): ").strip()
                filename = filename or default_filename
                
                filepath = extractor.export_to_excel(filename)
                if filepath:
                    print(f"Data exported to: {filepath}")
            
            else:
                print("Invalid format. Please choose 'csv' or 'excel'.")
            
            # Ask if they want to continue or quit after exporting
            continue_action = input("\nContinue extracting more data? (yes/no): ").strip().lower()
            if continue_action != 'yes':
                break
        
        elif action == 'quit':
            # Ask if they want to save before quitting if they have data
            if extractor.all_children:
                save_action = input("Save data before quitting? (yes/no): ").strip().lower()
                if save_action == 'yes':
                    export_format = input("Export as CSV or Excel? (csv/excel): ").strip().lower()
                    
                    if export_format == 'csv':
                        default_filename = f"child_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        filename = input(f"Enter filename (default: {default_filename}): ").strip()
                        filename = filename or default_filename
                        
                        filepath = extractor.export_to_csv(filename)
                        if filepath:
                            print(f"Data exported to: {filepath}")
                    
                    elif export_format == 'excel':
                        default_filename = f"child_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                        filename = input(f"Enter filename (default: {default_filename}): ").strip()
                        filename = filename or default_filename
                        
                        filepath = extractor.export_to_excel(filename)
                        if filepath:
                            print(f"Data exported to: {filepath}")
            
            print("\nThank you for using the ChildPaths Information Extractor. Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter 'add', 'export', or 'quit'.")

if __name__ == "__main__":
    main()