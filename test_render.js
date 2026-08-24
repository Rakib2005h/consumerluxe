const fs = require('fs');
const html = fs.readFileSync('index.html', 'utf8');
const main = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).find(s => s.includes('amazonProducts'));
function el() {
  return { classList: { add(){}, remove(){}, toggle(){}, contains: () => false }, style: {}, dataset: {},
    addEventListener(){}, setAttribute(){}, textContent: '', appendChild(){}, querySelectorAll: () => [],
    querySelector: () => el(), focus(){}, innerHTML: '' };
}
let gridHTML = '';
global.document = {
  getElementById: id => { const e = el(); if (id === 'productGrid') { Object.defineProperty(e, 'innerHTML', { get: () => gridHTML, set: v => { gridHTML = v; } }); } return e; },
  querySelectorAll: () => [], querySelector: () => el(), createElement: () => el(), body: el(), addEventListener(){}
};
global.window = global;
global.addEventListener = () => {}; global.removeEventListener = () => {};
global.matchMedia = () => ({ matches: false, addEventListener(){} });
global.localStorage = { getItem: () => null, setItem(){} };
global.IntersectionObserver = class { constructor(){} observe(){} disconnect(){} unobserve(){} };
global.requestAnimationFrame = fn => {}; global.innerWidth = 1440; global.scrollY = 0;

const test = `
console.log('products total:', products.length);
console.log('real price:', products.filter(p=>p.price!=null).length,
  '| check-price:', products.filter(p=>p.price==null).length,
  '| real list(strikethrough):', products.filter(p=>p.old!=null).length);
console.log('amzn links:', products.filter(p=>p.link.startsWith('https://amzn.to/')).length);
console.log('amazon imgs:', products.filter(p=>p.img.includes('m.media-amazon.com')).length);
currentFilter='all'; currentSort='featured'; currentSearch=''; renderProducts();
console.log('rendered cards:', (gridHTML.match(/<article/g)||[]).length);
console.log('Get Deal CTAs:', (gridHTML.match(/Get Deal/g)||[]).length,
  '| Check Price CTAs:', (gridHTML.match(/Check Price on Amazon/g)||[]).length,
  '| HOT DEAL badge:', gridHTML.includes('HOT DEAL'));
['Lifestyle','Fashion','Electronics','Beauty','Fitness'].forEach(f=>{
  currentFilter=f; renderProducts();
  console.log(f+':', (gridHTML.match(/<article/g)||[]).length, 'cards');
});
currentFilter='all'; currentSort='low'; renderProducts();
const m = gridHTML.match(/\\$[0-9.]+/);
console.log('cheapest-first price:', m && m[0]);
currentSort='discount'; renderProducts();
const d = gridHTML.match(/-(\\d+)%/);
console.log('biggest discount shown:', d && d[0]);
console.log('data-t attr present:', gridHTML.includes('data-t='));
console.log('placeholder for noimg:', gridHTML.includes('Image unavailable'));
console.log('no random prices:', !/(19|29|39|49)\\.99 \\u2014/.test(gridHTML));
`;
eval(main + test);
