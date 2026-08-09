// compare.html — 자격증 비교 도구
function examPath(name) { return encodeURIComponent(name).replace(/%28/g,'(').replace(/%29/g,')'); }

(function () {
  const inputA = document.getElementById('pickA');
  const inputB = document.getElementById('pickB');
  const suggestA = document.getElementById('suggestA');
  const suggestB = document.getElementById('suggestB');
  const resultEl = document.getElementById('cmpResult');

  let allExams = [];
  let selected = { a: null, b: null };

  function isEmpty(n) { return n === null || n === undefined || n === ''; }
  function fmtNum(n) {
    return isEmpty(n) ? '-' : Number(n).toLocaleString('ko-KR');
  }
  function fmtWon(n) {
    return isEmpty(n) ? '-' : Number(n).toLocaleString('ko-KR') + '원';
  }
  function fmtRate(n) {
    return isEmpty(n) ? '-' : n + '%';
  }

  function setupPicker(input, suggestBox, slot) {
    input.addEventListener('input', function () {
      const q = input.value.trim().toLowerCase();
      if (!q) { suggestBox.classList.remove('open'); return; }
      const matches = allExams.filter(function (e) { return e.name.toLowerCase().indexOf(q) !== -1; }).slice(0, 8);
      if (!matches.length) { suggestBox.classList.remove('open'); return; }
      suggestBox.innerHTML = matches.map(function (e) {
        return '<div class="cmp-suggestion-item" data-jmcd="' + e.jmcd + '">' +
          '<span class="cmp-suggestion-name">' + e.name + '</span>' +
          '<span class="cmp-suggestion-meta">' + e.field + ' · ' + e.series + '</span></div>';
      }).join('');
      suggestBox.classList.add('open');
      Array.prototype.forEach.call(suggestBox.querySelectorAll('.cmp-suggestion-item'), function (item) {
        item.addEventListener('click', function () {
          const jmcd = item.dataset.jmcd;
          const exam = allExams.find(function (e) { return e.jmcd === jmcd; });
          selected[slot] = exam;
          input.value = exam.name;
          suggestBox.classList.remove('open');
          render();
        });
      });
    });
    document.addEventListener('click', function (e) {
      if (!suggestBox.contains(e.target) && e.target !== input) suggestBox.classList.remove('open');
    });
  }

  function betterClass(val, otherVal, higherIsBetter) {
    if (isEmpty(val) || isEmpty(otherVal) || val === otherVal) return '';
    const isBetter = higherIsBetter ? val > otherVal : val < otherVal;
    return isBetter ? ' class="cmp-win"' : '';
  }

  function render() {
    const a = selected.a, b = selected.b;
    if (!a || !b) {
      resultEl.innerHTML = '<div class="cmp-empty">비교할 자격증 두 개를 검색해서 선택해주세요.</div>';
      return;
    }

    function row(label, va, vb, fmt, cmpA, cmpB) {
      return '<tr><td>' + label + '</td>' +
        '<td' + (cmpA || '') + '>' + fmt(va) + '</td>' +
        '<td' + (cmpB || '') + '>' + fmt(vb) + '</td></tr>';
    }

    const feeWCmpA = betterClass(a.fee_written, b.fee_written, false);
    const feeWCmpB = betterClass(b.fee_written, a.fee_written, false);
    const feePCmpA = betterClass(a.fee_practical, b.fee_practical, false);
    const feePCmpB = betterClass(b.fee_practical, a.fee_practical, false);
    const wRateCmpA = betterClass(a.written_rate, b.written_rate, true);
    const wRateCmpB = betterClass(b.written_rate, a.written_rate, true);
    const pRateCmpA = betterClass(a.practical_rate, b.practical_rate, true);
    const pRateCmpB = betterClass(b.practical_rate, a.practical_rate, true);
    const rankCmpA = betterClass(a.field_rank, b.field_rank, false);
    const rankCmpB = betterClass(b.field_rank, a.field_rank, false);

    resultEl.innerHTML =
      '<div class="table-wrap">' +
      '<table class="cmp-table">' +
      '<thead><tr><th></th><th class="cmp-name-cell">' + a.name + '</th><th class="cmp-name-cell">' + b.name + '</th></tr></thead>' +
      '<tbody>' +
      row('직무분야', a.field, b.field, function (v) { return v || '-'; }) +
      row('등급', a.series, b.series, function (v) { return v || '-'; }) +
      row('필기 수수료', a.fee_written, b.fee_written, fmtWon, feeWCmpA, feeWCmpB) +
      row('실기 수수료', a.fee_practical, b.fee_practical, fmtWon, feePCmpA, feePCmpB) +
      row('필기 합격률', a.written_rate, b.written_rate, fmtRate, wRateCmpA, wRateCmpB) +
      row('실기 합격률', a.practical_rate, b.practical_rate, fmtRate, pRateCmpA, pRateCmpB) +
      row('난이도', a.difficulty_label, b.difficulty_label, function (v) { return v || '-'; }) +
      row('최근 응시자수', a.recent_applicants, b.recent_applicants, fmtNum) +
      row('최근 합격자수', a.recent_passers, b.recent_passers, fmtNum) +
      row('분야 내 순위', a.field_rank ? (a.field_rank + '위 / ' + a.field_total + '종') : '-', b.field_rank ? (b.field_rank + '위 / ' + b.field_total + '종') : '-', function (v) { return v; }, rankCmpA, rankCmpB) +
      '</tbody></table></div>' +
      '<div style="display:flex;gap:12px;margin-top:16px;flex-wrap:wrap;">' +
      '<a href="' + a.url + '" class="filter-btn">📄 ' + a.name + ' 상세보기</a>' +
      '<a href="' + b.url + '" class="filter-btn">📄 ' + b.name + ' 상세보기</a>' +
      '</div>';
  }

  setupPicker(inputA, suggestA, 'a');
  setupPicker(inputB, suggestB, 'b');

  fetch('/data/exams-compare.json')
    .then(function (r) { return r.json(); })
    .then(function (data) {
      allExams = data.items || [];
      const params = new URLSearchParams(location.search);
      const aJmcd = params.get('a');
      const bJmcd = params.get('b');
      if (aJmcd) {
        const exam = allExams.find(function (e) { return e.jmcd === aJmcd; });
        if (exam) { selected.a = exam; inputA.value = exam.name; }
      }
      if (bJmcd) {
        const exam = allExams.find(function (e) { return e.jmcd === bJmcd; });
        if (exam) { selected.b = exam; inputB.value = exam.name; }
      }
      render();
    })
    .catch(function () {
      resultEl.innerHTML = '<div class="cmp-empty">비교 데이터를 불러오지 못했습니다.</div>';
    });
})();
