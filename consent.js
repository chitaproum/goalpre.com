/* Minimal cookie/ads notice. Stores the visitor's choice locally and tells ads.js
 * whether ads may load. NOTE: this is NOT a Google-certified CMP. Before enabling
 * AdSense for EEA/UK visitors, replace it with a certified consent platform
 * (see ADS-README.md) and keep calling PreBetAds.setConsent(true/false). */
(function () {
  'use strict';
  var KEY = 'goalpre-consent';
  function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function set(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
  function apply(v) {
    if (window.PreBetAds && typeof window.PreBetAds.setConsent === 'function') {
      window.PreBetAds.setConsent(v === 'granted');
    }
  }
  function banner() {
    var el = document.createElement('div');
    el.id = 'consentBanner';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-label', 'Cookie notice');
    el.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:9999;background:#10231a;color:#fff;' +
      'padding:12px 16px;font:14px/1.4 system-ui,sans-serif;display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:center';
    el.innerHTML = '<span>GoalPre uses cookies and local storage for preferences and, if enabled, advertising. ' +
      'See our <a href="privacy.html" style="color:#9fe3bf">Privacy &amp; Cookie Policy</a>.</span>' +
      '<button type="button" data-c="granted" style="padding:6px 14px;border:0;border-radius:4px;background:#0c7a4d;color:#fff;cursor:pointer">Accept</button>' +
      '<button type="button" data-c="denied" style="padding:6px 14px;border:1px solid #9fe3bf;border-radius:4px;background:transparent;color:#fff;cursor:pointer">Decline</button>';
    el.addEventListener('click', function (e) {
      var v = e.target && e.target.getAttribute && e.target.getAttribute('data-c');
      if (!v) return;
      set(v); apply(v); el.remove();
    });
    document.body.appendChild(el);
  }
  function init() {
    var v = get();
    if (v) { apply(v); } else { banner(); }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
  window.addEventListener('load', function () { var v = get(); if (v) apply(v); });
})();
