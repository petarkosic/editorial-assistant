# News Scout Agent

An AI-powered agent that automatically monitors a news feed, evaluates article importance and identifies breaking news stories.

## Overview

The News Scout Agent is the first component in our editorial AI system. It scans RSS feeds, uses AI to assess the importance of each article and generates reports highlighting the most significant stories.

## Features

- **Monitoring**: Scans RSS feeds for new content
- **AI-Powered Analysis**: Uses LLM to evaluate article importance
- **Smart Filtering**: Automatically filters out trivial updates and minor stories
- **Concise Summaries**: Generates one-sentence summaries of story significance
- **Priority Scoring**: Highlights stories with importance score ≥ 5/10
- **Automated Reporting**: Saves structured JSON reports with timestamps

## Quick Start

### Prerequisites

- Python 3.13+
- UV package manager (recommended)

### Installation

```bash
uv sync
```

### Configuration

The app uses **openai** python library for ease of use and familiar interface, but it has been configured to work with the Google Generative AI API.

Create an .env file and add the following:

```bash
OPENAI_API_KEY=<api key from ai studio>
OPENAI_API_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

The search is capped at **5** articles to avoid using too many tokens.
This number can be changed in code.

### Usage

```bash
uv run main.py
```

## Output Example

```bash
Analyzed 5 articles
Found 2 important stories:

Importance Score: 8/10
Title: White House begins plan for mass firings if there's a government shutdown
Link: [article-url]
Summary: The White House is preparing for potential government shutdown...
Reasoning: Government shutdowns have widespread impact; planning indicates high probability.
Description: [list of links for similar articles]
```
