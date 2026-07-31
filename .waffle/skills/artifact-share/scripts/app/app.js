(function () {
  'use strict';

  /* この画面が知っている外部は2つだけ。利用者プールと、管理の受け口。
     どちらの居場所も config.json から受け取る（環境ごとに変わるため、
     画面の中に焼き込まない）。 */
  var CONFIG = null;
  var $ = function (id) { return document.getElementById(id); };

  /* ── 覚えておくもの ──────────────────────────────────
     入り直すための券だけを残す。誰であるかを示す証明は短命なので、
     画面を開き直すたびに取り直す。 */
  var KEY = 'artifactshare.refresh';
  var session = { id: null, name: '', admin: false, refresh: null };

  function remember(tokens) {
    session.id = tokens.IdToken;
    if (tokens.RefreshToken) {
      session.refresh = tokens.RefreshToken;
      try { localStorage.setItem(KEY, tokens.RefreshToken); } catch (e) { /* 使えなくても続く */ }
    }
    var claims = readClaims(tokens.IdToken);
    session.name = claims['cognito:username'] || claims.email || '';
    session.admin = (claims['cognito:groups'] || []).indexOf('administrators') >= 0;
  }

  function forget() {
    session = { id: null, name: '', admin: false, refresh: null };
    try { localStorage.removeItem(KEY); } catch (e) { /* 同上 */ }
  }

  function readClaims(token) {
    try {
      var part = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      var bin = atob(part + '==='.slice((part.length + 3) % 4));
      var bytes = new Uint8Array(bin.length);
      for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      return JSON.parse(new TextDecoder('utf-8').decode(bytes));
    } catch (e) { return {}; }
  }

  /* ── 利用者プールとのやり取り ────────────────────────
     合言葉はここを通ってそのまま利用者プールへ渡る。この画面は覚えない。 */
  function cognito(action, body) {
    return fetch('https://cognito-idp.' + CONFIG.region + '.amazonaws.com/', {
      method: 'POST',
      headers: {
        'content-type': 'application/x-amz-json-1.1',
        'x-amz-target': 'AWSCognitoIdentityProviderService.' + action
      },
      body: JSON.stringify(body)
    }).then(function (r) {
      return r.json().then(function (d) {
        if (!r.ok) throw Object.assign(new Error(d.message || 'failed'), { kind: d.__type || '' });
        return d;
      });
    });
  }

  function signIn(mail, pass) {
    return cognito('InitiateAuth', {
      AuthFlow: 'USER_PASSWORD_AUTH',
      ClientId: CONFIG.clientId,
      AuthParameters: { USERNAME: mail, PASSWORD: pass }
    });
  }

  function answerNewPassword(mail, password, sessionToken) {
    return cognito('RespondToAuthChallenge', {
      ChallengeName: 'NEW_PASSWORD_REQUIRED',
      ClientId: CONFIG.clientId,
      Session: sessionToken,
      ChallengeResponses: { USERNAME: mail, NEW_PASSWORD: password }
    });
  }

  function refresh() {
    if (!session.refresh) return Promise.reject(new Error('no refresh'));
    return cognito('InitiateAuth', {
      AuthFlow: 'REFRESH_TOKEN_AUTH',
      ClientId: CONFIG.clientId,
      AuthParameters: { REFRESH_TOKEN: session.refresh }
    }).then(function (d) { remember(d.AuthenticationResult); });
  }

  /* ── 受け口とのやり取り ──────────────────────────────
     証明が古くなっていたら一度だけ取り直して、同じ要求をやり直す。
     入力の途中で締め出されないようにするため。 */
  function api(action, body, retried) {
    return fetch(CONFIG.apiUrl, {
      method: 'POST',
      headers: { 'content-type': 'application/json', authorization: 'Bearer ' + session.id },
      body: JSON.stringify(Object.assign({ action: action }, body || {}))
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (d) {
        if (r.status === 403 && d.error === 'NOT_INVITED' && !retried && session.refresh) {
          return refresh().then(function () { return api(action, body, true); },
                               function () { signedOut(); throw new Error('signed out'); });
        }
        if (!r.ok) throw Object.assign(new Error(d.message || '失敗しました'), { code: d.error || '' });
        return d;
      });
    });
  }

  /* ── 画面の出し入れ ──────────────────────────────── */
  function view(id) {
    document.querySelectorAll('.view').forEach(function (v) { v.classList.remove('on'); });
    $(id).classList.add('on');
    window.scrollTo(0, 0);
  }

  function openDlg(id) { var d = $(id); if (d.showModal) d.showModal(); }
  function chip(cls, text) { var e = document.createElement('span'); e.className = cls; e.textContent = text; return e; }
  function fmtSize(n) { return n < 1024 ? n + ' B' : (n / 1024).toFixed(1) + ' KB'; }

  var toastTimer = null;
  function toast(msg) {
    $('toast-text').textContent = msg;
    $('toast').classList.add('on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { $('toast').classList.remove('on'); }, 2600);
  }

  function fail(e) {
    toast(e && e.message ? e.message : '失敗しました');
  }

  /* ── ログイン ──────────────────────────────────── */
  var pendingSession = null, pendingMail = '';

  function gateForm(id) {
    ['loginform', 'newpassform', 'forgotform', 'resetform'].forEach(function (f) {
      $(f).hidden = f !== id;
    });
  }

  function showGate(message) {
    $('gate').hidden = false;
    gateForm('loginform');
    $('g-err').hidden = !message;
    if (message) $('g-err').textContent = message;
    $('g-pass').value = '';
    setTimeout(function () { $('g-mail').focus(); }, 40);
  }

  function signedOut() {
    forget();
    showGate('入り直してください。');
  }

  function entered() {
    $('gate').hidden = true;
    document.body.classList.toggle('is-admin', session.admin);
    var who = document.querySelector('.whoami');
    who.textContent = '';
    var av = document.createElement('span');
    av.className = 'avatar';
    av.textContent = (session.name || '?').slice(0, 2).toUpperCase();
    var out = document.createElement('button');
    out.type = 'button'; out.className = 'signout'; out.textContent = 'ログアウト';
    out.addEventListener('click', function () { forget(); showGate(''); });
    who.append(av, document.createTextNode(session.name), out);
    load();
  }

  $('loginform').addEventListener('submit', function (e) {
    e.preventDefault();
    var mail = $('g-mail').value.trim(), pass = $('g-pass').value;
    if (!mail || !pass) return;
    $('g-go').disabled = true;
    $('g-err').hidden = true;

    signIn(mail, pass).then(function (d) {
      if (d.ChallengeName === 'NEW_PASSWORD_REQUIRED') {
        pendingSession = d.Session; pendingMail = mail;
        gateForm('newpassform');
        setTimeout(function () { $('g-new').focus(); }, 40);
        return;
      }
      remember(d.AuthenticationResult);
      entered();
    }).catch(function () {
      // 合っていない理由を分けて伝えない。誰が招かれているかを探らせないため
      $('g-err').textContent = 'メールアドレスかパスワードが違います。';
      $('g-err').hidden = false;
    }).then(function () { $('g-go').disabled = false; });
  });

  $('newpassform').addEventListener('submit', function (e) {
    e.preventDefault();
    var a = $('g-new').value, b = $('g-new2').value;
    var err = $('g-newerr');
    if (a !== b) { err.textContent = '2つの入力が一致しません。'; err.hidden = false; return; }
    var bad = badPassword(a);
    if (bad) { err.textContent = bad; err.hidden = false; return; }

    $('g-newgo').disabled = true; err.hidden = true;
    answerNewPassword(pendingMail, a, pendingSession).then(function (d) {
      remember(d.AuthenticationResult);
      entered();
    }).catch(function (x) {
      err.textContent = x.message || 'この内容では決められません。';
      err.hidden = false;
    }).then(function () { $('g-newgo').disabled = false; });
  });

  /* ── 合言葉を忘れたとき ────────────────────────────
     招待に応じていない人はこの経路を使えない（利用者プールが拒む）。
     仮の合言葉を無くした人は、管理者に招き直してもらう。 */
  function badPassword(value) {
    if (value.length < 12) return '12文字以上にしてください。';
    if (!/[A-Z]/.test(value) || !/[a-z]/.test(value) || !/[0-9]/.test(value)) {
      return '大文字・小文字・数字をそれぞれ含めてください。';
    }
    return '';
  }

  $('g-forgot').addEventListener('click', function () {
    $('g-fmail').value = $('g-mail').value.trim();
    gateForm('forgotform');
    setTimeout(function () { $('g-fmail').focus(); }, 40);
  });

  document.querySelectorAll('.gate [data-back]').forEach(function (b) {
    b.addEventListener('click', function () { showGate(''); });
  });

  $('forgotform').addEventListener('submit', function (e) {
    e.preventDefault();
    var mail = $('g-fmail').value.trim();
    if (!mail) return;
    $('g-fgo').disabled = true;
    $('g-ferr').hidden = true;

    cognito('ForgotPassword', { ClientId: CONFIG.clientId, Username: mail })
      .catch(function () { /* 送れたかどうかを伝えない（下記） */ })
      .then(function () {
        // 招かれていない宛先でも同じ画面へ進む。送れたかどうかの違いから、
        // 誰が招かれているかを外から探れないようにするため
        pendingMail = mail;
        $('g-rlede').textContent = mail + ' 宛にコードを送りました。届いていない場合は、'
          + '迷惑メールに入っていないかを確かめてください。';
        gateForm('resetform');
        setTimeout(function () { $('g-code').focus(); }, 40);
        $('g-fgo').disabled = false;
      });
  });

  $('resetform').addEventListener('submit', function (e) {
    e.preventDefault();
    var code = $('g-code').value.trim(), pass = $('g-rnew').value;
    var err = $('g-rerr');
    var bad = badPassword(pass);
    if (!code) { $('g-code').focus(); return; }
    if (bad) { err.textContent = bad; err.hidden = false; return; }

    $('g-rgo').disabled = true; err.hidden = true;
    cognito('ConfirmForgotPassword', {
      ClientId: CONFIG.clientId, Username: pendingMail,
      ConfirmationCode: code, Password: pass
    }).then(function () {
      showGate('');
      $('g-mail').value = pendingMail;
      toast('パスワードを決めました。ログインしてください');
    }).catch(function (x) {
      err.textContent = /CodeMismatch|ExpiredCode/.test(x.kind || '')
        ? 'コードが違うか、期限が切れています。もう一度送ってください。'
        : (x.message || '決められませんでした。');
      err.hidden = false;
    }).then(function () { $('g-rgo').disabled = false; });
  });

  /* ── 一覧 ──────────────────────────────────────── */
  var ITEMS = [];

  function load() {
    var list = $('list');
    list.textContent = '';
    var busy = document.createElement('div');
    busy.className = 'busy'; busy.textContent = '読み込んでいます…';
    list.appendChild(busy);

    api('list').then(function (d) {
      ITEMS = d.artifacts || [];
      render();
      if (session.admin) loadMembers();
    }).catch(function (e) {
      list.textContent = '';
      var box = document.createElement('div'); box.className = 'failed';
      var p = document.createElement('p'); p.textContent = '一覧を読み込めませんでした。' + (e.message || '');
      var again = document.createElement('button');
      again.className = 'btn'; again.type = 'button'; again.textContent = 'もう一度';
      again.addEventListener('click', load);
      box.append(p, again); list.appendChild(box);
    });
  }

  function menuFor(item) {
    var wrap = document.createElement('div'); wrap.className = 'menu';
    var btn = document.createElement('button');
    btn.className = 'rowbtn'; btn.type = 'button'; btn.textContent = '⋯';
    btn.setAttribute('aria-label', item.name + ' の操作');
    btn.setAttribute('aria-expanded', 'false');
    var ul = document.createElement('ul'); ul.hidden = true;

    var mine = item.uploadedBy === session.name || !item.uploadedBy;
    var entries = [['開く']];
    // 中身を差し替えられるのは公開した本人だけ。管理者にも出さない
    if (mine && item.status === 'active') entries.push(['差し替えてアップロード']);
    if (item.status === 'active') entries.push(['トークンを再発行']);
    entries.push(['エクスポート']);
    if (session.admin) entries.push(['sep'], ['引き継ぐ']);
    entries.push(['sep'], item.status === 'active' ? ['無効化する', 'danger'] : ['再公開する']);

    entries.forEach(function (it) {
      var li = document.createElement('li');
      if (it[0] === 'sep') { li.className = 'sep'; }
      else {
        var b = document.createElement('button'); b.type = 'button'; b.textContent = it[0];
        if (it[1]) b.className = it[1];
        b.addEventListener('click', function (e) {
          e.stopPropagation();
          ul.hidden = true; btn.setAttribute('aria-expanded', 'false');
          act(it[0], item);
        });
        li.appendChild(b);
      }
      ul.appendChild(li);
    });

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = ul.hidden;
      document.querySelectorAll('.menu ul').forEach(function (u) { u.hidden = true; });
      document.querySelectorAll('.menu .rowbtn').forEach(function (b) { b.setAttribute('aria-expanded', 'false'); });
      ul.hidden = !open; btn.setAttribute('aria-expanded', String(open));
      if (open) {
        ul.classList.remove('up');
        var r = btn.getBoundingClientRect();
        if (window.innerHeight - r.bottom < ul.offsetHeight + 14) ul.classList.add('up');
      }
    });
    wrap.append(btn, ul);
    return wrap;
  }

  function viewerUrl(id) { return 'https://' + CONFIG.viewerDomain + '/p/' + id + '/'; }

  function copyText(text, done) {
    if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, done);
    else done();
  }

  function copyIcon() {
    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 16 16'); svg.setAttribute('aria-hidden', 'true');
    var r = document.createElementNS(ns, 'rect');
    r.setAttribute('x', '5.5'); r.setAttribute('y', '5.5');
    r.setAttribute('width', '8'); r.setAttribute('height', '8'); r.setAttribute('rx', '1.6');
    var path = document.createElementNS(ns, 'path');
    path.setAttribute('d', 'M10.5 5.5V3.6A1.1 1.1 0 0 0 9.4 2.5H3.6A1.1 1.1 0 0 0 2.5 3.6v5.8'
                         + 'a1.1 1.1 0 0 0 1.1 1.1h1.9');
    svg.append(r, path);
    return svg;
  }

  function render() {
    var q = $('q').value.trim().toLowerCase();
    var rows = ITEMS.filter(function (d) {
      if (!q) return true;
      var hay = (d.name + ' ' + (d.tags || []).join(' ') + ' ' + (d.docType || '')
                 + ' ' + (d.uploadedBy || '')).toLowerCase();
      return hay.indexOf(q) >= 0;
    });

    var list = $('list'); list.textContent = '';
    $('count').textContent = rows.length + ' 件';

    if (!rows.length) {
      var e = document.createElement('div'); e.className = 'empty';
      var p = document.createElement('p');
      p.textContent = ITEMS.length
        ? '条件に合うアーティファクトはありません。'
        : 'まだ何も公開していません。HTMLをドロップすると公開できます。';
      e.appendChild(p); list.appendChild(e);
      return;
    }

    rows.forEach(function (d) {
      var active = d.status === 'active';
      var row = document.createElement('div');
      row.className = 'row' + (active ? '' : ' off');

      var main = document.createElement('div'); main.className = 'main';
      var t = document.createElement('p'); t.className = 'title'; t.textContent = d.name;
      var sub = document.createElement('div'); sub.className = 'sub';
      // 管理者は全員のものを見るため、誰が公開したかが要る
      if (session.admin) sub.appendChild(chip('', d.uploadedBy === session.name ? '自分' : d.uploadedBy));
      sub.appendChild(d.docType ? chip('dtype', d.docType) : chip('dtype none', '種別なし'));
      (d.projects || []).forEach(function (p) { sub.appendChild(chip('proj', p)); });
      (d.tags || []).forEach(function (g) { sub.appendChild(chip('tag', g)); });
      sub.appendChild(chip('', fmtDate(d.updatedAt) + ' 更新'));
      main.append(t, sub);

      var c = document.createElement('button');
      c.type = 'button'; c.className = 'comments';
      var n = document.createElement('span');
      var count = d.comments || 0;
      n.className = 'cnum' + (count ? '' : ' zero');
      n.textContent = count ? count + '件' : '—';
      var w = document.createElement('span'); w.className = 'cwhen';
      w.textContent = count ? '' : 'コメントなし';
      c.append(n, w);
      c.disabled = true;   // コメントの読み出しは閲覧の面が持つ

      var end = document.createElement('div'); end.className = 'rowend';
      end.appendChild(active ? chip('status on', '公開中') : chip('status no', '無効化済み'));

      if (active) {
        var cp = document.createElement('button');
        cp.type = 'button'; cp.className = 'iconbtn';
        cp.title = 'URLをコピー'; cp.setAttribute('aria-label', d.name + ' のURLをコピー');
        cp.appendChild(copyIcon());
        cp.addEventListener('click', function (e) {
          e.stopPropagation();
          copyText(viewerUrl(d.artifactId), function () {
            toast('URLをコピーしました');
            cp.classList.add('ok');
            setTimeout(function () { cp.classList.remove('ok'); }, 1600);
          });
        });
        end.appendChild(cp);
      }
      end.appendChild(menuFor(d));

      row.append(main, c, end);
      list.appendChild(row);
    });
  }

  function fmtDate(epoch) {
    if (!epoch) return '—';
    var d = new Date(epoch * 1000);
    return (d.getMonth() + 1) + '/' + d.getDate();
  }

  /* ── 行の操作 ────────────────────────────────────── */
  var target = null;

  function act(label, item) {
    target = item;
    if (label === '開く') { window.open(viewerUrl(item.artifactId), '_blank'); return; }
    if (label === 'エクスポート') { $('exp-target').textContent = item.name; openDlg('dlg-export'); return; }
    if (label === '差し替えてアップロード') { $('rep-target').textContent = item.name; openDlg('dlg-replace'); return; }
    if (label === '引き継ぐ') return openTransfer(item);

    if (label === 'トークンを再発行') {
      $('rot-target').textContent = item.name;
      $('rot-1').classList.add('on'); $('rot-2').classList.remove('on');
      openDlg('dlg-rotate');
      return;
    }
    if (label === '無効化する') { $('dis-target').textContent = item.name; openDlg('dlg-disable'); return; }
    if (label === '再公開する') {
      $('rep2-target').textContent = item.name;
      $('rep2-1').classList.add('on'); $('rep2-2').classList.remove('on');
      openDlg('dlg-republish');
      return;
    }
  }

  $('rot-go').addEventListener('click', function (e) {
    e.preventDefault();
    api('rotate', { artifactId: target.artifactId }).then(function (d) {
      $('rot-target2').textContent = target.name;
      $('rot-token').textContent = d.token;
      $('rot-1').classList.remove('on'); $('rot-2').classList.add('on');
    }).catch(fail);
  });

  $('rep2-go').addEventListener('click', function (e) {
    e.preventDefault();
    api('enable', { artifactId: target.artifactId }).then(function (d) {
      $('rep2-target2').textContent = target.name;
      $('rep2-token').textContent = d.token;
      $('rep2-1').classList.remove('on'); $('rep2-2').classList.add('on');
      load();
    }).catch(fail);
  });

  document.querySelectorAll('#dlg-disable [value="ok"], #dlg-disable .btn.danger-b')
    .forEach(function (b) {
      b.addEventListener('click', function () {
        api('disable', { artifactId: target.artifactId })
          .then(function () { toast('公開を止めました。中身もコメントも残っています'); load(); })
          .catch(fail);
      });
    });

  /* ── 公開 ────────────────────────────────────────── */
  var picked = null;

  function inspect(text) {
    var doc = new DOMParser().parseFromString(text, 'text/html');
    var meta = function (name) {
      var m = doc.querySelector('meta[name="' + name + '"]');
      return m ? (m.getAttribute('content') || '').trim() : '';
    };
    var external = 0;
    doc.querySelectorAll('script[src], img[src], link[rel~="stylesheet"][href]')
      .forEach(function (el) {
        var url = el.getAttribute('src') || el.getAttribute('href') || '';
        if (/^(https?:)?\/\//i.test(url.trim())) external++;
      });
    var tags = meta('tags').split(',').map(function (s) { return s.trim(); }).filter(Boolean);
    var title = meta('title') || (doc.querySelector('title') || {}).textContent || '';
    return {
      documentId: meta('id'), docType: meta('type'), title: title.trim(),
      description: meta('description'), tags: tags, externalRefs: external,
      detected: !!(meta('id') && meta('type'))
    };
  }

  function row(dl, k, v) {
    var dt = document.createElement('dt'); dt.textContent = k;
    var dd = document.createElement('dd'); dd.textContent = v;
    dl.append(dt, dd);
  }

  function toConfirm(file, text) {
    picked = { file: file, text: text, found: inspect(text) };
    var f = picked.found;

    $('c-fname').textContent = file.name;
    $('c-fsize').textContent = fmtSize(file.size);
    $('confirm-lede').textContent = f.detected
      ? 'このHTMLから情報を読み取りました。このまま公開できます。'
      : '識別のための情報が見つかりませんでした。表示名だけ入力してください。';

    $('c-extwarn').hidden = !f.externalRefs;
    if (f.externalRefs) {
      $('c-extwarn-text').textContent =
        '外部を' + f.externalRefs + '件参照しています。閲覧者の環境では読み込まれず、見た目が崩れます。';
    }

    $('c-readout').hidden = !f.detected;
    $('c-manual').hidden = f.detected;
    if (f.detected) {
      var dl = $('c-kv'); dl.textContent = '';
      row(dl, '表示名', f.title);
      if (f.documentId) row(dl, '識別子', f.documentId);
      if (f.docType) row(dl, '種別', f.docType);
      if (f.description) row(dl, '要約', f.description);
      if (f.tags.length) row(dl, '分類の目印', f.tags.join('、'));
    } else {
      $('c-name').value = f.title || '';
    }
    view('v-confirm');
  }

  function handle(file) {
    if (!file) return;
    if (!/\.html?$/i.test(file.name)) { toast('HTMLファイルを選んでください'); return; }
    file.text().then(function (text) { toConfirm(file, text); });
  }

  $('publish').addEventListener('click', function () {
    var name = $('c-manual').hidden ? '' : $('c-name').value.trim();
    if (!$('c-manual').hidden && !name) { $('c-name').focus(); return; }

    $('publish').disabled = true;
    api('publish', { html: picked.text, displayName: name }).then(function (d) {
      $('done-name').textContent = d.descriptor.title;
      $('d-url').textContent = d.url;
      $('d-token').textContent = d.token;
      $('d-belongs').textContent = d.externalRefs
        ? '外部を' + d.externalRefs + '件参照しています。閲覧者の環境では読み込まれません。' : '';
      view('v-done');
      load();
    }).catch(fail).then(function () { $('publish').disabled = false; });
  });

  var dz = $('dz');
  ['dragenter', 'dragover'].forEach(function (t) {
    dz.addEventListener(t, function (e) { e.preventDefault(); dz.classList.add('hot'); });
  });
  ['dragleave', 'drop'].forEach(function (t) {
    dz.addEventListener(t, function (e) { e.preventDefault(); dz.classList.remove('hot'); });
  });
  dz.addEventListener('drop', function (e) { handle(e.dataTransfer.files[0]); });
  $('pick').addEventListener('click', function () { $('fileinput').click(); });
  $('fileinput').addEventListener('change', function () { handle(this.files[0]); });
  $('cancel').addEventListener('click', function () { picked = null; view('v-home'); });
  $('back').addEventListener('click', function () { view('v-home'); });

  /* 差し替え。共有URLもトークンもコメントも保たれる */
  var rdz = $('repdz');
  if (rdz) {
    ['dragenter', 'dragover'].forEach(function (t) {
      rdz.addEventListener(t, function (e) { e.preventDefault(); rdz.classList.add('hot'); });
    });
    ['dragleave', 'drop'].forEach(function (t) {
      rdz.addEventListener(t, function (e) { e.preventDefault(); rdz.classList.remove('hot'); });
    });
    rdz.addEventListener('drop', function (e) { replaceWith(e.dataTransfer.files[0]); });
  }
  if ($('rep-pick')) $('rep-pick').addEventListener('click', function () { $('rep-file').click(); });
  if ($('rep-file')) $('rep-file').addEventListener('change', function () { replaceWith(this.files[0]); });

  function replaceWith(file) {
    if (!file) return;
    file.text().then(function (text) {
      return api('replace', { artifactId: target.artifactId, html: text });
    }).then(function () {
      $('dlg-replace').close();
      toast('中身を入れ替えました。URLもトークンもコメントもそのままです');
      load();
    }).catch(fail);
  }

  document.querySelectorAll('[data-copy]').forEach(function (b) {
    b.addEventListener('click', function () {
      copyText($(b.dataset.copy).textContent, function () { toast('コピーしました'); });
    });
  });

  /* ── メンバー（管理者だけ） ───────────────────────── */
  var PEOPLE = [];

  function loadMembers() {
    api('publishers').then(function (d) {
      PEOPLE = d.publishers || [];
      renderMembers();
    }).catch(function () { /* 一覧が主目的なので、ここは黙って諦める */ });
  }

  function renderMembers() {
    var list = $('mlist');
    if (!list) return;
    list.textContent = '';
    $('mcount').textContent = PEOPLE.length + ' 人';

    PEOPLE.forEach(function (p) {
      var row = document.createElement('div'); row.className = 'mrow';
      var main = document.createElement('div');
      var name = document.createElement('p'); name.className = 'mname';
      name.textContent = p.name + (p.id === session.name ? '（自分）' : '');
      var mail = document.createElement('span'); mail.className = 'mmail'; mail.textContent = p.email || '';
      main.append(name, mail);

      var count = document.createElement('div'); count.className = 'mcount';
      var b = document.createElement('b'); b.textContent = owned(p.id);
      count.append(b, document.createTextNode('件を公開'));

      var end = document.createElement('div'); end.className = 'rowend';
      var chipEl = document.createElement('span');
      if (p.status === 'invited') { chipEl.className = 'rolechip pending'; chipEl.textContent = '招待中'; }
      else if (p.admin) { chipEl.className = 'rolechip admin'; chipEl.textContent = '管理者'; }
      else { chipEl.className = 'rolechip member'; chipEl.textContent = '投稿者'; }
      end.appendChild(chipEl);
      if (p.id !== session.name) end.appendChild(memberMenu(p));

      row.append(main, count, end);
      list.appendChild(row);
    });
  }

  function owned(id) {
    return ITEMS.filter(function (d) { return d.uploadedBy === id; }).length;
  }

  function memberMenu(p) {
    var wrap = document.createElement('div'); wrap.className = 'menu';
    var btn = document.createElement('button');
    btn.className = 'rowbtn'; btn.type = 'button'; btn.textContent = '⋯';
    btn.setAttribute('aria-label', p.name + ' の操作');
    btn.setAttribute('aria-expanded', 'false');
    var ul = document.createElement('ul'); ul.hidden = true;

    if (p.status === 'invited') {
      var rl = document.createElement('li');
      var rb = document.createElement('button');
      rb.type = 'button'; rb.textContent = '招待をもう一度送る';
      rb.addEventListener('click', function (e) {
        e.stopPropagation(); ul.hidden = true;
        api('resend-invite', { publisherId: p.id })
          .then(function () { toast(p.email + ' へ招待を送り直しました'); })
          .catch(fail);
      });
      rl.appendChild(rb); ul.appendChild(rl);
      var sep = document.createElement('li'); sep.className = 'sep'; ul.appendChild(sep);
    }

    var li = document.createElement('li');
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'danger'; b.textContent = 'メンバーから外す';
    b.addEventListener('click', function (e) {
      e.stopPropagation(); ul.hidden = true; openRemove(p);
    });
    li.appendChild(b); ul.appendChild(li);

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = ul.hidden;
      document.querySelectorAll('.menu ul').forEach(function (u) { u.hidden = true; });
      ul.hidden = !open; btn.setAttribute('aria-expanded', String(open));
    });
    wrap.append(btn, ul);
    return wrap;
  }

  function fillPicker(select, exclude) {
    select.textContent = '';
    PEOPLE.filter(function (p) { return p.id !== exclude && p.status !== 'invited'; })
      .forEach(function (p) {
        var o = document.createElement('option');
        o.value = p.id; o.textContent = p.name + (p.email ? '（' + p.email + '）' : '');
        select.appendChild(o);
      });
  }

  var transferring = null;
  function openTransfer(item) {
    transferring = item;
    $('tr-lede').textContent =
      '「' + item.name + '」を手入れできる人を、' + (item.uploadedBy || '') + ' から移します。';
    fillPicker($('tr-to'), item.uploadedBy);
    openDlg('dlg-transfer');
  }

  $('tr-go').addEventListener('click', function () {
    api('transfer', { artifactId: transferring.artifactId, toPublisher: $('tr-to').value })
      .then(function (d) { toast(d.to + ' へ引き継ぎました'); load(); })
      .catch(fail);
  });

  if ($('invite-open')) {
    $('invite-open').addEventListener('click', function () {
      $('inv-mail').value = '';
      openDlg('dlg-invite');
      setTimeout(function () { $('inv-mail').focus(); }, 40);
    });
  }

  $('inv-go').addEventListener('click', function (e) {
    var mail = $('inv-mail').value.trim();
    if (!mail) { e.preventDefault(); $('inv-mail').focus(); return; }
    api('invite', { email: mail })
      .then(function () { toast(mail + ' を招きました。仮のパスワードが本人宛に届きます'); loadMembers(); })
      .catch(fail);
  });

  var removing = null;
  function openRemove(p) {
    removing = p;
    var count = owned(p.id);
    $('rm-title').textContent = p.name + ' をメンバーから外す';
    $('rm-lede').textContent = '外すと、この人は新しく公開できなくなります。';
    $('rm-warn').hidden = !count;
    $('rm-field').hidden = !count;
    if (count) {
      var warn = $('rm-warn-text');
      warn.textContent = '';
      var strong = document.createElement('b'); strong.textContent = count + '件';
      warn.append(document.createTextNode('この人が公開したものが '), strong,
                  document.createTextNode(' あります。このまま外すと、公開を止めることも'
                    + '閲覧トークンを再発行することも、誰にもできなくなります。'));
      fillPicker($('rm-to'), p.id);
    }
    openDlg('dlg-remove');
  }

  $('rm-go').addEventListener('click', function () {
    var count = owned(removing.id);
    var to = count ? $('rm-to').value : null;
    var moves = count
      ? ITEMS.filter(function (d) { return d.uploadedBy === removing.id; })
             .map(function (d) { return api('transfer', { artifactId: d.artifactId, toPublisher: to }); })
      : [];

    // 先に引き継いでから外す。逆にすると、引き継ぐ相手を指せなくなる
    Promise.all(moves)
      .then(function () { return api('remove-publisher', { publisherId: removing.id }); })
      .then(function () {
        toast(count ? removing.name + ' を外し、' + count + '件を引き継ぎました'
                    : removing.name + ' を外しました');
        load();
      }).catch(fail);
  });

  /* ── 起動 ────────────────────────────────────────── */
  document.addEventListener('click', function () {
    document.querySelectorAll('.menu ul').forEach(function (u) { u.hidden = true; });
    document.querySelectorAll('.menu .rowbtn').forEach(function (b) { b.setAttribute('aria-expanded', 'false'); });
  });
  $('q').addEventListener('input', render);

  document.querySelectorAll('dialog [data-close], dialog [value="cancel"]').forEach(function (b) {
    b.addEventListener('click', function () { b.closest('dialog').close(); });
  });

  fetch('config.json').then(function (r) { return r.json(); }).then(function (c) {
    CONFIG = c;
    try { session.refresh = localStorage.getItem(KEY); } catch (e) { session.refresh = null; }
    if (!session.refresh) { showGate(''); return; }
    refresh().then(entered, function () { forget(); showGate(''); });
  }).catch(function () {
    document.body.textContent = '設定を読み込めませんでした。artifactshare update-function を実行してください。';
  });
})();
