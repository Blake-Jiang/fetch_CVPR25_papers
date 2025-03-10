# CVPR Paper Finder

A tool to fetch papers from CVPR conference website, filter them by keywords, search for matching papers on arXiv, and generate a table of results.

## Features

- Fetch papers from CVPR conference website
- Filter papers by keywords
- Search for matching papers on arXiv
- Generate results in CSV, Excel, HTML, or Markdown format
- Web interface for easy use
- All results are saved in the 'results' folder for better organization

## Installation

1. Ensure Python 3.6+ is installed
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Web Interface

Run the web application:

```bash
python app.py
```

Then open your browser and navigate to `http://localhost:5000`

### Command Line

Basic usage:

```bash
python paper_fetcher.py
```

This will use the default URL (https://cvpr.thecvf.com/Conferences/2025/AcceptedPapers) to fetch papers and generate results in CSV format.

### Command Line Parameters

- `--url`: URL of CVPR accepted papers list (default is 2025 list)
- `--keywords`: Keywords to filter papers (can provide multiple)
- `--output`: Output format, choose from csv, excel, html, or markdown (default is csv)

### Examples

Filter by keywords and output as Excel:

```bash
python paper_fetcher.py --keywords diffusion transformer attention --output excel
```

Specify a different CVPR year:

```bash
python paper_fetcher.py --url https://cvpr.thecvf.com/Conferences/2024/AcceptedPapers
```

Generate Markdown format results (suitable for viewing on GitHub):

```bash
python paper_fetcher.py --keywords GAN 3D --output markdown
```

## Output

The script generates a table with the following columns:

- CVPR Title: Original CVPR paper title
- CVPR Authors: Paper authors
- arXiv Link: Link to the paper found on arXiv
- PDF Link: Direct link to the paper PDF
- arXiv Title: Title of the paper found on arXiv

Result files are saved in the 'results' directory with filenames based on the keywords:
- CSV: `results/keyword1_keyword2.csv`
- Excel: `results/keyword1_keyword2.xlsx`
- HTML: `results/keyword1_keyword2.html`
- Markdown: `results/keyword1_keyword2.md`

If no keywords are provided, the filename will be `results/all_papers.[format]`.

## Notes

- Web scraping may fail if the CVPR website structure changes, code adjustments may be needed
- arXiv API has request rate limits, the script includes delays to avoid exceeding limits
- Title matching is based on a similarity algorithm and may not be 100% accurate 