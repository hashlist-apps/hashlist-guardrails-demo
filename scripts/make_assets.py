#!/usr/bin/env python3
"""Regenerates assets/*.svg (animated, self-contained). Standard library only. Run: python scripts/make_assets.py
The checker-catch animation embeds the real output of guardrails/checker.py."""
import subprocess, sys, os, html
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

SANS='"Funnel Sans", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif'
MONO='"Martian Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'
PAPER="#EDEDE7"; PAPER2="#E3E4DD"; PAPER3="#D5D8CF"; INK="#151815"; INK2="#3C413C"; GAUGE="#6F756F"; RULE="#C9CCC4"
BOARD="#22362E"; BOARD2="#2B4238"; BRULE="#3D5448"; ONB="#E8E9E2"; ONB2="#A3B2A9"
RED="#BF3B2A"; REDD="#EC6B55"; OK="#7CC796"; FIX="#9FE0B3"; GB="#3E6A52"; NAVY="#0D1A2E"; BAR="#111A28"; CODE="#C9D4E6"; CM="#6F86A8"; KW="#E39A60"

def pct(t, loop): return round(t/loop*100, 3)

class Anim:
    """Collects keyframes. Base style of each element is its final frame (used for reduced motion)."""
    def __init__(self, loop):
        self.loop=loop; self.css=[]; self.n=0; self.fade=350; self.out=loop-450
    def vis(self, on, off=None, base=1.0, dy=0, peak=1.0):
        """opacity animation: hidden, fade in at `on`, optionally fade out at `off`, fade out for loop reset."""
        self.n+=1; name=f"a{self.n}"; L=self.loop; f=self.fade
        pts=[(0,0),(on,0),(on+f,peak)]
        if off is not None: pts+= [(off,peak),(off+f,0)]
        else: pts+= [(self.out,peak),(L-100,0)]
        if off is not None: pts+=[(L,0)]
        kf="".join(f"{pct(t,L)}%{{opacity:{v}" + (f";transform:translateY({dy if v==0 else 0}px)" if dy else "") + "}" for t,v in pts)
        self.css.append(f"@keyframes {name}{{{kf}}}")
        self.css.append(f".{name}{{animation:{name} {L}ms linear infinite}}")
        return name
    def raw(self, kf, extra=""):
        self.n+=1; name=f"a{self.n}"
        self.css.append(f"@keyframes {name}{{{kf}}}")
        self.css.append(f".{name}{{animation:{name} {self.loop}ms linear infinite;{extra}}}")
        return name
    def type(self, start, end, steps, width, vis_on=None):
        """returns (cover_class, cursor_class). cover is scaleX 1 -> 0 stepwise, cursor slides along."""
        L=self.loop; a,b=pct(start,L),pct(end,L)
        cov=self.raw(f"0%,{a}%{{transform:scaleX(1);animation-timing-function:steps({steps},end)}}{b}%{{transform:scaleX(0)}}{pct(L-300,L)}%{{transform:scaleX(0)}}{pct(L-150,L)}%,100%{{transform:scaleX(1)}}",
                     "transform-box:fill-box;transform-origin:right center")
        cur=self.raw(f"0%{{opacity:0}}{round(a-0.01,3)}%{{opacity:0}}{a}%{{opacity:1;transform:translateX(0);animation-timing-function:steps({steps},end)}}{b}%{{opacity:1;transform:translateX({width}px)}}{pct(end+250,L)}%,100%{{opacity:0;transform:translateX({width}px)}}")
        return cov, cur
    def style(self, base_css, reduced_css=""):
        return ("<style>"+base_css+"".join(self.css)+
                "@media (prefers-reduced-motion:reduce){[class^=a],[class*=\" a\"]{animation:none!important}}"+"</style>")

def fonts_css():
    return (f".sans{{font-family:{SANS}}}.mono{{font-family:{MONO}}}")

def esc(s): return html.escape(s, quote=False)

# ------------------------------------------------------------------ harness.svg
def harness():
    W,H=960,360
    A=Anim(9000)
    o=[]
    def card_cls(on): return A.vis(on, dy=4)
    eng=card_cls(200); arr1=A.vis(700); l1=A.vis(700)
    l2=A.vis(1000); l3=A.vis(1400)
    run1=A.vis(1800,2500+0)   # running, off at 2500 handled by fade
    fail=A.vis(2500,3950)
    run2=A.vis(4000,4650)
    ok=A.vis(4700)
    l4=A.vis(4000)
    # strike on line 3 : opacity drops to .45 and strike line scales in at 3200
    strike=A.raw(f"0%,{pct(3200,9000)}%{{transform:scaleX(0)}}{pct(3500,9000)}%{{transform:scaleX(1)}}{pct(8550,9000)}%{{transform:scaleX(1)}}{pct(8900,9000)}%,100%{{transform:scaleX(0)}}","transform-box:fill-box;transform-origin:left center")
    l3dim=A.raw(f"0%{{opacity:0}}{pct(1400,9000)}%{{opacity:0}}{pct(1750,9000)}%{{opacity:1}}{pct(3200,9000)}%{{opacity:1}}{pct(3500,9000)}%{{opacity:.45}}{pct(8550,9000)}%{{opacity:.45}}{pct(8900,9000)}%,100%{{opacity:0}}")
    arr2=A.vis(5300); res=A.vis(5700, dy=4)
    c2,k2=A.type(1000,1600,38,round(38*6.9))
    c3,k3=A.type(1400,2200,49,round(49*6.9))
    dots=A.raw("0%{opacity:.25}50%{opacity:1}100%{opacity:.25}", "animation-duration:900ms")
    css=fonts_css()+f"""
.sans{{font-family:{SANS}}}
.l1,.l2,.l3,.l3b,.l4,.arr,.eng,.res,.run,.fail,.ok{{opacity:1}}
.run,.fail{{opacity:0}}
.l3b{{opacity:.45}}
.cov{{fill:{NAVY}}}.cur{{fill:{CODE};opacity:0}}
.strike{{transform:scaleX(1)}}
"""
    css+= "".join([""])
    # element classes wired to animations
    css+=f".eng.{eng},.res.{res}{{}}"
    parts=[]
    P=parts.append
    P(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">')
    P('<title id="t">Hashlist harness loop (demo)</title>')
    P('<desc id="d">An engineer prompt goes through the AI agent and checker.py. The first draft fails rule R-001 because the board measured 410 us, not the datasheet 230 us. The fix passes and goes back to the engineer checked and fixed. Demo data, fictional project.</desc>')
    P(A.style(css))
    P(f'<rect width="{W}" height="{H}" rx="14" fill="{BOARD}"/>')
    P(f'<rect x="14" y="44" width="{W-28}" height="{H-84}" rx="8" fill="{BOARD2}" stroke="{BRULE}"/>')
    P(f'<text x="28" y="28" class="mono" font-size="10" letter-spacing=".6" fill="{ONB2}">HASHLIST / HARNESS ENGINEERING</text>')
    P(f'<text x="{W-28}" y="28" class="mono" text-anchor="end" font-size="10" letter-spacing=".6" fill="{ONB2}">PROMPT, AGENT, CHECKER, BACK CHECKED AND FIXED</text>')
    # engineer card
    P(f'<g class="eng {eng}" style="opacity:1"><rect x="30" y="92" width="190" height="168" rx="8" fill="{PAPER}"/>'
      f'<circle cx="52" cy="118" r="6" fill="none" stroke="{INK2}" stroke-width="1.4"/><path d="M41 138 q0-12 11-12 q11 0 11 12" fill="none" stroke="{INK2}" stroke-width="1.4"/>'
      f'<text x="72" y="126" class="mono" font-size="10" letter-spacing=".6" fill="{GAUGE}">ENGINEER</text>'
      f'<text class="sans" font-size="16" fill="{INK}"><tspan x="44" y="168">Add the 3V3 power-up</tspan><tspan x="44" y="190">delay before enabling</tspan><tspan x="44" y="212">the CAN transceiver</tspan></text></g>')
    # arrows
    def arrow(x,cls): return (f'<g class="arr {cls}"><line x1="{x}" y1="176" x2="{x+24}" y2="176" stroke="{ONB2}" stroke-width="1.5"/>'
                              f'<path d="M{x+24} 170 l8 6 l-8 6z" fill="{ONB2}"/></g>')
    P(arrow(222,arr1)); P(arrow(716,arr2))
    # IDE
    ix,iy,iw,ih=256,60,454,236
    P(f'<g><rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="6" fill="{NAVY}" stroke="#23324A"/>'
      f'<rect x="{ix}" y="{iy}" width="{iw}" height="24" rx="6" fill="{BAR}"/><rect x="{ix}" y="{iy+14}" width="{iw}" height="10" fill="{BAR}"/>'
      f'<circle cx="{ix+14}" cy="{iy+12}" r="3.5" fill="#23324A"/><circle cx="{ix+27}" cy="{iy+12}" r="3.5" fill="#23324A"/><circle cx="{ix+40}" cy="{iy+12}" r="3.5" fill="#23324A"/>'
      f'<text x="{ix+60}" y="{iy+16}" class="mono" font-size="9.5" fill="{CM}">src/bsp/power.c</text></g>')
    ly=[iy+54,iy+80,iy+106,iy+132]
    tx=ix+44
    for i,y in enumerate(ly,1):
        P(f'<text x="{ix+16}" y="{y}" class="mono" font-size="11" fill="#4A5A75">{i}</text>')
    CW=6.9
    import re as _re
    code=lambda y,cls,inner,extra="": f'<text x="{tx}" y="{y}" class="mono {cls}" font-size="11.5" textLength="{round(len(_re.sub("<[^>]+>","",inner).replace("&lt;","<"))*CW,1)}" lengthAdjust="spacingAndGlyphs" xml:space="preserve" {extra}>{inner}</text>'
    P(code(ly[0],f"l1 {l1}",f'<tspan fill="{CM}">/* 3V3 settle before CAN PHY enable */</tspan>'))
    P(code(ly[1],f"l2 {l2}",f'<tspan fill="{CM}">/* board log: pmic_3v3_settle = 410 us */</tspan>'))
    P(f'<g class="{l3dim}" style="opacity:.45">'+code(ly[2],"",f'<tspan fill="{KW}">#define</tspan> PMIC_3V3_SETTLE_US <tspan fill="{CODE}">230u</tspan>  <tspan fill="{CM}">/* datasheet */</tspan>',f'fill="{CODE}"')+'</g>')
    P(f'<rect class="{strike}" x="{tx}" y="{ly[2]-4}" width="{round(49*6.9)}" height="1.6" fill="{REDD}"/>')
    P(code(ly[3],f"l4 {l4}",f'<tspan fill="{FIX}">#define PMIC_3V3_SETTLE_US 410u  /* board rev B */</tspan>'))
    # typing covers (hide text in the typing window; line 2 and 3)
    for (y,cov,cur,w) in ((ly[1],c2,k2,round(38*6.9)),(ly[2],c3,k3,round(49*6.9))):
        P(f'<rect class="{cov}" x="{tx-2}" y="{y-14}" width="{w+16}" height="20" fill="{NAVY}" style="transform:scaleX(0)"/>')
        P(f'<rect class="{cur}" x="{tx}" y="{y-12}" width="1.8" height="15" fill="{CODE}" style="opacity:0"/>')
    # status bar
    sy=iy+ih-56
    P(f'<rect x="{ix+1}" y="{sy}" width="{iw-2}" height="55" rx="5" fill="{BAR}"/><line x1="{ix+1}" y1="{sy}" x2="{ix+iw-1}" y2="{sy}" stroke="#23324A"/>')
    P(f'<text x="{ix+16}" y="{sy+33}" class="mono" font-size="11" fill="{CM}">checker.py</text>')
    sx=ix+100
    st=lambda cls,fill,txt,extra="": f'<text x="{sx}" y="{sy+33}" class="mono {cls}" font-size="11.5" fill="{fill}" xml:space="preserve" {extra}>{txt}</text>'
    P(st(f"run {run1}",CODE,"running ···","style=\"opacity:0\""))
    P(st(f"fail {fail}",REDD,"fail · R-001 board measured 410 us","style=\"opacity:0\""))
    P(st(f"run {run2}",CODE,"running ···","style=\"opacity:0\""))
    P(st(f"ok {ok}",OK,"pass · all rules"))
    # result card
    P(f'<g class="res {res}"><rect x="750" y="92" width="180" height="168" rx="8" fill="{PAPER}" stroke="{GB}" stroke-width="1.6"/>'
      f'<text x="766" y="120" class="mono" font-size="9.5" letter-spacing=".6" fill="{GAUGE}">BACK TO THE ENGINEER</text>'
      f'<text class="sans" font-size="16" fill="{INK}"><tspan x="766" y="152">Checked and fixed,</tspan><tspan x="766" y="174">ready to review</tspan></text>'
      f'<path d="M766 220 l5 5 l10-11" fill="none" stroke="{GB}" stroke-width="2"/>'
      f'<text x="792" y="224" class="mono" font-size="11" fill="{GB}">all rules pass</text></g>')
    P(f'<text x="28" y="{H-16}" class="mono" font-size="9" letter-spacing=".5" fill="{ONB2}">DEMO DATA. FICTIONAL ECU, NOT A REAL PRODUCT.  HASHLIST.COM</text>')
    P('</svg>')
    return "\n".join(parts).replace("@@STYLE@@",A.style(css))


def run_checker(*args):
    env=dict(os.environ, PYTHONUTF8="1")
    r=subprocess.run([sys.executable,"guardrails/checker.py",*args],capture_output=True,text=True,encoding="utf-8",env=env)
    return r.stdout.rstrip("\n").split("\n"), r.returncode

# ------------------------------------------------------------- checker-catch.svg
def catch():
    W,H=1000,360; L=10000
    A=Anim(L)
    fail_lines,rc1=run_checker("--path","examples/HL-0001/fail")
    pass_lines,rc2=run_checker("--path","examples/HL-0001/pass")
    CWd=6.2
    cmd1="$ python guardrails/checker.py --path examples/HL-0001/fail"
    cmd2="$ python guardrails/checker.py --path examples/HL-0001/pass"
    note="# agent reads GA-001 (410 us) and fixes the draft"
    lines=[]  # (text, color, on_ms, type_info)
    y0=62; lh=17
    rows=[]
    rows.append((cmd1,CODE,300,("type",300,1500)))
    t=1900
    for i,l in enumerate(fail_lines):
        col=REDD if " fail " in l and l.startswith("checker.py") else (CM if l.strip().startswith(("at ","report","not:")) else CODE)
        if l.startswith("            golden"): col=FIX
        rows.append((l,col,t,None)); t+=230
    rows.append((f"exit {rc1}",REDD,t+200,None)); t+=900
    rows.append((note,CM,t,None)); t+=900
    rows.append((cmd2,CODE,t,("type",t,t+1300))); t+=1700
    for l in pass_lines:
        rows.append((l,OK,t,None)); t+=250
    rows.append((f"exit {rc2}",OK,t+150,None))
    css=fonts_css()
    P=[]
    P.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">')
    P.append('<title id="t">checker.py catches an AI error (demo)</title>')
    P.append('<desc id="d">checker.py runs on the AI draft for the PMIC settle time. It reports rule R-001, the golden answer 410 us and the failure report. After the fix it reports pass. Demo data, fictional project.</desc>')
    # chart timings
    bar1=A.raw(f"0%,{pct(1900,L)}%{{transform:scaleY(0)}}{pct(2700,L)}%{{transform:scaleY(1)}}{pct(L-450,L)}%{{transform:scaleY(1)}}{pct(L-100,L)}%,100%{{transform:scaleY(0)}}","transform-box:fill-box;transform-origin:bottom")
    lim=A.vis(1900)
    flag=A.vis(2900,t-1500 if False else 5400)
    bar1dim=A.raw(f"0%{{opacity:1}}{pct(5400,L)}%{{opacity:1}}{pct(5900,L)}%{{opacity:.35}}{pct(L-450,L)}%{{opacity:.35}}{pct(L-100,L)}%,100%{{opacity:1}}")
    bar2=A.raw(f"0%,{pct(t-250*len(pass_lines)-50,L)}%{{transform:scaleY(0)}}{pct(t+500,L)}%{{transform:scaleY(1)}}{pct(L-450,L)}%{{transform:scaleY(1)}}{pct(L-100,L)}%,100%{{transform:scaleY(0)}}","transform-box:fill-box;transform-origin:bottom")
    lab2=A.vis(t+300)
    passflag=A.vis(t+300)
    css_extra=""
    P.append('@@STYLE@@')
    P.append(f'<rect width="{W}" height="{H}" rx="14" fill="{BOARD}"/>')
    P.append(f'<text x="28" y="28" class="mono" font-size="10" letter-spacing=".6" fill="{ONB2}">HASHLIST / CHECKER.PY CATCHES THE ERROR</text>')
    P.append(f'<text x="{W-28}" y="28" class="mono" text-anchor="end" font-size="10" letter-spacing=".6" fill="{ONB2}">DEMO DATA. FICTIONAL ECU.</text>')
    # terminal
    tx0,ty0,tw,th=20,44,700,290
    P.append(f'<rect x="{tx0}" y="{ty0}" width="{tw}" height="{th}" rx="8" fill="{NAVY}" stroke="#23324A"/>')
    P.append(f'<rect x="{tx0}" y="{ty0}" width="{tw}" height="22" rx="8" fill="{BAR}"/><rect x="{tx0}" y="{ty0+12}" width="{tw}" height="10" fill="{BAR}"/>')
    P.append(f'<text x="{tx0+14}" y="{ty0+15}" class="mono" font-size="9.5" fill="{CM}">terminal</text>')
    y=y0+22
    for text,col,on,ty in rows:
        txt=esc(text).replace("  ","  ")
        n=len(text)
        tl=f'textLength="{round(n*CWd,1)}" lengthAdjust="spacingAndGlyphs"' if n>0 else ""
        cls=A.vis(on) if ty is None else None
        if ty is None:
            P.append(f'<text x="{tx0+14}" y="{y}" class="mono {cls}" font-size="10.5" fill="{col}" {tl} xml:space="preserve">{esc(text)}</text>')
        else:
            _,a,b=ty
            cov,cur=A.type(a,b,n,round(n*CWd))
            P.append(f'<text x="{tx0+14}" y="{y}" class="mono" font-size="10.5" fill="{col}" {tl} xml:space="preserve">{esc(text)}</text>')
            P.append(f'<rect class="{cov}" x="{tx0+12}" y="{y-12}" width="{round(n*CWd)+14}" height="16" fill="{NAVY}" style="transform:scaleX(0)"/>')
            P.append(f'<rect class="{cur}" x="{tx0+14}" y="{y-11}" width="1.8" height="13" fill="{CODE}" style="opacity:0"/>')
        y+=lh
    # instrument card
    cx,cy,cw,ch=736,44,244,290
    P.append(f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="8" fill="{PAPER}"/>')
    P.append(f'<text x="{cx+16}" y="{cy+24}" class="mono" font-size="9.5" letter-spacing=".6" fill="{GAUGE}">PMIC 3V3 SETTLE, US</text>')
    base=cy+ch-40; top=cy+50; scale=(base-top)/500
    for v in (0,100,200,300,400,500):
        yy=base-v*scale
        P.append(f'<line x1="{cx+44}" y1="{yy:.1f}" x2="{cx+cw-16}" y2="{yy:.1f}" stroke="{RULE}" stroke-width="1"/>')
        P.append(f'<text x="{cx+38}" y="{yy+3:.1f}" text-anchor="end" class="mono" font-size="8.5" fill="{GAUGE}">{v}</text>')
    h1=230*scale; h2=410*scale
    P.append(f'<rect class="{bar1} {bar1dim}" x="{cx+58}" y="{base-h1:.1f}" width="60" height="{h1:.1f}" fill="{RED}" style="transform:scaleY(1)"/>')
    P.append(f'<rect class="{bar2}" x="{cx+142}" y="{base-h2:.1f}" width="60" height="{h2:.1f}" fill="{GB}"/>')
    P.append(f'<text x="{cx+88}" y="{base-h1-8:.1f}" text-anchor="middle" class="mono" font-size="10" fill="{RED}">230</text>')
    P.append(f'<text x="{cx+172}" y="{base-h2+20:.1f}" text-anchor="middle" class="mono {lab2}" font-size="11" fill="{PAPER}">410</text>')
    P.append(f'<text x="{cx+88}" y="{base+16}" text-anchor="middle" class="mono" font-size="8.5" letter-spacing=".4" fill="{INK2}">AI DRAFT</text>')
    P.append(f'<text x="{cx+172}" y="{base+16}" text-anchor="middle" class="mono" font-size="8.5" letter-spacing=".4" fill="{INK2}">FIXED</text>')
    ly_=base-410*scale
    P.append(f'<g class="{lim}"><line x1="{cx+44}" y1="{ly_:.1f}" x2="{cx+cw-16}" y2="{ly_:.1f}" stroke="{RED}" stroke-width="1.4" stroke-dasharray="5 3"/>'
             f'<text x="{cx+48}" y="{ly_-5:.1f}" text-anchor="start" class="mono" font-size="8.5" letter-spacing=".4" fill="{RED}">BOARD MEASURED 410</text></g>')
    P.append(f'<g class="{flag}"><rect x="{cx+46}" y="{cy+ch-96:.0f}" width="84" height="20" rx="3" fill="{RED}"/><text x="{cx+88}" y="{cy+ch-82:.0f}" text-anchor="middle" class="mono" font-size="10" letter-spacing=".6" fill="{PAPER}">R-001 FAIL</text></g>')
    P.append(f'<g class="{passflag}"><rect x="{cx+135}" y="{cy+ch-96:.0f}" width="74" height="20" rx="3" fill="{GB}"/><text x="{cx+172}" y="{cy+ch-82:.0f}" text-anchor="middle" class="mono" font-size="10" letter-spacing=".6" fill="{PAPER}">PASS</text></g>')
    P.append('</svg>')
    return "\n".join(P).replace("@@STYLE@@",A.style(fonts_css()))

# ------------------------------------------------------------------ timeline.svg
def timeline():
    W,H=1000,456; L=12000
    A=Anim(L)
    P=[]
    P.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">')
    P.append('<title id="t">Without and with guardrails, the PMIC settle time case (demo)</title>')
    P.append('<desc id="d">Top row: an agent reads board data of 410 us, then the datasheet 230 us, checks 230 us with a test that has 230 us built in, and answers 230 us, which is wrong. Bottom row: with guardrails the same start, then rules and golden answers, then the checker rejects the test, and the agent answers 410 us. Demo data, fictional project.</desc>')
    P.append('@@STYLE@@')
    P.append(f'<rect width="{W}" height="{H}" rx="14" fill="{PAPER}"/>')
    P.append(f'<text x="28" y="30" class="mono" font-size="10" letter-spacing=".6" fill="{GAUGE}">HASHLIST / WHERE THE GUARDRAIL ACTS, INSIDE THE AGENT\'S REASONING</text>')
    P.append(f'<text x="{W-28}" y="30" class="mono" text-anchor="end" font-size="10" letter-spacing=".6" fill="{GAUGE}">DEMO DATA. FICTIONAL ECU.</text>')
    bw,gap,x0=222,16,28
    def box(i,y,label,lines,style,on,tag=None):
        x=x0+i*(bw+gap)
        fill,stroke,txt,lab={"plain":(PAPER2,RULE,INK,GAUGE),"bad":("#F6E3DF",RED,RED,RED),"guard":(INK,INK,PAPER,ONB2),"ok":("#E3EFE7",GB,INK,GB)}[style]
        cls=A.vis(on,dy=4)
        g=[f'<g class="{cls}"><rect x="{x}" y="{y}" width="{bw}" height="108" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="{1.6 if style in("bad","ok") else 1}"/>',
           f'<text x="{x+14}" y="{y+24}" class="mono" font-size="10" letter-spacing=".6" fill="{lab}">{label}</text>']
        for k,ln in enumerate(lines):
            wt = ' font-weight="600"' if style in ("bad","ok") else ""
            g.append(f'<text x="{x+14}" y="{y+50+k*20}" class="sans" font-size="15" fill="{txt}"{wt}>{esc(ln)}</text>')
        g.append('</g>')
        P.append("".join(g))
    y1,y2=74,262
    P.append(f'<text x="{x0}" y="{y1-10}" class="mono" font-size="10" letter-spacing=".6" fill="{INK2}">WITHOUT GUARDRAILS</text>')
    P.append(f'<text x="{x0}" y="{y2-10}" class="mono" font-size="10" letter-spacing=".6" fill="{INK2}">WITH HASHLIST GUARDRAILS</text>')
    box(0,y1,"1.1 MIN",["Reads the board's own","test data 410 µs"],"plain",300)
    box(1,y1,"1.5 MIN",["Reads datasheet:","230 µs"],"plain",1500)
    box(2,y1,"4.7 MIN",["Checks 230 µs with a test","that has 230 µs built in"],"plain",2700)
    box(3,y1,"11.8 MIN",["Answers 230 µs.","Correct: 410 µs."],"bad",4200)
    box(0,y2,"SAME START",["Reads the board's own","test data 410 µs"],"plain",700)
    box(1,y2,"RULES + ANSWERS",["Measured data on this","board beats the datasheet"],"guard",4700)
    box(2,y2,"CHECKER.PY",["Rejects a test that only","repeats the datasheet"],"guard",5600)
    box(3,y2,"ANSWER",["Answers 410 µs, from","the board's test data"],"ok",6700)
    # red arrow
    ax=x0+1*(bw+gap)+bw+gap//2+0
    arr=A.vis(3300)
    P.append(f'<g class="{arr}"><line x1="{ax}" y1="{y1+112}" x2="{ax}" y2="{y2-30}" stroke="{RED}" stroke-width="2"/><path d="M{ax-6} {y2-34} l6 10 l6 -10z" fill="{RED}"/>'
             f'<text x="{ax+12}" y="{(y1+y2)//2+58}" class="sans" font-size="13" fill="{RED}" font-style="italic">The guardrail steps in while the agent reasons</text></g>')
    lab=A.vis(7500)
    P.append(f'<g class="{lab}"><rect x="{x0}" y="{y2+124}" width="{W-2*x0}" height="58" rx="6" fill="{INK}"/>'
             f'<text x="{x0+16}" y="{y2+147}" class="mono" font-size="11" letter-spacing=".6" fill="{PAPER}">DEMO RESULT: 8 MODELS x 3 ATTEMPTS, 24 OF 24 RIGHT WITH THE GUARDRAIL FILES</text>'
             f'<text x="{x0+16}" y="{y2+167}" class="mono" font-size="10" letter-spacing=".5" fill="{ONB2}">HOW IT WORKS: agent reads rules.md, checks the golden answer database, verifies its own output</text></g>')
    P.append('</svg>')
    return "\n".join(P).replace("@@STYLE@@",A.style(fonts_css()))

# ---------------------------------------------------------------------- loop.svg
def loop():
    import math
    W,H=900,870; L=12000
    A=Anim(L)
    cx,cy,R=450,415,225
    steps=[("Capture","Your engineers report an AI failure","YOUR TEAM"),
           ("Reconstruct","Experts recreate the environment","HASHLIST"),
           ("Evaluate","The failure is re-run across AI models","HASHLIST"),
           ("Golden set","The correct answer and checker are written","HASHLIST"),
           ("Integrate","Rules and checker go into your toolchain","HASHLIST"),
           ("Audit","Your engineers re-run the prompt to check the fix","YOUR TEAM")]
    P=[]
    P.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">')
    P.append('<title id="t">The six step loop: guardrails grow with every failure (demo)</title>')
    P.append('<desc id="d">A ring of six steps: capture, reconstruct, evaluate, golden set, integrate, audit. A dot travels around the ring and each step fills as it passes. The counter in the centre grows from 1 to 10 fixed failures. Demo data.</desc>')
    # prepare dot rotation keyframes: node k reached at 2000*(k-1) ms
    dot=A.raw(f"0%{{transform:rotate(0deg)}}{pct(10000,L)}%{{transform:rotate(300deg)}}{pct(L-100,L)}%,100%{{transform:rotate(360deg)}}","transform-box:view-box;transform-origin:%dpx %dpx"%(cx,cy))
    P.append('@@STYLE@@')
    P.append(f'<rect width="{W}" height="{H}" rx="14" fill="{PAPER}"/>')
    P.append(f'<text x="28" y="30" class="mono" font-size="10" letter-spacing=".6" fill="{GAUGE}">HASHLIST / THE LOOP: EACH FAILURE IS FIXED ONCE, THE FIX APPLIES ACROSS THE ORGANISATION</text>')
    P.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{RULE}" stroke-width="2" stroke-dasharray="3 6"/>')
    nodes=[]
    for i,(nm,desc,who) in enumerate(steps):
        ang=math.radians(-90+60*i); x=cx+R*math.cos(ang); y=cy+R*math.sin(ang)
        mine=(who=="YOUR TEAM")
        P.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="34" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>')
        P.append(f'<text x="{x:.1f}" y="{y+9:.1f}" text-anchor="middle" class="mono" font-size="26" fill="{INK}">{i+1}</text>')
        fill=A.raw(f"0%{{opacity:0}}{pct(max(2000*i-60,0),L)}%{{opacity:0}}{pct(2000*i+250,L)}%{{opacity:1}}{pct(L-450,L)}%{{opacity:1}}{pct(L-100,L)}%,100%{{opacity:0}}")
        P.append(f'<g class="{fill}" style="opacity:1"><circle cx="{x:.1f}" cy="{y:.1f}" r="34" fill="{INK}"/><text x="{x:.1f}" y="{y+9:.1f}" text-anchor="middle" class="mono" font-size="26" fill="{PAPER}">{i+1}</text></g>')
        # labels: tag, name, description
        words=desc.split(); lines=[]; cur=""
        for w in words:
            if len(cur)+len(w)+1>26 and cur: lines.append(cur); cur=w
            else: cur=(cur+" "+w).strip()
        lines.append(cur)
        tag_col=INK if mine else GB
        total=14+26+16*len(lines)
        if i==0: lx,anchor,top=x,"middle",y-46-total
        elif i==3: lx,anchor,top=x,"middle",y+52
        elif i in (1,2): lx,anchor,top=x+50,"start",y-total/2
        else: lx,anchor,top=x-50,"end",y-total/2
        P.append(f'<text x="{lx:.1f}" y="{top+10:.1f}" text-anchor="{anchor}" class="mono" font-size="9" letter-spacing=".6" fill="{tag_col}">{who}</text>')
        P.append(f'<text x="{lx:.1f}" y="{top+36:.1f}" text-anchor="{anchor}" class="sans" font-size="20" font-weight="600" fill="{INK}">{nm}</text>')
        for k,ln in enumerate(lines):
            P.append(f'<text x="{lx:.1f}" y="{top+56+16*k:.1f}" text-anchor="{anchor}" class="sans" font-size="13" fill="{INK2}">{esc(ln)}</text>')
    # dot
    P.append(f'<g class="{dot}"><circle cx="{cx}" cy="{cy-R}" r="9" fill="{RED}"/><circle cx="{cx}" cy="{cy-R}" r="15" fill="none" stroke="{RED}" stroke-opacity=".35" stroke-width="2"/></g>')
    # centre
    P.append(f'<text x="{cx}" y="{cy-62}" text-anchor="middle" class="sans" font-size="21" font-weight="600" fill="{INK}">Guardrails grow</text>')
    P.append(f'<text x="{cx}" y="{cy-38}" text-anchor="middle" class="sans" font-size="21" font-weight="600" fill="{INK}">with every failure</text>')
    for n in range(1,11):
        on=(n-1)*1100; off=n*1100
        nm=A.vis(on, off if n<10 else None)
        P.append(f'<text class="mono {nm}" x="{cx}" y="{cy+40}" text-anchor="middle" style="opacity:{1 if n==10 else 0}" font-size="64" fill="{INK}">{n}</text>')
    P.append(f'<text x="{cx}" y="{cy+72}" text-anchor="middle" class="mono" font-size="10" letter-spacing=".6" fill="{GAUGE}">RULES, EACH LINKED TO ITS FAILURE</text>')
    P.append(f'<text x="{cx}" y="{cy+90}" text-anchor="middle" class="mono" font-size="10" letter-spacing=".6" fill="{GAUGE}">(DEMO DATA)</text>')
    P.append(f'<rect x="28" y="{H-62}" width="{W-56}" height="34" rx="6" fill="{INK}"/>')
    P.append(f'<text x="{W//2}" y="{H-40}" text-anchor="middle" class="mono" font-size="10.5" letter-spacing=".5" fill="{PAPER}">YOUR ENGINEERS SPEND MINUTES ON STEPS 1 AND 6. HASHLIST CARRIES STEPS 2 TO 5.</text>')
    P.append('</svg>')
    return "\n".join(P).replace("@@STYLE@@",A.style(fonts_css()))

def write(name, text):
    open(f"assets/{name}","w",encoding="utf-8").write(text)

if __name__=="__main__":
    write("harness.svg", harness())
    write("checker-catch.svg", catch())
    write("timeline.svg", timeline())
    write("loop.svg", loop())
