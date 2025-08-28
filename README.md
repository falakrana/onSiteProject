# Natural Language to Database Schema Generator

This project leverages the power of Google Gemini AI and LangChain to transform natural language business requirements into well-normalized relational database schemas. It's designed to assist developers and database architects in quickly prototyping and validating database designs.

## Features

*   **Intelligent Schema Generation**: Convert descriptive business requirements into a 3NF-compliant database schema with automatically identified tables, fields, data types, primary keys, foreign keys, and relationships.
*   **SQL Query Samples**: Automatically generates practical SQL queries (INSERT, SELECT with JOINs, UPDATE, DELETE) to demonstrate the usage of the generated schema.
*   **Schema Optimization Suggestions**: Provides valuable recommendations for improving schema performance and security, including indexing strategies, normalization refinements, and handling large datasets.
*   **Built-in Schema Validation**: Identifies common database design issues, such as missing primary keys or incorrect foreign key references, to ensure robust schema design.
*   **Flexible Modes**: Offers a demo mode with predefined business scenarios and an interactive mode for custom requirement input.
*   **Extensible Architecture**: Designed for easy integration and extension with potential features like migration script generation, visual ERD diagrams, and multi-database support.

## Installation

To get started with this project, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repository-name.git
    cd your-repository-name
    ```
    (Note: Replace `your-username/your-repository-name.git` with the actual repository URL)

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv onSiteEnv
    ```

3.  **Activate the virtual environment:**
    *   **On Windows:**
        ```bash
        .\onSiteEnv\Scripts\activate
        ```
    *   **On macOS/Linux:**
        ```bash
        source onSiteEnv/bin/activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Set up your Google API Key:**
    Obtain a Google API Key from the [Google AI Studio](https://ai.google.dev/).
    Create a `.env` file in the project root directory and add your API key:
    ```
    GOOGLE_API_KEY="your_google_api_key_here"
    ```

## Usage

### Demo Mode

To run the predefined demo, execute the `schema_generator.py` script without any arguments:

```bash
python schema_generator.py
```

You will be presented with a list of example business requirements to choose from, or you can press Enter to use the first default option.

### Interactive Mode

For custom business requirements, use the `--interactive` flag:

```bash
python schema_generator.py --interactive
```

The program will then prompt you to enter your business requirement, and it will generate the schema, example queries, and optimization suggestions based on your input.

## Project Structure

*   `schema_generator.py`: The main script containing the logic for schema generation, query generation, optimization, and validation.
*   `requirements.txt`: Lists all the Python dependencies required for the project.

## Dependencies

The project relies on the following key libraries:

*   `langchain`: For building applications with large language models.
*   `langchain-google-genai`: Integrates Google Gemini AI with LangChain.
*   `google-generativeai`: The official Python SDK for Google Gemini API.
*   `python-dotenv`: To load environment variables from a `.env` file.

## Future Enhancements

The project is designed with extensibility in mind, with potential future features including:

*   **Migration Script Generation**: Automating the creation of `CREATE TABLE` statements for various database systems.
*   **Visual Schema Diagrams**: Generating Entity-Relationship Diagrams (ERD) to visualize the database schema.
*   **Performance Benchmarking**: Simulating query performance and identifying bottlenecks.
*   **Multi-database Support**: Extending schema generation to support different SQL databases like PostgreSQL, MySQL, etc.
*   **Business Rule Validation**: Implementing checks against domain-specific business rules and constraints.
*   **API Generation**: Automatically generating REST API endpoints directly from the database schema.
