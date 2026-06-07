from __future__ import annotations

import json
from typing import Any, Dict


def html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _nav(active: str) -> str:
    items = [
        ("avatar", "Avatar"),
        ("agents", "Agents"),
        ("terminal", "Terminal"),
        ("plan", "Plan"),
        ("repo", "Repository"),
        ("memory", "Memory"),
        ("browser", "Browser"),
        ("tests", "Tests"),
        ("git", "Git"),
        ("status", "Status"),
    ]
    out = []
    for key, label in items:
        cls = "active" if key == active else ""
        href = "/" if key == "avatar" else f"/{key}"
        out.append(f'<a class="nav-link {cls}" href="{href}">{label}</a>')
    return "".join(out)


def _styles(theme: str) -> str:
    accent = "#a78bfa" if theme == "violet" else "#34d399" if theme == "emerald" else "#22d3ee"
    css = """
    :root{--panel:rgba(8,12,20,.66);--text:#e5e7eb;--muted:#93a3b8;--accent:__ACCENT__;--line:rgba(255,255,255,.08);--glass:rgba(255,255,255,.06)}
    *{box-sizing:border-box} body{margin:0;font-family:"JetBrains Mono","SFMono-Regular","Consolas","Liberation Mono",ui-monospace,monospace;background:
      radial-gradient(circle at 15% 20%, rgba(34,211,238,.22), transparent 18%),
      radial-gradient(circle at 85% 20%, rgba(167,139,250,.18), transparent 20%),
      radial-gradient(circle at 50% 70%, rgba(52,211,153,.16), transparent 24%),
      radial-gradient(circle at 50% 50%, rgba(255,255,255,.05), transparent 40%),
      linear-gradient(180deg,#02040a,#060912 42%,#090d15 72%,#040507);color:var(--text);min-height:100vh;overflow:hidden;position:relative}
    body::before{content:"";position:fixed;inset:0;background-image:
      radial-gradient(rgba(255,255,255,.08) 1px, transparent 1px),
      linear-gradient(rgba(255,255,255,.02) 1px, transparent 1px);
      background-size:28px 28px, 100% 56px;mask-image:radial-gradient(circle at center, rgba(0,0,0,.85), transparent 88%);pointer-events:none;opacity:.22}
    .app{display:grid;grid-template-columns:96px 1fr;height:100vh;padding:16px;gap:16px}
    .sidebar{background:linear-gradient(180deg, rgba(8,12,20,.88), rgba(8,12,20,.52));backdrop-filter:blur(18px);border:1px solid var(--line);border-radius:22px;padding:14px;display:flex;flex-direction:column;gap:10px;box-shadow:0 30px 80px rgba(0,0,0,.35)}
    .brand{width:56px;height:56px;border-radius:18px;background:
      radial-gradient(circle at 30% 25%, rgba(255,255,255,.35), transparent 28%),
      linear-gradient(135deg,var(--accent),#4f46e5 56%, #0f172a);display:grid;place-items:center;font-weight:800;letter-spacing:.08em;box-shadow:0 16px 34px rgba(34,211,238,.18)}
    .nav-link{display:block;padding:12px 10px;border-radius:14px;color:var(--muted);text-decoration:none;border:1px solid transparent;text-align:center;font-size:.78rem;letter-spacing:.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .nav-link.active,.nav-link:hover{background:rgba(34,211,238,.12);border-color:rgba(34,211,238,.24);color:#fff}
    .main{display:grid;grid-template-rows:68px 1fr;gap:16px;min-width:0;position:relative}
    .main::after{content:"";position:fixed;inset:0;background:
      radial-gradient(circle at 50% 12%, rgba(34,211,238,.08), transparent 18%),
      radial-gradient(circle at 50% 100%, rgba(167,139,250,.08), transparent 22%);
      pointer-events:none;mix-blend-mode:screen;opacity:.85}
    .topbar{background:linear-gradient(180deg, rgba(10,14,24,.82), rgba(10,14,24,.55));backdrop-filter:blur(18px);border:1px solid var(--line);border-radius:8px;padding:0 20px;display:grid;grid-template-columns:minmax(260px,1fr) minmax(0,2fr);gap:16px;align-items:center;box-shadow:0 18px 50px rgba(0,0,0,.2);font-weight:600;letter-spacing:.02em;min-width:0}
    .topbar>div{min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.topbar>div:last-child{text-align:right}
    .content{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:16px;min-height:0;overflow:auto;padding-bottom:8px;align-content:start}
    .panel{position:relative;background:linear-gradient(180deg, rgba(10,14,24,.78), rgba(10,14,24,.52));backdrop-filter:blur(18px);border:1px solid var(--line);border-radius:8px;padding:18px;overflow:hidden;min-height:0;box-shadow:0 22px 70px rgba(0,0,0,.2)}
    .panel::before{content:"";position:absolute;inset:0;border-radius:inherit;background:linear-gradient(135deg, rgba(255,255,255,.09), transparent 30%, transparent 70%, rgba(255,255,255,.04));pointer-events:none;opacity:.6}
    .span-12{grid-column:span 12} .span-8{grid-column:span 8} .span-6{grid-column:span 6} .span-4{grid-column:span 4} .span-3{grid-column:span 3}
    html,body,.app,.main,.content,.panel,.sidebar,.topbar,button,input,textarea,select,.tool-pill,.feed-item,.memory-item,.console,.nav-link,.label,.value,.muted{font-family:"JetBrains Mono","SFMono-Regular","Consolas","Liberation Mono",ui-monospace,monospace}
    .avatar{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;min-height:560px;position:relative;overflow:hidden;padding:72px 24px 24px}
    .command-center{grid-column:span 12;display:grid;grid-template-columns:minmax(460px,1.25fr) minmax(360px,.75fr);gap:16px;min-height:calc(100vh - 116px);align-items:start}
    .avatar-stage{position:relative;height:calc(100vh - 116px);min-height:520px;overflow:hidden;border:1px solid var(--line);border-radius:8px;background:linear-gradient(180deg,rgba(8,12,20,.62),rgba(3,7,13,.86));display:flex;align-items:center;justify-content:center;padding:20px}
    .avatar-stage .avatar{width:100%;height:100%;min-height:0;padding:96px 20px 20px;background:transparent;border:0;box-shadow:none;justify-content:flex-end}
    .avatar-stage .orb{width:min(390px,calc(100% - 56px),calc(100vh - 260px));z-index:1}
    .avatar-stage .bubble{position:absolute;right:22px;top:22px;max-width:min(360px,40%);max-height:150px}
    .ops-column{display:grid;grid-template-rows:auto auto minmax(0,1fr);gap:12px;height:calc(100vh - 116px);min-height:520px;min-width:0}
    .query-box{display:grid;grid-template-columns:1fr auto;gap:10px}
    .query-box input{height:48px}
    .status-row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
    .model-pill{display:flex;align-items:center;justify-content:space-between;gap:12px;border:1px solid var(--line);border-radius:8px;padding:10px 12px;background:rgba(255,255,255,.035);min-width:0}
    .model-pill strong,.model-pill span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .agent-roster{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
    .agent-chip{border:1px solid var(--line);border-radius:8px;padding:10px;background:rgba(255,255,255,.035);min-width:0}
    .agent-chip strong{display:block;color:#fff;font-size:.84rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .agent-chip span{display:block;color:var(--muted);font-size:.74rem;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .compact-scroll{max-height:100%;overflow:auto}
    .avatar::before{content:"";position:absolute;inset:10% 14%;background:
      radial-gradient(circle at 50% 45%, rgba(34,211,238,.18), transparent 26%),
      radial-gradient(circle at 50% 50%, rgba(167,139,250,.12), transparent 36%);
      filter:blur(8px);animation:ambientPulse 6s ease-in-out infinite;pointer-events:none}
    .avatar::after{content:"";position:absolute;inset:auto 12% 4% 12%;height:12%;background:radial-gradient(ellipse at center, rgba(34,211,238,.22), transparent 68%);filter:blur(18px);opacity:.9;pointer-events:none}
    .scene{position:absolute;inset:0;pointer-events:none;overflow:hidden}
    .scene .grid{position:absolute;inset:8% 6%;background:
      linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,.04) 1px, transparent 1px);
      background-size:42px 42px;mask-image:radial-gradient(circle at center, black 38%, transparent 78%);opacity:.22;transform:perspective(800px) rotateX(68deg) translateY(18%)}
    .scene .orbit{position:absolute;left:50%;top:50%;width:min(680px,96%);aspect-ratio:1/1;border-radius:50%;transform:translate(-50%,-50%);border:1px solid rgba(34,211,238,.16);box-shadow:inset 0 0 50px rgba(34,211,238,.08),0 0 80px rgba(34,211,238,.06);animation:spin 34s linear infinite}
    .scene .orbit.two{width:min(540px,78%);border-color:rgba(167,139,250,.12);animation-direction:reverse;animation-duration:26s}
    .scene .scan{position:absolute;left:0;right:0;top:50%;height:2px;background:linear-gradient(90deg,transparent,rgba(52,211,153,.9),transparent);filter:blur(.1px);box-shadow:0 0 24px rgba(52,211,153,.65);animation:scan 4.8s ease-in-out infinite}
    .scene .dots{position:absolute;inset:0;background-image:radial-gradient(rgba(255,255,255,.08) 1px, transparent 1px);background-size:18px 18px;opacity:.12}
    .orb{width:min(560px,100%);aspect-ratio:1/1;border-radius:50%;position:relative;background:
      radial-gradient(circle at 30% 25%,rgba(255,255,255,.28),transparent 22%),
      radial-gradient(circle at 50% 60%, rgba(34,211,238,.08), transparent 34%),
      linear-gradient(160deg,#0f172a,#07101b 48%,#0a1020 72%,#111827);box-shadow:0 34px 90px rgba(0,0,0,.55),inset 0 0 44px rgba(34,211,238,.18),0 0 90px rgba(34,211,238,.08);transform:perspective(1200px) rotateX(10deg) rotateY(-14deg);transition:transform .18s ease;animation:idleFloat 4.9s ease-in-out infinite}
    .orb::before{content:"";position:absolute;inset:6%;border-radius:50%;border:1px solid rgba(255,255,255,.08);box-shadow:inset 0 0 20px rgba(255,255,255,.02), 0 0 60px rgba(34,211,238,.1);pointer-events:none}
    .orb::after{content:"";position:absolute;inset:-8%;border-radius:50%;background:radial-gradient(circle at 50% 50%,rgba(34,211,238,.18),transparent 56%);opacity:.95;filter:blur(16px);pointer-events:none}
    .face{position:absolute;inset:0;border-radius:50%;overflow:hidden;border:1px solid rgba(255,255,255,.12)}
    .hair{position:absolute;left:50%;top:7%;width:62%;height:24%;transform:translateX(-50%);background:
      radial-gradient(ellipse at 50% 100%, rgba(15,23,42,.96) 0 56%, transparent 57%),
      linear-gradient(180deg, rgba(6,10,18,.98), rgba(18,27,44,.88));border-radius:48% 48% 46% 46%/72% 72% 42% 42%;box-shadow:0 12px 30px rgba(0,0,0,.35)}
    .brow{position:absolute;top:27%;width:72px;height:12px;border-top:4px solid rgba(226,232,240,.78);border-radius:50%}
    .brow.left{left:30%;transform:rotate(-8deg)} .brow.right{right:30%;transform:rotate(8deg)}
    .eye{position:absolute;width:54px;height:54px;border-radius:50%;background:
      radial-gradient(circle at 38% 32%, rgba(255,255,255,.8) 0 12%, rgba(255,255,255,.1) 18%, rgba(255,255,255,.04) 44%, rgba(5,10,20,.78) 70%),
      radial-gradient(circle at 50% 50%, rgba(34,211,238,.12), transparent 55%);
      top:31%;overflow:hidden;border:1px solid rgba(255,255,255,.18);box-shadow:0 0 22px rgba(34,211,238,.12), inset 0 0 16px rgba(255,255,255,.05)} .eye.left{left:35%} .eye.right{right:35%}
    .eye::after{content:"";position:absolute;inset:8%;border-radius:50%;border:1px solid rgba(255,255,255,.08);opacity:.7}
    .pupil{position:absolute;inset:10px;border-radius:50%;background:
      radial-gradient(circle at 30% 28%,#f8fbff 0 12%,#38bdf8 14% 20%,#0f172a 21% 54%,#000 56% 100%);
      box-shadow:0 0 12px rgba(56,189,248,.18), inset 0 0 12px rgba(255,255,255,.06);transform:translate(var(--px,0px),var(--py,0px));transition:transform .08s linear}
    .nose{position:absolute;left:50%;top:46%;width:18px;height:40px;transform:translateX(-50%);border-left:2px solid rgba(255,255,255,.12);border-right:2px solid rgba(255,255,255,.06);border-radius:12px;opacity:.45}
    .cheek{position:absolute;top:49%;width:48px;height:24px;border-radius:50%;background:radial-gradient(circle, rgba(255,255,255,.08), transparent 70%);filter:blur(1px);opacity:.55}
    .cheek.left{left:23%} .cheek.right{right:23%}
    .mouth{position:absolute;left:50%;top:58%;width:110px;height:24px;transform:translateX(-50%);border-radius:0 0 34px 34px;background:linear-gradient(180deg,rgba(10,16,26,.12),rgba(10,16,26,.88));border-bottom:2px solid rgba(255,255,255,.16);box-shadow:0 0 18px rgba(34,211,238,.06);transition:all .2s ease}
    .mouth.smile{height:14px;border-bottom-width:3px;border-radius:0 0 32px 32px;box-shadow:0 0 12px rgba(52,211,153,.22)}
    .neck{position:absolute;left:50%;bottom:-2%;width:20%;height:15%;transform:translateX(-50%);border-radius:0 0 24px 24px;background:linear-gradient(180deg,#101a2a,#070b11);box-shadow:inset 0 0 22px rgba(0,0,0,.25)}
    .shoulders{position:absolute;left:50%;bottom:-12%;width:78%;height:28%;transform:translateX(-50%);border-radius:42% 42% 20% 20%;background:linear-gradient(180deg,rgba(8,12,19,.1),rgba(3,7,13,.92) 36%,rgba(3,7,13,.98));box-shadow:0 -24px 64px rgba(0,0,0,.45),inset 0 0 18px rgba(255,255,255,.04)}
    .chest{position:absolute;left:50%;bottom:-4%;width:44%;height:22%;transform:translateX(-50%);border-radius:42px;background:linear-gradient(180deg,rgba(34,211,238,.08),rgba(255,255,255,.02));border:1px solid rgba(255,255,255,.05)}
    .hand{position:absolute;bottom:2%;width:12%;height:18%;border-radius:40% 40% 50% 50%;background:linear-gradient(180deg,rgba(255,255,255,.05),rgba(7,11,18,.75));filter:blur(.1px);opacity:.72}
    .hand.left{left:5%;transform:rotate(12deg)} .hand.right{right:5%;transform:rotate(-12deg)}
    .rings{position:absolute;inset:-10%;pointer-events:none;opacity:.75} .ring{position:absolute;inset:12%;border-radius:50%;border:1px solid rgba(34,211,238,.2);box-shadow:inset 0 0 20px rgba(34,211,238,.05);animation:spin 18s linear infinite} .ring.two{inset:18%;animation-duration:22s;animation-direction:reverse} .ring.three{inset:24%;animation-duration:28s}
    .particles{position:absolute;inset:0;pointer-events:none;overflow:hidden} .particle{position:absolute;width:6px;height:6px;border-radius:999px;background:rgba(34,211,238,.8);filter:blur(.2px);opacity:.0;animation:floatUp 3.2s ease-in-out infinite}
    @keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
    @keyframes floatUp{0%{transform:translateY(12px) scale(.7);opacity:0}20%{opacity:.7}60%{opacity:.35}100%{transform:translateY(-80px) scale(1.2);opacity:0}}
    @keyframes idleFloat{0%,100%{transform:perspective(1200px) rotateX(10deg) rotateY(-14deg) translateY(0)}50%{transform:perspective(1200px) rotateX(11deg) rotateY(-13deg) translateY(-8px)}}
    @keyframes ambientPulse{0%,100%{opacity:.5;transform:scale(.98)}50%{opacity:.92;transform:scale(1.04)}}
    @keyframes scan{0%{transform:translateY(-180px);opacity:.1}35%{opacity:.9}50%{transform:translateY(0);opacity:.8}100%{transform:translateY(180px);opacity:.1}}
    .state-thinking .eye,.state-planning .eye,.state-researching .eye,.state-coding .eye,.state-testing .eye,.state-debugging .eye{box-shadow:0 0 18px rgba(34,211,238,.12)}
    .state-thinking .rings,.state-planning .rings,.state-researching .rings,.state-coding .rings,.state-testing .rings,.state-debugging .rings{opacity:1}
    .state-success .orb{box-shadow:0 30px 70px rgba(0,0,0,.45),inset 0 0 32px rgba(52,211,153,.18),0 0 40px rgba(52,211,153,.2)}
    .state-error .orb{box-shadow:0 30px 70px rgba(0,0,0,.45),inset 0 0 32px rgba(251,113,133,.15),0 0 40px rgba(251,113,133,.12)}
    .state-thinking .mouth{transform:translateX(-50%) scaleX(.92)}
    .state-coding .pupil{box-shadow:0 0 18px rgba(56,189,248,.24), inset 0 0 12px rgba(255,255,255,.08)}
    .state-testing .orb{filter:saturate(1.05)}
    .state-thinking .brow{transform:translateY(-2px)}
    .state-debugging .brow.left{transform:rotate(18deg) translateY(2px)}
    .state-debugging .brow.right{transform:rotate(-18deg) translateY(2px)}
    .state-success .mouth{border-radius:0 0 30px 30px;height:16px}
    .bubble{position:relative;align-self:flex-end;max-width:320px;max-height:170px;overflow:auto;padding:14px 16px;border-radius:18px 18px 18px 6px;background:rgba(9,13,22,.92);border:1px solid var(--line);box-shadow:0 16px 36px rgba(0,0,0,.35);z-index:2}
    .bubble .state{color:var(--accent);font-size:.75rem;text-transform:uppercase;letter-spacing:.16em;margin-bottom:8px}
    .stat-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}
    .stat{padding:16px;border-radius:18px;background:rgba(255,255,255,.03);border:1px solid var(--line);min-width:0}
    .label{color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.12em} .value{font-size:1.6rem;margin-top:6px;color:#fff}
    .list{margin:0;padding-left:18px;line-height:1.7} .muted{color:var(--muted)} .feed{display:grid;gap:10px} .feed-item{padding:12px 14px;border-radius:16px;background:rgba(255,255,255,.03);border:1px solid var(--line)} .console{font-family:ui-monospace,Menlo,monospace;background:#05070c;padding:14px;border-radius:16px;border:1px solid var(--line);min-height:220px;max-height:520px;white-space:pre-wrap;overflow:auto} textarea,input{width:100%;background:#05070c;color:#fff;border:1px solid var(--line);border-radius:14px;padding:12px 14px;font:inherit} button{background:linear-gradient(135deg,var(--accent),#4f46e5);border:0;color:#fff;padding:12px 16px;border-radius:14px;font-weight:700;cursor:pointer} button:hover{filter:brightness(1.05)}
    .tool-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
    .tool-launcher{display:grid;grid-template-columns:1.2fr 2fr auto;gap:10px;align-items:center}
    .tool-pill{padding:10px 12px;border-radius:14px;background:rgba(255,255,255,.04);border:1px solid var(--line);color:#fff;font-size:.82rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .workflow-strip{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:10px 0 14px}
    .workflow-strip div,.agent-card{padding:12px;border-radius:8px;background:rgba(255,255,255,.035);border:1px solid var(--line);min-width:0}
    .workflow-strip span{display:block;color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.08em}
    .workflow-strip strong{display:block;margin-top:6px;color:#fff;font-size:1rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .agent-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
    .agent-card strong{color:#fff}.agent-card div{margin:6px 0;color:var(--text)}.agent-card small{display:block;color:var(--muted);line-height:1.45;white-space:pre-wrap}
    .result-console{min-height:260px;border-color:rgba(34,211,238,.18);box-shadow:inset 0 0 24px rgba(34,211,238,.04)}
    .hero-bar{display:flex;gap:12px;align-items:center;justify-content:space-between;padding:10px 14px;border-radius:18px;background:rgba(255,255,255,.04);border:1px solid var(--line)}
    .hero-bar strong{font-size:.9rem;letter-spacing:.16em;text-transform:uppercase}
    .hero-bar span{color:var(--muted);font-size:.8rem}
    body{background:linear-gradient(135deg,#0f1418 0%,#1d1713 42%,#29332d 72%,#101418 100%);font-family:Inter,ui-sans-serif,system-ui,sans-serif}.sidebar,.topbar,.panel{background:rgba(27,31,31,.72);border-color:rgba(232,220,201,.16);box-shadow:0 24px 80px rgba(0,0,0,.34)}.nav-link{border-radius:8px}.nav-link.active,.nav-link:hover{background:rgba(200,164,106,.16);border-color:rgba(200,164,106,.34);color:#f8efe1}.brand,button{background:linear-gradient(135deg,#7ba88d,#c8a46a 62%,#e8dcc9);color:#111827;box-shadow:0 16px 42px rgba(200,164,106,.22)}.avatar-stage{background:linear-gradient(160deg,rgba(22,24,22,.78),rgba(85,65,42,.26)),linear-gradient(45deg,rgba(123,168,141,.12),rgba(200,164,106,.16));border-radius:8px}.avatar-stage::after{content:"";position:absolute;left:12%;right:12%;bottom:8%;height:20%;background:radial-gradient(ellipse at center,rgba(200,164,106,.22),transparent 68%);filter:blur(18px);pointer-events:none}.scene .orbit,.rings,.legacy-orb{display:none}.scene .grid{opacity:.1}.akshat-portrait{width:min(520px,88%);aspect-ratio:1/1;object-fit:cover;border-radius:8px;box-shadow:0 46px 110px rgba(0,0,0,.52),0 0 0 1px rgba(232,220,201,.16),0 0 70px rgba(200,164,106,.13);z-index:1;transition:transform .2s ease,filter .25s ease;animation:portraitBreathe 4.6s ease-in-out infinite;transform-origin:50% 62%}.avatar.state-thinking .akshat-portrait,.avatar.state-coding .akshat-portrait,.avatar.state-testing .akshat-portrait{animation:portraitWork 2.4s ease-in-out infinite;filter:saturate(1.08) contrast(1.03)}.avatar.state-speaking .akshat-portrait{animation:portraitTalk 1.35s ease-in-out infinite}.avatar.state-success .akshat-portrait{animation:portraitSuccess 1.8s ease-in-out infinite}.avatar.state-error .akshat-portrait{animation:portraitError .9s ease-in-out infinite}.bubble{background:rgba(16,20,20,.9);border-color:rgba(232,220,201,.18);border-radius:8px}.model-pill,.agent-chip,.stat,.feed-item,.tool-pill,.workflow-strip div,.agent-card{background:rgba(232,220,201,.07);border-color:rgba(232,220,201,.14);border-radius:8px}.console,input,select,textarea{background:rgba(12,16,16,.74);border-color:rgba(232,220,201,.16);border-radius:8px}.chat-thread{height:210px;overflow:auto;display:grid;align-content:start;gap:8px;margin-top:12px}.chat-line{padding:10px 12px;border-radius:8px;max-width:88%;line-height:1.45}.chat-line.user{justify-self:end;background:rgba(123,168,141,.22)}.chat-line.assistant{justify-self:start;background:rgba(200,164,106,.15)}@keyframes portraitBreathe{0%,100%{transform:translateY(0) scale(1) rotate(0)}50%{transform:translateY(-8px) scale(1.014) rotate(.35deg)}}@keyframes portraitWork{0%,100%{transform:translateY(-2px) scale(1.01) rotate(-.4deg)}50%{transform:translateY(-12px) scale(1.025) rotate(.7deg)}}@keyframes portraitTalk{0%,100%{transform:translateY(0) scale(1)}45%{transform:translateY(-5px) scale(1.018)}}@keyframes portraitSuccess{0%,100%{transform:translateY(-4px) scale(1.015)}50%{transform:translateY(-16px) scale(1.035) rotate(.5deg)}}@keyframes portraitError{0%,100%{transform:translateX(0)}25%{transform:translateX(-5px)}75%{transform:translateX(5px)}}
    @media (max-width:860px){.app{grid-template-columns:1fr} .sidebar{display:none} .command-center{grid-template-columns:1fr;min-height:auto}.avatar-stage{min-height:70vh}.avatar-stage .bubble{max-width:82%;right:14px;top:14px}.stat-grid,.workflow-strip,.agent-grid,.status-row,.agent-roster{grid-template-columns:1fr} .span-8,.span-6,.span-4,.span-3,.span-12{grid-column:span 12} .content{grid-template-columns:1fr}}
    """
    return css.replace("__ACCENT__", accent)


def body_for_page(active: str, state: Dict[str, Any]) -> str:
    prompt = html_escape(state.get("prompt", ""))
    plan = state.get("plan", []) or ["Waiting for task"]
    todo_list = state.get("todo_list", []) or ["Waiting for task"]
    memory = state.get("memory", [])
    habits = state.get("habits", [])
    tool_logs = state.get("tool_logs", [])
    steps = state.get("steps_done", []) or ["No steps executed"]
    errors = state.get("errors", []) or ["No errors"]
    tests = html_escape(state.get("tests", {}).get("summary", "Not run"))
    browser = html_escape(state.get("browser", {}).get("notes", "No browser verification yet"))
    git = html_escape(json.dumps(state.get("git", {}), indent=2)) if state.get("git") else "Git status not connected yet."
    avatar_state = html_escape(state.get("avatar_state", "Idle"))
    current_action = html_escape(state.get("current_action", "Waiting"))
    workflow = state.get("workflow", {}) or {}
    current_agent = html_escape(state.get("current_agent") or workflow.get("current_agent", "Idle"))
    quality_score = html_escape(str(state.get("quality_score", workflow.get("quality_score", 0))))
    security_score = html_escape(str(state.get("security_score", workflow.get("security_score", 0))))
    iteration_count = html_escape(str(state.get("iteration_count", workflow.get("iteration_count", 0))))
    final_deliverable = html_escape(state.get("final_deliverable") or workflow.get("final_deliverable", "No deliverable yet."))
    chat_items = state.get("chat", [])[-8:]
    chat_html = "".join(f"<div class='chat-line {html_escape(item.get('role','assistant'))}'>{html_escape(item.get('content',''))}</div>" for item in chat_items)
    chat_html = chat_html or "<div class='chat-line assistant'>Hi, I am AKSHAT. I can chat normally, and I will start the engineering agents when you ask for software work.</div>"
    ollama = state.get("ollama", {}) or {}
    engine_ready = bool(ollama.get("ready"))
    engine_connected = bool(ollama.get("connected"))
    engine_message = html_escape(ollama.get("message", "Inference engine offline"))
    engine_model = html_escape(ollama.get("resolved_model") or ollama.get("configured_model") or "unset")
    engine_state = "Connected" if engine_ready else "Offline" if not engine_connected else "Model Missing"
    tools = state.get("active_tools", []) or []
    tool_options = "".join(f'<option value="{html_escape(str(tool))}">{html_escape(str(tool))}</option>' for tool in tools)
    tool_pills = "".join(f"<div class='tool-pill'>{html_escape(tool)}</div>" for tool in tools) or "<div class='muted'>No tools registered.</div>"
    memory_cards = "".join(
        f"<div class='memory-item'><strong>{html_escape(item['kind'])}</strong><div>{html_escape(item['summary'])}</div><small>{html_escape(item['created_at'])}</small></div>"
        for item in memory
    ) or "<div class='muted'>No memory yet.</div>"
    habit_cards = "".join(
        f"<div class='memory-item'><strong>{html_escape(item['kind'])}</strong><div>{html_escape(item['pattern'])}</div><small>{html_escape(item['created_at'])} - confidence {item['confidence']:.2f}</small></div>"
        for item in habits
    ) or "<div class='muted'>No habits learned yet.</div>"
    tool_log_cards = "".join(
        f"<div class='agent-card'><strong>{html_escape(item.get('tool_name', 'tool'))}</strong><div>{html_escape(item.get('agent_name', 'AKSHAT'))} - {html_escape(item.get('reason', ''))}</div><small>{html_escape(item.get('created_at', ''))}</small></div>"
        for item in tool_logs[:12]
    ) or "<div class='muted'>No tool calls logged yet.</div>"
    plan_list = "".join(f"<li>{html_escape(item)}</li>" for item in plan)
    steps_list = "".join(f"<li>{html_escape(item)}</li>" for item in steps)
    todo_list_html = "".join(f"<li>{html_escape(item)}</li>" for item in todo_list)
    errors_list = "".join(f"<li>{html_escape(item)}</li>" for item in errors)
    agent_events = workflow.get("events", []) if isinstance(workflow.get("events", []), list) else []
    agent_cards = "".join(
        f"<div class='agent-card'><strong>{html_escape(item.get('agent', 'Agent'))}</strong><div>{html_escape(item.get('task', ''))}</div><small>{html_escape(item.get('output', ''))[:220]}</small></div>"
        for item in agent_events
    ) or "<div class='muted'>No workflow run yet.</div>"
    agent_page_cards = "".join(
        f"<div class='agent-card' data-agent-name='{html_escape(name)}'><strong>{html_escape(name)}</strong><div>{html_escape(role)}</div><small data-agent-output>{html_escape((workflow.get('agent_outputs', {}) or {}).get(name, 'Waiting for assigned work.'))[:520]}</small></div>"
        for name, role in [
            ("Project Manager", "Turns the user request into requirements and tasks."),
            ("Architect", "Designs the technical approach and system structure."),
            ("Developer", "Produces implementation changes or deliverables."),
            ("Tester", "Runs validation and reports failures."),
            ("Reviewer", "Checks quality, security, and maintainability."),
            ("Improver", "Plans fixes and iteration when validation fails."),
            ("Memory Agent", "Stores outcomes, fixes, and learned patterns."),
            ("AKSHAT", "Prepares the final result for the user."),
        ]
    )
    feed = '<div class="feed" id="live-feed"></div>'
    avatar_panel = f"""
    <section class="panel span-8 avatar">
      <div class="scene">
        <div class="grid"></div>
        <div class="dots"></div>
        <div class="orbit"></div>
        <div class="orbit two"></div>
        <div class="scan"></div>
      </div>
      <div class="bubble"><div class="state" id="avatar-state">{avatar_state}</div><div>{current_action}</div></div>
      <div class="particles" id="avatar-particles"><div class="particle" style="left:20%;top:72%;animation-delay:0s"></div><div class="particle" style="left:40%;top:82%;animation-delay:.8s"></div><div class="particle" style="left:62%;top:78%;animation-delay:1.2s"></div><div class="particle" style="left:78%;top:70%;animation-delay:1.8s"></div></div>
      <div class="rings"><div class="ring one"></div><div class="ring two"></div><div class="ring three"></div></div>
      <img class="akshat-portrait" id="avatar-orb" src="/assets/akshat-avatar.png" alt="AKSHAT avatar">
      <div class="orb legacy-orb state-{state.get('avatar_state','idle').lower().replace(' ','-')}">
        <div class="face">
          <div class="hair"></div>
          <div class="brow left"></div>
          <div class="brow right"></div>
          <div class="eye left"><div class="pupil"></div></div>
          <div class="eye right"><div class="pupil"></div></div>
          <div class="cheek left"></div>
          <div class="cheek right"></div>
          <div class="nose"></div>
          <div class="mouth"></div>
          <div class="neck"></div>
          <div class="shoulders"></div>
          <div class="chest"></div>
          <div class="hand left"></div>
          <div class="hand right"></div>
        </div>
      </div>
    </section>"""
    hero_bar = f"""
    <section class="panel span-12">
      <div class="hero-bar">
        <div><strong>AKSHAT</strong> <span>local autonomous engineering OS</span></div>
        <div class="muted">Inference Engine - {engine_model} - {engine_message}</div>
      </div>
    </section>"""
    task_panel = f"""
    <section class="panel span-4">
      <div class="label">Task Input</div>
      <input id="task-input" placeholder="Describe a software task, not a chat message" value="{prompt}">
      <div style="height:12px"></div>
      <button onclick="submitTask()">Run Workflow</button>
      <div style="height:12px"></div>
      <div class="muted">AKSHAT takes software tasks, assigns agents, runs validation, and reports progress here.</div>
    </section>"""
    stack_panel = f"""
    <section class="panel span-4">
      <div class="label">System Status</div>
      <div class="stat-grid" style="grid-template-columns:1fr;">
        <div class="stat"><div class="label">Inference Engine</div><div class="value">{engine_state}</div></div>
        <div class="stat"><div class="label">Active Model</div><div class="value">{engine_model}</div></div>
      </div>
      <div style="height:12px"></div>
      <div class="muted">{engine_message}</div>
    </section>"""
    tools_panel = f"""
    <section class="panel span-12">
      <div class="label">Active Tools</div>
      <div class="tool-grid">{tool_pills}</div>
    </section>"""
    todo_panel = f"""
    <section class="panel span-12">
      <div class="label">Todo List</div>
      <ul class="list" data-todo-list>{todo_list_html}</ul>
    </section>"""
    workflow_panel = f"""
    <section class="panel span-12">
      <div class="label">Agent Workflow</div>
      <div class="workflow-strip"><div><span>Current Agent</span><strong data-current-agent>{current_agent}</strong></div><div><span>Iterations</span><strong>{iteration_count}</strong></div><div><span>Quality</span><strong>{quality_score}</strong></div><div><span>Security</span><strong>{security_score}</strong></div></div>
      <div class="agent-grid">{agent_cards}</div>
    </section>"""
    deliverable_panel = f"""
    <section class="panel span-12">
      <div class="label">Final Deliverable</div>
      <div class="console result-console" data-final-result>{final_deliverable}</div>
    </section>"""
    habits_panel = f"""
    <section class="panel span-12">
      <div class="label">Learned Habits</div>
      <div class="feed">{habit_cards}</div>
    </section>"""
    tool_log_panel = f"""
    <section class="panel span-12">
      <div class="label">Tool Invocation Logs</div>
      <div class="agent-grid">{tool_log_cards}</div>
    </section>"""
    agent_roster = "".join(
        f"<div class='agent-chip'><strong>{name}</strong><span>{role}</span></div>"
        for name, role in [
            ("Project Manager", "requirements"),
            ("Architect", "system design"),
            ("Developer", "code changes"),
            ("Tester", "validation"),
            ("Reviewer", "quality and risk"),
            ("Improver", "fix iteration"),
            ("Memory Agent", "learning"),
        ]
    )
    command_center = f"""
    <section class="command-center">
      <div class="avatar-stage">
        {avatar_panel}
      </div>
      <aside class="ops-column">
        <section class="panel">
          <div class="model-pill">
            <strong>AKSHAT</strong>
            <span>{engine_model} - {engine_state}</span>
          </div>
          <div style="height:12px"></div>
          <div class="query-box">
            <input id="task-input" placeholder="Talk to AKSHAT or ask for software work" value="{prompt}">
            <button onclick="submitTask()">Send</button>
          </div>
          <div id="chat-thread" class="chat-thread">{chat_html}</div>
        </section>
        <section class="panel">
          <div class="label">Operating State</div>
          <div class="status-row">
            <div class="stat"><div class="label">State</div><div class="value" data-current-state>{avatar_state}</div></div>
            <div class="stat"><div class="label">Agent</div><div class="value" data-current-agent>{current_agent}</div></div>
            <div class="stat"><div class="label">Tools</div><div class="value" data-tool-count>{len(tools)}</div></div>
          </div>
        </section>
        <section class="panel compact-scroll">
          <div class="label">Agent Organization</div>
          <div class="agent-roster">{agent_roster}</div>
          <div style="height:14px"></div>
          <div class="label">Todo List</div>
          <ul class="list" data-todo-list>{todo_list_html}</ul>
          <div style="height:14px"></div>
          <div class="label">Recent Tool Calls</div>
          <div class="agent-grid">{tool_log_cards}</div>
        </section>
      </aside>
    </section>
    <section class="panel span-6"><div class="label">Agent Workflow</div><div class="workflow-strip"><div><span>Current Agent</span><strong data-current-agent>{current_agent}</strong></div><div><span>Iterations</span><strong>{iteration_count}</strong></div><div><span>Quality</span><strong>{quality_score}</strong></div><div><span>Security</span><strong>{security_score}</strong></div></div><div class="agent-grid">{agent_cards}</div></section>
    <section class="panel span-6"><div class="label">Final Result</div><div class="console result-console" data-final-result>{final_deliverable}</div></section>
    """
    if active == "terminal":
        return f"""
        <section class="panel span-8"><div class="label">AKSHAT Conversation</div><div class="query-box"><input id="task-input" placeholder="Say hi, ask a question, or describe software work" value="{prompt}"><button onclick="submitTask()">Send</button></div><div id="chat-thread" class="chat-thread">{chat_html}</div></section>
        <section class="panel span-4"><div class="label">Inference Engine</div><div class="stat-grid" style="grid-template-columns:1fr;"><div class="stat"><div class="label">Connection</div><div class="value">{engine_state}</div></div><div class="stat"><div class="label">Model</div><div class="value">{engine_model}</div></div></div><div style="height:12px"></div><div class="muted">{engine_message}</div></section>
        <section class="panel span-8"><div class="label">Command Stream</div><div class="console" id="console">{current_action}\nStatus: {html_escape(state.get('status', 'idle'))}\nAgent: {current_agent}</div></section>
        <section class="panel span-4"><div class="label">Workflow Queue</div><ul class="list" data-todo-list>{todo_list_html}</ul></section>
        <section class="panel span-12"><div class="label">Advanced Tool Runner</div><div class="tool-launcher"><select id="tool-name">{tool_options}</select><input id="tool-args" placeholder='JSON args, e.g. {{"path":"src/akshat_local.py"}}'><button onclick="runTool()">Run Tool</button></div><div class="console" id="tool-output">Select a tool to execute.</div></section>
        <section class="panel span-12"><div class="label">Live Activity Feed</div>{feed}</section>"""
    if active == "agents":
        return f"""
        <section class="panel span-12"><div class="label">Assign Work To AKSHAT</div><div class="query-box"><input id="task-input" placeholder="Build, fix, test, inspect, or improve software" value="{prompt}"><button onclick="submitTask()">Run Agents</button></div></section>
        <section class="panel span-12"><div class="label">Agent Control Room</div><div class="workflow-strip"><div><span>Current Agent</span><strong data-current-agent>{current_agent}</strong></div><div><span>Iterations</span><strong>{iteration_count}</strong></div><div><span>Quality</span><strong>{quality_score}</strong></div><div><span>Security</span><strong>{security_score}</strong></div></div></section>
        <section class="panel span-12"><div class="label">Dedicated Agents</div><div class="agent-grid">{agent_page_cards}</div></section>
        <section class="panel span-6"><div class="label">Todo List</div><ul class="list" data-todo-list>{todo_list_html}</ul></section>
        <section class="panel span-6"><div class="label">Final Result</div><div class="console result-console" data-final-result>{final_deliverable}</div></section>
        <section class="panel span-12"><div class="label">Live Activity Feed</div>{feed}</section>
        <section class="panel span-12"><div class="label">Tool Invocation Logs</div><div class="agent-grid">{tool_log_cards}</div></section>"""
    if active == "memory":
        return f"""
        <section class="panel span-4"><div class="label">Memory Viewer</div><div class="feed" id="memory-feed">{memory_cards}</div></section>
        <section class="panel span-8"><div class="label">Current Plan</div><ul class="list" data-plan-list>{plan_list}</ul></section>
        <section class="panel span-12"><div class="label">Todo List</div><ul class="list" data-todo-list>{todo_list_html}</ul></section>
        <section class="panel span-12"><div class="label">Live Activity Feed</div>{feed}</section>"""
    if active == "timeline":
        return f"""
        <section class="panel span-12"><div class="label">Current Plan</div><ul class="list" data-plan-list>{plan_list}</ul></section>
        <section class="panel span-12"><div class="label">Live Activity Feed</div>{feed}</section>"""
    if active == "browser":
        return f"""
        <section class="panel span-8"><div class="label">Browser Preview</div><div class="muted">{browser}</div></section>
        <section class="panel span-4"><div class="label">System Status</div><div class="stat-grid" style="grid-template-columns:1fr;"><div class="stat"><div class="label">Avatar</div><div class="value">{avatar_state}</div></div><div class="stat"><div class="label">Current Action</div><div class="value">{current_action}</div></div></div></section>"""
    if active == "tests":
        return f"""
        <section class="panel span-6"><div class="label">Test Results</div><div class="muted">{tests}</div><ul class="list">{errors_list}</ul></section>
        <section class="panel span-6"><div class="label">Repository Explorer</div><div class="muted">Repository inspection hooks will be connected here.</div></section>"""
    if active == "git":
        return f"""
        <section class="panel span-12"><div class="label">Git Changes</div><pre style="white-space:pre-wrap;margin:0">{git}</pre></section>"""
    if active == "settings":
        return """
        <section class="panel span-12"><div class="label">Settings</div><div class="muted">Theme, density, browser, and tool configuration go here.</div></section>"""
    if active == "repo":
        return """
        <section class="panel span-12"><div class="label">Repository Explorer</div><div class="muted">Repository inspection hooks will be connected here.</div></section>"""
    if active == "status":
        return f"""
        {hero_bar}
        <section class="panel span-4">{task_panel}</section>
        <section class="panel span-4">{avatar_panel}</section>
        <section class="panel span-4">{stack_panel}</section>
        {tools_panel}
        {todo_panel}
        {workflow_panel}
        {deliverable_panel}
        {tool_log_panel}
        {habits_panel}
        <section class="panel span-6"><div class="label">Current Plan</div><ul class="list" data-plan-list>{plan_list}</ul></section>
        <section class="panel span-6"><div class="label">Live Console</div><div class="console">{current_action}</div></section>
        <section class="panel span-12"><div class="label">Live Activity Feed</div>{feed}</section>"""
    return command_center


def render_page(title: str, active: str, state: Dict[str, Any], theme: str, density: str) -> str:
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html_escape(title)}</title><style>{_styles(theme)}</style></head>
<body>
<div class="app">
  <aside class="sidebar">
    <div class="brand">A</div>
    {_nav(active)}
  </aside>
  <main class="main">
    <div class="topbar">
      <div><strong>AKSHAT</strong> <span class="muted">Autonomous AI Software Engineer</span></div>
      <div class="muted" data-current-action>{html_escape(state.get("avatar_state", "Idle"))} / {html_escape(state.get("current_action", "Waiting"))}</div>
    </div>
    <div class="content">{body_for_page(active, state)}</div>
  </main>
</div>
<script src="/avatar_runtime.js"></script>
</body></html>"""
    return html
