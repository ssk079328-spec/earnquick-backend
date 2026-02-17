// Monetag Zone IDs
const MONETAG_CONFIG = {
    vignetteZone: '10616027',
    rewardedZone: '10603637',
    interstitialZone: '10603638'
};

// Load Monetag SDKs
(function() {
    // Rewarded Ad SDK
    var s1 = document.createElement('script');
    s1.type = 'text/javascript';
    s1.async = true;
    s1.src = '//libtl.com/sdk.js?zone=' + MONETAG_CONFIG.rewardedZone;
    s1.setAttribute('data-zone', MONETAG_CONFIG.rewardedZone);
    s1.setAttribute('data-sdk', 'show_' + MONETAG_CONFIG.rewardedZone);
    document.body.appendChild(s1);

    // Vignette Banner
    var s2 = document.createElement('script');
    s2.type = 'text/javascript';
    s2.async = true;
    s2.src = 'https://nap5k.com/tag.min.js?zone=' + MONETAG_CONFIG.vignetteZone;
    s2.setAttribute('data-zone', MONETAG_CONFIG.vignetteZone);
    document.body.appendChild(s2);

    // Interstitial SDK
    var s3 = document.createElement('script');
    s3.type = 'text/javascript';
    s3.async = true;
    s3.src = '//libtl.com/sdk.js?zone=' + MONETAG_CONFIG.interstitialZone;
    s3.setAttribute('data-zone', MONETAG_CONFIG.interstitialZone);
    s3.setAttribute('data-sdk', 'show_' + MONETAG_CONFIG.interstitialZone);
    document.body.appendChild(s3);
})();
