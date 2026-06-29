import React, {
  createContext, useContext, useState, useEffect, useCallback, useRef,
} from 'react';
import { authAPI, userAPI } from './api';

/* ─────────────────────────────────────────────────────────────────────────────
   DESIGN SYSTEM
   Fonts  : Plus Jakarta Sans (display 800) + Inter (body)
            → replicates the Yeve-style heavy/light contrast
   Tokens : CSS custom properties on :root — dark mode swaps via [data-theme=dark]
   Palette: blue #1a73e8 / teal #0d9488 (light) ; blue #60a5fa / teal #2dd4bf (dark)
   Signature: breathing pulse dot on availability + mixed-weight hero headline
              with gradient accent word (like Yeve's coloured "pop-up")
───────────────────────────────────────────────────────────────────────────── */

const BASE_CSS = `
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

/* ── CSS custom properties ── */
:root {
  --bg:          #f7f8fa;
  --bg2:         #eef0f4;
  --surface:     #ffffff;
  --surface2:    #f3f4f6;
  --surface3:    #e8eaed;
  --border:      #e2e4e8;
  --border2:     #d0d3da;
  --text:        #111318;
  --text-sub:    #4b5563;
  --text-mute:   #9ca3af;
  --accent:      #1a73e8;
  --accent-l:    #dbeafe;
  --accent-d:    #1557b0;
  --teal:        #0d9488;
  --teal-l:      #ccfbf1;
  --success:     #15803d;
  --success-l:   #dcfce7;
  --danger:      #dc2626;
  --danger-l:    #fee2e2;
  --warn:        #d97706;
  --warn-l:      #fef3c7;
  --shadow-sm:   0 1px 3px rgba(0,0,0,.08),0 1px 2px rgba(0,0,0,.06);
  --shadow-md:   0 4px 12px rgba(0,0,0,.08),0 2px 6px rgba(0,0,0,.05);
  --shadow-lg:   0 12px 32px rgba(0,0,0,.1),0 4px 12px rgba(0,0,0,.06);
  --radius-sm:   8px;
  --radius-md:   12px;
  --radius-lg:   16px;
  --radius-xl:   24px;
}

[data-theme="dark"] {
  --bg:          #0d1117;
  --bg2:         #161b22;
  --surface:     #1c2128;
  --surface2:    #252d38;
  --surface3:    #2d3748;
  --border:      #30363d;
  --border2:     #444c56;
  --text:        #e6edf3;
  --text-sub:    #8b949e;
  --text-mute:   #6e7681;
  --accent:      #60a5fa;
  --accent-l:    #1e3a5f;
  --accent-d:    #93c5fd;
  --teal:        #2dd4bf;
  --teal-l:      #0d3330;
  --success:     #4ade80;
  --success-l:   #052e16;
  --danger:      #f87171;
  --danger-l:    #450a0a;
  --warn:        #fbbf24;
  --warn-l:      #451a03;
  --shadow-sm:   0 1px 3px rgba(0,0,0,.4);
  --shadow-md:   0 4px 12px rgba(0,0,0,.4);
  --shadow-lg:   0 12px 32px rgba(0,0,0,.5);
}

/* ── Reset ── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;scroll-behavior:smooth}

body{
  background:var(--bg);
  color:var(--text);
  font-family:'Inter',system-ui,sans-serif;
  font-size:15px;line-height:1.6;min-height:100vh;
  transition:background .25s,color .25s;
}

h1,h2,h3,h4,h5{
  font-family:'Plus Jakarta Sans',sans-serif;
  font-weight:800;line-height:1.15;
}

button,input,select,textarea{font-family:inherit}
button{cursor:pointer;border:none;background:none}
a{color:var(--accent);text-decoration:none}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px}

/* ── Scrollbar ── */
::-webkit-scrollbar{width:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:99px}

/* ── Animations ── */
@keyframes fadeUp    {from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:none}}
@keyframes fadeIn    {from{opacity:0}to{opacity:1}}
@keyframes spin      {to{transform:rotate(360deg)}}
@keyframes pulse     {0%,100%{opacity:1;transform:scale(1)}50%{opacity:.55;transform:scale(.82)}}
@keyframes toastIn   {from{opacity:0;transform:translateX(110%)}to{opacity:1;transform:none}}
@keyframes shrink    {from{width:100%}to{width:0}}
@keyframes sk        {0%,100%{opacity:.35}50%{opacity:.7}}
@keyframes pageIn    {from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}

.fadeUp {animation:fadeUp .4s cubic-bezier(.22,.68,0,1.2) both}
.fadeIn {animation:fadeIn .3s ease both}
.pageIn {animation:pageIn .3s ease both}

/* ── Surfaces ── */
.surface   {background:var(--surface);border-radius:var(--radius-md);border:1px solid var(--border)}
.surface-lg{background:var(--surface);border-radius:var(--radius-lg);border:1px solid var(--border)}
.surface-xl{background:var(--surface);border-radius:var(--radius-xl);border:1px solid var(--border)}
.surface:hover,.surface-lg:hover{box-shadow:var(--shadow-md)}

/* ── Lift on hover ── */
.lift{transition:transform .2s ease,box-shadow .2s ease}
.lift:hover{transform:translateY(-4px);box-shadow:var(--shadow-lg)}

/* ── Buttons ── */
.btn{
  display:inline-flex;align-items:center;justify-content:center;gap:8px;
  padding:10px 22px;font-size:14px;font-weight:600;border-radius:var(--radius-sm);
  cursor:pointer;transition:all .15s ease;white-space:nowrap;
  -webkit-user-select:none;user-select:none;font-family:'Plus Jakarta Sans',sans-serif;
}
.btn:disabled{opacity:.45;cursor:not-allowed;pointer-events:none}

.btn-primary{
  background:var(--accent);color:#fff;
  box-shadow:0 1px 4px rgba(26,115,232,.35);
}
.btn-primary:hover{background:var(--accent-d);box-shadow:0 4px 12px rgba(26,115,232,.4);transform:translateY(-1px)}
.btn-primary:active{transform:scale(.98)}

.btn-ghost{
  background:transparent;color:var(--text-sub);
  border:1.5px solid var(--border);
}
.btn-ghost:hover{background:var(--surface2);border-color:var(--border2);color:var(--text)}

.btn-text{
  background:transparent;color:var(--accent);
  padding:6px 10px;font-size:14px;font-weight:600;border-radius:6px;
}
.btn-text:hover{background:var(--accent-l)}

/* ── Fields ── */
.field{margin-bottom:18px}
.field-label{
  display:block;margin-bottom:6px;
  font-size:11.5px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
  color:var(--text-sub);
}
.field-input{
  width:100%;padding:11px 14px;
  background:var(--surface);border:1.5px solid var(--border);
  border-radius:10px;color:var(--text);font-size:14px;outline:none;
  transition:border-color .15s,box-shadow .15s;
}
.field-input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(96,165,250,.18)}
.field-input::placeholder{color:var(--text-mute)}

/* ── Password strength ── */
.pw-bar{height:3px;border-radius:99px;transition:width .3s,background .3s}

/* ── Badges ── */
.badge{
  display:inline-flex;align-items:center;gap:5px;
  padding:3px 10px;border-radius:99px;
  font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;
  font-family:'Plus Jakarta Sans',sans-serif;
}

/* ── Pulse dot ── */
.pulse-dot{
  width:7px;height:7px;border-radius:50%;
  display:inline-block;flex-shrink:0;
  animation:pulse 2.2s ease-in-out infinite;
}

/* ── Nav ── */
.nav-pill{
  padding:7px 15px;font-size:14px;font-weight:500;
  border-radius:99px;color:var(--text-sub);transition:all .15s;
  font-family:'Plus Jakarta Sans',sans-serif;
}
.nav-pill:hover{background:var(--surface2);color:var(--text)}
.nav-pill.active{
  background:var(--accent-l);color:var(--accent);font-weight:700;
  position:relative;
}

/* ── Toast ── */
.toast-stack{position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:10px;pointer-events:none}
.toast{
  min-width:300px;max-width:380px;padding:14px 18px;border-radius:14px;
  display:flex;gap:12px;align-items:flex-start;pointer-events:all;
  animation:toastIn .3s cubic-bezier(.22,.68,0,1.2);
  box-shadow:var(--shadow-lg);position:relative;overflow:hidden;
  background:var(--surface);border:1px solid var(--border);
}
.toast::after{content:'';position:absolute;bottom:0;left:0;height:2.5px;animation:shrink 4s linear forwards}
.toast-ok::after{background:var(--success)}
.toast-err::after{background:var(--danger)}
.toast-icon{font-size:16px;font-weight:800;flex-shrink:0;margin-top:1px}
.toast-ok  .toast-icon{color:var(--success)}
.toast-err .toast-icon{color:var(--danger)}

/* ── Stars ── */
.star-on {color:#f59e0b;font-size:13px}
.star-off{color:var(--border2);font-size:13px}

/* ── Skeleton ── */
.sk{background:var(--surface2);border-radius:6px;animation:sk 1.5s ease-in-out infinite}

/* ── Divider ── */
.hr{border:none;border-top:1px solid var(--border);margin:20px 0}

/* ── Section overline (teal label above headings) ── */
.overline{
  display:inline-flex;align-items:center;gap:6px;
  font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
  color:var(--teal);margin-bottom:12px;font-family:'Plus Jakarta Sans',sans-serif;
}
.overline::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--teal);display:block}

/* ── Filter bar sticky ── */
.filter-bar{
  position:sticky;top:60px;z-index:100;
  background:var(--bg);border-bottom:1px solid var(--border);
  padding:12px 0;
  transition:background .25s;
}

/* ── Theme toggle ── */
.theme-btn{
  width:36px;height:36px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  background:var(--surface2);color:var(--text-sub);
  transition:all .2s;font-size:16px;border:1px solid var(--border);
}
.theme-btn:hover{background:var(--surface3);color:var(--text);transform:rotate(15deg)}

/* ── Hero gradient text ── */
.gradient-text{
  background:linear-gradient(135deg,#60a5fa,#2dd4bf);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;
}

/* ── Tabs ── */
.tab-bar{display:flex;gap:4px;background:var(--surface2);padding:5px;border-radius:12px;width:fit-content}
.tab{
  padding:8px 20px;border-radius:9px;font-size:14px;font-weight:600;
  color:var(--text-sub);transition:all .15s;
  font-family:'Plus Jakarta Sans',sans-serif;
}
.tab.active{background:var(--surface);color:var(--accent);box-shadow:var(--shadow-sm)}

/* ── Search hero input ── */
.hero-search{
  width:100%;max-width:560px;
  background:rgba(255,255,255,.12);
  border:1.5px solid rgba(255,255,255,.25);
  border-radius:14px;padding:14px 20px 14px 48px;
  color:#fff;font-size:15px;outline:none;
  backdrop-filter:blur(8px);
  transition:background .2s,border-color .2s;
}
.hero-search::placeholder{color:rgba(255,255,255,.55)}
.hero-search:focus{background:rgba(255,255,255,.18);border-color:rgba(255,255,255,.5)}
`;

/* ─── Context ────────────────────────────────────────────────────────────── */
const AuthCtx  = createContext(null);
const ToastCtx = createContext(null);
const ThemeCtx = createContext(null);
const useAuth  = () => useContext(AuthCtx);
const useToast = () => useContext(ToastCtx);
const useTheme = () => useContext(ThemeCtx);

/* ─── Theme provider ─────────────────────────────────────────────────────── */
function ThemeProvider({ children }) {
  const [dark, setDark] = useState(() => {
    const saved = localStorage.getItem('helia-theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
    localStorage.setItem('helia-theme', dark ? 'dark' : 'light');
  }, [dark]);

  const toggle = useCallback(() => setDark(d => !d), []);
  return <ThemeCtx.Provider value={{ dark, toggle }}>{children}</ThemeCtx.Provider>;
}

/* ─── Toast provider ─────────────────────────────────────────────────────── */
function ToastProvider({ children }) {
  const [list, setList] = useState([]);
  const show = useCallback((msg, type = 'ok') => {
    const id = Date.now() + Math.random();
    setList(p => [...p, { id, msg, type }]);
    setTimeout(() => setList(p => p.filter(t => t.id !== id)), 4200);
  }, []);
  return (
    <ToastCtx.Provider value={show}>
      {children}
      <div className="toast-stack">
        {list.map(t => (
          <div key={t.id} className={`toast toast-${t.type}`}>
            <span className="toast-icon">{t.type === 'ok' ? '✓' : '✕'}</span>
            <span style={{ fontSize: 14, lineHeight: 1.5, color: 'var(--text)' }}>{t.msg}</span>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

/* ─── Auth provider ──────────────────────────────────────────────────────── */
function AuthProvider({ children }) {
  const [user, setUser]       = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const u = localStorage.getItem('user');
    const t = localStorage.getItem('token');
    if (u && t) try { setUser(JSON.parse(u)); } catch {}
    setLoading(false);
  }, []);
  const login = (token, refresh, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };
  const logout = () => { localStorage.clear(); setUser(null); };
  return (
    <AuthCtx.Provider value={{ user, login, logout, loading }}>
      {!loading && children}
    </AuthCtx.Provider>
  );
}

/* ─── Atoms ──────────────────────────────────────────────────────────────── */
function Spinner({ size = 20, color = 'var(--accent)' }) {
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%',
      border: '2px solid var(--border)', borderTopColor: color,
      animation: 'spin .7s linear infinite', flexShrink: 0,
    }} />
  );
}

function Stars({ rating = 0, max = 5 }) {
  return (
    <span style={{ display: 'inline-flex', gap: 1 }}>
      {Array.from({ length: max }).map((_, i) => (
        <span key={i} className={i < Math.round(rating) ? 'star-on' : 'star-off'}>★</span>
      ))}
    </span>
  );
}

function Badge({ children, bg, color, dot }) {
  return (
    <span className="badge" style={{ background: bg, color }}>
      {dot && <span className="pulse-dot" style={{ background: color }} />}
      {children}
    </span>
  );
}

function Field({ label, type = 'text', ...rest }) {
  return (
    <div className="field">
      {label && <label className="field-label">{label}</label>}
      <input type={type} className="field-input" {...rest} />
    </div>
  );
}

function SelectField({ label, children, ...rest }) {
  return (
    <div className="field">
      {label && <label className="field-label">{label}</label>}
      <select className="field-input" {...rest}>{children}</select>
    </div>
  );
}

function Avatar({ name = '?', size = 40, fontSize = 16 }) {
  const palette = ['#1a73e8','#0d9488','#7c3aed','#db2777','#ea580c','#0369a1'];
  const bg = palette[(name.charCodeAt(0) + name.charCodeAt(1)) % palette.length];
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%', background: bg,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      color: '#fff', fontSize, fontWeight: 800, flexShrink: 0,
      fontFamily: "'Plus Jakarta Sans',sans-serif",
    }}>
      {name[0].toUpperCase()}
    </div>
  );
}

/* Password strength meter */
function PasswordStrength({ password }) {
  const score = !password ? 0
    : [/.{8,}/, /[A-Z]/, /[0-9]/, /[^A-Za-z0-9]/]
        .filter(r => r.test(password)).length;
  const bars  = [
    { w: '25%', bg: 'var(--danger)' },
    { w: '50%', bg: 'var(--warn)' },
    { w: '75%', bg: '#3b82f6' },
    { w: '100%', bg: 'var(--success)' },
  ];
  const labels = ['','Weak','Fair','Good','Strong'];
  if (!password) return null;
  const b = bars[score - 1] || bars[0];
  return (
    <div style={{ marginTop: -10, marginBottom: 16 }}>
      <div style={{ height: 3, background: 'var(--surface2)', borderRadius: 99, overflow: 'hidden' }}>
        <div className="pw-bar" style={{ width: b.w, background: b.bg, height: '100%' }} />
      </div>
      <div style={{ fontSize: 11, color: b.bg, marginTop: 4, fontWeight: 600 }}>{labels[score]}</div>
    </div>
  );
}

/* ─── Navbar ─────────────────────────────────────────────────────────────── */
function Navbar({ page, setPage }) {
  const { user, logout } = useAuth();
  const { dark, toggle } = useTheme();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', fn);
    return () => window.removeEventListener('scroll', fn);
  }, []);

  return (
    <nav style={{
      position: 'sticky', top: 0, zIndex: 200, height: 60,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 28px',
      background: scrolled
        ? dark ? 'rgba(13,17,23,.88)' : 'rgba(247,248,250,.88)'
        : 'var(--bg)',
      backdropFilter: scrolled ? 'blur(20px)' : 'none',
      borderBottom: `1px solid ${scrolled ? 'var(--border)' : 'transparent'}`,
      transition: 'background .25s,border-color .25s',
    }}>
      {/* Left — logo + nav links */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
        <button onClick={() => setPage('home')} style={{
          fontFamily: "'Plus Jakarta Sans',sans-serif",
          fontSize: 20, fontWeight: 800, letterSpacing: '-1px',
          background: 'linear-gradient(135deg,var(--accent),var(--teal))',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          marginRight: 20,
        }}>Helia</button>
        {[['home','Home'],['doctors','Find Doctors']].map(([p,l]) => (
          <button key={p} className={`nav-pill${page===p?' active':''}`} onClick={() => setPage(p)}>{l}</button>
        ))}
        {user && (
          <button className={`nav-pill${page==='dashboard'?' active':''}`} onClick={() => setPage('dashboard')}>
            Dashboard
          </button>
        )}
      </div>

      {/* Right — theme + auth */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        {/* Dark / light toggle */}
        <button className="theme-btn" onClick={toggle} title={dark ? 'Switch to light mode' : 'Switch to dark mode'}>
          {dark ? '☀️' : '🌙'}
        </button>

        {user ? (
          <>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '4px 12px 4px 5px',
              background: 'var(--accent-l)', borderRadius: 99,
              cursor: 'pointer', border: '1px solid transparent',
            }} onClick={() => setPage('dashboard')}>
              <Avatar name={user.email} size={28} fontSize={12} />
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)' }}>
                {user.email.split('@')[0]}
              </span>
            </div>
            <button className="btn btn-ghost" onClick={logout}
              style={{ padding: '7px 16px', fontSize: 13 }}>
              Sign out
            </button>
          </>
        ) : (
          <>
            <button className="btn btn-ghost" onClick={() => setPage('login')}
              style={{ padding: '7px 18px' }}>Sign in</button>
            <button className="btn btn-primary" onClick={() => setPage('register')}
              style={{ padding: '8px 20px' }}>Get started</button>
          </>
        )}
      </div>
    </nav>
  );
}

/* ─── Home page ──────────────────────────────────────────────────────────── */
function HomePage({ setPage, setFilters: setGlobalFilters }) {
  const [specialties, setSpecialties] = useState([]);
  const [heroSearch, setHeroSearch]   = useState('');

  useEffect(() => {
    userAPI.listSpecialties().then(r => setSpecialties(r.data)).catch(() => {});
  }, []);

  const handleHeroSearch = () => {
    if (heroSearch.trim()) {
      setGlobalFilters(f => ({ ...f, search: heroSearch }));
    }
    setPage('doctors');
  };

  const icons = {
    'Cardiology':'❤️','Dermatology':'✨','Neurology':'🧠','Orthopaedics':'🦴',
    'Paediatrics':'👶','General Practice':'🩺','Psychiatry':'💬',
    'Ophthalmology':'👁️','Gynaecology':'🌸','Oncology':'🎗️','ENT':'👂',
    'Radiology':'🔬',
  };

  const display = specialties.length > 0
    ? specialties
    : ['Cardiology','Dermatology','Neurology','Orthopaedics','Paediatrics',
       'General Practice','Psychiatry','Ophthalmology'].map(n => ({ id: n, name: n }));

  return (
    <div className="pageIn">
      {/* ── Hero ── */}
      <section style={{
        background: 'linear-gradient(150deg, #0f172a 0%, #1e3a5f 45%, #0d3330 100%)',
        padding: '96px 24px 80px', textAlign: 'center', color: '#fff',
        position: 'relative', overflow: 'hidden',
      }}>
        {/* Ambient glows */}
        {[
          { top: -120, right: -80, size: 460, color: 'rgba(26,115,232,.18)' },
          { bottom: -80, left: -60, size: 340, color: 'rgba(13,148,136,.22)' },
          { top: '40%', left: '50%', size: 200, color: 'rgba(96,165,250,.1)' },
        ].map((g, i) => (
          <div key={i} style={{
            position: 'absolute', width: g.size, height: g.size,
            borderRadius: '50%', background: g.color, filter: 'blur(80px)',
            top: g.top, bottom: g.bottom, left: g.left, right: g.right,
            pointerEvents: 'none', transform: g.left === '50%' ? 'translate(-50%,-50%)' : undefined,
          }} />
        ))}

        <div style={{ position: 'relative', maxWidth: 720, margin: '0 auto' }}>
          <div className="overline" style={{ justifyContent: 'center', color: '#5eead4' }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#5eead4', display: 'block' }} />
            Healthcare, reimagined
          </div>

          {/* Yeve-style headline — heavy black + gradient accent word */}
          <h1 style={{
            fontSize: 'clamp(44px,7vw,76px)',
            fontWeight: 800, letterSpacing: '-2.5px',
            lineHeight: 1.08, color: '#fff', marginBottom: 24,
          }}>
            Find the right doctor,{' '}
            <span className="gradient-text">book instantly.</span>
          </h1>

          <p style={{
            fontSize: 18, color: 'rgba(255,255,255,.72)',
            maxWidth: 520, margin: '0 auto 40px', lineHeight: 1.75,
          }}>
            Connect with verified specialists, manage appointments and health records — all in one place.
          </p>

          {/* Hero search */}
          <div style={{ position: 'relative', maxWidth: 520, margin: '0 auto 32px' }}>
            <span style={{ position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)', fontSize: 18, pointerEvents: 'none' }}>🔍</span>
            <input
              className="hero-search"
              placeholder="Search by name, specialty…"
              value={heroSearch}
              onChange={e => setHeroSearch(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleHeroSearch()}
            />
            {heroSearch && (
              <button onClick={handleHeroSearch} className="btn btn-primary"
                style={{ position: 'absolute', right: 6, top: '50%', transform: 'translateY(-50%)', padding: '7px 16px', fontSize: 13, borderRadius: 10 }}>
                Search
              </button>
            )}
          </div>

          <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button className="btn btn-primary" onClick={() => setPage('doctors')}
              style={{ padding: '13px 32px', fontSize: 15, borderRadius: 12, background: '#fff', color: '#1a73e8' }}>
              Browse all doctors
            </button>
            <button className="btn btn-ghost" onClick={() => setPage('register')}
              style={{ padding: '13px 32px', fontSize: 15, borderRadius: 12, color: '#fff', borderColor: 'rgba(255,255,255,.28)' }}>
              Create free account
            </button>
          </div>
        </div>

        {/* Stats row */}
        <div style={{
          display: 'flex', justifyContent: 'center', gap: 48, marginTop: 60,
          flexWrap: 'wrap', position: 'relative',
        }}>
          {[['500+','Specialists'],['30+','Specialties'],['10k+','Appointments'],['50k+','Patients']].map(([v,l]) => (
            <div key={l} style={{ textAlign: 'center' }}>
              <div style={{
                fontSize: 28, fontWeight: 800, color: '#60a5fa',
                fontFamily: "'Plus Jakarta Sans',sans-serif",
                letterSpacing: '-1px',
              }}>{v}</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,.5)', marginTop: 3, textTransform: 'uppercase', letterSpacing: '.08em' }}>{l}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Specialties ── */}
      <section style={{ maxWidth: 1160, margin: '0 auto', padding: '72px 24px' }}>
        <div className="overline">Browse by specialty</div>
        <h2 style={{ fontSize: 38, letterSpacing: '-1.5px', marginBottom: 8, color: 'var(--text)' }}>
          Find the right specialist
        </h2>
        <p style={{ color: 'var(--text-sub)', marginBottom: 40, fontSize: 16 }}>
          {display.length} specialties across our verified network.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(144px,1fr))', gap: 12 }}>
          {display.map((s, i) => (
            <div key={s.id} className="surface lift fadeUp"
              onClick={() => setPage('doctors')}
              style={{ padding: '22px 14px', textAlign: 'center', cursor: 'pointer', animationDelay: `${i * .035}s` }}>
              <div style={{ fontSize: 28, marginBottom: 10 }}>{icons[s.name] || '🏥'}</div>
              <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', lineHeight: 1.3, fontFamily: "'Plus Jakarta Sans',sans-serif" }}>{s.name}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How it works ── */}
      <section style={{ background: 'var(--surface)', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)', padding: '72px 24px' }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <div className="overline" style={{ justifyContent: 'center' }}>Simple process</div>
          <h2 style={{ fontSize: 38, letterSpacing: '-1.5px', textAlign: 'center', marginBottom: 56, color: 'var(--text)' }}>
            Healthcare in three steps
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(240px,1fr))', gap: 40 }}>
            {[
              { n:'01', emoji:'🔍', title:'Search', desc:'Filter by specialty, availability, fee, or language to find your ideal doctor.' },
              { n:'02', emoji:'📅', title:'Book',   desc:'Select an open time slot and confirm your appointment in under a minute.' },
              { n:'03', emoji:'🩺', title:'Attend', desc:'Show up and receive care. Your records and history are automatically saved.' },
            ].map(s => (
              <div key={s.n} style={{ textAlign: 'center' }}>
                <div style={{
                  width: 72, height: 72, borderRadius: 20,
                  background: 'var(--accent-l)', margin: '0 auto 20px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 28, border: '1px solid var(--border)',
                }}>{s.emoji}</div>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--teal)', letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 8 }}>{s.n}</div>
                <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 10, color: 'var(--text)', fontFamily: "'Plus Jakarta Sans',sans-serif" }}>{s.title}</h3>
                <p style={{ color: 'var(--text-sub)', fontSize: 14, lineHeight: 1.75 }}>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section style={{ padding: '80px 24px', textAlign: 'center' }}>
        <div style={{ maxWidth: 520, margin: '0 auto' }}>
          <h2 style={{ fontSize: 38, letterSpacing: '-1.5px', marginBottom: 16, color: 'var(--text)' }}>
            Ready to take control of{' '}
            <span className="gradient-text">your health?</span>
          </h2>
          <p style={{ color: 'var(--text-sub)', marginBottom: 32, fontSize: 16 }}>
            Join thousands of patients who trust Helia.
          </p>
          <button className="btn btn-primary" onClick={() => setPage('register')}
            style={{ padding: '14px 36px', fontSize: 16, borderRadius: 12 }}>
            Get started for free
          </button>
        </div>
      </section>

      <footer style={{ borderTop: '1px solid var(--border)', padding: '24px', textAlign: 'center' }}>
        <p style={{ fontSize: 13, color: 'var(--text-mute)' }}>
          © 2025 Helia · Built on AWS · Containerised with Docker Compose
        </p>
      </footer>
    </div>
  );
}

/* ─── Auth card ──────────────────────────────────────────────────────────── */
function AuthCard({ title, subtitle, icon, children }) {
  return (
    <div style={{
      minHeight: 'calc(100vh - 60px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 24,
      background: 'radial-gradient(ellipse at 55% 0%, var(--accent-l) 0%, var(--bg) 65%)',
    }}>
      <div className="surface-xl fadeUp" style={{ padding: '44px 48px', width: '100%', maxWidth: 440, boxShadow: 'var(--shadow-lg)' }}>
        {icon && <div style={{ fontSize: 36, marginBottom: 14 }}>{icon}</div>}
        <h2 style={{ fontSize: 30, letterSpacing: '-1px', marginBottom: 6, color: 'var(--text)' }}>{title}</h2>
        <p style={{ color: 'var(--text-sub)', marginBottom: 32, fontSize: 15 }}>{subtitle}</p>
        {children}
      </div>
    </div>
  );
}

/* ─── Auth page ──────────────────────────────────────────────────────────── */
function AuthPage({ mode, setPage }) {
  const { login }    = useAuth();
  const toast        = useToast();
  const [form, setF] = useState({ email: '', password: '', role: 'patient' });
  const [busy, setBusy] = useState(false);
  const isLogin = mode === 'login';

  const go = async () => {
    setBusy(true);
    try {
      if (isLogin) {
        const { data } = await authAPI.login(form);
        login(data.access_token, data.refresh_token, { email: form.email, role: form.role });
        toast('Welcome back!');
        setPage('dashboard');
      } else {
        await authAPI.register(form);
        toast('Account created — sign in now.');
        setPage('login');
      }
    } catch (err) {
      const d = err.response?.data?.detail;
      toast(Array.isArray(d) ? d[0]?.msg : (d || 'Something went wrong'), 'err');
    } finally { setBusy(false); }
  };

  return (
    <AuthCard
      icon={isLogin ? '👋' : '🏥'}
      title={isLogin ? 'Welcome back' : 'Create your account'}
      subtitle={isLogin ? 'Sign in to access your health dashboard.' : 'Book appointments with top specialists.'}
    >
      <Field label="Email address" type="email" placeholder="you@example.com"
        value={form.email} onChange={e => setF({ ...form, email: e.target.value })}
        onKeyDown={e => e.key === 'Enter' && go()} autoFocus />

      <Field label="Password" type="password" placeholder="At least 8 characters"
        value={form.password} onChange={e => setF({ ...form, password: e.target.value })}
        onKeyDown={e => e.key === 'Enter' && go()} />

      {!isLogin && <PasswordStrength password={form.password} />}

      {!isLogin && (
        <SelectField label="Registering as" value={form.role} onChange={e => setF({ ...form, role: e.target.value })}>
          <option value="patient">Patient — book appointments</option>
          <option value="doctor">Doctor — manage my schedule</option>
        </SelectField>
      )}

      <button className="btn btn-primary" onClick={go} disabled={busy}
        style={{ width: '100%', padding: 14, fontSize: 15, borderRadius: 10, marginTop: 4 }}>
        {busy ? <Spinner size={18} color="#fff" /> : (isLogin ? 'Sign in' : 'Create account')}
      </button>

      {isLogin && (
        <button className="btn btn-text" onClick={() => setPage('forgot-password')}
          style={{ width: '100%', marginTop: 10, textAlign: 'center' }}>
          Forgot your password?
        </button>
      )}

      <div className="hr" style={{ margin: '24px 0' }} />

      <p style={{ textAlign: 'center', fontSize: 14, color: 'var(--text-sub)' }}>
        {isLogin ? "Don't have an account?" : 'Already have an account?'}{' '}
        <button className="btn-text" onClick={() => setPage(isLogin ? 'register' : 'login')}
          style={{ fontWeight: 700, color: 'var(--accent)' }}>
          {isLogin ? 'Sign up free' : 'Sign in'}
        </button>
      </p>
    </AuthCard>
  );
}

/* ─── Forgot / Reset password ────────────────────────────────────────────── */
function ForgotPasswordPage({ setPage }) {
  const toast = useToast();
  const [email, setEmail] = useState('');
  const [busy, setBusy]   = useState(false);
  const go = async () => {
    setBusy(true);
    try { await authAPI.forgotPassword({ email }); toast('Reset link sent — check your email.'); setPage('reset-password'); }
    catch { toast('Something went wrong', 'err'); }
    finally { setBusy(false); }
  };
  return (
    <AuthCard icon="🔑" title="Reset your password" subtitle="Enter your email and we'll send a reset link.">
      <Field label="Email address" type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} onKeyDown={e => e.key === 'Enter' && go()} autoFocus />
      <button className="btn btn-primary" onClick={go} disabled={busy} style={{ width: '100%', padding: 14, fontSize: 15, borderRadius: 10 }}>
        {busy ? <Spinner size={18} color="#fff" /> : 'Send reset link'}
      </button>
      <button className="btn btn-text" onClick={() => setPage('login')} style={{ width: '100%', marginTop: 12, textAlign: 'center' }}>← Back to sign in</button>
    </AuthCard>
  );
}

function ResetPasswordPage({ setPage }) {
  const toast = useToast();
  const [f, setF] = useState({ token: '', new_password: '', confirm: '' });
  const [busy, setBusy] = useState(false);
  const go = async () => {
    if (f.new_password !== f.confirm) return toast('Passwords do not match', 'err');
    setBusy(true);
    try { await authAPI.resetPassword({ token: f.token, new_password: f.new_password }); toast('Password updated.'); setPage('login'); }
    catch (err) { toast(err.response?.data?.detail || 'Reset failed', 'err'); }
    finally { setBusy(false); }
  };
  return (
    <AuthCard icon="🔒" title="Set new password" subtitle="Paste the token from your email below.">
      <Field label="Reset token" placeholder="Paste token here" value={f.token} onChange={e => setF({ ...f, token: e.target.value })} />
      <Field label="New password" type="password" placeholder="Min. 8 characters" value={f.new_password} onChange={e => setF({ ...f, new_password: e.target.value })} />
      <PasswordStrength password={f.new_password} />
      <Field label="Confirm password" type="password" placeholder="Repeat password" value={f.confirm} onChange={e => setF({ ...f, confirm: e.target.value })} />
      <button className="btn btn-primary" onClick={go} disabled={busy} style={{ width: '100%', padding: 14, fontSize: 15, borderRadius: 10 }}>
        {busy ? <Spinner size={18} color="#fff" /> : 'Update password'}
      </button>
    </AuthCard>
  );
}

/* ─── Skeleton ───────────────────────────────────────────────────────────── */
function DoctorSkeleton() {
  return (
    <div className="surface" style={{ padding: 24 }}>
      <div style={{ display: 'flex', gap: 14, marginBottom: 16 }}>
        <div className="sk" style={{ width: 52, height: 52, borderRadius: '50%', flexShrink: 0 }} />
        <div style={{ flex: 1 }}>
          <div className="sk" style={{ height: 13, width: '68%', marginBottom: 8 }} />
          <div className="sk" style={{ height: 11, width: '45%', marginBottom: 8 }} />
          <div className="sk" style={{ height: 11, width: '55%' }} />
        </div>
      </div>
      <div className="sk" style={{ height: 11, width: '90%', marginBottom: 6 }} />
      <div className="sk" style={{ height: 11, width: '65%', marginBottom: 20 }} />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="sk" style={{ height: 26, width: 60 }} />
        <div className="sk" style={{ height: 36, width: 100, borderRadius: 8 }} />
      </div>
    </div>
  );
}

/* ─── Doctors page ───────────────────────────────────────────────────────── */
function DoctorsPage({ setPage, setSelectedDoctor, filters, setFilters }) {
  const [doctors, setDoctors]         = useState([]);
  const [specialties, setSpecialties] = useState([]);
  const [loading, setLoading]         = useState(true);
  const toast = useToast();

  useEffect(() => {
    userAPI.listSpecialties().then(r => setSpecialties(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const p = {};
    if (filters.specialty_id)  p.specialty_id  = filters.specialty_id;
    if (filters.is_available)  p.is_available  = filters.is_available === 'true';
    if (filters.min_fee)       p.min_fee       = filters.min_fee;
    if (filters.max_fee)       p.max_fee       = filters.max_fee;
    userAPI.listDoctors(p)
      .then(r => setDoctors(r.data))
      .catch(() => toast('Could not load doctors', 'err'))
      .finally(() => setLoading(false));
  }, [filters.specialty_id, filters.is_available, filters.min_fee, filters.max_fee]);

  const visible = doctors.filter(d =>
    !filters.search || `${d.first_name} ${d.last_name} ${d.qualification || ''}`.toLowerCase().includes(filters.search.toLowerCase())
  );

  const hasFilters = filters.search || filters.specialty_id || filters.is_available || filters.min_fee || filters.max_fee;

  return (
    <div className="pageIn">
      {/* Sticky filter bar */}
      <div className="filter-bar">
        <div style={{ maxWidth: 1180, margin: '0 auto', padding: '0 24px', display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Search */}
          <div style={{ position: 'relative', flex: '1 1 200px', minWidth: 180 }}>
            <span style={{ position: 'absolute', left: 11, top: '50%', transform: 'translateY(-50%)', fontSize: 15, pointerEvents: 'none', color: 'var(--text-mute)' }}>🔍</span>
            <input className="field-input" placeholder="Name or specialty…"
              value={filters.search || ''}
              onChange={e => setFilters(f => ({ ...f, search: e.target.value }))}
              style={{ paddingLeft: 34, paddingTop: 8, paddingBottom: 8 }} />
          </div>

          <select className="field-input" value={filters.specialty_id}
            onChange={e => setFilters(f => ({ ...f, specialty_id: e.target.value }))}
            style={{ flex: '0 1 170px', width: 'auto', paddingTop: 8, paddingBottom: 8 }}>
            <option value="">All specialties</option>
            {specialties.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>

          <select className="field-input" value={filters.is_available}
            onChange={e => setFilters(f => ({ ...f, is_available: e.target.value }))}
            style={{ flex: '0 1 150px', width: 'auto', paddingTop: 8, paddingBottom: 8 }}>
            <option value="">Any availability</option>
            <option value="true">Available now</option>
          </select>

          <input className="field-input" type="number" placeholder="Min £"
            value={filters.min_fee}
            onChange={e => setFilters(f => ({ ...f, min_fee: e.target.value }))}
            style={{ flex: '0 1 90px', width: 'auto', paddingTop: 8, paddingBottom: 8 }} />

          <input className="field-input" type="number" placeholder="Max £"
            value={filters.max_fee}
            onChange={e => setFilters(f => ({ ...f, max_fee: e.target.value }))}
            style={{ flex: '0 1 90px', width: 'auto', paddingTop: 8, paddingBottom: 8 }} />

          {hasFilters && (
            <button className="btn btn-ghost"
              onClick={() => setFilters({ search:'', specialty_id:'', is_available:'', min_fee:'', max_fee:'' })}
              style={{ padding: '7px 14px', fontSize: 13, flexShrink: 0 }}>
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Page body */}
      <div style={{ maxWidth: 1180, margin: '0 auto', padding: '36px 24px' }}>
        <div style={{ marginBottom: 28 }}>
          <div className="overline">Our network</div>
          <h2 style={{ fontSize: 36, letterSpacing: '-1.5px', color: 'var(--text)' }}>Find a Doctor</h2>
        </div>

        {!loading && (
          <p style={{ color: 'var(--text-sub)', fontSize: 14, marginBottom: 20 }}>
            {visible.length} doctor{visible.length !== 1 ? 's' : ''} found
          </p>
        )}

        {loading ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(300px,1fr))', gap: 16 }}>
            {Array(6).fill(0).map((_, i) => <DoctorSkeleton key={i} />)}
          </div>
        ) : visible.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '80px 24px' }}>
            <div style={{ fontSize: 56, marginBottom: 16 }}>👨‍⚕️</div>
            <h3 style={{ fontSize: 20, marginBottom: 8, color: 'var(--text)' }}>No doctors found</h3>
            <p style={{ color: 'var(--text-sub)', fontSize: 14 }}>Try adjusting your filters.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(300px,1fr))', gap: 16 }}>
            {visible.map((doc, i) => (
              <div key={doc.id} className="surface lift fadeUp"
                style={{ padding: 24, cursor: 'pointer', animationDelay: `${i * .045}s`, display: 'flex', flexDirection: 'column' }}
                onClick={() => { setSelectedDoctor(doc); setPage('doctor-profile'); }}>

                {/* Fee badge — top right */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
                  <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start', flex: 1, minWidth: 0 }}>
                    <Avatar name={`${doc.first_name} ${doc.last_name}`} size={50} fontSize={18} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 2, lineHeight: 1.3, fontFamily: "'Plus Jakarta Sans',sans-serif", color: 'var(--text)' }}>
                        Dr. {doc.first_name} {doc.last_name}
                      </h3>
                      <p style={{ fontSize: 12, color: 'var(--text-sub)', marginBottom: 5 }}>
                        {doc.qualification || 'General Practitioner'}
                      </p>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                        <Stars rating={doc.rating} />
                        <span style={{ fontSize: 11, color: 'var(--text-mute)' }}>({doc.total_reviews})</span>
                      </div>
                    </div>
                  </div>
                  {/* Fee — prominent top right */}
                  <div style={{ textAlign: 'right', flexShrink: 0, marginLeft: 8 }}>
                    <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--text)', fontFamily: "'Plus Jakarta Sans',sans-serif", letterSpacing: '-1px' }}>
                      £{parseFloat(doc.consultation_fee || 0).toFixed(0)}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-mute)', textTransform: 'uppercase', letterSpacing: '.04em' }}>per visit</div>
                  </div>
                </div>

                {/* Tags */}
                <div style={{ display: 'flex', gap: 6, marginBottom: 12, flexWrap: 'wrap' }}>
                  <Badge bg="var(--accent-l)" color="var(--accent)">{doc.experience_years} yrs</Badge>
                  {doc.is_available
                    ? <Badge bg="var(--success-l)" color="var(--success)" dot>Available</Badge>
                    : <Badge bg="var(--surface2)" color="var(--text-mute)">Unavailable</Badge>}
                </div>

                {doc.bio && (
                  <p style={{ fontSize: 13, color: 'var(--text-sub)', lineHeight: 1.65, marginBottom: 16, flex: 1 }}>
                    {doc.bio.length > 88 ? doc.bio.slice(0, 88) + '…' : doc.bio}
                  </p>
                )}

                <div style={{ borderTop: '1px solid var(--border)', paddingTop: 14, marginTop: 'auto', display: 'flex', justifyContent: 'flex-end' }}>
                  <span style={{ fontSize: 13, color: 'var(--accent)', fontWeight: 600, fontFamily: "'Plus Jakarta Sans',sans-serif" }}>View profile →</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Doctor profile ─────────────────────────────────────────────────────── */
function DoctorProfilePage({ doctor, setPage }) {
  const { user } = useAuth();
  const toast    = useToast();
  const [slots, setSlots]     = useState([]);
  const [reviews, setReviews] = useState([]);
  const [tab, setTab]         = useState('about');

  useEffect(() => {
    if (!doctor) return;
    userAPI.getDoctorSlots(doctor.id).then(r => setSlots(r.data)).catch(() => {});
    userAPI.getDoctorReviews(doctor.id).then(r => setReviews(r.data)).catch(() => {});
  }, [doctor]);

  if (!doctor) return null;

  const days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];

  return (
    <div className="pageIn" style={{ maxWidth: 980, margin: '0 auto', padding: '40px 24px' }}>
      <button className="btn btn-ghost" onClick={() => setPage('doctors')}
        style={{ marginBottom: 24, padding: '8px 16px', fontSize: 13 }}>
        ← Back to results
      </button>

      {/* Profile hero */}
      <div className="surface-lg" style={{ padding: 36, marginBottom: 18, boxShadow: 'var(--shadow-md)' }}>
        <div style={{ display: 'flex', gap: 28, flexWrap: 'wrap', alignItems: 'flex-start' }}>
          <Avatar name={`${doctor.first_name} ${doctor.last_name}`} size={96} fontSize={36} />
          <div style={{ flex: 1, minWidth: 220 }}>
            <h2 style={{ fontSize: 32, letterSpacing: '-1.5px', marginBottom: 4, color: 'var(--text)' }}>
              Dr. {doctor.first_name} {doctor.last_name}
            </h2>
            <p style={{ color: 'var(--text-sub)', marginBottom: 14, fontSize: 16 }}>{doctor.qualification}</p>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
              <Badge bg="var(--accent-l)" color="var(--accent)">{doctor.experience_years} yrs experience</Badge>
              {doctor.is_available
                ? <Badge bg="var(--success-l)" color="var(--success)" dot>Available</Badge>
                : <Badge bg="var(--surface2)" color="var(--text-mute)">Unavailable</Badge>}
              {doctor.languages && <Badge bg="var(--warn-l)" color="var(--warn)">{doctor.languages}</Badge>}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Stars rating={doctor.rating} />
              <span style={{ color: 'var(--text-sub)', fontSize: 14 }}>
                {doctor.rating.toFixed(1)} · {doctor.total_reviews} reviews
              </span>
            </div>
          </div>
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <div style={{ fontFamily: "'Plus Jakarta Sans',sans-serif", fontSize: 44, fontWeight: 800, color: 'var(--text)', lineHeight: 1, letterSpacing: '-2px' }}>
              £{parseFloat(doctor.consultation_fee || 0).toFixed(0)}
            </div>
            <div style={{ color: 'var(--text-mute)', fontSize: 13, marginBottom: 16 }}>per consultation</div>
            <button className="btn btn-primary" style={{ padding: '12px 28px', borderRadius: 10 }}
              onClick={() => user ? toast('Appointment booking coming soon!') : setPage('login')}>
              Book appointment
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tab-bar" style={{ marginBottom: 18 }}>
        {[['about','About'],['availability','Availability'],['reviews',`Reviews${reviews.length ? ` (${reviews.length})` : ''}`]].map(([k,l]) => (
          <button key={k} className={`tab${tab===k?' active':''}`} onClick={() => setTab(k)}>{l}</button>
        ))}
      </div>

      {/* Tab content */}
      <div className="surface-lg fadeIn" style={{ padding: 28 }}>
        {tab === 'about' && (
          <>
            <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 14, color: 'var(--text)', fontFamily: "'Plus Jakarta Sans',sans-serif" }}>About</h3>
            <p style={{ color: 'var(--text-sub)', lineHeight: 1.8, fontSize: 15 }}>{doctor.bio || 'No biography provided.'}</p>
            {doctor.clinic_address && (
              <div style={{ marginTop: 20, padding: 16, background: 'var(--surface2)', borderRadius: 10 }}>
                <p style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-mute)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>Location</p>
                <p style={{ fontSize: 14, color: 'var(--text)' }}>📍 {doctor.clinic_address}</p>
              </div>
            )}
          </>
        )}
        {tab === 'availability' && (
          <>
            <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16, color: 'var(--text)', fontFamily: "'Plus Jakarta Sans',sans-serif" }}>Weekly schedule</h3>
            {slots.length === 0
              ? <p style={{ color: 'var(--text-sub)' }}>No availability set yet.</p>
              : slots.map(s => (
                <div key={s.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: 'var(--surface2)', borderRadius: 10, marginBottom: 8 }}>
                  <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text)', fontFamily: "'Plus Jakarta Sans',sans-serif" }}>{days[s.day_of_week]}</span>
                  <span style={{ color: 'var(--text-sub)', fontSize: 14 }}>{s.start_time} – {s.end_time}</span>
                  <Badge bg="var(--accent-l)" color="var(--accent)">{s.slot_duration} min</Badge>
                </div>
              ))}
          </>
        )}
        {tab === 'reviews' && (
          <>
            <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16, color: 'var(--text)', fontFamily: "'Plus Jakarta Sans',sans-serif" }}>Patient reviews</h3>
            {reviews.length === 0
              ? <p style={{ color: 'var(--text-sub)' }}>No reviews yet.</p>
              : reviews.map(r => (
                <div key={r.id} style={{ paddingBottom: 16, borderBottom: '1px solid var(--border)', marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <Stars rating={r.rating} />
                    <span style={{ color: 'var(--text-mute)', fontSize: 12 }}>{new Date(r.created_at).toLocaleDateString()}</span>
                  </div>
                  {r.comment && <p style={{ color: 'var(--text)', fontSize: 14, lineHeight: 1.65 }}>{r.comment}</p>}
                </div>
              ))}
          </>
        )}
      </div>
    </div>
  );
}

/* ─── Dashboard ──────────────────────────────────────────────────────────── */
function DashboardPage({ setPage }) {
  const { user } = useAuth();
  return (
    <div className="pageIn" style={{ maxWidth: 1040, margin: '0 auto', padding: '48px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, marginBottom: 40 }}>
        <div>
          <div className="overline">Your dashboard</div>
          <h2 style={{ fontSize: 36, letterSpacing: '-1.5px', color: 'var(--text)' }}>
            Hello, {user?.email.split('@')[0]} 👋
          </h2>
          <p style={{ color: 'var(--text-sub)', marginTop: 4 }}>Here's your health overview.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setPage('doctors')} style={{ padding: '11px 24px' }}>
          + Book appointment
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: 14, marginBottom: 32 }}>
        {[
          { label:'Upcoming',  value:'0',  unit:'appointments', icon:'📅', color:'var(--accent)',  bg:'var(--accent-l)'  },
          { label:'Completed', value:'0',  unit:'visits',       icon:'✅', color:'var(--success)', bg:'var(--success-l)' },
          { label:'Pending',   value:'£0', unit:'payments',     icon:'💳', color:'var(--warn)',    bg:'var(--warn-l)'    },
        ].map(s => (
          <div key={s.label} className="surface" style={{ padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
              <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.08em', color: 'var(--text-mute)', fontFamily: "'Plus Jakarta Sans',sans-serif" }}>{s.label}</span>
              <span style={{ fontSize: 20 }}>{s.icon}</span>
            </div>
            <div style={{ fontSize: 40, fontWeight: 800, color: s.color, fontFamily: "'Plus Jakarta Sans',sans-serif", letterSpacing: '-2px', lineHeight: 1 }}>{s.value}</div>
            <div style={{ fontSize: 13, color: 'var(--text-mute)', marginTop: 6 }}>{s.unit}</div>
          </div>
        ))}
      </div>

      <div className="surface-lg" style={{ padding: 48, textAlign: 'center' }}>
        <div style={{ fontSize: 56, marginBottom: 16 }}>🩺</div>
        <h3 style={{ fontSize: 22, fontWeight: 700, marginBottom: 10, color: 'var(--text)', fontFamily: "'Plus Jakarta Sans',sans-serif" }}>No appointments yet</h3>
        <p style={{ color: 'var(--text-sub)', marginBottom: 28, maxWidth: 360, margin: '0 auto 28px', lineHeight: 1.7 }}>
          Find a doctor and book your first appointment in under a minute.
        </p>
        <button className="btn btn-primary" onClick={() => setPage('doctors')} style={{ padding: '12px 32px', borderRadius: 10 }}>
          Browse doctors
        </button>
      </div>
    </div>
  );
}

/* ─── Root ───────────────────────────────────────────────────────────────── */
export default function App() {
  const [page, setPage]             = useState('home');
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [filters, setFilters]       = useState({
    search: '', specialty_id: '', is_available: '', min_fee: '', max_fee: '',
  });

  const screen = () => {
    switch (page) {
      case 'login':           return <AuthPage mode="login"    setPage={setPage} />;
      case 'register':        return <AuthPage mode="register" setPage={setPage} />;
      case 'forgot-password': return <ForgotPasswordPage       setPage={setPage} />;
      case 'reset-password':  return <ResetPasswordPage        setPage={setPage} />;
      case 'doctors':         return <DoctorsPage setPage={setPage} setSelectedDoctor={setSelectedDoc} filters={filters} setFilters={setFilters} />;
      case 'doctor-profile':  return <DoctorProfilePage doctor={selectedDoc} setPage={setPage} />;
      case 'dashboard':       return <DashboardPage setPage={setPage} />;
      default:                return <HomePage setPage={setPage} setFilters={setFilters} />;
    }
  };

  return (
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <style>{BASE_CSS}</style>
          <Navbar page={page} setPage={setPage} />
          <main>{screen()}</main>
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}
