# Microsoft Capstone Project - Copilot

This project aims to extract HTML content from websites, process it, and store the resulting data into a vector database. Additionally, it provides functionality to query the stored data using user input.

## Setup

Make sure to install the required dependencies by running:

```bash
pip -r requirements.txt
```

## Usage

1. **Set up Environment Variables:**

Make sure to set your API keys for OpenAI and Together APIs in a `.env` file:

```dotenv
OPENAI_API_KEY=your_openai_api_key
TOGETHER_API_KEY=your_together_api_key
```

2. **Run Latest Python Notebook**

Latest notebook is `test_week10.ipynb` but play around further with `test_week10_master.ipynb`

## PLEASE READ

- **Run the Saving HTML Data section** Fetches and saves HTML content from a given URL into a file. If it fails for any URL then *MANUALLY* add HTML content into a new file.
- **Table Summarize Flag** Update the `summarize` parameter of `process_html` function to pass either raw HTML or summarized table for chunking
- **Random Distractor Text** Update the `distractor_string` and `distractor_insertion_perc` variable to include some random text in between existing content to confuse the LLM with some %

## Contributing

Feel free to contribute to this project by forking it and submitting pull requests.

## License

This project is not licensed.