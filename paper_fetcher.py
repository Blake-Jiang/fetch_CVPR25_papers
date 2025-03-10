#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import argparse
from urllib.parse import quote
import os

def fetch_cvpr_papers(url):
    """
    Fetch accepted papers list from CVPR conference website
    """
    print("Fetching papers from CVPR website...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        papers_data = []
        
        # Find table rows based on the provided HTML structure
        table_rows = soup.find_all('tr')
        
        for row in table_rows:
            # Find paper title in <strong> tag
            title_element = row.find('strong')
            if title_element:
                title = title_element.get_text().strip()
                
                # Find author information (in <i> tag)
                authors_element = row.find('i')
                authors = authors_element.get_text().strip() if authors_element else ""
                
                # Extract other potentially useful information (abstract, keywords, etc.)
                abstract = ""
                td_elements = row.find_all('td')
                if len(td_elements) > 1:
                    # Try to extract more information from the second td element
                    abstract = td_elements[1].get_text().strip()
                
                if title and len(title) > 10:  # Simple filter for too short texts
                    papers_data.append({
                        'title': title,
                        'authors': authors,
                        'abstract': abstract
                    })
        
        # If no papers found with the above method, try alternative methods
        if not papers_data:
            # Try to find all <strong> tags
            title_elements = soup.find_all('strong')
            
            for element in title_elements:
                title = element.get_text().strip()
                if title and len(title) > 10:
                    # Try to find adjacent author information
                    parent = element.parent
                    authors_element = parent.find('i') if parent else None
                    authors = authors_element.get_text().strip() if authors_element else ""
                    
                    papers_data.append({
                        'title': title,
                        'authors': authors
                    })
        
        print(f"Found {len(papers_data)} papers")
        return papers_data
    
    except Exception as e:
        print(f"Error fetching CVPR papers list: {e}")
        return []

def filter_papers_by_keywords(papers_data, keywords):
    """
    Filter papers based on keywords
    """
    if not keywords:
        return papers_data
    
    filtered_papers = []
    for paper in papers_data:
        title = paper['title'].lower()
        authors = paper['authors'].lower()
        
        # Combine title and author information into a single string for searching
        search_text = title + " " + authors
        
        # Check if any keyword is in the search text
        if any(keyword.lower() in search_text for keyword in keywords):
            filtered_papers.append(paper)
    
    print(f"After filtering by keywords, {len(filtered_papers)} papers remain")
    return filtered_papers

def search_arxiv(paper_data):
    """
    Search for papers on arXiv
    """
    title = paper_data['title']
    authors = paper_data['authors']
    
    base_url = "https://export.arxiv.org/api/query"
    
    # Clean title, remove special characters
    clean_title = re.sub(r'[^\w\s]', ' ', title)
    # Take the first few keywords from the title for searching
    search_terms = ' '.join(clean_title.split()[:8])
    
    # If author information is available, extract the first author's surname
    first_author = ""
    if authors:
        # Try to extract the first author
        author_match = re.search(r'([A-Za-z]+)', authors)
        if author_match:
            first_author = author_match.group(1)
    
    # Build search query
    search_query = f'ti:"{search_terms}"'
    if first_author:
        search_query += f' AND au:{first_author}'
    
    params = {
        'search_query': search_query,
        'start': 0,
        'max_results': 5
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'xml')
        entries = soup.find_all('entry')
        
        if entries:
            for entry in entries:
                entry_title = entry.find('title').text.strip()
                # Use simple similarity check
                if are_titles_similar(title, entry_title):
                    arxiv_url = entry.find('id').text.strip()
                    pdf_url = arxiv_url.replace('abs', 'pdf') + '.pdf'
                    return {
                        'arxiv_url': arxiv_url,
                        'pdf_url': pdf_url,
                        'arxiv_title': entry_title
                    }
        else:
            print(f"No matching paper found on arXiv: {title}")
            return None
        
    except Exception as e:
        print(f"Error searching arXiv ({title}): {e}")
        return None

def are_titles_similar(title1, title2):
    """
    Check if two titles are similar
    """
    # Convert titles to lowercase and remove special characters
    t1 = re.sub(r'[^\w\s]', '', title1.lower())
    t2 = re.sub(r'[^\w\s]', '', title2.lower())
    
    # Split into words
    words1 = set(t1.split())
    words2 = set(t2.split())
    
    # Calculate proportion of common words
    common_words = words1.intersection(words2)
    similarity = len(common_words) / max(len(words1), len(words2))
    
    return similarity > 0.5  # Consider similar if similarity is greater than 50%

def create_results_table(papers_data):
    """
    Create results table
    """
    df = pd.DataFrame(papers_data)
    return df

def save_results(df, output_format='csv', keywords=None, filename_base=None):
    """
    Save results to the results folder
    """
    # Create results directory if it doesn't exist
    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    # Use keywords for filename if provided, otherwise use timestamp
    if filename_base:
        base_name = filename_base
    else:
        base_name = '_'.join(keywords) if keywords else 'all_papers'
    
    if output_format == 'csv':
        filename = os.path.join(results_dir, f"{base_name}.csv")
        df.to_csv(filename, index=False, encoding='utf-8-sig')
    elif output_format == 'excel':
        filename = os.path.join(results_dir, f"{base_name}.xlsx")
        df.to_excel(filename, index=False)
    elif output_format == 'html':
        filename = os.path.join(results_dir, f"{base_name}.html")
        
        # Create HTML table with styling
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>CVPR Paper Search Results</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                h1 {{
                    color: #333;
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                th, td {{
                    padding: 12px 15px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #4CAF50;
                    color: white;
                    position: sticky;
                    top: 0;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                a {{
                    color: #2196F3;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #666;
                    font-size: 0.9em;
                }}
                .search-info {{
                    margin-bottom: 20px;
                    padding: 10px;
                    background-color: #e7f3fe;
                    border-left: 6px solid #2196F3;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>CVPR Paper Search Results</h1>
                <div class="search-info">
                    <p>Search time: {timestamp}</p>
                    <p>Total papers found: {total}</p>
                </div>
                {table}
                <div class="footer">
                    <p>Generated by CVPR Paper Search Tool</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Process links to make them clickable
        def make_clickable(val):
            if val != 'Not Found' and val.startswith('http'):
                return f'<a href="{val}" target="_blank">{val}</a>'
            return val
        
        for col in ['arXiv Link', 'PDF Link']:
            if col in df.columns:
                df[col] = df[col].apply(make_clickable)
        
        # Generate HTML table
        html_table = df.to_html(index=False, escape=False)
        
        # Fill template
        html_content = html_template.format(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            total=len(df),
            table=html_table
        )
        
        # Save HTML file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
    elif output_format == 'markdown':
        filename = os.path.join(results_dir, f"{base_name}.md")
        
        # Create Markdown content
        md_content = f"# CVPR Paper Search Results\n\n"
        md_content += f"## Search Information\n\n"
        md_content += f"- Search time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        md_content += f"- Keywords: {', '.join(keywords) if keywords else 'None'}\n"
        md_content += f"- Total papers found: {len(df)}\n\n"
        
        md_content += f"## Paper List\n\n"
        
        # Create Markdown table
        # Headers
        headers = df.columns
        md_content += "| " + " | ".join(headers) + " |\n"
        md_content += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        
        # Table content
        for _, row in df.iterrows():
            row_values = []
            for col in headers:
                val = row[col]
                # Process links
                if col in ['arXiv Link', 'PDF Link'] and val != 'Not Found' and isinstance(val, str) and val.startswith('http'):
                    val = f"[Link]({val})"
                # Handle content that may contain pipe symbols
                if isinstance(val, str):
                    # Escape all characters that might break the table
                    val = val.replace('|', '\\|').replace('\n', ' ').replace('\r', '')
                    val = val.replace('_', '\\_').replace('*', '\\*')  # Escape Markdown format characters
                    # Truncate long text
                    if len(val) > 100 and col not in ['arXiv Link', 'PDF Link']:
                        val = val[:97] + "..."
                row_values.append(str(val))
            md_content += "| " + " | ".join(row_values) + " |\n"
        
        # Add footer
        md_content += "\n\n*Generated by CVPR Paper Search Tool*"
        
        # Save Markdown file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    print(f"Results saved to {filename}")
    return filename

def main():
    parser = argparse.ArgumentParser(description='Fetch papers from CVPR website and search on arXiv')
    parser.add_argument('--url', type=str, default='https://cvpr.thecvf.com/Conferences/2025/AcceptedPapers',
                        help='URL of CVPR accepted papers list')
    parser.add_argument('--keywords', type=str, nargs='+', help='Keywords to filter papers')
    parser.add_argument('--output', type=str, choices=['csv', 'excel', 'html', 'markdown'], default='csv',
                        help='Output format (csv, excel, html, markdown)')
    
    args = parser.parse_args()
    
    # Fetch paper list
    papers_data = fetch_cvpr_papers(args.url)
    
    if not papers_data:
        print("No papers found. Please check the URL or if the website structure has changed.")
        return
    
    # Filter papers by keywords
    if args.keywords:
        papers_data = filter_papers_by_keywords(papers_data, args.keywords)
    
    if not papers_data:
        print("No matching papers found after filtering.")
        return
    
    # Search papers on arXiv
    results_data = []
    total = len(papers_data)
    
    print(f"Starting arXiv search for {total} papers...")
    
    for i, paper_data in enumerate(papers_data):
        print(f"Processing {i+1}/{total}: {paper_data['title'][:50]}...")
        
        arxiv_info = search_arxiv(paper_data)
        
        result_data = {
            'CVPR Title': paper_data['title'],
            'CVPR Authors': paper_data['authors'],
            'arXiv Link': arxiv_info['arxiv_url'] if arxiv_info else 'Not Found',
            'PDF Link': arxiv_info['pdf_url'] if arxiv_info else 'Not Found',
            'arXiv Title': arxiv_info['arxiv_title'] if arxiv_info else 'Not Found'
        }
        
        results_data.append(result_data)
        
        # Avoid too frequent requests
        time.sleep(1)
    
    # Create results table
    df = create_results_table(results_data)
    
    # Generate filename based on keywords
    filename_base = '_'.join(args.keywords) if args.keywords else 'all_papers'
    
    # Save results, passing keywords information
    output_file = save_results(df, args.output, args.keywords, filename_base)
    
    print(f"Processing complete! Processed {total} papers, results saved to {output_file}")

if __name__ == "__main__":
    main() 