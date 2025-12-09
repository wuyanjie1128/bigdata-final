(function () {
  const sel = document.getElementById("langSelect");
  if (!sel) return;

  sel.addEventListener("change", () => {
    const lang = sel.value;

    // set cookie for 1 year
    document.cookie = `lang=${lang}; path=/; max-age=31536000`;

    // preserve current path, update query param
    const url = new URL(window.location.href);
    url.searchParams.set("lang", lang);
    window.location.href = url.toString();
  });
})();
