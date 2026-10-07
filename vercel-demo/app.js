const data = {
  summary: { clientes: 50, pedidos: 101, faturamento: 12430, ticket: 123.07, acessos: 10000, erros: 884 },
  sales: [645.8,225.2,704,732.1,260.3,390.2,134.5,359.4,690.4,165.5,664.4,137.5,487.5,283.7,655.8,742,696.4,341.1,278.9,266.2,212.2,779.2,743.1,27,164.4,223.1,479,433.2,292.6,169.5],
  cities: [{name:'Recife',value:4080},{name:'Olinda',value:2954},{name:'Paulista',value:1776},{name:'Jaboatão',value:1190}],
  pages: [{name:'/promocoes',value:1483},{name:'/pedido',value:1443},{name:'/',value:1434},{name:'/produtos',value:1423},{name:'/cardapio',value:1410},{name:'/carrinho',value:1410},{name:'/checkout',value:1397}],
  statuses: [{name:'200',value:8185,color:'#7ed957'},{name:'201',value:523,color:'#28c8d7'},{name:'304',value:408,color:'#8a7dff'},{name:'400–500',value:884,color:'#ff6b35'}],
  products: [
    ['X-Burguer','Hambúrguer',22.90,555],['X-Bacon','Hambúrguer',27.90,563],['X-Salada','Hambúrguer',24.90,557],
    ['Batata Frita','Acompanhamento',14.90,548],['Refrigerante','Bebida',7,537],['Suco','Bebida',9,553],
    ['Combo Individual','Combo',39.90,532],['Combo Família','Combo',89.90,545]
  ]
};

const money = value => value.toLocaleString('pt-BR', {style:'currency', currency:'BRL'});
const number = value => value.toLocaleString('pt-BR');

const kpis = [
  ['Clientes', number(data.summary.clientes), 'base operacional', '↗'],
  ['Pedidos', number(data.summary.pedidos), 'transações concluídas', '↗'],
  ['Faturamento', money(data.summary.faturamento), 'calculado no servidor', '↗'],
  ['Ticket médio', money(data.summary.ticket), 'por pedido', '↗'],
  ['Acessos', number(data.summary.acessos), 'logs processados', '↗'],
  ['Erros HTTP', number(data.summary.erros), '8,84% do tráfego', '↘']
];
document.querySelector('#kpis').innerHTML = kpis.map(([label,value,note,trend],i) => `
  <article class="kpi ${i===2?'accent':''}"><div><small>${label}</small><span>${trend}</span></div><strong>${value}</strong><p>${note}</p></article>`).join('');

const maxSale = Math.max(...data.sales);
const points = data.sales.map((v,i) => `${(i/(data.sales.length-1))*100},${94-(v/maxSale)*78}`).join(' ');
const area = `0,100 ${points} 100,100`;
document.querySelector('#salesChart').innerHTML = `<svg viewBox="0 0 100 100" preserveAspectRatio="none" role="img"><defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff6b35" stop-opacity=".42"/><stop offset="1" stop-color="#ff6b35" stop-opacity="0"/></linearGradient></defs><polygon points="${area}" fill="url(#fill)"/><polyline points="${points}" fill="none" stroke="#ff6b35" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>`;

const maxCity = Math.max(...data.cities.map(item=>item.value));
document.querySelector('#cityChart').innerHTML = data.cities.map((item,i)=>`
  <div class="bar-row"><div><span>${String(i+1).padStart(2,'0')}</span><b>${item.name}</b><strong>${number(item.value)}</strong></div><div class="bar-track"><i style="width:${item.value/maxCity*100}%"></i></div></div>`).join('');

const maxPage = Math.max(...data.pages.map(item=>item.value));
document.querySelector('#pageChart').innerHTML = data.pages.map(item=>`
  <div class="hbar"><span>${item.name}</span><div><i style="width:${item.value/maxPage*100}%"></i></div><b>${number(item.value)}</b></div>`).join('');

document.querySelector('#statusLegend').innerHTML = data.statuses.map(item=>`
  <div><i style="background:${item.color}"></i><span>HTTP ${item.name}</span><strong>${number(item.value)}</strong></div>`).join('');

document.querySelector('#productRows').innerHTML = data.products.map(([name,category,price,stock])=>`
  <tr><td><b>${name}</b></td><td>${category}</td><td>${money(price)}</td><td><span class="stock">${stock} un.</span></td><td><span class="active">Ativo</span></td></tr>`).join('');

const observer = new IntersectionObserver(entries => entries.forEach(entry => {
  if(entry.isIntersecting) entry.target.classList.add('visible');
}), {threshold:.12});
document.querySelectorAll('.panel,.challenge,.arch-node,.kpi,.evidence-grid>div').forEach(el=>observer.observe(el));

document.querySelectorAll('a[href^="#"]').forEach(anchor => anchor.addEventListener('click', event => {
  const target = document.querySelector(anchor.getAttribute('href'));
  if(target){ event.preventDefault(); target.scrollIntoView({behavior:'smooth'}); }
}));
