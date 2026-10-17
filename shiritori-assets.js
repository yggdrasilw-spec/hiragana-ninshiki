/* Dictionary paths stay relative; only this trusted origin supplies stored images. */
(function(root){
  const origin = 'https://shiritori-images.yggdrasil-learning.workers.dev';
  function url(value){
    const path = String(value || '').replace(/^\.\//, '');
    return path === 'shiritori_title.png' || /^assets\/shiritori\/[a-zA-Z0-9_-]+\.(png|jpe?g|webp)$/i.test(path)
      ? origin + '/' + path : null;
  }
  root.ShiritoriAssets = Object.freeze({ origin, url });
  if(typeof module !== 'undefined') module.exports = root.ShiritoriAssets;
})(typeof window === 'undefined' ? globalThis : window);
