const fs = require("fs");
const https = require("https");
const path = require("path");

const rootDir = path.resolve(__dirname, "..");
const repositoriesConfigPath = path.join(rootDir, "_data", "repositories.yml");
const outputPath = path.join(rootDir, "assets", "json", "repo-metadata.json");

function loadConfiguredRepos(filePath) {
  const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
  const repos = [];
  let inRepoList = false;

  for (const line of lines) {
    if (!inRepoList) {
      if (/^\s*github_repos:\s*$/.test(line)) {
        inRepoList = true;
      }
      continue;
    }

    if (/^[A-Za-z0-9_]+\s*:/.test(line)) {
      break;
    }

    if (!line.trim() || /^\s*#/.test(line)) {
      continue;
    }

    const match = line.match(/^\s*-\s+(.+?)\s*$/);
    if (match) {
      repos.push(match[1].trim());
    }
  }

  if (!repos.length) {
    throw new Error("No repositories found in _data/repositories.yml under github_repos.");
  }

  return repos;
}

function loadExistingMetadata(filePath) {
  if (!fs.existsSync(filePath)) {
    return {};
  }

  try {
    const existing = JSON.parse(fs.readFileSync(filePath, "utf8"));
    return existing.repos || {};
  } catch (error) {
    console.warn(`Ignoring invalid existing metadata at ${filePath}: ${error.message}`);
    return {};
  }
}

function requestJson(url, headers) {
  return new Promise((resolve, reject) => {
    const request = https.get(url, { headers }, (response) => {
      let body = "";

      response.on("data", (chunk) => {
        body += chunk;
      });

      response.on("end", () => {
        let payload = {};
        if (body) {
          try {
            payload = JSON.parse(body);
          } catch (error) {
            reject(new Error(`Invalid JSON from ${url}: ${error.message}`));
            return;
          }
        }

        if (response.statusCode < 200 || response.statusCode >= 300) {
          const message = payload.message || `HTTP ${response.statusCode}`;
          reject(new Error(message));
          return;
        }

        resolve(payload);
      });
    });

    request.on("error", reject);
  });
}

async function fetchRepoMetadata(repo, headers) {
  const data = await requestJson(`https://api.github.com/repos/${repo}`, headers);
  return {
    description: data.description || "",
    language: data.language || "",
    stargazers_count: data.stargazers_count || 0,
    forks_count: data.forks_count || 0,
  };
}

async function main() {
  const repos = loadConfiguredRepos(repositoriesConfigPath);
  const existingRepos = loadExistingMetadata(outputPath);
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
  const headers = {
    Accept: "application/vnd.github+json",
    "User-Agent": "jzh15-homepage-repo-metadata",
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const metadata = {};
  const failures = [];

  for (const repo of repos) {
    try {
      metadata[repo] = await fetchRepoMetadata(repo, headers);
      console.log(`Fetched metadata for ${repo}`);
    } catch (error) {
      if (existingRepos[repo]) {
        metadata[repo] = existingRepos[repo];
        console.warn(`Falling back to existing metadata for ${repo}: ${error.message}`);
      } else {
        failures.push(`${repo}: ${error.message}`);
      }
    }
  }

  if (failures.length) {
    throw new Error(`Failed to fetch repository metadata:\n${failures.join("\n")}`);
  }

  const nextPayload = { repos: metadata };
  fs.writeFileSync(outputPath, `${JSON.stringify(nextPayload, null, 2)}\n`);
  console.log(`Wrote ${outputPath}`);
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
