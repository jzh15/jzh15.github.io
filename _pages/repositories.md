---
layout: page
permalink: /repositories/
title: repositories
nav: true
nav_order: 4
---

{% if site.repo_users_enabled and site.data.repositories.github_users %}

## GitHub users

<div class="repositories d-flex flex-wrap flex-md-row flex-column justify-content-between align-items-center">
  {% for user in site.data.repositories.github_users %}
    {% include repository/repo_user.liquid username=user %}
  {% endfor %}
</div>

---

{% endif %}

{% if site.data.repositories.github_repos %}

## GitHub Repositories

<div class="repositories d-flex flex-wrap flex-md-row flex-column justify-content-between align-items-center">
  {% for repo in site.data.repositories.github_repos %}
    {% include repository/repo.liquid repository=repo %}
  {% endfor %}
</div>
{% endif %}

{% if site.repo_cards_mode == 'html' %}

  <script
    src="{{ '/assets/js/repo-cards.js' | relative_url | bust_file_cache }}"
    data-repo-metadata-url="{{ '/assets/json/repo-metadata.json' | relative_url | bust_file_cache }}"
  ></script>

{% endif %}
