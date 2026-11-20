/* Valle Café: carrito y pedidos públicos. Los precios se recalculan en Flask. */
(() => {
  const menu = JSON.parse(document.getElementById('menu-data').textContent);
  const byId = new Map(menu.map(item => [item.id, item]));
  const storageKey = 'valle_cafe_cart_v1';
  let cart = {};
  try {
    const stored = JSON.parse(localStorage.getItem(storageKey) || '{}');
    if (stored && typeof stored === 'object' && !Array.isArray(stored)) {
      for (const [id, qty] of Object.entries(stored)) if (byId.has(id) && Number.isInteger(qty) && qty > 0) cart[id] = Math.min(qty, 99);
    }
  } catch (_) { /* Descartar almacenamiento inválido. */ }
  const $ = selector => document.querySelector(selector);
  const money = value => `S/ ${Number(value).toFixed(2)}`;
  const count = () => Object.values(cart).reduce((total, qty) => total + qty, 0);
  const total = () => Object.entries(cart).reduce((sum, [id, qty]) => sum + byId.get(id).precio * qty, 0);
  let toastTimer;

  function toast(message) {
    const box = $('#toast');
    box.textContent = message;
    box.classList.add('visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => box.classList.remove('visible'), 3200);
  }
  function save() { localStorage.setItem(storageKey, JSON.stringify(cart)); renderCart(); }
  function change(id, delta) {
    const next = (cart[id] || 0) + delta;
    if (next <= 0) delete cart[id]; else cart[id] = Math.min(next, 99);
    save();
  }
  function renderCart() {
    $('#cartCount').textContent = count();
    $('#drawerCount').textContent = `(${count()})`;
    $('#cartTotal').textContent = money(total());
    $('#checkoutTotal').textContent = money(total());
    $('#checkoutButton').disabled = count() === 0;
    const lines = Object.entries(cart);
    const box = $('#cartItems');
    box.replaceChildren();
    if (!lines.length) {
      const empty = document.createElement('div'); empty.className = 'cart-empty';
      empty.innerHTML = '<div>☕</div><h3>Tu carrito espera algo delicioso.</h3><p>Explora nuestro menú y agrega tus favoritos.</p>';
      box.append(empty);
      return;
    }
    for (const [id, qty] of lines) {
      const item = byId.get(id);
      const line = document.createElement('div'); line.className = 'cart-line';
      const icon = document.createElement('div'); icon.className = 'cart-line-icon'; icon.textContent = item.icono;
      const content = document.createElement('div');
      const name = document.createElement('strong'); name.textContent = item.nombre;
      const sub = document.createElement('small'); sub.textContent = `${money(item.precio)} por unidad`;
      const controls = document.createElement('div'); controls.className = 'cart-controls';
      const minus = document.createElement('button'); minus.textContent = '−'; minus.setAttribute('aria-label', `Quitar un ${item.nombre}`); minus.addEventListener('click', () => change(id, -1));
      const amount = document.createElement('span'); amount.textContent = qty;
      const plus = document.createElement('button'); plus.textContent = '+'; plus.setAttribute('aria-label', `Agregar otro ${item.nombre}`); plus.addEventListener('click', () => change(id, 1));
      controls.append(minus, amount, plus); content.append(name, sub, controls);
      const price = document.createElement('span'); price.className = 'cart-line-price'; price.textContent = money(item.precio * qty);
      line.append(icon, content, price); box.append(line);
    }
  }
  function toggleCart(open) {
    document.body.classList.toggle('cart-open', open);
    $('#cartDrawer').setAttribute('aria-hidden', String(!open));
  }
  $('#openCart').addEventListener('click', () => toggleCart(true));
  $('#closeCart').addEventListener('click', () => toggleCart(false));
  $('#cartBackdrop').addEventListener('click', () => toggleCart(false));
  document.addEventListener('keydown', e => { if (e.key === 'Escape') toggleCart(false); });
  document.querySelectorAll('.add-product').forEach(button => button.addEventListener('click', () => {
    const item = byId.get(button.dataset.id);
    change(item.id, 1);
    toast(`${item.nombre} agregado a tu pedido ✓`);
  }));
  document.querySelectorAll('.category-pill').forEach(button => button.addEventListener('click', () => {
    document.querySelectorAll('.category-pill').forEach(b => b.classList.toggle('active', b === button));
    document.querySelectorAll('.product-card').forEach(card => { card.hidden = button.dataset.filter !== 'Todos' && card.dataset.category !== button.dataset.filter; });
  }));
  $('#menuToggle').addEventListener('click', () => {
    const open = $('.store-nav').classList.toggle('open');
    $('#menuToggle').setAttribute('aria-expanded', String(open));
  });
  document.querySelectorAll('.store-nav a').forEach(link => link.addEventListener('click', () => $('.store-nav').classList.remove('open')));
  $('#checkoutButton').addEventListener('click', () => {
    if (!count()) return;
    toggleCart(false);
    $('#checkoutMessage').textContent = '';
    $('#checkoutDialog').showModal();
  });
  $('#closeCheckout').addEventListener('click', () => $('#checkoutDialog').close());
  $('#checkoutForm').addEventListener('submit', async event => {
    event.preventDefault();
    if (!count()) return;
    const button = $('#confirmOrder');
    button.disabled = true; button.textContent = 'Registrando pedido…';
    const data = Object.fromEntries(new FormData(event.target).entries());
    data.items = Object.entries(cart).map(([id, cantidad]) => ({ id, cantidad }));
    try {
      const response = await fetch('/api/pedidos', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
      const result = await response.json();
      if (!response.ok) throw Error(result.error || 'No se pudo registrar el pedido.');
      cart = {}; save();
      event.target.reset();
      $('#checkoutDialog').close();
      toast(`¡Pedido confirmado! N.º ${result.pedido_ids.join(', #')}. Consulta el estado con tu correo.`);
    } catch (error) {
      $('#checkoutMessage').textContent = error.message;
      $('#checkoutMessage').style.color = '#a5473d';
    } finally { button.disabled = false; button.textContent = 'Confirmar pedido ↗'; }
  });
  $('#trackingForm').addEventListener('submit', async event => {
    event.preventDefault();
    const result = $('#trackingResult'); result.textContent = 'Buscando tus pedidos…';
    try {
      const correo = $('#trackingEmail').value.trim();
      const telefono = $('#trackingPhone').value.trim();
      const response = await fetch(`/api/seguimiento?correo=${encodeURIComponent(correo)}&telefono=${encodeURIComponent(telefono)}`);
      const payload = await response.json();
      if (!response.ok) throw Error(payload.error || 'No se pudo consultar.');
      result.replaceChildren();
      if (!payload.pedidos.length) { result.textContent = 'Todavía no encontramos pedidos asociados con ese correo.'; return; }
      for (const order of payload.pedidos) {
        const line = document.createElement('div'); line.className = 'tracking-item';
        line.textContent = `#${order.id} · ${order.producto} (${order.cantidad}) — ${order.estado}`;
        result.append(line);
      }
    } catch (error) { result.textContent = error.message; }
  });
  renderCart();
})();
