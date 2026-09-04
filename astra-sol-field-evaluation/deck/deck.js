(() => {
  const slides = [...document.querySelectorAll('.slide')];
  const counter = document.getElementById('counter');
  let active = Math.max(0, slides.findIndex(s => '#'+s.id === location.hash));
  let presenting = window.innerWidth > 800;
  function scale() {
    const widthScale = (window.innerWidth - 24) / 1280;
    const heightScale = (window.innerHeight - 82) / 720;
    document.documentElement.style.setProperty('--stage-scale', Math.min(widthScale, heightScale));
  }
  function render() {
    document.body.classList.toggle('presentation', presenting);
    slides.forEach((s,i) => s.classList.toggle('active',i===active));
    counter.textContent = `${active+1} / ${slides.length}`;
    document.getElementById('overview').setAttribute('aria-pressed',String(!presenting));
    document.getElementById('overview').textContent = presenting ? 'Overview' : 'Present';
    history.replaceState(null,'','#'+slides[active].id);
    scale();
  }
  function go(delta) {
    active = Math.min(slides.length-1,Math.max(0,active+delta));
    render();
    if (!presenting) slides[active].scrollIntoView({behavior:'smooth',block:'start'});
  }
  document.getElementById('prev').onclick = () => go(-1);
  document.getElementById('next').onclick = () => go(1);
  document.getElementById('overview').onclick = () => {presenting=!presenting;render(); if(!presenting)slides[active].scrollIntoView();};
  document.getElementById('fullscreen').onclick = async () => {
    if(document.fullscreenElement) await document.exitFullscreen();
    else {presenting=true;render();await document.documentElement.requestFullscreen();}
  };
  window.addEventListener('keydown',e => {
    if(e.target.matches('a,button,input,textarea,select')) return;
    if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();go(1);}
    if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();go(-1);}
    if(e.key==='Home'){active=0;render();}
    if(e.key==='End'){active=slides.length-1;render();}
    if(e.key.toLowerCase()==='o'){presenting=!presenting;render();}
  });
  window.addEventListener('resize',scale);
  render();
})();
