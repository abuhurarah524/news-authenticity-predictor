const contents = document.querySelector('#report-contents');
const toggle = document.querySelector('#contents-toggle');
const article = document.querySelector('#report-content');
toggle.addEventListener('click', () => {
  const open = toggle.getAttribute('aria-expanded') !== 'true';
  toggle.setAttribute('aria-expanded', String(open));
  contents.classList.toggle('open', open);
});
contents.querySelectorAll('nav a').forEach(link => link.addEventListener('click', () => {
  contents.classList.remove('open');
  toggle.setAttribute('aria-expanded', 'false');
}));
let fontSize = 16;
function setSize(change) {
  fontSize = Math.min(22, Math.max(14, fontSize + change));
  article.style.setProperty('--reading-size', `${fontSize}px`);
  document.querySelector('#smaller-text').disabled = fontSize === 14;
  document.querySelector('#larger-text').disabled = fontSize === 22;
}
document.querySelector('#smaller-text').addEventListener('click', () => setSize(-1));
document.querySelector('#larger-text').addEventListener('click', () => setSize(1));
document.querySelector('#print-report').addEventListener('click', () => window.print());
const navLinks = [...contents.querySelectorAll('nav a')];
const sections = navLinks.map(link => document.getElementById(link.hash.slice(1)));
let scheduled = false;
function updateReading() {
  const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
  document.querySelector('#reading-progress').style.width = `${maxScroll > 0 ? Math.min(100, window.scrollY / maxScroll * 100) : 0}%`;
  let current = 0;
  sections.forEach((section, index) => { if (section.getBoundingClientRect().top <= 120) current = index; });
  navLinks.forEach((link, index) => {
    link.classList.toggle('active', index === current);
    if (index === current) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  });
  scheduled = false;
}
window.addEventListener('scroll', () => { if (!scheduled) { scheduled = true; requestAnimationFrame(updateReading); } }, { passive: true });
window.addEventListener('resize', updateReading);
updateReading();
