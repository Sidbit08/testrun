(() => {
  const audios = [...document.querySelectorAll('.bg-audio')];
  const play = () => audios.forEach(a => a.play().catch(() => {}));
  window.addEventListener('click', play, {once:true, passive:true});
  window.addEventListener('keydown', play, {once:true});
  play();
})();
