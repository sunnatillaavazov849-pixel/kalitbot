// Nusxalash tugmalari: <button data-copy="#id"> yoki data-copy-text="..."
document.addEventListener("click", function (e) {
  var b = e.target.closest("[data-copy],[data-copy-text]");
  if (!b) return;
  var text = b.getAttribute("data-copy-text");
  if (text === null) { var el = document.querySelector(b.getAttribute("data-copy")); text = el ? el.textContent.trim() : ""; }
  var old = b.textContent;
  function done(msg) { b.textContent = msg; setTimeout(function () { b.textContent = old; }, 1600); }
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(function () { done("Nusxalandi"); }, function () { done("Ctrl+C"); });
  } else { done("Ctrl+C"); }
});
// Fayl tanlanganda nomini ko'rsatish
document.addEventListener("change", function (e) {
  if (e.target.matches("input[type=file][data-show]")) {
    var out = document.querySelector(e.target.getAttribute("data-show"));
    if (out) out.textContent = e.target.files.length ? e.target.files[0].name : "";
  }
});
