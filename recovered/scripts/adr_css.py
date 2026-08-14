ADR_CSS = """
  /* ── comparison 部品 ───────────────────────────── */
  .fig--structure, .fig--session { margin:0; display:flex; flex-direction:column; gap:.9rem; }
  .fig--structure figcaption, .fig--session figcaption { font-size:.78rem; color:var(--ink-faint); }
  .fig__sides { display:flex; gap:1.8rem; align-items:stretch; flex-wrap:wrap; }
  .panel { flex:1 1 20rem; display:flex; flex-direction:column; gap:.55rem; }
  .panel--before { --tone:var(--warn);   --tone-bg:var(--warn-bg); }
  .panel--after  { --tone:var(--render); --tone-bg:var(--render-bg); }
  .panel__label { font-family:var(--mono); font-size:.68rem; letter-spacing:.1em; color:var(--tone); }
  .panel__body { display:flex; gap:.8rem; align-items:stretch; flex:1; }
  .panel__reading { font-size:.76rem; color:var(--ink-faint); margin:0; }

  .frame { border:1.4px dashed var(--tone); border-radius:10px; padding:1.5rem 1.1rem 1.2rem;
           position:relative; display:flex; justify-content:center; flex:1; }
  .frame__label { position:absolute; top:-.6rem; left:.9rem; padding:0 .4rem;
                  background:var(--paper); font-size:.66rem; color:var(--tone); white-space:nowrap; }

  .box { background:var(--surface-2); border:1px solid var(--rule); border-radius:6px;
         padding:.45rem .85rem; font-size:.84rem; white-space:nowrap; }
  .box--focus, .box--moved { background:var(--tone-bg); border-color:var(--tone); color:var(--tone); font-weight:600; }

  .tree { display:flex; flex-direction:column; align-items:center; }
  .kids { --gap:1rem; --stem:.75rem; display:flex; gap:var(--gap);
          position:relative; margin-top:calc(var(--stem) * 2); }
  .limb { position:relative; display:flex; flex-direction:column; align-items:center; }
  .wire { position:absolute; background:var(--rule); }
  .wire--stem { top:calc(var(--stem) * -2); left:50%; width:1px; height:var(--stem); }
  .wire--drop { top:calc(var(--stem) * -1); left:50%; width:1px; height:var(--stem); }
  /* 横の桁は、箱の幅を参照しない。隙間の半分と、自分の中心だけで書く */
  .wire--bar  { top:calc(var(--stem) * -1); height:1px;
                left:calc(var(--gap) / -2); right:calc(var(--gap) / -2); }
  .limb:first-of-type .wire--bar { left:50%; }
  .limb:last-of-type  .wire--bar { right:50%; }
  .limb:only-of-type  .wire--bar { display:none; }

  .link { align-self:center; display:flex; flex-direction:column; align-items:center;
          gap:.15rem; color:var(--tone); font-size:.68rem; flex:none; }
  .link__line { width:2.6rem; border-top:1.4px dashed currentColor; position:relative; }
  .link__line::before { content:""; position:absolute; left:-1px; top:-4px;
                        border:4px solid transparent; border-right-color:currentColor; }

  /* ── session 部品 ─────────────────────────────── */
  .scene { display:flex; flex-direction:column; gap:.6rem; }
  .scene__label { font-size:.78rem; color:var(--ink-soft); margin:0; }
  .scene__pair { display:grid; gap:1rem; }
  @media (min-width:54rem) { .scene__pair { grid-template-columns:1fr 1fr; } }
  .win { border-radius:9px; overflow:hidden; border:1px solid #2A313C; background:#151A22; }
  .win--before { --tone:#D98A62; } .win--after { --tone:#6BC0C7; }
  .win__bar { display:flex; align-items:center; gap:.5rem; padding:.45rem .7rem; background:#1E242E; }
  .win__dots { width:2.6rem; height:.6rem; flex:none;
    background:radial-gradient(circle 4px at 4px 50%, #E06C60 98%, transparent 0),
               radial-gradient(circle 4px at 17px 50%, #E0B341 98%, transparent 0),
               radial-gradient(circle 4px at 30px 50%, #5FB37A 98%, transparent 0); }
  .win__title { font-family:var(--mono); font-size:.68rem; color:#8B95A3; }
  .win__tag { margin-left:auto; font-size:.62rem; padding:.1rem .45rem; border-radius:4px;
              color:var(--tone); border:1px solid var(--tone); }
  .win__body { margin:0; padding:.9rem 1rem; font-family:var(--mono); font-size:.7rem;
               line-height:1.75; color:#C8D0DA; overflow-x:auto; }
  .line { display:block; white-space:pre; }
  .line--comment { color:#6E7885; }
  .line--command { color:#E3E8EF; }
  .line--output  { color:#9FB6C4; margin:.5rem 0; }
  .line--note    { color:var(--tone); margin-top:.5rem; }
"""