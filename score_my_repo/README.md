# Score My Repo

This project provides tools to retrieve and analyze GitHub repository statistics using both the GitHub REST API and the GitHub GraphQL API.

## Project Structure

```
score_my_repo
├── src
│   ├── get_views_rest.py       # Retrieves views from a specified GitHub repository using the REST API.
│   ├── get_stats_graphql.py    # Obtains statistics such as significant users, stars, and forks using the GraphQL API.
│   └── utils.py                 # Contains utility functions for shared functionality between scripts.
├── requirements.txt             # Lists the dependencies required for the project.
└── README.md                    # Documentation for the project.
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd score_my_repo
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Retrieving Views

To retrieve views from a GitHub repository using the REST API, run the following command:

```
python src/get_views_rest.py
```

You will be prompted to enter the GitHub repository URL and your personal access token.

### Obtaining Statistics

To obtain statistics such as significant users, stars, and forks using the GraphQL API, run:

```
python src/get_stats_graphql.py
```

You will need to provide your personal access token for authentication.

## Contributing

Feel free to submit issues or pull requests if you have suggestions or improvements for the project.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.