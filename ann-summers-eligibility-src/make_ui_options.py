"""Build ui-options.html: the real checker (index.html) + a style switch for options A / B / C,
pre-filled with an example. Run after build.py. Optional arg: extra output path."""
import io, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
s = io.open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()

CSS = r"""<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800&display=swap" rel="stylesheet">
<style>
/* ===== concept switcher ===== */
#splash{display:none!important}
body{padding-top:52px}
.cx{position:fixed;top:0;left:0;right:0;z-index:400;display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 16px;background:#111;color:#fff;font:600 13px/1.2 Jost,system-ui,sans-serif}
.cx b{color:#FF8CC6;letter-spacing:.14em;text-transform:uppercase;font-size:11px;margin-right:4px}
.cx button{border:1px solid #555;background:#1c1c1c;color:#fff;border-radius:999px;padding:7px 14px;font:inherit;cursor:pointer}
.cx button[aria-pressed=true]{background:#E6007E;border-color:#E6007E}
.cx span{color:#aaa;font-weight:400;margin-left:6px}
.cx a{margin-left:auto;color:#fff}
@media (max-width:640px){body{padding-top:96px}.cx span{display:none}}
.journey{top:52px!important}
@media (max-width:640px){.journey{top:96px!important}}

/* ===== shared by A, B, C: Levy Report titles ===== */
:root[data-concept]{--mag:#D10A7D}
:root[data-concept] header .app{font-family:Montserrat,Arial,sans-serif;font-weight:700;letter-spacing:0;text-transform:none;font-size:15px;color:#fff}
/* form section titles: "01 The apprentice" in Montserrat with a magenta highlighter */
:root[data-concept] .step{font-family:Montserrat,Arial,sans-serif;font-weight:800;font-size:23px;letter-spacing:0;text-transform:none;color:var(--ink);position:relative;z-index:0;gap:10px;margin-bottom:18px}
:root[data-concept] .step b{display:inline;background:none;width:auto;height:auto;border-radius:0;color:var(--mag);font-size:23px;font-weight:800}
:root[data-concept] .step b::before{content:"0"}
:root[data-concept] .step::after{content:"";position:absolute;z-index:-1;left:36px;bottom:3px;width:70px;height:11px;background:var(--mag)}
:root[data-concept] .step b{position:relative}
/* result titles */
:root[data-concept] section.results h3{font-family:Montserrat,Arial,sans-serif;font-weight:800;font-size:22px;letter-spacing:0;text-transform:none;color:var(--ink);display:inline-block;position:relative;z-index:0;margin-bottom:16px}
:root[data-concept] section.results h3::before{content:"";position:absolute;z-index:-1;left:-8px;bottom:3px;width:46%;height:10px;background:#F5D9E6}
/* the verdict word */
:root[data-concept] .verdict .k{letter-spacing:.06em}
:root[data-concept] .verdict h2{font-family:Montserrat,Arial,sans-serif;font-weight:800;font-size:44px;letter-spacing:0;display:inline-block;position:relative;z-index:0;justify-self:start}
:root[data-concept] .verdict h2::before{content:"";position:absolute;z-index:-1;left:-10px;top:.12em;width:40%;height:.5em;background:var(--mag)}
/* journey: 01-04 numbers, magenta underline on the current step */
:root[data-concept] .journey a{border-radius:0;border:0;border-bottom:3px solid transparent;padding:10px 4px 8px;background:none!important;font-family:Montserrat,Arial,sans-serif;font-weight:700}
:root[data-concept] .journey .n{display:inline;border:0!important;background:none!important;width:auto;height:auto;color:var(--muted)!important;font-family:Montserrat,Arial,sans-serif;font-weight:800;font-size:14px}
:root[data-concept] .journey .n::before{content:"0"}
:root[data-concept] .journey li.res .n::before{content:""}
:root[data-concept] .journey li.done .n{color:var(--mag)!important}
:root[data-concept] .journey li.current a{border-bottom-color:var(--mag);color:var(--ink)}
:root[data-concept] .journey li + li::before{width:18px}
:root[data-concept] .journey li.res a{background:#000!important;color:#fff;padding:6px 12px;border:0}
:root[data-concept] .journey li.res .n{color:#fff!important}

/* ===== B and C: one black moment - the verdict ===== */
:root[data-concept=b] .verdict,:root[data-concept=c] .verdict{background:#000!important;border-color:#000!important;color:#eee}
:root[data-concept=b] .verdict h2,:root[data-concept=c] .verdict h2{color:#fff}
:root[data-concept=b] .verdict .k,:root[data-concept=c] .verdict .k{color:#bbb!important}
:root[data-concept=b] .verdict p,:root[data-concept=c] .verdict p{color:#eee}
:root[data-concept=b] .verdict b,:root[data-concept=c] .verdict b{color:#fff}

/* ===== C only: black slab banners open the form sections ===== */
:root[data-concept=c] .step{background:#000;color:#fff;display:inline-flex;height:46px;padding:0 56px 0 20px;margin:-20px 0 18px -20px;clip-path:polygon(0 0,calc(100% - 40px) 0,100% 100%,0 100%);font-size:19px}
:root[data-concept=c] .step b{font-size:19px}
:root[data-concept=c] .step::after{display:none}
</style>
</head>"""
i = s.index('</head>'); s = s[:i] + CSS + s[i + len('</head>'):]

JS = r"""<div class="cx" role="toolbar" aria-label="Concept options"><b>Concept</b>
  <button type="button" data-c="a">A · Titles only</button><button type="button" data-c="b">B · + black verdict</button><button type="button" data-c="c">C · + slab sections</button>
  <span id="cxNote"></span><a href="as-eligibility-r8v3k.html">Live checker ↗</a></div>
<script>
(function(){
  const notes={a:'Report titles and 01–04 numbering on the calm live layout.',b:'A, plus the verdict as the one black panel.',c:'B, plus black slab banners opening each form section.'};
  const set=c=>{ document.documentElement.setAttribute('data-concept',c); document.querySelectorAll('.cx button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.c===c))); document.getElementById('cxNote').textContent=notes[c]; };
  document.querySelector('.cx').addEventListener('click',e=>{ const b=e.target.closest('button[data-c]'); if(b) set(b.dataset.c); });
  set((location.hash||'#a').slice(1)||'a');
  document.documentElement.setAttribute('data-theme','light');
  window.addEventListener('load',async()=>{
    const v=(id,x)=>{ const e=document.getElementById(id); e.value=x; e.dispatchEvent(new Event('input')); };
    v('name','Jordan'); v('dob','2002-05-20'); v('start','2027-06-01'); document.getElementById('assumeAll').click();
    document.getElementById('jdText').value='Job title: Assistant Accountant\n\nMain duties:\n- Prepare monthly management accounts and journals, accruals and prepayments\n- Reconcile bank accounts, balance sheet and control accounts each month\n- Process supplier invoices and purchase ledger payments; resolve supplier queries\n- Support the year-end audit and VAT returns\n- Maintain the fixed asset register and assist with budgeting and forecasting\n- Use Excel and the finance system to produce reports for the finance team\n- Communicate with stakeholders across the business and maintain confidentiality of financial data';
    try{ await document.getElementById('jdGo').onclick(); const b=document.querySelector('#jdOut .jdr li button'); if(b) b.click(); }catch(e){}
    document.documentElement.setAttribute('data-theme','light'); window.scrollTo(0,0);
  });
})();
</script>
</body>"""
i = s.rindex('</body>'); s = s[:i] + JS + s[i + len('</body>'):]
s = s.replace('<title>Ann Summers Eligibility Checker</title>', '<title>Checker Style Options</title>', 1)
targets = [os.path.join(HERE, 'ui-options.html')] + sys.argv[1:]
for t in targets: io.open(t, 'w', encoding='utf-8').write(s)
print('built ui-options ->', ', '.join(targets))
