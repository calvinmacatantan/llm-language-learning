# Language Transcript Analyzer

A local Flask web app for parsing ChatGPT conversation transcripts and evaluating them on multiple metrics using the OpenAI API.

## Features
- Paste a ChatGPT transcript and have it automatically parsed into turns.
- Removes common boilerplate and export UI junk.
- Analyzes the transcript on:
  - **Fluency** (0–5)
  - **Coherence** (0–5)
  - **Complexity** (0–5)
  - **Engagement** (0–5)
  - **Frustration** (0–5)
- Each metric includes:
  - Score
  - Confidence (0–1)
  - Evidence supporting the score
- Clean, card-based UI with option to view parsed turns.
- All processing runs locally except the OpenAI API call.

## Requirements
- Python 3.8+
- An [OpenAI API key](https://platform.openai.com/account/api-keys)

## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/calvinmacatantan/llm-language-learning
    cd llm-language-learning
    ```

2. **Create a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate     # macOS/Linux
    .venv\Scripts\activate        # Windows
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Set your API key**:
    Create a `.env` file in the project root:
    ```bash
    echo "OPENAI_API_KEY=sk-yourkeyhere" > .env
    ```

## Usage

1. Run the Flask app:
    ```bash
    python app.py
    ```
2. Open your browser and go to:
    ```
    http://127.0.0.1:5000
    ```
3. Paste a ChatGPT transcript into the text area.
4. Click **Parse & Analyze**.
5. View the results in the UI.