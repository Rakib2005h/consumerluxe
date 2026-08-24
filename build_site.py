#!/usr/bin/env python3
"""Build real-data site: inject products-data.json into index.html, gate GA, fix categories/sitemap."""
import json, re, datetime

d = json.load(open('data/products-data.json'))

GENERIC = {"men's","women's","the","4","6","18","boys'","girls'","japanese","men","women","a","an"}
items = []
for p in d['products']:
    if 'dup_of' in p:
        continue
    title = (p.get('title') or 'Amazon Product').replace('"', '\u2033')
    brand = p.get('brand') or ''
    if not brand:
        first = title.split(' ', 1)[0]
        brand = first if first.lower() not in GENERIC and len(first) <= 16 else 'Amazon'
    price = p.get('price')
    old = p.get('list_price')
    if price is None or old is None or old <= price:
        old = None
    cat = p.get('cat') or 'Lifestyle'
    if p['n'] == 43:
        cat = 'Fitness'
    img = p.get('img')
    img_url = f"https://m.media-amazon.com/images/I/{img}._AC_SX355_.jpg" if img else ""
    items.append({
        "id": 200 + p['n'], "cat": cat, "brand": brand, "title": title,
        "price": price, "old": old, "img": img_url, "link": p['link'],
        "asof": p.get('price_as_of') or '', "dead": bool(p.get('dead')),
    })

amazon_js = json.dumps(items, ensure_ascii=False, indent=0)

html = open('index.html').read()
orig = html

# ---- 1. GA consent gate (head) ----
ga_old = """<script async src="https://www.googletagmanager.com/gtag/js?id=G-C0QK3JP39N"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}gtag('js',new Date());gtag('config','G-C0QK3JP39N',{anonymize_ip:true});</script>"""
ga_new = """<script>/* GA loads only after cookie consent (see setCookieConsent) */
window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}
window.__loadGA=function(){if(window.__gaLoaded)return;window.__gaLoaded=true;var s=document.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id=G-C0QK3JP39N';document.head.appendChild(s);gtag('js',new Date());gtag('config','G-C0QK3JP39N',{anonymize_ip:true});};
try{if(localStorage.getItem('cl_cookie')==='accepted')window.__loadGA();}catch(e){}
</script>"""
assert ga_old in html, "GA block not found"
html = html.replace(ga_old, ga_new)

# ---- 2. setCookieConsent wires GA ----
cc_old = "function setCookieConsent(a){localStorage.setItem('cl_cookie',a?'accepted':'declined');document.getElementById('cookieBanner').classList.remove('show');if(a)showToast('✦ Preferences saved');}"
cc_new = "function setCookieConsent(a){localStorage.setItem('cl_cookie',a?'accepted':'declined');document.getElementById('cookieBanner').classList.remove('show');if(a&&window.__loadGA)window.__loadGA();if(a)showToast('✦ Preferences saved');}"
assert cc_old in html, "cookie consent fn not found"
html = html.replace(cc_old, cc_new)

# ---- 3. Replace fake data block with real data ----
m = re.search(r'// 79 Amazon Affiliate Links.*?\.\.\.amznProducts\n\];', html, re.S)
assert m, "fake data block not found"
block = m.group(0)
# keep the 6 AliExpress literals from the old products array
ali = re.search(r'const products=\[(.*?)\.\.\.amznProducts', block, re.S)
ali_lit = ali.group(1).rstrip().rstrip(',') if ali else ''
new_block = "// Real verified product data (Amazon prices/images checked Aug 2026 via camelcamelcamel)\n"
new_block += "const amazonProducts=" + amazon_js + ";\n"
new_block += "const products=[" + ali_lit + ",...amazonProducts];"
html = html.replace(block, new_block)

# ---- 4. renderProducts: honest price display ----
rp_old_start = "function renderProducts(){"
rp_old_end = "setTimeout(observeReveal,50);\n}"
m2 = re.search(re.escape(rp_old_start) + r'.*?' + re.escape(rp_old_end), html, re.S)
assert m2, "renderProducts not found"
rp_new = """function renderProducts(){
let list=[...products];
if(currentFilter!=='all')list=list.filter(p=>p.cat===currentFilter);
if(currentSearch)list=list.filter(p=>(p.title+' '+p.brand+' '+p.cat).toLowerCase().includes(currentSearch));
if(currentSort==='low')list=list.filter(p=>p.price!=null).sort((a,b)=>a.price-b.price).concat(list.filter(p=>p.price==null));
else if(currentSort==='high')list=list.filter(p=>p.price!=null).sort((a,b)=>b.price-a.price).concat(list.filter(p=>p.price==null));
else if(currentSort==='discount')list.sort((a,b)=>sv(b)-sv(a));
function sv(p){return p.old&&p.price!=null?1-p.price/p.old:0}
if(!list.length){grid.innerHTML='<p style="grid-column:1/-1;text-align:center;color:var(--mt);padding:40px;font-family:Cormorant Garamond,serif;font-size:18px;font-style:italic">No items match your search.</p>';return;}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;')}
const PH='data:image/svg+xml;utf8,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="355" height="355"><rect width="100%" height="100%" fill="#1a1a2e"/><text x="50%" y="46%" fill="#c9a86a" font-family="serif" font-size="22" text-anchor="middle">Consumer Luxe</text><text x="50%" y="56%" fill="#8b8b9e" font-family="sans-serif" font-size="13" text-anchor="middle">Image unavailable</text></svg>');
grid.innerHTML=list.map(p=>{
const disc=p.old&&p.price!=null?Math.round((1-p.price/p.old)*100):0;
const saved=savedItems.has(p.id)?'saved':'';
const badge=disc>=40?'HOT DEAL':disc>=15?'BEST VALUE':'';
const bdClass=badge==='BEST VALUE'?'premium':'';
const src=p.img||PH;
const meta=p.dead?'Currently unavailable — check Amazon':(p.asof?'Price checked '+p.asof:'Verified listing');
const priceHtml=p.price==null
?'<div class="pw"><span class="pp" style="font-size:13px;letter-spacing:0">See current price on Amazon</span></div>'
:'<div class="pw"><span class="pp">$'+p.price.toFixed(2)+'</span>'+(p.old?'<span class="po">$'+p.old.toFixed(2)+'</span><span class="pd">-'+disc+'%</span>':'')+'</div>';
const cta=p.price==null?'Check Price on Amazon \\u2192':'Get Deal \\u2192';
return`<article class="pc"><div class="pm"><img src="${src}" alt="${esc(p.title)}" loading="lazy" onerror="this.onerror=null;this.src='${PH}'"/>${badge?`<span class="bd ${bdClass}">${badge}</span>`:''}<button class="sv ${saved}" onclick="toggleSave(${p.id})" aria-label="Save" aria-pressed="${saved?'true':'false'}">\\u2665</button></div><div class="pb-body"><div class="mtop"><span class="cn">${p.cat}</span><span class="mr">${esc(p.brand)}</span></div><h3 class="tt">${esc(p.title)}</h3><div class="verified-row">${meta}</div>${priceHtml}<a href="${p.link}" class="dl" data-t="${esc(p.title)}" rel="sponsored nofollow noopener" target="_blank" onclick="trackClick(this.getAttribute(\\'data-t\\'))">${cta}</a></div></article>`;
}).join('');
setTimeout(observeReveal,50);
}"""
html = html.replace(m2.group(0), rp_new)

# ---- 5. Category tiles: real images, real categories ----
m3 = re.search(r'<div class="cat-grid">.*?</div>\s*</div>\s*</section>\s*\n\s*<!-- TRUST BAR -->', html, re.S)
assert m3, "cat-grid not found"
tiles = """<div class="cat-grid">
<a href="#deals" class="cat-item reveal" data-filter="Fashion"><img src="https://m.media-amazon.com/images/I/91ndakLSZiL._AC_SX355_.jpg" alt="Fashion"/><div class="cat-arrow">→</div><div class="cat-content"><div class="cat-num">Chapter 01</div><h3>Fashion</h3><p>33 curated finds — lounge sets, cargo & denim</p></div></a>
<a href="#deals" class="cat-item reveal" data-filter="Lifestyle"><img src="https://m.media-amazon.com/images/I/41-jz641kdL._AC_SX355_.jpg" alt="Home and Lifestyle"/><div class="cat-arrow">→</div><div class="cat-content"><div class="cat-num">Chapter 02</div><h3>Home & Living</h3><p>25 picks — mattresses, kitchen, fans & decor</p></div></a>
<a href="#deals" class="cat-item reveal" data-filter="Electronics"><img src="https://m.media-amazon.com/images/I/71eW8nbT6NL._AC_SX355_.jpg" alt="Electronics"/><div class="cat-arrow">→</div><div class="cat-content"><div class="cat-num">Chapter 03</div><h3>Electronics</h3><p>12 picks — portable monitors, chargers & fans</p></div></a>
<a href="#deals" class="cat-item reveal" data-filter="Beauty"><img src="https://m.media-amazon.com/images/I/31-1+GW0x0L._AC_SX355_.jpg" alt="Beauty"/><div class="cat-arrow">→</div><div class="cat-content"><div class="cat-num">Chapter 04</div><h3>Beauty</h3><p>4 essentials — smile care & daily rituals</p></div></a>
<a href="#deals" class="cat-item reveal" data-filter="Fitness"><img src="https://m.media-amazon.com/images/I/71CUmyhYe2L._AC_SX355_.jpg" alt="Fitness"/><div class="cat-arrow">→</div><div class="cat-content"><div class="cat-num">Chapter 05</div><h3>Fitness</h3><p>Recovery & training gear</p></div></a>
</div>
</div>
</section>

<!-- TRUST BAR -->"""
html = html.replace(m3.group(0), tiles)
html = html.replace('Six Worlds of <em>Refined</em> Living', 'Five Worlds of <em>Refined</em> Living')

# ---- 6. Filter buttons: drop Jewelry ----
html = html.replace('<button class="fb" data-filter="Jewelry">Jewelry</button>\n', '')

# ---- 7. Category tile click sets filter ----
fb_bind = "document.querySelectorAll('.fb').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.fb').forEach(x=>x.classList.remove('active'));b.classList.add('active');currentFilter=b.dataset.filter;renderProducts();}));"
assert fb_bind in html
html = html.replace(fb_bind, fb_bind + """
document.querySelectorAll('.cat-item[data-filter]').forEach(t=>t.addEventListener('click',()=>{const f=t.dataset.filter;const btn=document.querySelector('.fb[data-filter="'+f+'"]');if(btn)btn.click();}));""")

# ---- 8. Honest trust-bar + hero numbers ----
n_items = 6 + len(items)  # 6 AliExpress + N Amazon
html = html.replace('<div class="trust-num" data-target="200">0+</div>', f'<div class="trust-num" data-target="{n_items}">0</div>')
html = html.replace('<span class="hero-meta-num">200+</span>', f'<span class="hero-meta-num">{n_items}</span>')

open('index.html', 'w').write(html)

# ---- 9. sitemap lastmod ----
today = datetime.date.today().isoformat()
sm = open('sitemap.xml').read().replace('2026-07-20T00:00:00+00:00', today + 'T00:00:00+00:00')
open('sitemap.xml', 'w').write(sm)

print(f"OK: {len(items)} real products injected, total cards {n_items}")
print("leftover Math.random:", 'Math.random' in html)
print("leftover amznLinks:", 'amznLinks' in html)
print("leftover Jewelry:", 'Jewelry' in html)
print("GA gated:", '__loadGA' in html)
