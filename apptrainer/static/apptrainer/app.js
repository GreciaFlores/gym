/* AppTrainer: marcar ejercicios sin recargar + gráfica de peso (SVG, sin dependencias). */
(function () {
  'use strict';

  // --- Marcar ejercicios ---
  var progress = document.querySelector('[data-progress]');
  document.querySelectorAll('form[data-toggle]').forEach(function (form) {
    form.addEventListener('submit', function (ev) {
      if (!window.fetch) return; // sin fetch: envío normal del formulario
      ev.preventDefault();
      var card = form.closest('.ex');
      card.classList.toggle('is-done'); // respuesta inmediata
      fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'fetch' },
        credentials: 'same-origin',
      })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function (d) {
          card.classList.toggle('is-done', d.hecho);
          if (progress) {
            progress.querySelector('.bar > i').style.width = d.porcentaje + '%';
            progress.querySelector('[data-num]').textContent = d.hechos + '/' + d.total;
            var banner = document.querySelector('[data-done]');
            if (banner) banner.classList.toggle('show', d.completada);
          }
          var block = card.closest('.block');
          if (block) {
            var done = block.querySelectorAll('.ex.is-done').length;
            block.querySelector('[data-count]').textContent = done + '/' + block.querySelectorAll('.ex').length;
          }
        })
        .catch(function () { form.submit(); }); // si falla, que el servidor decida
    });
  });

  // --- Fecha de la sesión: cambiar la fecha recarga el día ---
  document.querySelectorAll('[data-autosubmit]').forEach(function (input) {
    input.addEventListener('change', function () { if (input.value) input.form.submit(); });
  });

  // --- Peso por ejercicio: total en vivo y marca automática ---
  var sinGuardar = false;
  function numero(texto) {
    var t = (texto || '').trim().replace(',', '.');
    return /^\d+(\.\d{1,2})?$/.test(t) ? parseFloat(t) : null;
  }
  function calcularTotal(bloque) {
    var modo = bloque.querySelector('input[type=radio]:checked');
    var v = function (campo) { var i = bloque.querySelector('[data-campo=' + campo + ']'); return i ? numero(i.value) : null; };
    modo = modo ? modo.value : 'total';
    if (modo === 'barra') {
      var b = v('barra');
      if (bloque.querySelector('[data-campo=lado]')) { var l = v('lado'); return (b === null && l === null) ? null : (b || 0) + 2 * (l || 0); }
      var d = v('discos'); return (b === null && d === null) ? null : (b || 0) + (d || 0);
    }
    if (modo === 'mancuernas') { var m = v('mancuerna'); return m === null ? null : m * 2; }
    return v('total');
  }
  function formato(n) { return (Math.round(n * 100) / 100).toString().replace('.', ','); }

  document.querySelectorAll('[data-carga]').forEach(function (bloque) {
    var salida = bloque.querySelector('[data-total]');
    function actualizar() {
      var total = calcularTotal(bloque);
      salida.textContent = total === null ? '—' : formato(total);
      return total;
    }
    bloque.addEventListener('input', function () { sinGuardar = true; actualizar(); });
    bloque.addEventListener('change', function () {
      sinGuardar = true;
      var total = actualizar();
      // Si anotas un peso válido, el ejercicio cuenta como hecho (sin pedirte otro toque).
      var card = bloque.closest('.ex');
      var toggle = card && card.querySelector('form[data-toggle]');
      if (total && toggle && !card.classList.contains('is-done')) {
        if (toggle.requestSubmit) toggle.requestSubmit();
        else toggle.dispatchEvent(new Event('submit', { cancelable: true }));
      }
    });
  });
  // --- Comentarios: contador y aviso de cambios sin guardar ---
  var comentario = document.querySelector('[data-comentario]');
  if (comentario) {
    var contador = document.querySelector('[data-contador]');
    comentario.addEventListener('input', function () { sinGuardar = true; contador.textContent = comentario.value.length; });
  }
  var guardar = document.querySelector('[data-save-form]');
  if (guardar) guardar.addEventListener('submit', function () { sinGuardar = false; });
  window.addEventListener('beforeunload', function (ev) {
    if (sinGuardar) { ev.preventDefault(); ev.returnValue = ''; }
  });

  // --- Gráfica de peso ---
  var host = document.getElementById('grafica');
  var raw = document.getElementById('datos-peso');
  if (!host || !raw) return;
  var datos = JSON.parse(raw.textContent);
  if (datos.length < 2) return;
  var tip = document.querySelector('.chart-tip');
  var NS = 'http://www.w3.org/2000/svg';

  function el(name, attrs, parent) {
    var n = document.createElementNS(NS, name);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  function fmtFecha(iso) {
    var p = iso.split('-');
    return p[2] + '/' + p[1];
  }
  function fmtKg(v) { return v.toFixed(1).replace('.', ','); }

  function dibujar() {
    var W = host.clientWidth, H = host.clientHeight;
    host.innerHTML = '';
    host.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    var m = { t: 12, r: 12, b: 26, l: 38 };
    var vals = datos.reduce(function (a, d) { return a.concat([d.kg, d.media]); }, []);
    var min = Math.floor(Math.min.apply(null, vals) - 1), max = Math.ceil(Math.max.apply(null, vals) + 1);
    var x = function (i) { return m.l + (W - m.l - m.r) * (i / (datos.length - 1)); };
    var y = function (v) { return m.t + (H - m.t - m.b) * (1 - (v - min) / (max - min)); };

    var defs = el('defs', {}, host);
    var g = el('linearGradient', { id: 'area', x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
    el('stop', { offset: '0%', 'stop-color': '#7c5cd6', 'stop-opacity': .28 }, g);
    el('stop', { offset: '100%', 'stop-color': '#7c5cd6', 'stop-opacity': 0 }, g);

    for (var i = 0; i <= 4; i++) {
      var v = min + (max - min) * i / 4;
      el('line', { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), stroke: '#e9e1fb', 'stroke-width': 1 }, host);
      var t = el('text', { x: m.l - 8, y: y(v) + 4, 'text-anchor': 'end' }, host);
      t.textContent = v.toFixed(0);
    }
    [0, datos.length - 1].forEach(function (i) {
      var t = el('text', { x: x(i), y: H - 6, 'text-anchor': i ? 'end' : 'start' }, host);
      t.textContent = fmtFecha(datos[i].fecha);
    });

    var linea = datos.map(function (d, i) { return (i ? 'L' : 'M') + x(i) + ',' + y(d.kg); }).join(' ');
    el('path', { d: linea + ' L' + x(datos.length - 1) + ',' + (H - m.b) + ' L' + x(0) + ',' + (H - m.b) + ' Z', fill: 'url(#area)' }, host);
    el('path', {
      d: datos.map(function (d, i) { return (i ? 'L' : 'M') + x(i) + ',' + y(d.media); }).join(' '),
      fill: 'none', stroke: '#f58fb5', 'stroke-width': 3, 'stroke-dasharray': '2 6', 'stroke-linecap': 'round', 'stroke-linejoin': 'round'
    }, host);
    el('path', { d: linea, fill: 'none', stroke: '#7c5cd6', 'stroke-width': 3.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, host);

    datos.forEach(function (d, i) {
      var c = el('circle', { cx: x(i), cy: y(d.kg), r: 5, fill: '#fff', stroke: '#7c5cd6', 'stroke-width': 3 }, host);
      var hit = el('circle', { cx: x(i), cy: y(d.kg), r: 18, fill: 'transparent', tabindex: 0 }, host);
      var show = function () {
        tip.textContent = fmtFecha(d.fecha) + ' · ' + fmtKg(d.kg) + ' kg';
        tip.style.left = x(i) + 'px';
        tip.style.top = y(d.kg) + 'px';
        tip.style.display = 'block';
        c.setAttribute('r', 7);
      };
      var hide = function () { tip.style.display = 'none'; c.setAttribute('r', 5); };
      hit.addEventListener('mouseenter', show);
      hit.addEventListener('focus', show);
      hit.addEventListener('click', show);
      hit.addEventListener('mouseleave', hide);
      hit.addEventListener('blur', hide);
    });
  }

  dibujar();
  var timer;
  window.addEventListener('resize', function () { clearTimeout(timer); timer = setTimeout(dibujar, 120); });
})();
