import os
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv
import datetime

# Load environment variables from .env file if it exists
load_dotenv()   

def get_token():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Warning: GITHUB_TOKEN environment variable not set.")
    return token

def parse_repo_url(repo_url):
    # Expects https://github.com/owner/repo
    path = urlparse(repo_url).path.strip("/")
    owner, repo = path.split("/")[:2]
    return owner, repo

def run_graphql_query(query, variables, token):
    headers = {"Authorization": f"bearer {token}"}
    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=headers
    )
    if resp.status_code != 200:
        print("GraphQL query failed:", resp.text)
        return None
    # print("**************GraphQL query successful***************")
    return resp.json()

def get_repo_stats_and_users(owner, repo, token):
    # Helper for paginated user collection
    def collect_users(field):
        users = set()
        after = None
        while True:
            if field == "stargazers":
                query = """
                query($owner: String!, $repo: String!, $after: String) {
                  repository(owner: $owner, name: $repo) {
                    stargazers(first: 100, after: $after) {
                      pageInfo { hasNextPage endCursor }
                      nodes { login }
                    }
                  }
                }
                """
            elif field == "watchers":
                query = """
                query($owner: String!, $repo: String!, $after: String) {
                  repository(owner: $owner, name: $repo) {
                    watchers(first: 100, after: $after) {
                      pageInfo { hasNextPage endCursor }
                      nodes { login }
                    }
                  }
                }
                """
            else:  # forks
                query = """
                query($owner: String!, $repo: String!, $after: String) {
                  repository(owner: $owner, name: $repo) {
                    forks(first: 100, after: $after) {
                      pageInfo { hasNextPage endCursor }
                      nodes { owner { login } }
                    }
                  }
                }
                """
            variables = {"owner": owner, "repo": repo, "after": after}
            data = run_graphql_query(query, variables, token)
            if not data or "data" not in data or not data["data"]["repository"]:
                break
            repo_data = data["data"]["repository"]
            if field == "stargazers":
                nodes = repo_data["stargazers"]["nodes"]
                page_info = repo_data["stargazers"]["pageInfo"]
                users.update([u["login"] for u in nodes])
            elif field == "watchers":
                nodes = repo_data["watchers"]["nodes"]
                page_info = repo_data["watchers"]["pageInfo"]
                users.update([u["login"] for u in nodes])
            else:
                nodes = repo_data["forks"]["nodes"]
                page_info = repo_data["forks"]["pageInfo"]
                users.update([f["owner"]["login"] for f in nodes])
            if page_info["hasNextPage"]:
                after = page_info["endCursor"]
            else:
                break
        return users

    # Collect all users
    all_stargazers = collect_users("stargazers")
    all_watchers = collect_users("watchers")
    all_forks = collect_users("forks")

    # Get counts (no pagination needed)
    query_counts = """
    query($owner: String!, $repo: String!) {
      repository(owner: $owner, name: $repo) {
        stargazerCount
        watchers { totalCount }
        forkCount
      }
    }
    """
    variables = {"owner": owner, "repo": repo}
    data = run_graphql_query(query_counts, variables, token)
    repo_data = data["data"]["repository"] if data and "data" in data and data["data"]["repository"] else {}
    stars = repo_data.get("stargazerCount", 0)
    watches = repo_data.get("watchers", {}).get("totalCount", 0)
    forks_count = repo_data.get("forkCount", 0)

    return stars, watches, forks_count, all_stargazers, all_watchers, all_forks

def get_contributions_last_year(username, token):
    today = datetime.date.today()
    last_year = today - datetime.timedelta(days=365)
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
          }
        }
        company
        repositories {
          totalCount
        }
      }
    }
    """
    variables = {
        "login": username,
        "from": last_year.isoformat() + "T00:00:00Z",
        "to": today.isoformat() + "T23:59:59Z"
    }
    data = run_graphql_query(query, variables, token)
    # print(data)
    if not data or "data" not in data or not data["data"]["user"]:
        return 0, "", 0
    user = data["data"]["user"]
    contributions = user["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    company = user.get("company", "")
    public_repos = user["repositories"]["totalCount"]
    return contributions, company, public_repos

def is_significant_user(login, token):
    contributions, company, public_repos = get_contributions_last_year(login, token)
    # 1. Company contains 'microsoft'
    if company and "microsoft" in company.lower():
        return [True, "msft"]
    # 2. At least 50 public contributions in the past year AND at least 50 public repos
    if contributions >= 50 and public_repos >= 5:
        return [True, "other"]
    return [False, False]


def main():
    token = get_token()
    if not token:
        print("Token required for views and user info. Exiting.")
        return
    repo_url = input("Enter GitHub repo address (e.g., https://github.com/owner/repo): ").strip()
    while(repo_url != ""):
        owner, repo = parse_repo_url(repo_url)

        # 1. Get stars, watches, forks, and users via GraphQL
        stars, watches, forks, stargazers, watchers_set, forks_users = get_repo_stats_and_users(owner, repo, token)
        print(f"Stars: {stars}, Watches: {watches}, Forks: {forks}")

        all_users = stargazers | watchers_set | forks_users
        print(f"Total unique users (starred, watched, forked): {len(all_users)}")

        # 2. Get number of unique significant users
        significant_users = set()
        msft_users = set()
        for login in all_users:
            sig, kind = is_significant_user(login, token)
            if sig:
                significant_users.add(login)
                if kind == "msft":
                    msft_users.add(login)
        print(f"Number of unique significant users: {len(significant_users)}")
        print(f"Number of unique MSFT users: {len(msft_users)}")

        # 3. Calculate scores
        power_users_rate = len(significant_users) / len(all_users) if all_users else 0
        msft_users_rate = len(msft_users) / len(all_users) if all_users else 0

        print(f"Power users rate: {power_users_rate:.2f}")
        print(f"MSFT users rate: {msft_users_rate:.2f}")
        repo_url = input("Enter GitHub repo address (e.g., https://github.com/owner/repo): ").strip()

if __name__ == "__main__":
    main()