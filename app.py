#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, send_file
from datetime import datetime
import os
from paper_fetcher import fetch_cvpr_papers, filter_papers_by_keywords, search_arxiv, create_results_table, save_results

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch', methods=['POST'])
def fetch():
    # Get form data
    url = request.form.get('url', 'https://cvpr.thecvf.com/Conferences/2025/AcceptedPapers')
    keywords = request.form.get('keywords', '')
    output_format = request.form.get('output_format', 'html')
    
    # Process keywords
    keywords_list = [k.strip() for k in keywords.split(',') if k.strip()] if keywords else None
    
    # Fetch papers
    papers_data = fetch_cvpr_papers(url)
    
    if not papers_data:
        return render_template('error.html', message="No papers found. Please check the URL or if the website structure has changed.")
    
    # Filter papers by keywords
    if keywords_list:
        papers_data = filter_papers_by_keywords(papers_data, keywords_list)
    
    if not papers_data:
        return render_template('error.html', message="No papers match the provided keywords.")
    
    # Search on arXiv
    results_data = []
    total = len(papers_data)
    
    for i, paper_data in enumerate(papers_data):
        arxiv_info = search_arxiv(paper_data)
        
        result_data = {
            'CVPR Title': paper_data['title'],
            'CVPR Authors': paper_data['authors'],
            'arXiv Link': arxiv_info['arxiv_url'] if arxiv_info else 'Not Found',
            'PDF Link': arxiv_info['pdf_url'] if arxiv_info else 'Not Found',
            'arXiv Title': arxiv_info['arxiv_title'] if arxiv_info else 'Not Found'
        }
        
        results_data.append(result_data)
    
    # Create results table
    df = create_results_table(results_data)
    
    # Generate filename based on keywords
    filename_base = '_'.join(keywords_list) if keywords_list else 'all_papers'
    
    # Save results
    output_file = save_results(df, output_format, keywords_list, filename_base)
    
    if output_format == 'html':
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return render_template('results.html', results=results_data, total=total, keywords=keywords_list, current_time=current_time)
    else:
        return send_file(output_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5019) 