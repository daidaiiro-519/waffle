(function () {
  'use strict';

  /* この画面が外へ出るのは利用者プールだけ。管理APIは同じ出所の /api
     にあり、配信の口が内側で署名して届ける。関数URLの居場所を画面が
     知る必要はなく、出所をまたぐ要求も起きない。 */
  var CONFIG = null;
  var $ = function (id) { return document.getElementById(id); };

  /* ── 覚えておくもの ──────────────────────────────────
     入り直すための券だけを残す。誰であるかを示す証明は短命なので、
     画面を開き直すたびに取り直す。 */
  var KEY = 'artifactshare.refresh';
  var session = { token: null, who: '', label: '', admin: false, refresh: null };

  function remember(tokens) {
    session.token = tokens.IdToken;
    if (tokens.RefreshToken) {
      session.refresh = tokens.RefreshToken;
      try { localStorage.setItem(KEY, tokens.RefreshToken); } catch (e) { /* 使えなくても続く */ }
    }
    var claims = readClaims(tokens.IdToken);
    // 突き合わせに使う値。宛先で入る設定なので、人が読める文字列ではない
    session.who = claims['cognito:username'] || '';
    // 画面に出す名前。読めるのはこちら
    session.label = claims.email || session.who;
    session.admin = (claims['cognito:groups'] || []).indexOf('administrators') >= 0;
  }

  function forget() {
    session = { token: null, who: '', label: '', admin: false, refresh: null };
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

  /* ── 管理APIとのやり取り ──────────────────────────────
     証明が古くなっていたら一度だけ取り直して、同じ要求をやり直す。
     入力の途中で締め出されないようにするため。 */
  function api(action, body, retried) {
    return fetch('/api', {
      method: 'POST',
      // authorization は使えない。配信の口が関数へ署名するのに使うため
      headers: { 'content-type': 'application/json', 'x-id-token': session.token },
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
    clearSecrets();
    setTimeout(function () { $('g-mail').focus(); }, 40);
  }

  function signedOut() {
    forget();
    showGate('入り直してください。');
  }

  function clearSecrets() {
    // 仕様の操作保証: 合言葉と確認コードをこの側に残さない。
    // 画面が隠れても入力欄の値は残るため、明示的に消す
    ['g-pass', 'g-new', 'g-new2', 'g-code', 'g-rnew'].forEach(function (id) {
      if ($(id)) $(id).value = '';
    });
  }

  function entered() {
    clearSecrets();
    $('gate').hidden = true;
    document.body.classList.toggle('is-admin', session.admin);
    var who = document.querySelector('.whoami');
    who.textContent = '';
    var av = document.createElement('span');
    av.className = 'avatar';
    av.textContent = (session.label || '?').slice(0, 2).toUpperCase();
    var out = document.createElement('button');
    out.type = 'button'; out.className = 'signout'; out.textContent = 'ログアウト';
    out.addEventListener('click', function () { forget(); showGate(''); });
    who.append(av, document.createTextNode(session.label), out);
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
      if (/NotAuthorized|InvalidParameter/.test(x.kind || '')) {
        // まだ一度も入っていない人は、この経路を使えない（仕様の
        // RESET_NOT_AVAILABLE）。管理者に招き直してもらうほかない
        err.textContent = 'この宛先はまだ招待に応じていません。'
          + '管理者に招待を送り直してもらってください。';
      } else if (/CodeMismatch|ExpiredCode/.test(x.kind || '')) {
        err.textContent = 'コードが違うか、期限が切れています。もう一度送ってください。';
      } else {
        err.textContent = x.message || '決められませんでした。';
      }
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
      loadProjects();
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

    var mine = item.uploadedBy === session.who || !item.uploadedBy;
    var entries = [['開く']];
    // 中身を差し替えられるのは公開した本人だけ。管理者にも出さない
    if (mine && item.status === 'active') entries.push(['差し替えてアップロード']);
    if (item.status === 'active') entries.push(['配布先'], ['プロジェクトを変える']);
    if (item.status !== 'active') entries.push(['配布先を見る']);
    entries.push(['エクスポート']);
    if (session.admin) entries.push(['sep'], ['引き継ぐ']);
    entries.push(['sep'], item.status === 'active' ? ['公開を止める'] : ['再公開する']);

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
      if (session.admin) sub.appendChild(chip('', publisherLabel(d.uploadedBy)));
      sub.appendChild(d.docType ? chip('dtype', d.docType) : chip('dtype none', '種別なし'));
      (d.projects || []).forEach(function (p) { sub.appendChild(chip('proj', p)); });
      (d.tags || []).forEach(function (g) { sub.appendChild(chip('tag', g)); });
      if (d.status === 'active') sub.appendChild(chip('dist', '配布先 ' + (d.distributions || 0) + '件'));
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
      if (count) {
        c.setAttribute('aria-label', d.name + ' のコメント' + count + '件を読む');
        c.title = 'コメントを読む';
        c.addEventListener('click', function (e) { e.stopPropagation(); openComments(d); });
      } else { c.disabled = true; }

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
    if (label === 'エクスポート') { exportArtifact(item); return; }
    if (label === '差し替えてアップロード') { $('rep-target').textContent = item.name; openDlg('dlg-replace'); return; }
    if (label === '引き継ぐ') return openTransfer(item);

    if (label === '配布先') return openTokens(item, false);
    if (label === '配布先を見る') return openTokens(item, true);
    if (label === 'プロジェクトを変える') return openProjects(item);
    if (label === '公開を止める') { $('dis-target').textContent = item.name; openDlg('dlg-disable'); return; }
    if (label === '再公開する') {
      $('rep2-target').textContent = item.name;
      $('rep2-1').classList.add('on'); $('rep2-2').classList.remove('on');
      openDlg('dlg-republish');
      return;
    }
  }

  $('rep2-go').addEventListener('click', function (e) {
    e.preventDefault();
    api('enable', { artifactId: target.artifactId }).then(function () {
      $('rep2-target2').textContent = target.name;
      $('rep2-1').classList.remove('on'); $('rep2-2').classList.add('on');
      load();
    }).catch(fail);
  });

  document.querySelectorAll('#dlg-disable [value="ok"], #dlg-disable .btn.danger-b')
    .forEach(function (b) {
      b.addEventListener('click', function () {
        // 尋ねた答えに従う。既定は取り出してから止める——止めたあとでも取り出せるが、
        // 止める判断をした人が手元に持たないまま画面を離れると、次に開くまで
        // 中身を確かめられない
        var first = $('dis-export').checked
          ? exportArtifact(target)
          : Promise.resolve();
        Promise.resolve(first)
          .then(function () { return api('disable', { artifactId: target.artifactId }); })
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

  /* ── 寄せられたコメントを読む ──────────────────────
     閲覧者は閲覧トークンで開いた画面から読み書きし、投稿者はここから読む。
     指しているものは同じで、保存されている形も同じ。 */
  var DECISION = { approve: 'この方向でOK', revise: '修正希望' };

  function openComments(item) {
    $('cm-target').textContent = item.name;
    var list = $('cm-list');
    list.textContent = '';
    var busy = document.createElement('p');
    busy.className = 'busy'; busy.textContent = '読み込んでいます…';
    list.appendChild(busy);
    $('cm-sum').textContent = '';
    openDlg('dlg-comments');

    api('comments', { artifactId: item.artifactId })
      .then(function (d) { renderComments(d); })
      .catch(function (e) {
        list.textContent = '';
        var p = document.createElement('p');
        p.className = 'busy'; p.textContent = '読み込めませんでした。' + (e.message || '');
        list.appendChild(p);
      });
  }

  function when(iso) {
    var d = new Date(iso);
    return isNaN(d) ? '' : (d.getMonth() + 1) + '/' + d.getDate();
  }

  function renderComments(d) {
    var list = $('cm-list');
    list.textContent = '';

    var said = d.comments.filter(function (c) { return c.kind !== 'divider'; });
    var approve = said.filter(function (c) { return c.decision === 'approve'; }).length;
    var revise = said.filter(function (c) { return c.decision === 'revise'; }).length;
    var people = said.reduce(function (set, c) {
      if (set.indexOf(c.author) < 0) set.push(c.author);
      return set;
    }, []).length;

    var sum = said.length + '件・' + people + '人';
    if (approve) sum += '・この方向でOK ' + approve;
    if (revise) sum += '・修正希望 ' + revise;
    // 読めなかったものを黙って落とすと、これで全部だと思い込む
    if (d.unreadable) sum += '（読めなかったもの ' + d.unreadable + '件）';
    $('cm-sum').textContent = sum;

    if (!said.length) {
      var e = document.createElement('p');
      e.className = 'busy'; e.textContent = 'まだコメントはありません。';
      list.appendChild(e);
      return;
    }

    d.comments.forEach(function (c) {
      if (c.kind === 'divider') {
        var sep = document.createElement('p');
        sep.className = 'cmdivider';
        sep.textContent = 'ここで中身が差し替えられました';
        list.appendChild(sep);
        return;
      }
      var el = document.createElement('div');
      el.className = 'cmitem' + (c.parentId ? ' reply' : '');

      var head = document.createElement('div'); head.className = 'cmtop';
      head.appendChild(chip('cwho', c.author));
      if (DECISION[c.decision]) {
        head.appendChild(chip('cdec ' + c.decision, DECISION[c.decision]));
      }
      head.appendChild(chip('cwhen', when(c.postedAt)));

      var body = document.createElement('div'); body.className = 'cbody';
      body.textContent = c.body;      // 受け取った値は必ず文字として描く

      el.append(head, body);
      list.appendChild(el);
    });
  }

  /* ── 取り出す ──────────────────────────────────────
     まとめるのはここ。管理APIは読むだけで、保管へは書かない。 */
  function exportArtifact(item) {
    // 呼び出し元が終わりを待てるように返す（止める前に取り出す経路が使う）
    return api('export', { artifactId: item.artifactId }).then(function (d) {
      var name = (d.name || item.artifactId).replace(/[\\/:*?"<>|]/g, '_');
      save(name + '.html', d.content, 'text/html;charset=utf-8');
      save(name + '.comments.json',
           JSON.stringify(d.comments, null, 2), 'application/json;charset=utf-8');
      toast(d.unreadable
        ? '取り出しました（読めなかったコメントが' + d.unreadable + '件あります）'
        : '中身とコメントを取り出しました');
    }).catch(fail);
  }

  function save(filename, text, type) {
    var url = URL.createObjectURL(new Blob([text], { type: type }));
    var a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  /* ── プロジェクト ──────────────────────────────────
     自分が持ち主のものと、共有のものが並ぶ。共有なら自分のアーティファクトを
     入れられるため、持ち主でなくても一覧に出す。 */
  var PROJECTS = [];

  function loadProjects() {
    api('projects').then(function (d) {
      PROJECTS = d.projects || [];
      renderProjects();
    }).catch(function () { /* 一覧が主目的なので、ここは黙って諦める */ });
  }

  function renderProjects() {
    var wrap = $('plist');
    if (!wrap) return;
    wrap.textContent = '';
    $('pcount').textContent = PROJECTS.length + ' 件';

    if (!PROJECTS.length) {
      var e = document.createElement('div');
      e.className = 'empty';
      var p0 = document.createElement('p');
      p0.textContent = 'まだプロジェクトがありません。まとめて見せたいときに作ります。';
      e.appendChild(p0); wrap.appendChild(e);
      return;
    }

    PROJECTS.forEach(function (p) {
      var active = p.status === 'active';
      var card = document.createElement('div');
      card.className = 'pcard' + (active ? '' : ' off');

      var main = document.createElement('div'); main.className = 'pmain';
      var name = document.createElement('p'); name.className = 'pname'; name.textContent = p.name;
      var meta = document.createElement('div'); meta.className = 'pmeta';
      if (p.projectKey) meta.appendChild(chip('pkey', p.projectKey));
      meta.appendChild(chip('', p.artifactCount + ' 件のアーティファクト'));
      // 共有のものにだけ印を出す。個人が既定なので、違う方に付ける
      if (p.scope === 'SHARED') meta.appendChild(chip('shared', '共有'));
      if (!p.isMine) meta.appendChild(chip('', p.owner + ' が作成'));
      main.append(name, meta);

      var end = document.createElement('div'); end.className = 'pend';
      end.appendChild(active ? chip('status on', '公開中') : chip('status no', '無効化済み'));
      // 見せ方を変えられるのは持ち主と管理者だけ
      if (p.isMine || session.admin) end.appendChild(projectMenu(p));
      end.appendChild(chip('chev', '›'));

      card.append(main, end);
      card.setAttribute('role', 'button');
      card.setAttribute('tabindex', '0');
      card.addEventListener('click', function (e) {
        if (e.target.closest('.menu')) return;   // ⋯ を押したときは開かない
        openProject(p.projectId);
      });
      card.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openProject(p.projectId); }
      });
      wrap.appendChild(card);
    });
  }

  /* ── プロジェクトの中身 ─────────────────────────────
     入れられるのは自分が公開したものだけ。他人のものは選べない。 */
  var opened = null;

  function openProject(projectId) {
    api('project', { projectId: projectId }).then(function (d) {
      opened = d;
      var p = d.project;
      $('pd-name').textContent = p.name;
      $('pd-key').textContent = p.projectKey || '';
      $('pd-key').hidden = !p.projectKey;
      $('pd-url').textContent = 'https://' + CONFIG.viewerDomain + '/proj/' + p.projectId + '/';

      var st = $('pd-status');
      st.className = 'status ' + (p.status === 'active' ? 'on' : 'no');
      st.textContent = p.status === 'active' ? '公開中' : '無効化済み';

      var scope = $('pd-scope');
      scope.textContent = p.scope === 'SHARED' ? '共有' : '個人';
      scope.className = p.scope === 'SHARED' ? 'shared' : 'status no';

      // 見せ方を変えられるのは持ち主と管理者だけ
      $('pd-rotate').hidden = !(p.isMine || session.admin);

      renderMembersOf(d);
      view('v-projdetail');
    }).catch(fail);
  }

  function renderMembersOf(d) {
    var box = $('pd-arts');
    box.textContent = '';
    $('pd-count').textContent = d.artifacts.length + ' 件';

    d.artifacts.forEach(function (a) {
      var row = document.createElement('div'); row.className = 'arow';
      var main = document.createElement('div');
      var t = document.createElement('p'); t.className = 'atitle'; t.textContent = a.name;
      var sub = document.createElement('div'); sub.className = 'asub';
      if (a.docType) sub.appendChild(chip('dtype', a.docType));
      if (!a.isMine) sub.appendChild(chip('', publisherLabel(a.uploadedBy)));
      if (a.status !== 'active') sub.appendChild(chip('status no', '無効化済み'));
      main.append(t, sub);

      var end = document.createElement('div');
      // 外せるのは自分が公開したものだけ。他人のものは動かせない
      if (a.isMine) {
        var b = document.createElement('button');
        b.className = 'rowbtn'; b.type = 'button'; b.textContent = '外す';
        b.setAttribute('aria-label', a.name + ' をこのプロジェクトから外す');
        b.addEventListener('click', function () {
          api('unassign', { artifactId: a.artifactId, projectId: d.project.projectId })
            .then(function () {
              toast('外しました。アーティファクト自体は残っています');
              openProject(d.project.projectId);
              loadProjects();
            }).catch(fail);
        });
        end.appendChild(b);
      }
      row.append(main, end);
      box.appendChild(row);
    });

    // 加える。選べるのは自分が公開していて、まだ入っていないものだけ
    var inside = {};
    d.artifacts.forEach(function (a) { inside[a.artifactId] = true; });
    var addable = ITEMS.filter(function (x) {
      return x.status === 'active' && !inside[x.artifactId];
    });

    var add = document.createElement('div'); add.className = 'addrow';
    if (!addable.length) {
      var note = document.createElement('span');
      note.style.fontSize = '12.5px';
      note.style.color = 'var(--ink-faint)';
      note.textContent = ITEMS.length
        ? '入れられるものがありません。公開中のものはすべて入っています。'
        : 'まだ何も公開していません。';
      add.appendChild(note);
    } else {
      var sel = document.createElement('select');
      sel.setAttribute('aria-label', '入れるアーティファクトを選ぶ');
      addable.forEach(function (x) {
        var o = document.createElement('option');
        o.value = x.artifactId; o.textContent = x.name;
        sel.appendChild(o);
      });
      var go = document.createElement('button');
      go.className = 'btn sm'; go.type = 'button'; go.textContent = '追加する';
      go.addEventListener('click', function () {
        api('assign', { artifactId: sel.value, projectId: d.project.projectId })
          .then(function () {
            toast('入れました。このプロジェクトのトークンでも開けます');
            openProject(d.project.projectId);
            loadProjects();
          }).catch(fail);
      });
      add.append(sel, go);
    }
    box.appendChild(add);
  }

  $('pd-back').addEventListener('click', function () { view('v-projects'); });

  $('pd-rotate').addEventListener('click', function () {
    openTokens({ artifactId: null, projectId: opened.project.projectId,
                 name: opened.project.name, status: opened.project.status }, false);
  });

  function projectMenu(p) {
    var wrap = document.createElement('div'); wrap.className = 'menu';
    var btn = document.createElement('button');
    btn.className = 'rowbtn'; btn.type = 'button'; btn.textContent = '⋯';
    btn.setAttribute('aria-label', p.name + ' の操作');
    btn.setAttribute('aria-expanded', 'false');
    var ul = document.createElement('ul'); ul.hidden = true;

    var active = p.status === 'active';
    var entries = [['URLをコピー']];
    if (active) entries.push(['配布先']);
    entries.push(['sep'], active ? ['公開を止める'] : ['再公開する']);

    entries.forEach(function (it) {
      var li = document.createElement('li');
      if (it[0] === 'sep') { li.className = 'sep'; }
      else {
        var b = document.createElement('button'); b.type = 'button'; b.textContent = it[0];
        if (it[1]) b.className = it[1];
        b.addEventListener('click', function (e) {
          e.stopPropagation(); ul.hidden = true;
          projectAct(it[0], p);
        });
        li.appendChild(b);
      }
      ul.appendChild(li);
    });

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = ul.hidden;
      document.querySelectorAll('.menu ul').forEach(function (u) { u.hidden = true; });
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

  /* ── 配布先 ──
     1つの対象（共有アーティファクトかプロジェクト）に、閲覧トークンを複数持てる。
     一覧が返すのは名前と期限だけで、値は発行の瞬間にしか出ない。 */
  var TK_MAX = 5;
  var tkTarget = null, tkReadOnly = false, tkList = [], tkPending = null;

  function tkSubject() {
    return tkTarget.projectId ? { projectId: tkTarget.projectId }
                              : { artifactId: tkTarget.artifactId };
  }
  function tkIsProject() { return !!tkTarget.projectId; }
  function tkPane(n) {
    ['tk-1', 'tk-2', 'tk-3'].forEach(function (id, i) {
      $(id).classList.toggle('on', i === n - 1);
    });
  }
  function tkDays(expiresAt) {
    if (!expiresAt) return null;                       // 期限なし（プロジェクトだけ）
    return Math.max(0, Math.ceil((expiresAt * 1000 - Date.now()) / 86400000));
  }
  function tkWhen(t) {
    var d = tkDays(t.expiresAt);
    if (d === null) return '期限なし';
    if (d === 0) return '今日まで — 今日の終わりに期限切れ';
    if (d === 1) return '明日まで — あと1日';
    return fmtDate(t.expiresAt) + 'まで（あと' + d + '日）';
  }

  function openTokens(item, readOnly) {
    tkTarget = item; tkReadOnly = !!readOnly; tkList = [];
    var label = (tkIsProject() ? 'プロジェクト：' : '共有アーティファクト：') + item.name;
    ['tk-target', 'tk-target2', 'tk-target3'].forEach(function (id) { $(id).textContent = label; });
    $('tk-url').textContent = tkIsProject()
      ? 'https://' + CONFIG.viewerDomain + '/proj/' + item.projectId + '/'
      : 'https://' + CONFIG.viewerDomain + '/p/' + item.artifactId + '/';
    tkPane(1); tkRender(true); openDlg('dlg-tokens');
    api('view-tokens', tkSubject()).then(function (d) {
      tkList = d.viewTokens || [];
      tkRender(false);
    }).catch(fail);
  }

  function tkRender(loading) {
    var box = $('tk-list'); box.textContent = '';
    if (loading) {
      var w = document.createElement('div'); w.className = 'tkempty';
      var wp = document.createElement('p'); wp.textContent = '読み込んでいます…';
      w.appendChild(wp); box.appendChild(w);
      $('tk-add').hidden = true; $('tk-revokeall').hidden = true;
      $('tk-count').hidden = true; $('tk-n').textContent = ''; $('tk-ro').hidden = true;
      return;
    }
    if (!tkList.length) {
      var e = document.createElement('div'); e.className = 'tkempty';
      var msg = document.createElement('p');
      msg.textContent = tkIsProject()
        ? 'いまは誰もこのプロジェクトを開けません。公開そのものは止まっていません。'
        : 'いまは誰も開けません。公開そのものは止まっていません。閲覧トークンを発行すると、その配布先だけが開けるようになります。';
      e.appendChild(msg);
      if (!tkReadOnly) {
        var go = document.createElement('button');
        go.className = 'btn'; go.type = 'button'; go.textContent = '閲覧トークンを発行';
        go.addEventListener('click', tkOpenAdd);
        e.appendChild(go);
      }
      box.appendChild(e);
    }
    tkList.slice().sort(function (a, b) {
      if (!a.expiresAt) return 1;
      if (!b.expiresAt) return -1;
      return a.expiresAt - b.expiresAt;
    }).forEach(function (t) {
      var row = document.createElement('div'); row.className = 'tkrow';
      var n = document.createElement('span'); n.className = 'tkname'; n.textContent = t.name;
      var d = tkDays(t.expiresAt);
      var w = document.createElement('span');
      w.className = 'tkwhen' + (d !== null && d <= 1 ? ' soon' : '');
      w.textContent = tkWhen(t);
      row.append(n, w);
      if (!tkReadOnly) {
        var off = document.createElement('button');
        off.className = 'tkoff'; off.type = 'button'; off.textContent = '無効にする';
        off.setAttribute('aria-label', t.name + ' の閲覧トークンを無効にする');
        off.addEventListener('click', function () { tkAsk(t); });
        row.appendChild(off);
      }
      box.appendChild(row);
    });
    var full = tkList.length >= TK_MAX;
    $('tk-n').textContent = tkList.length ? '配布先 ' + tkList.length + '件' : '';
    var c = $('tk-count');
    c.hidden = !tkList.length;
    c.textContent = '同時に渡せるのは' + TK_MAX + '件まで'
      + (full ? '。発行するには、どれかを先に無効にするか、期限切れを待ってください。' : '');
    c.classList.toggle('full', full);
    $('tk-add').hidden = tkReadOnly || !tkList.length;
    $('tk-add').disabled = full;
    $('tk-revokeall').hidden = tkReadOnly || !tkList.length;
    $('tk-ro').hidden = !tkReadOnly;
  }

  function tkOpenAdd() {
    $('tk-name').value = '';
    var week = document.querySelector('input[name="tk-ttl"][value="7"]');
    if (week) week.checked = true;
    $('tk-err').hidden = true;
    tkPane(2);
    setTimeout(function () { $('tk-name').focus(); }, 40);
  }
  $('tk-add').addEventListener('click', tkOpenAdd);
  $('tk-back').addEventListener('click', function () { tkPane(1); });
  $('tk-done').addEventListener('click', function () {
    tkPane(1);
    api('view-tokens', tkSubject()).then(function (d) {
      tkList = d.viewTokens || []; tkRender(false); load();
    }).catch(fail);
  });
  /* 発行の直後だけは Esc を受けない。二度と表示できない値が、
     手応えのないひと押しで消えるのを防ぐ */
  $('dlg-tokens').addEventListener('cancel', function (e) {
    if ($('tk-3').classList.contains('on')) e.preventDefault();
  });

  $('tk-go').addEventListener('click', function () {
    var name = $('tk-name').value.trim(), err = $('tk-err');
    if (!name) { err.textContent = '配布先の名前を入れてください。'; err.hidden = false; return; }
    var picked = document.querySelector('input[name="tk-ttl"]:checked');
    var pick = picked ? picked.value : '7';
    var body = { name: name };
    if (tkTarget.projectId) body.projectId = tkTarget.projectId;
    else body.artifactId = tkTarget.artifactId;
    if (pick !== 'none') body.ttl = (pick === 'month' ? 30 : parseInt(pick, 10)) * 24 * 60 * 60;
    err.hidden = true;
    api('issue-token', body).then(function (d) {
      $('tk-issued').textContent = '配布先「' + name + '」の閲覧トークン';
      $('tk-token').textContent = d.token;
      tkPane(3);
    }).catch(function (e) { err.textContent = (e && e.message) || '発行できませんでした。'; err.hidden = false; });
  });

  function tkAsk(t) {
    tkPending = t;
    var rest = tkList.length - 1;
    $('rv-head').textContent = 'この閲覧トークンを無効にしますか';
    $('rv-target').textContent = t.name + ' — ' + tkTarget.name;
    $('rv-kn').textContent = 'この配布先に渡したトークンでは開けなくなる。一度無効にすると元へは戻せません';
    $('rv-ky').textContent = (rest > 0 ? '他の' + rest + '件の配布先のトークン・' : '')
      + 'URL・寄せられたコメント。公開そのものも止まりません'
      + (rest === 0 ? '（これで誰も開けなくなります）' : '');
    openDlg('dlg-revoke');
  }
  $('tk-revokeall').addEventListener('click', function () {
    tkPending = null;
    $('rv-head').textContent = 'すべての閲覧トークンを無効にしますか';
    $('rv-target').textContent = tkTarget.name;
    $('rv-kn').textContent = 'いま渡している' + tkList.length
      + '件ぶんのトークンが、すべて開けなくなる。元へは戻せません';
    $('rv-ky').textContent = tkIsProject()
      ? '入っているアーティファクトは、それぞれの閲覧トークンで引き続き開けます。公開そのものも止まりません'
      : 'URL・寄せられたコメント。公開そのものも止まりません';
    openDlg('dlg-revoke');
  });
  $('rv-go').addEventListener('click', function () {
    var body = tkSubject(), action = 'revoke-all-tokens';
    if (tkPending) { action = 'revoke-token'; body.tokenId = tkPending.tokenId; }
    var count = tkList.length;
    api(action, body).then(function () {
      $('dlg-revoke').close();
      toast(tkPending ? tkPending.name + ' の閲覧トークンを無効にしました'
                      : count + '件の閲覧トークンを無効にしました');
      return api('view-tokens', tkSubject());
    }).then(function (d) {
      tkList = d.viewTokens || []; tkRender(false); load();
    }).catch(fail);
  });

  /* ── プロジェクトを変える ──
     所属は「誰が開けるか」を広げる操作なので、公開したあとも変えられる必要がある */
  var PROJ_MAX = 3;
  var pjItem = null, pjPicked = [];

  function openProjects(item) {
    pjItem = item;
    pjPicked = (item.projects || []).slice();
    $('pj-target').textContent = item.name;
    $('pj-q').value = '';
    pjRender();
    openDlg('dlg-projects');
    if (!PROJECTS.length) loadProjects();
  }

  function pjRender() {
    var picked = $('pj-picked'); picked.textContent = '';
    pjPicked.forEach(function (name) {
      var tag = document.createElement('span'); tag.className = 'pjtag';
      tag.appendChild(document.createTextNode(name));
      var x = document.createElement('button');
      x.type = 'button'; x.textContent = '✕';
      x.setAttribute('aria-label', name + ' から外す');
      x.addEventListener('click', function () {
        pjPicked = pjPicked.filter(function (v) { return v !== name; });
        pjRender();
      });
      tag.appendChild(x); picked.appendChild(tag);
    });

    var full = pjPicked.length >= PROJ_MAX;
    var q = $('pj-q').value.trim();
    var rest = PROJECTS.filter(function (p) {
      return p.status === 'active' && pjPicked.indexOf(p.name) < 0 && (!q || p.name.indexOf(q) >= 0);
    });

    var box = $('pj-list'); box.textContent = '';
    if (!rest.length) {
      var none = document.createElement('div'); none.className = 'pjnone';
      none.textContent = q ? '「' + q + '」に当たるプロジェクトはありません。'
                           : 'ほかに入れられるプロジェクトはありません。';
      box.appendChild(none);
    }
    rest.forEach(function (p) {
      var b = document.createElement('button');
      b.className = 'pjopt'; b.type = 'button'; b.textContent = p.name;
      b.disabled = full;
      b.addEventListener('click', function () {
        pjPicked.push(p.name); $('pj-q').value = ''; pjRender();
      });
      box.appendChild(b);
    });

    $('pj-limit').textContent = '入れられるのは' + PROJ_MAX + '件までです'
      + (full ? '。追加するには、どれかを先に外してください。'
              : '（いま' + pjPicked.length + '件）。');
  }

  $('pj-q').addEventListener('input', pjRender);
  $('pj-go').addEventListener('click', function () {
    var was = pjItem.projects || [];
    var byName = {};
    PROJECTS.forEach(function (p) { byName[p.name] = p.projectId; });
    var added = pjPicked.filter(function (n) { return was.indexOf(n) < 0; });
    var removed = was.filter(function (n) { return pjPicked.indexOf(n) < 0; });
    var calls = added.map(function (n) {
      return api('assign', { artifactId: pjItem.artifactId, projectId: byName[n] });
    }).concat(removed.map(function (n) {
      return api('unassign', { artifactId: pjItem.artifactId, projectId: byName[n] });
    }));
    Promise.all(calls).then(function () {
      $('dlg-projects').close();
      toast(pjPicked.length ? 'プロジェクトを更新しました' : 'どのプロジェクトからも外しました');
      load();
    }).catch(fail);
  });

  var targetProject = null;

  function projectAct(label, p) {
    targetProject = p;
    if (label === 'URLをコピー') {
      copyText('https://' + CONFIG.viewerDomain + '/proj/' + p.projectId + '/',
               function () { toast('URLをコピーしました'); });
      return;
    }
    if (label === '配布先') return openTokens(
      { artifactId: null, projectId: p.projectId, name: p.name, status: p.status }, false);
    if (label === '公開を止める') {
      api('disable-project', { projectId: p.projectId })
        .then(function () { toast('公開を止めました。入っているものは個別に開けます'); loadProjects(); })
        .catch(fail);
      return;
    }
    api('enable-project', { projectId: p.projectId })
      .then(function () { toast('再公開しました。止める前に渡した閲覧トークンはそのまま使えます'); loadProjects(); })
      .catch(fail);
  }

  $('new-project').addEventListener('click', function () {
    $('np-name').value = '';
    document.querySelector('[name="np-scope"][value="PERSONAL"]').checked = true;
    $('np-1').classList.add('on'); $('np-2').classList.remove('on');
    openDlg('dlg-newproj');
    setTimeout(function () { $('np-name').focus(); }, 40);
  });

  $('np-go').addEventListener('click', function () {
    var name = $('np-name').value.trim();
    if (!name) { $('np-name').focus(); return; }
    var scope = document.querySelector('[name="np-scope"]:checked').value;

    $('np-go').disabled = true;
    api('create-project', { displayName: name, scope: scope }).then(function (d) {
      $('np-name2').textContent = d.name;
      $('np-url').textContent = d.url;
      $('np-token').textContent = d.token;
      $('np-1').classList.remove('on'); $('np-2').classList.add('on');
      loadProjects();
    }).catch(fail).then(function () { $('np-go').disabled = false; });
  });

  /* ── メンバー（管理者だけ） ───────────────────────── */
  var PEOPLE = [];

  function loadMembers() {
    api('publishers').then(function (d) {
      PEOPLE = d.publishers || [];
      renderMembers();
      render();          // 公開した人を読める名前で出し直す
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
      name.textContent = p.name + (p.id === session.who ? '（自分）' : '');
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
      if (p.id !== session.who) end.appendChild(memberMenu(p));

      row.append(main, count, end);
      list.appendChild(row);
    });
  }

  function owned(id) {
    return ITEMS.filter(function (d) { return d.uploadedBy === id; }).length;
  }

  function publisherLabel(id) {
    if (id === session.who) return '自分';
    for (var i = 0; i < PEOPLE.length; i++) {
      if (PEOPLE[i].id === id) return PEOPLE[i].name || PEOPLE[i].email || id;
    }
    return id;
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

  document.querySelectorAll('.nav a').forEach(function (a, i) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      document.querySelectorAll('.nav a').forEach(function (x) { x.classList.remove('cur'); });
      a.classList.add('cur');
      view(i === 0 ? 'v-home' : 'v-projects');
      if (i === 1) loadProjects();
    });
  });

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
