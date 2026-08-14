CSS = """
  :root{
    --paper:#EDF0F3; --surface:#FFF; --surface-2:#F5F7F9;
    --ink:#171B23; --ink-soft:#4B5563; --ink-faint:#79828F;
    --rule:#C3CAD2; --rule-soft:#E4E9EE;
    --warn:#9A4A21; --warn-bg:#F7EAE2;
    --acc:#16636B;  --acc-bg:#E2EFF0;
    --tone-0:#16636B; --tone-1:#9A4A21; --tone-2:#7A4368; --tone-3:#8A8F98;
    --sans:"Hiragino Kaku Gothic ProN","Yu Gothic","Noto Sans JP",system-ui,sans-serif;
    --mono:ui-monospace,"Cascadia Mono",Menlo,monospace;
  }
  @media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
    --paper:#10131A; --surface:#191E27; --surface-2:#1F2631;
    --ink:#E3E8EF; --ink-soft:#A9B3C0; --ink-faint:#7B8694;
    --rule:#2E3742; --rule-soft:#242C37;
    --warn:#E0A17A; --warn-bg:#2E211A; --acc:#6BC0C7; --acc-bg:#132A2C;
    --tone-0:#6BC0C7; --tone-1:#E0A17A; --tone-2:#D19CC0; --tone-3:#767E8A;
  }}

  /* ── 箱（どの型でも共通） ───────────────────── */
  .b{background:var(--surface-2);border:1px solid var(--rule);border-radius:6px;
     padding:.42rem .8rem;font-size:.84rem;line-height:1.5;
     display:flex;flex-direction:column;gap:.1rem;align-items:center;
     justify-self:center;align-self:center;white-space:nowrap;}
  .b__sub{font-size:.68rem;color:var(--ink-faint);}
  .b__row{font-size:.72rem;color:var(--ink-soft);align-self:flex-start;}
  .b:has(.b__row){align-items:flex-start;padding:.5rem .8rem;}
  .b:has(.b__row) .b__name{align-self:center;font-weight:600;
     border-bottom:1px solid var(--rule-soft);width:100%;text-align:center;padding-bottom:.3rem;margin-bottom:.25rem;}
  .b--focus{background:var(--acc-bg);border-color:var(--acc);color:var(--acc);font-weight:600;}
  .b--added{border-color:var(--acc);color:var(--acc);}
  .b--removed{border-style:dashed;color:var(--ink-faint);text-decoration:line-through;}
  .b--start{background:var(--ink);border-color:var(--ink);width:.7rem;height:.7rem;padding:0;border-radius:50%;}
  .b--end{border-width:3px;border-style:double;width:.9rem;height:.9rem;padding:0;border-radius:50%;}

  /* ── 点と線 ── 段と列だけで組む。pxは一つも無い ── */
  .graph{display:grid;grid-template-columns:repeat(var(--cols),auto);
         column-gap:1.1rem;justify-content:center;align-items:center;}
  .graph > i.w{background:var(--rule);}
  .w--v{width:1px;justify-self:center;align-self:stretch;min-height:1.6rem;}
  .w--h{height:1px;align-self:center;justify-self:stretch;}
  .w--back{background:var(--warn);opacity:.6;}
  .w__label{font-size:.66rem;color:var(--ink-faint);justify-self:center;align-self:center;
            background:var(--paper);padding:0 .3rem;z-index:1;white-space:nowrap;}

  /* ── 対比 ─────────────────────────────── */
  .cmp{display:flex;gap:1.8rem;align-items:stretch;flex-wrap:wrap;}
  .panel{flex:1 1 19rem;display:flex;flex-direction:column;gap:.5rem;}
  .panel--before{--tone:var(--warn);--tone-bg:var(--warn-bg);}
  .panel--after{--tone:var(--acc);--tone-bg:var(--acc-bg);}
  .panel__label{font-family:var(--mono);font-size:.66rem;letter-spacing:.1em;color:var(--tone);}
  .panel__body{display:flex;gap:.7rem;align-items:stretch;flex:1;}
  .panel__note{font-size:.74rem;color:var(--ink-faint);margin:0;}
  .frame{border:1.3px dashed var(--tone);border-radius:10px;padding:1.4rem 1rem 1.1rem;
         position:relative;display:flex;justify-content:center;flex:1;}
  .frame--transcript{border:none;padding:0;}
  .frame__label{position:absolute;top:-.58rem;left:.8rem;padding:0 .35rem;
                background:var(--paper);font-size:.64rem;color:var(--tone);white-space:nowrap;}
  .link{align-self:center;display:flex;flex-direction:column;align-items:center;gap:.1rem;
        color:var(--tone);font-size:.66rem;flex:none;}
  .link i{width:2.4rem;border-top:1.3px dashed currentColor;position:relative;display:block;}
  .link i::before{content:"";position:absolute;left:-1px;top:-4px;
                  border:4px solid transparent;border-right-color:currentColor;}

  /* ── 木 ─────────────────────────────── */
  .tr{display:flex;flex-direction:column;align-items:center;}
  .kids{--gap:1rem;--stem:.7rem;display:flex;gap:var(--gap);position:relative;
        margin-top:calc(var(--stem)*2);}
  .limb{position:relative;display:flex;flex-direction:column;align-items:center;}
  .tw{position:absolute;background:var(--rule);}
  .tw--stem{top:calc(var(--stem)*-2);left:50%;width:1px;height:var(--stem);}
  .tw--drop{top:calc(var(--stem)*-1);left:50%;width:1px;height:var(--stem);}
  .tw--bar{top:calc(var(--stem)*-1);height:1px;
           left:calc(var(--gap)/-2);right:calc(var(--gap)/-2);}
  .limb:first-of-type .tw--bar{left:50%;}
  .limb:last-of-type .tw--bar{right:50%;}
  .limb:only-of-type .tw--bar{display:none;}

  /* ── 操作と返り値 ───────────────────────── */
  .win{flex:1;border-radius:9px;overflow:hidden;border:1px solid #2A313C;background:#151A22;}
  .win__bar{display:flex;align-items:center;gap:.5rem;padding:.4rem .7rem;background:#1E242E;}
  .win__bar span{font-family:var(--mono);font-size:.66rem;color:#8B95A3;}
  .win__dots{width:2.4rem;height:.55rem;flex:none;display:block;
    background:radial-gradient(circle 3.5px at 4px 50%,#E06C60 98%,transparent 0),
               radial-gradient(circle 3.5px at 16px 50%,#E0B341 98%,transparent 0),
               radial-gradient(circle 3.5px at 28px 50%,#5FB37A 98%,transparent 0);}
  .win__body{margin:0;padding:.8rem .9rem;background:none;border:none;
             font-family:var(--mono);font-size:.68rem;line-height:1.7;color:#C8D0DA;overflow-x:auto;}
  .ln{display:block;white-space:pre;}
  .ln--comment{color:#6E7885;} .ln--command{color:#E3E8EF;}
  .ln--output{color:#9FB6C4;margin:.4rem 0;} .ln--note{color:#6BC0C7;margin-top:.4rem;}

  /* ── 一覧の差分 ─────────────────────────── */
  .ls{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:.28rem;}
  .it{font-size:.8rem;padding:.26rem .7rem .26rem 1.45rem;border-radius:5px;
      background:var(--surface-2);border:1px solid var(--rule);position:relative;white-space:nowrap;}
  .it::before{position:absolute;left:.5rem;font-family:var(--mono);font-size:.68rem;color:var(--ink-faint);}
  .it--unchanged::before{content:"・";}
  .it--added{border-color:var(--acc);color:var(--acc);} .it--added::before{content:"＋";color:var(--acc);}
  .it--removed{border-style:dashed;color:var(--ink-faint);} .it--removed::before{content:"−";}

  /* ── 帯 ─────────────────────────────── */
  .lanes{display:flex;flex-direction:column;gap:.35rem;}
  .lane{display:flex;align-items:center;gap:.7rem;}
  .lane__name{font-size:.74rem;color:var(--ink-soft);min-width:6rem;text-align:right;flex:none;}
  .lane__track{flex:1;display:grid;grid-template-columns:repeat(var(--span),1fr);
               gap:2px;background:var(--rule-soft);border-radius:5px;padding:2px;}
  .bar{height:1.2rem;border-radius:3px;background:var(--tone-0);display:flex;align-items:center;
       justify-content:center;font-size:.64rem;color:#fff;overflow:hidden;}
  .bar--warn{background:var(--tone-1);} .bar--soft{background:var(--tone-3);}

  /* ── 量 ─────────────────────────────── */
  .am{display:flex;gap:1.6rem;align-items:center;flex-wrap:wrap;}
  .am__ring{width:6.4rem;height:6.4rem;border-radius:50%;display:grid;place-items:center;flex:none;}
  .am__ring span{width:4rem;height:4rem;border-radius:50%;background:var(--paper);
                 display:grid;place-items:center;font-size:.76rem;font-weight:600;}
  .am__list{display:flex;flex-direction:column;gap:.35rem;min-width:15rem;flex:1;}
  .am__row{display:grid;grid-template-columns:auto 1fr auto;align-items:center;
           gap:.5rem;font-size:.74rem;}
  .am__chip{width:.6rem;height:.6rem;border-radius:2px;display:block;}
  .am__row b{font-variant-numeric:tabular-nums;font-weight:600;}
  .am__bar{grid-column:1/-1;height:.32rem;border-radius:99px;display:block;}

  /* ── 分類 ─────────────────────────────── */
  .mx{display:grid;grid-template-columns:auto 1fr;grid-template-rows:1fr auto;
      gap:.5rem;align-items:center;}
  .mx__y{writing-mode:vertical-rl;transform:rotate(180deg);font-size:.68rem;color:var(--ink-faint);}
  .mx__x{grid-column:2;font-size:.68rem;color:var(--ink-faint);text-align:center;}
  .mx__plot{position:relative;height:13rem;border-left:1px solid var(--rule);
            border-bottom:1px solid var(--rule);background:
            linear-gradient(to right,transparent 49.7%,var(--rule-soft) 49.7% 50.3%,transparent 50.3%),
            linear-gradient(to top,transparent 49.7%,var(--rule-soft) 49.7% 50.3%,transparent 50.3%);}
  .mx__q{position:absolute;font-size:.64rem;color:var(--ink-faint);}
  .mx__q--0{right:.4rem;top:.3rem;} .mx__q--1{left:.4rem;top:.3rem;}
  .mx__q--2{left:.4rem;bottom:.3rem;} .mx__q--3{right:.4rem;bottom:.3rem;}
  .pt{position:absolute;transform:translate(-50%,50%);background:var(--surface);
      border:1px solid var(--acc);color:var(--acc);border-radius:5px;
      padding:.16rem .5rem;font-size:.68rem;white-space:nowrap;}

  /* ── やり取り ───────────────────────────── */
  .ex{display:grid;grid-template-columns:repeat(var(--who),1fr);
      row-gap:.5rem;align-items:center;position:relative;}
  .ex__who{justify-self:center;background:var(--surface-2);border:1px solid var(--rule);
           border-radius:6px;padding:.35rem .8rem;font-size:.76rem;white-space:nowrap;z-index:1;}
  .ex__life{justify-self:center;width:1px;background:var(--rule);align-self:stretch;}
  .ex__msg{position:relative;display:flex;justify-content:center;padding-bottom:.35rem;
           border-bottom:1.2px solid var(--ink-faint);}
  .ex__msg span{font-size:.7rem;color:var(--ink-soft);background:var(--paper);padding:0 .4rem;}
  .ex__msg--return{border-bottom-style:dashed;}
  .ex__msg::after{content:"";position:absolute;right:-1px;bottom:-4px;
                  border:4px solid transparent;border-left-color:var(--ink-faint);}
  .ex__msg--rtl::after{right:auto;left:-1px;border-left-color:transparent;border-right-color:var(--ink-faint);}
  .ex__note{justify-self:center;background:var(--warn-bg);border:1px solid var(--warn);
            color:var(--warn);border-radius:5px;padding:.2rem .6rem;font-size:.68rem;}

  /* ── 箱組み ───────────────────────────── */
  .bks{display:grid;grid-template-columns:repeat(var(--cols),1fr);gap:.5rem;}
  .bk{background:var(--surface-2);border:1px solid var(--rule);border-radius:6px;
      padding:.6rem .8rem;font-size:.78rem;text-align:center;}
  .bk--focus{background:var(--acc-bg);border-color:var(--acc);color:var(--acc);}
"""
