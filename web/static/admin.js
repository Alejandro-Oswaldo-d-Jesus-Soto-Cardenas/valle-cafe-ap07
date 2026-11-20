document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('admin-sidebar');
  const menu = document.getElementById('admin-menu');
  menu?.addEventListener('click', () => sidebar?.classList.toggle('open'));
  const links = [...document.querySelectorAll('.admin-nav a')];
  const activeLink = () => {
    const hash = window.location.hash || '#dashboard';
    links.forEach(link => link.classList.toggle('active', link.getAttribute('href') === hash));
    sidebar?.classList.remove('open');
  };
  window.addEventListener('hashchange', activeLink);
  activeLink();
  const search = document.getElementById('admin-client-search');
  search?.addEventListener('input', () => {
    const term = search.value.trim().toLocaleLowerCase('es');
    document.querySelectorAll('.admin-client-row').forEach(row => {
      row.hidden = !(row.dataset.search || '').includes(term);
    });
  });
  const orderSearch = document.getElementById('order-search');
  const orderStatus = document.getElementById('order-status');
  const rows = [...document.querySelectorAll('.order-item[data-order-search]')];
  const filterOrders = () => {
    const term = (orderSearch?.value || '').trim().toLocaleLowerCase('es');
    const status = orderStatus?.value || '';
    let visible = 0;
    for (const row of rows) {
      const matches = (row.dataset.orderSearch || '').includes(term) && (!status || row.dataset.orderStatus === status);
      row.hidden = !matches;
      if (matches) visible++;
    }
    document.getElementById('order-results').textContent = `${visible} de ${rows.length} pedidos visibles`;
    document.getElementById('order-no-results').hidden = visible !== 0 || rows.length === 0;
  };
  orderSearch?.addEventListener('input', filterOrders);
  orderStatus?.addEventListener('change', filterOrders);
  document.getElementById('order-clear')?.addEventListener('click', () => {
    orderSearch.value = '';
    orderStatus.value = '';
    filterOrders();
    orderSearch.focus();
  });
});
