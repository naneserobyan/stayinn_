document.addEventListener('DOMContentLoaded',()=>{
 // --- Booking-like live filters: range values update instantly and results refresh automatically ---
 const filterForm=document.querySelector('.filters form');
 const minRange=document.getElementById('minPrice'), maxRange=document.getElementById('maxPrice');
 const minOut=document.getElementById('minOut'), maxOut=document.getElementById('maxOut');
 const currency=window.STAYINN_CURRENCY || 'AMD';
 let filterTimer=null;
 function fmt(v){ return Math.round(Number(v)).toLocaleString('ru-RU')+' '+currency; }
 function syncRanges(){
   if(!minRange||!maxRange)return;
   let a=Number(minRange.value), b=Number(maxRange.value);
   if(a>b){ if(document.activeElement===minRange) b=a; else a=b; minRange.value=a; maxRange.value=b; }
   if(minOut)minOut.textContent=fmt(a);
   if(maxOut)maxOut.textContent=fmt(b);
 }
 function refreshResults(){
   if(!filterForm)return;
   clearTimeout(filterTimer);
   filterTimer=setTimeout(()=>filterForm.requestSubmit(),280);
 }
 if(minRange&&maxRange){
   syncRanges();
   minRange.addEventListener('input',()=>{syncRanges();refreshResults()});
   maxRange.addEventListener('input',()=>{syncRanges();refreshResults()});
 }
 if(filterForm){
   filterForm.querySelectorAll('input[type=checkbox],input[type=radio],select').forEach(el=>{
     if(el.id!=='minPrice'&&el.id!=='maxPrice') el.addEventListener('change',()=>filterForm.requestSubmit());
   });
 }

 document.querySelectorAll('[data-modal-open]').forEach(b=>b.onclick=()=>document.getElementById(b.dataset.modalOpen+'-modal').classList.add('open'));
 document.querySelectorAll('[data-modal-close]').forEach(b=>b.onclick=()=>b.closest('.modal').classList.remove('open'));
 document.querySelectorAll('.modal').forEach(m=>m.addEventListener('click',e=>{if(e.target===m)m.classList.remove('open')}));
 const ci=document.getElementById('ci'),co=document.getElementById('co'),sum=document.getElementById('booking-summary');
 function calc(){if(!ci||!co)return;let a=new Date(ci.value),b=new Date(co.value);if(!ci.value||!co.value||b<=a){sum.textContent='Выберите даты';return}let n=Math.round((b-a)/86400000),t=n*window.HOTEL_PRICE;sum.innerHTML='<b>'+window.HOTEL_PRICE.toLocaleString('ru-RU')+' AMD × '+n+' ноч.</b><b>'+t.toLocaleString('ru-RU')+' AMD</b>'} if(ci){ci.onchange=calc;co.onchange=calc}
 // --- карта: пины с ценой + popup-карточка (фото, звёзды, рейтинг, доступность) ---
 function popupHtml(p) {
   const stars = '★'.repeat(p.stars || 0);
   const unavailable = p.available === false
     ? '<p class="popup-unavailable">К сожалению, на ваши даты на нашем сайте здесь нет доступных вариантов.</p>'
     : '';
   return '' +
     '<div class="map-popup">' +
       '<img src="' + p.photo + '" alt="' + p.name + '">' +
       '<div class="map-popup-body">' +
         '<b>' + p.name + '</b>' +
         '<div class="map-popup-stars">' + stars + '</div>' +
         '<div class="map-popup-rating"><span class="rating-badge">' + Number(p.rating).toFixed(1) + '</span> ' + p.rating_word + ' · ' + p.reviews + ' отзывов</div>' +
         unavailable +
         '<div class="map-popup-price">' + Number(p.price).toLocaleString('ru-RU') + ' AMD <small>/ ночь</small></div>' +
         '<a class="map-popup-link" href="' + p.url + '">Смотреть →</a>' +
       '</div>' +
     '</div>';
 }

 const pts = window.STAYINN_POINTS || [];
 const YEREVAN = [40.177, 44.503];

 function initMap(id) {
   const el = document.getElementById(id);
   if (!el || !window.L) return;
   const map = L.map(id, { attributionControl: false }).setView(YEREVAN, 12);
   L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);
   const bounds = [];
   let targetMarker = null;

   pts.forEach(p => {
     const icon = L.divIcon({
       className: '',
       html: '<div class="price-pin">' + Number(p.price * (currency === 'AMD' ? 1 : (currency === 'RUB' ? 0.215 : 0.00256))).toLocaleString('ru-RU', {maximumFractionDigits:0}) + ' ' + currency + '</div>',
       iconSize: [120, 30],
       iconAnchor: [60, 15],
     });
     const marker = L.marker([p.lat, p.lng], { icon }).addTo(map).bindPopup(popupHtml(p), { maxWidth: 260 });
     
     if (id === 'full-map' && window.FOCUS_ID && String(p.id) === String(window.FOCUS_ID)) {
       targetMarker = marker;
     }

     bounds.push([p.lat, p.lng]);
   });

   if (id === 'full-map' && window.FOCUS_ID && targetMarker) {
     map.setView(targetMarker.getLatLng(), 15);
     targetMarker.openPopup();
   } else if (bounds.length) {
     const lats = bounds.map(b => b[0]), lngs = bounds.map(b => b[1]);
     const spread = Math.max(Math.max(...lats) - Math.min(...lats), Math.max(...lngs) - Math.min(...lngs));
     if (spread < 3) {
       map.fitBounds(bounds, { padding: [30, 30] });
     }
   }
}
 if (document.getElementById('search-map')) initMap('search-map');
 if (document.getElementById('full-map')) initMap('full-map');

 if (document.getElementById('hotel-map') && window.HOTEL_POINT) {
   const p = window.HOTEL_POINT;
   const map = L.map('hotel-map', {
     attributionControl: false,
     zoomControl: false,
     dragging: false,
     scrollWheelZoom: false,
     doubleClickZoom: false,
     boxZoom: false,
     keyboard: false,
     touchZoom: false,
   }).setView([p.lat, p.lng], 14);
   L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);
   L.marker([p.lat, p.lng]).addTo(map).bindPopup(popupHtml(p), { maxWidth: 260 });
 }

 document.addEventListener('keydown', e => {
   if (e.key === 'Escape') document.querySelectorAll('.review-drawer-overlay').forEach(x => x.remove());
 });

 document.querySelectorAll('.review-open').forEach(b => b.addEventListener('click', async () => {
   // Remove any already-open review drawer first, so clicks never stack up
   // multiple overlays on top of each other (that was the "frozen" feeling).
   document.querySelectorAll('.review-drawer-overlay').forEach(x => x.remove());

   const id = b.dataset.reviewId;
   const propName = document.querySelector('h1') ? document.querySelector('h1').textContent : '';
   const r = await fetch('/api/reviews/' + id).then(x => x.json());

   let html = '<div class="review-drawer">' +
     '<button class="modal-x" data-modal-close>×</button>' +
     '<h2>' + propName + ': отзывы гостей</h2>' +
     '<div class="review-list">';
   r.forEach((x, i) => {
     const hideExtra = i >= 6;
     html += '<div class="review' + (hideExtra ? ' extra-review' : '') + '"' + (hideExtra ? ' style="display:none"' : '') + '>' +
       '<div class="avatar">' + x.initial + '</div>' +
       '<div><div class="review-meta"><b>' + x.author + '</b><span>' + x.country + ' · ' + x.date + '</span><strong>' + x.score + '</strong></div>' +
       '<b>' + x.title + '</b><p>' + x.pos + '</p>' +
       (x.neg ? '<p class="negative">Минусы: ' + x.neg + '</p>' : '') +
       '</div></div>';
   });
   if (r.length > 6) html += '<button class="primary show-more" style="padding:11px 18px;margin-top:10px">Показать ещё</button>';
   html += '</div></div>';

   const overlay = document.createElement('div');
   overlay.className = 'review-drawer-overlay open';
   overlay.innerHTML = html;
   document.body.appendChild(overlay);

   function closeDrawer() { overlay.remove(); }
   overlay.querySelector('[data-modal-close]').onclick = closeDrawer;
   overlay.onclick = e => { if (e.target === overlay) closeDrawer(); };

   const more = overlay.querySelector('.show-more');
   if (more) more.onclick = () => {
     overlay.querySelectorAll('.extra-review').forEach(x => x.style.display = 'grid');
     more.remove();
   };
 }));


 document.querySelectorAll('.show-more-checklist').forEach(link=>{
   link.addEventListener('click',()=>{
     const more=link.nextElementSibling;
     const showing=!more.hidden;
     more.hidden=showing;
     link.textContent=showing?'Ещё':'Свернуть';
   });
 });


 const typeChecks=document.querySelectorAll('.type-cb');
 function applyTypeFilter(){
   const active=[...typeChecks].filter(c=>c.checked).map(c=>c.dataset.cat);
   document.querySelectorAll('.avail-row').forEach(row=>{
     row.style.display=(active.length===0||active.includes(row.dataset.cat))?'':'none';
   });
 }
 typeChecks.forEach(c=>c.addEventListener('change',applyTypeFilter));

 // --- Guests dropdown (Взрослые/Дети, +/- steppers) ---
 const guestsField = document.getElementById('guestsField');
 if (guestsField) {
   const toggle = document.getElementById('guestsToggle');
   const panel = document.getElementById('guestsPanel');
   const summary = document.getElementById('guestsSummary');
   const doneBtn = document.getElementById('guestsDone');
   const counts = {
     adults: parseInt(document.getElementById('adultsInput').value, 10) || 1,
     children: parseInt(document.getElementById('childrenInput').value, 10) || 0,
   };
   const bounds = { adults: [1, 16], children: [0, 10] };

   function render() {
     document.getElementById('adultsCount').textContent = counts.adults;
     document.getElementById('childrenCount').textContent = counts.children;
     document.getElementById('adultsInput').value = counts.adults;
     document.getElementById('childrenInput').value = counts.children;
     let text = counts.adults + ' взросл.';
     if (counts.children) text += ', ' + counts.children + ' дет' + (counts.children === 1 ? 'ей' : 'ей');
     summary.textContent = text;
   }

   toggle.addEventListener('click', e => { e.stopPropagation(); panel.hidden = !panel.hidden; });
   if (doneBtn) doneBtn.addEventListener('click', e => { e.stopPropagation(); panel.hidden = true; });
   document.addEventListener('click', e => { if (!panel.hidden && !guestsField.contains(e.target)) panel.hidden = true; });

   guestsField.querySelectorAll('.step-btn').forEach(btn => {
     btn.addEventListener('click', e => {
       e.stopPropagation();
       const key = btn.dataset.target, dir = parseInt(btn.dataset.dir, 10);
       const [min, max] = bounds[key];
       counts[key] = Math.min(max, Math.max(min, counts[key] + dir));
       render();
     });
   });
 }
});