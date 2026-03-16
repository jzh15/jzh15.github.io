(() => {
  const cards = document.querySelectorAll(".repo-card-html[data-repo]");
  if (!cards.length) return;
  const metadataUrl = document.currentScript?.dataset.repoMetadataUrl || "/assets/json/repo-metadata.json";

  const numberFormatter = new Intl.NumberFormat("en", { notation: "compact" });

  const updateCard = (card, data) => {
    const desc = card.querySelector(".repo-card-desc");
    const lang = card.querySelector(".repo-card-lang");
    const stars = card.querySelector(".repo-card-stars");
    const forks = card.querySelector(".repo-card-forks");

    if (desc) {
      desc.textContent = data.description || "No description available.";
    }
    if (lang) {
      lang.textContent = data.language || "—";
    }
    if (stars) {
      stars.textContent = `★ ${numberFormatter.format(data.stargazers_count || 0)}`;
    }
    if (forks) {
      forks.textContent = `⑂ ${numberFormatter.format(data.forks_count || 0)}`;
    }
  };

  const markUnavailable = (card) => {
    const desc = card.querySelector(".repo-card-desc");
    if (desc) {
      desc.textContent = "Description unavailable.";
    }
  };

  fetch(metadataUrl)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Repository metadata error: ${response.status}`);
      }
      return response.json();
    })
    .then((payload) => {
      const repos = payload.repos || {};

      cards.forEach((card) => {
        const repo = card.getAttribute("data-repo");
        if (!repo || !repo.includes("/")) return;

        const data = repos[repo];
        if (data) {
          updateCard(card, data);
        } else {
          markUnavailable(card);
        }
      });
    })
    .catch(() => {
      cards.forEach(markUnavailable);
    });
})();
