// Every product link comes from assets/config.js (one value: appOrigin).
(function () {
  var c = window.OUTCROP_SITE || {};
  var early = document.querySelectorAll('[data-early]');
  for (var i = 0; i < early.length; i++) { if (c.earlyAccessUrl) early[i].href = c.earlyAccessUrl; }
})();
