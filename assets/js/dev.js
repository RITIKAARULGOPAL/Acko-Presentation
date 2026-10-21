/* A slide opened on its own (double-click slides/<id>.html): load the deck's styles, the data, the chrome and the engine around it,
   so it runs exactly as it will in the joined deck — arrows, notes (N), index (O), the walk's music — offline, no server.
   The build ignores this: it takes only what sits between <!-- slide:start --> and <!-- slide:end --> in each slide file. */
(function () {
  var me = document.currentScript && document.currentScript.src;
  var root = me ? me.replace(/assets\/js\/dev\.js.*$/, "") : "../";
  // every path in a slide is written from the project root (assets/img/…), as in the joined deck: the slide file says
  // <base href="../"> itself (so the browser's early image fetches use it too); set one here only if it doesn't
  if (!document.querySelector("base")) document.write('<base href="' + root + '">');
  var css = ["assets/css/app.css", "assets/css/plan-hover.css"];
  var js = ["assets/vendor/three.min.js", "data/keyplans.js", "data/plan-dxf.js", "data/axo-dxf.js", "data/site-floor.js", "assets/js/shell.js", "assets/js/plan-hover.js", "assets/js/app.js"];
  document.write(css.map(function (h) { return '<link rel="stylesheet" href="' + h + '">'; }).join("") +
    js.map(function (s) { return '<script src="' + s + '"><\/script>'; }).join(""));
  document.addEventListener("DOMContentLoaded", function () { if (window.ACKO) window.ACKO.start(); });
})();
