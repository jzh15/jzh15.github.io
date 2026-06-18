require "json"

# Exposes the cached GitHub repository metadata produced at build time by
# _scripts/fetch-repo-metadata.js (assets/json/repo-metadata.json) as
# site.data['repo_metadata'].
#
# This lets templates render star counts statically at build time instead of
# relying on shields.io's live /github/stars/ endpoint, which intermittently
# renders "Stars: invalid" whenever shields.io exhausts its shared, unauthenticated
# GitHub API rate limit. The cached counts are fetched with a GitHub token on every
# deploy (and refreshed daily by the update-repo-metadata workflow), so they are
# always available and never rate-limited.
module Jekyll
  class RepoMetadataGenerator < Jekyll::Generator
    safe true
    priority :high

    def generate(site)
      path = File.join(site.source, "assets", "json", "repo-metadata.json")
      return unless File.exist?(path)

      begin
        payload = JSON.parse(File.read(path))
      rescue JSON::ParserError => e
        Jekyll.logger.warn "RepoMetadata:", "Could not parse #{path}: #{e.message}"
        return
      end

      site.data["repo_metadata"] = payload["repos"] || {}
    end
  end
end
