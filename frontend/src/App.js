import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI, userAPI } from './api';

/* ─── Design tokens ──────────────────────────────────────────────────────── */
const S = {
  bg:      '#f0f4f8',
  white:   '#ffffff',
  card:    '#ffffff',
  border:  '#e2e8f0',
  accent:  '#0ea5e9',
  accentD: '#0284c7',
  success: '#10b981',
  danger:  '#f43f5e',
  warn:    '#f59e0b',
  text:    '#1e293b',
  muted:   '#64748b',
  muted2:  '#94a3b8',
};

const globalCSS = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: ${S.bg};
    color: ${S.text};
    font-family: 'Source Sans 3', sans-serif;
    font-size: 15px;
    line-height: 1.65;
    min-height: 100vh;
  }
  h1,h2,h3,h4 { font-family: 'Playfair Display', serif; }
  button { cursor: pointer; font-family: inherit; }
  input, select, textarea { font-family: inherit; }

  @keyframes fadeUp { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:none; } }
  @keyframes spin   { to { transform: rotate(360deg); } }
  @keyframes slideIn { from { opacity:0; transform:translateX(24px); } to { opacity:1; transform:none; } }
  @keyframes progress { from { width:100%; } to { width:0%; } }

  .fade-up  { animation: fadeUp  0.3s ease forwards; }
  .slide-in { animation: slideIn 0.25s ease forwards; }

  .btn-primary {
    display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    padding: 11px 24px; font-size: 14px; font-weight: 600;
    background: ${S.accent}; color: #fff;
    border: none; border-radius: 8px; cursor: pointer;
    transition: background 0.15s, transform 0.1s, box-shadow 0.15s;
    box-shadow: 0 1px 3px rgba(14,165,233,0.3);
  }
  .btn-primary:hover:not(:disabled) { background: ${S.accentD}; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(14,165,233,0.3); }
  .btn-primary:active:not(:disabled) { transform: scale(0.98); }
  .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

  .btn-ghost {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 9px 18px; font-size: 13px; font-weight: 600;
    background: transparent; color: ${S.muted};
    border: 1px solid ${S.border}; border-radius: 8px; cursor: pointer;
    transition: all 0.15s;
  }
  .btn-ghost:hover { color: ${S.text}; border-color: #cbd5e1; background: #f8fafc; }

  .btn-danger {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 7px 14px; font-size: 13px; font-weight: 600;
    background: #fff1f2; color: ${S.danger};
    border: 1px solid #fecdd3; border-radius: 8px; cursor: pointer;
    transition: all 0.15s;
  }
  .btn-danger:hover { background: #ffe4e6; }

  .field { margin-bottom: 18px; }
  .field label { display: block; margin-bottom: 6px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: ${S.muted}; }
  .field input, .field select, .field textarea {
    width: 100%; padding: 10px 14px;
    background: #fff; border: 1px solid ${S.border};
    border-radius: 8px; color: ${S.text}; font-size: 14px; outline: none;
    transition: border-color 0.15s, box-shadow 0.15s;
  }
  .field input:focus, .field select:focus, .field textarea:focus {
    border-color: ${S.accent}; box-shadow: 0 0 0 3px rgba(14,165,233,0.12);
  }
  .field input::placeholder { color: ${S.muted2}; }

  .card {
    background: ${S.white}; border: 1px solid ${S.border};
    border-radius: 12px; transition: box-shadow 0.2s, transform 0.2s;
  }
  .card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.08); }

  .badge {
    display: inline-block; padding: 3px 10px; border-radius: 99px;
    font-size: 11px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
  }

  .toast-wrap { position: fixed; bottom: 24px; right: 24px; z-index: 9999; display: flex; flex-direction: column; gap: 10px; }
  .toast {
    min-width: 280px; max-width: 360px; padding: 14px 18px; border-radius: 10px;
    font-size: 14px; font-weight: 500; display: flex; gap: 10px; align-items: flex-start;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15); animation: slideIn 0.25s ease; position: relative; overflow: hidden;
  }
  .toast::after { content:''; position:absolute; bottom:0; left:0; height:3px; animation: progress 3.5s linear forwards; }
  .toast-success { background:#f0fdf4; border:1px solid #bbf7d0; color:#166534; }
  .toast-success::after { background: ${S.success}; }
  .toast-error   { background:#fff1f2; border:1px solid #fecdd3; color:#9f1239; }
  .toast-error::after { background: ${S.danger}; }

  .divider { border:none; border-top:1px solid ${S.border}; margin:20px 0; }

  .spinner { width:22px; height:22px; border-radius:50%; border:2px solid ${S.border}; border-top-color:${S.accent}; animation:spin 0.7s linear infinite; }

  .nav-link {
    padding: 8px 16px; font-size: 14px; font-weight: 600;
    color: ${S.muted}; background: transparent; border: none; border-radius: 8px;
    cursor: pointer; transition: all 0.15s;
  }
  .nav-link:hover { color: ${S.text}; background: #f1f5f9; }
  .nav-link.active { color: ${S.accent}; background: #e0f2fe; }

  .star { color: #fbbf24; font-size: 14px; }
  .star.empty { color: ${S.border}; }

  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: ${S.bg}; }
  ::-webkit-scrollbar-thumb { background: ${S.border}; border-radius: 3px; }
`;

/* ─── Context ────────────────────────────────────────────────────────────── */
const AuthContext  = createContext(null);
const ToastContext = createContext(null);
function useAuth()  { return useContext(AuthContext); }
function useToast() { return useContext(ToastContext); }

/* ─── Toast ──────────────────────────────────────────────────────────────── */
function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const show = useCallback((msg, type = 'success') => {
    const id = Date.now();
    setToasts(p => [...p, { id, msg, type }]);
    setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 3600);
  }, []);
  return (
    <ToastContext.Provider value={show}>
      {children}
      <div className="toast-wrap">
        {toasts.map(t => (
          <div key={t.id} className={`toast toast-${t.type}`}>
            <span style={{ fontWeight: 800 }}>{t.type === 'success' ? '✓' : '✕'}</span>
            <span>{t.msg}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

/* ─── Auth ───────────────────────────────────────────────────────────────── */
function AuthProvider({ children }) {
  const [user, setUser]     = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const stored = localStorage.getItem('user');
    const token  = localStorage.getItem('token');
    if (stored && token) setUser(JSON.parse(stored));
    setLoading(false);
  }, []);
  const login  = (token, refreshToken, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('refresh_token', refreshToken);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };
  const logout = () => {
    localStorage.clear();
    setUser(null);
  };
  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
}

/* ─── Shared components ──────────────────────────────────────────────────── */
function Field({ label, type = 'text', ...props }) {
  return (
    <div className="field">
      {label && <label>{label}</label>}
      <input type={type} {...props} />
    </div>
  );
}

function Spinner() {
  return <div className="spinner" />;
}

function Stars({ rating, max = 5 }) {
  return (
    <span>
      {Array.from({ length: max }).map((_, i) => (
        <span key={i} className={`star${i < Math.round(rating) ? '' : ' empty'}`}>★</span>
      ))}
    </span>
  );
}

function Badge({ children, color = S.accent }) {
  return (
    <span className="badge" style={{ background: color + '18', color, border: `1px solid ${color}33` }}>
      {children}
    </span>
  );
}

/* ─── Navbar ─────────────────────────────────────────────────────────────── */
function Navbar({ page, setPage }) {
  const { user, logout } = useAuth();
  return (
    <nav style={{
      background: S.white, borderBottom: `1px solid ${S.border}`,
      padding: '0 32px', height: 64,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      position: 'sticky', top: 0, zIndex: 100,
      boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
        <span onClick={() => setPage('home')} style={{
          fontFamily: 'Playfair Display, serif', fontSize: 22, fontWeight: 800,
          color: S.accent, cursor: 'pointer',
        }}>
          Helia
        </span>
        <div style={{ display: 'flex', gap: 4 }}>
          <button className={`nav-link${page === 'home' ? ' active' : ''}`} onClick={() => setPage('home')}>Home</button>
          <button className={`nav-link${page === 'doctors' ? ' active' : ''}`} onClick={() => setPage('doctors')}>Find Doctors</button>
          {user && (
            <button className={`nav-link${page === 'dashboard' ? ' active' : ''}`} onClick={() => setPage('dashboard')}>Dashboard</button>
          )}
        </div>
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        {user ? (
          <>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '5px 12px 5px 8px', background: '#f0f9ff',
              border: `1px solid #bae6fd`, borderRadius: 99,
            }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%',
                background: S.accent, color: '#fff',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 13, fontWeight: 700,
              }}>
                {user.email[0].toUpperCase()}
              </div>
              <span style={{ fontSize: 13, fontWeight: 600, color: S.accentD }}>{user.email}</span>
            </div>
            <button className="btn-ghost" onClick={logout}>Sign out</button>
          </>
        ) : (
          <>
            <button className="btn-ghost" onClick={() => setPage('login')}>Sign in</button>
            <button className="btn-primary" onClick={() => setPage('register')}>Get started</button>
          </>
        )}
      </div>
    </nav>
  );
}

/* ─── Home page ──────────────────────────────────────────────────────────── */
function HomePage({ setPage }) {
  const [specialties, setSpecialties] = useState([]);

  useEffect(() => {
    userAPI.listSpecialties()
      .then(r => setSpecialties(r.data))
      .catch(() => {});
  }, []);

  const stats = [
    { label: 'Doctors',      value: '500+',  icon: '👨‍⚕️' },
    { label: 'Specialties',  value: '30+',   icon: '🏥' },
    { label: 'Appointments', value: '10k+',  icon: '📅' },
    { label: 'Patients',     value: '50k+',  icon: '❤️' },
  ];

  return (
    <div>
      {/* Hero */}
      <div style={{
        background: `linear-gradient(135deg, #0ea5e9, #0284c7)`,
        padding: '80px 40px', textAlign: 'center', color: '#fff',
      }}>
        <h1 style={{ fontSize: 52, fontWeight: 800, marginBottom: 16, lineHeight: 1.1 }}>
          Your Health, Our Priority
        </h1>
        <p style={{ fontSize: 18, opacity: 0.9, marginBottom: 36, maxWidth: 560, margin: '0 auto 36px' }}>
          Book appointments with top doctors in your area. Fast, easy, and reliable.
        </p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
          <button className="btn-primary" onClick={() => setPage('doctors')}
            style={{ background: '#fff', color: S.accent, fontSize: 16, padding: '14px 32px' }}>
            Find a Doctor
          </button>
          <button className="btn-ghost" onClick={() => setPage('register')}
            style={{ color: '#fff', borderColor: 'rgba(255,255,255,0.4)', fontSize: 16, padding: '14px 32px' }}>
            Create Account
          </button>
        </div>
      </div>

      {/* Stats */}
      <div style={{ background: S.white, borderBottom: `1px solid ${S.border}`, padding: '32px 40px' }}>
        <div style={{ maxWidth: 900, margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 24 }}>
          {stats.map(s => (
            <div key={s.label} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 32, marginBottom: 4 }}>{s.icon}</div>
              <div style={{ fontSize: 28, fontWeight: 800, fontFamily: 'Playfair Display', color: S.accent }}>{s.value}</div>
              <div style={{ color: S.muted, fontSize: 14 }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Specialties */}
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '60px 24px' }}>
        <h2 style={{ fontSize: 32, textAlign: 'center', marginBottom: 8 }}>Browse by Specialty</h2>
        <p style={{ textAlign: 'center', color: S.muted, marginBottom: 40 }}>Find the right specialist for your needs</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 16 }}>
          {specialties.length > 0 ? specialties.map(s => (
            <div key={s.id} className="card fade-up" onClick={() => setPage('doctors')}
              style={{ padding: 24, textAlign: 'center', cursor: 'pointer' }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>🏥</div>
              <p style={{ fontWeight: 600, fontSize: 14, color: S.text }}>{s.name}</p>
            </div>
          )) : (
            // Placeholder specialties before seeding
            ['Cardiology','Dermatology','Neurology','Orthopaedics','Paediatrics','General Practice'].map(name => (
              <div key={name} className="card fade-up" onClick={() => setPage('doctors')}
                style={{ padding: 24, textAlign: 'center', cursor: 'pointer' }}>
                <div style={{ fontSize: 32, marginBottom: 8 }}>🏥</div>
                <p style={{ fontWeight: 600, fontSize: 14 }}>{name}</p>
              </div>
            ))
          )}
        </div>
      </div>

      {/* How it works */}
      <div style={{ background: S.white, padding: '60px 24px' }}>
        <div style={{ maxWidth: 900, margin: '0 auto' }}>
          <h2 style={{ fontSize: 32, textAlign: 'center', marginBottom: 48 }}>How It Works</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 32 }}>
            {[
              { step: '1', title: 'Find a Doctor', desc: 'Search by specialty, location, or availability', icon: '🔍' },
              { step: '2', title: 'Book Appointment', desc: 'Choose a convenient time slot and confirm', icon: '📅' },
              { step: '3', title: 'Get Care',        desc: 'Attend your appointment and feel better', icon: '❤️' },
            ].map(item => (
              <div key={item.step} style={{ textAlign: 'center' }}>
                <div style={{
                  width: 64, height: 64, borderRadius: '50%',
                  background: '#e0f2fe', margin: '0 auto 16px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 28,
                }}>
                  {item.icon}
                </div>
                <h3 style={{ fontSize: 18, marginBottom: 8 }}>{item.title}</h3>
                <p style={{ color: S.muted, fontSize: 14 }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Auth pages ─────────────────────────────────────────────────────────── */
function AuthPage({ mode, setPage }) {
  const { login }           = useAuth();
  const toast               = useToast();
  const [form, setForm]     = useState({ email: '', password: '', role: 'patient' });
  const [otp, setOtp]       = useState('');
  const [needOtp, setNeedOtp] = useState(false);
  const [loading, setLoading] = useState(false);
  const isLogin = mode === 'login';

  const handleSubmit = async () => {
    setLoading(true);
    try {
      if (isLogin) {
        const { data } = await authAPI.login({ ...form, otp_code: otp || undefined });
        login(data.access_token, data.refresh_token, { email: form.email, role: 'patient' });
        toast('Welcome back!');
        setPage('dashboard');
      } else {
        await authAPI.register(form);
        toast('Account created! Check your email to verify.');
        setPage('verify-email');
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string' && detail.includes('2FA')) {
        setNeedOtp(true);
        toast('2FA code sent to your email', 'success');
      } else if (Array.isArray(detail)) {
        toast(detail[0]?.msg || 'Validation error', 'error');
      } else {
        toast(detail || 'Something went wrong', 'error');
      }
    } finally { setLoading(false); }
  };

  return (
    <div style={{ minHeight: 'calc(100vh - 64px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24, background: S.bg }}>
      <div className="card fade-up" style={{ padding: '40px 44px', width: '100%', maxWidth: 420 }}>
        <h2 style={{ fontSize: 28, fontWeight: 800, marginBottom: 6 }}>
          {isLogin ? 'Welcome back' : 'Create account'}
        </h2>
        <p style={{ color: S.muted, marginBottom: 32, fontSize: 14 }}>
          {isLogin ? 'Sign in to your Helia account' : 'Join Helia to book appointments'}
        </p>

        <Field label="Email" type="email" value={form.email}
          onChange={e => setForm({ ...form, email: e.target.value })} placeholder="you@example.com" />
        <Field label="Password" type="password" value={form.password}
          onChange={e => setForm({ ...form, password: e.target.value })} placeholder="••••••••" />

        {!isLogin && (
          <div className="field">
            <label>I am a</label>
            <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
              <option value="patient">Patient</option>
              <option value="doctor">Doctor</option>
            </select>
          </div>
        )}

        {needOtp && (
          <Field label="2FA Code (sent to your email)" value={otp}
            onChange={e => setOtp(e.target.value)} placeholder="123456" />
        )}

        <button className="btn-primary" onClick={handleSubmit} disabled={loading}
          style={{ width: '100%', marginTop: 8, padding: '13px', fontSize: 15 }}>
          {loading ? <Spinner /> : (isLogin ? 'Sign in' : 'Create account')}
        </button>

        <p style={{ textAlign: 'center', marginTop: 24, color: S.muted, fontSize: 13 }}>
          {isLogin ? "Don't have an account? " : 'Already have an account? '}
          <span onClick={() => setPage(isLogin ? 'register' : 'login')}
            style={{ color: S.accent, cursor: 'pointer', fontWeight: 700 }}>
            {isLogin ? 'Register' : 'Sign in'}
          </span>
        </p>
        {isLogin && (
          <p style={{ textAlign: 'center', marginTop: 10, fontSize: 13 }}>
            <span onClick={() => setPage('forgot-password')}
              style={{ color: S.muted, cursor: 'pointer', textDecoration: 'underline' }}>
              Forgot your password?
            </span>
          </p>
        )}
      </div>
    </div>
  );
}

/* ─── Verify email page ──────────────────────────────────────────────────── */
function VerifyEmailPage({ setPage }) {
  const toast = useToast();
  const [code, setCode]     = useState('');
  const [loading, setLoading] = useState(false);

  const handleVerify = async () => {
    setLoading(true);
    try {
      await authAPI.verifyEmail({ token: code });
      toast('Email verified! You can now sign in.');
      setPage('login');
    } catch (err) {
      toast(err.response?.data?.detail || 'Invalid code', 'error');
    } finally { setLoading(false); }
  };

  return (
    <div style={{ minHeight: 'calc(100vh - 64px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <div className="card fade-up" style={{ padding: '40px 44px', width: '100%', maxWidth: 420, textAlign: 'center' }}>
        <div style={{ fontSize: 52, marginBottom: 16 }}>📧</div>
        <h2 style={{ fontSize: 26, marginBottom: 8 }}>Verify your email</h2>
        <p style={{ color: S.muted, marginBottom: 28, fontSize: 14 }}>
          Enter the 6-digit code sent to your email address.
          Check Mailhog at <strong>http://localhost:8025</strong>
        </p>
        <Field label="Verification code" value={code}
          onChange={e => setCode(e.target.value)} placeholder="123456"
          style={{ textAlign: 'center', fontSize: 24, letterSpacing: 8 }} />
        <button className="btn-primary" onClick={handleVerify} disabled={loading}
          style={{ width: '100%', padding: '13px', fontSize: 15 }}>
          {loading ? <Spinner /> : 'Verify email'}
        </button>
        <p style={{ marginTop: 20, fontSize: 13 }}>
          <span onClick={() => setPage('login')} style={{ color: S.accent, cursor: 'pointer' }}>
            Back to sign in
          </span>
        </p>
      </div>
    </div>
  );
}

/* ─── Forgot/Reset password ──────────────────────────────────────────────── */
function ForgotPasswordPage({ setPage }) {
  const toast = useToast();
  const [email, setEmail]     = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await authAPI.forgotPassword({ email });
      toast('Check your email for a reset link (Mailhog: localhost:8025)');
      setPage('reset-password');
    } catch (err) {
      toast(err.response?.data?.detail || 'Error', 'error');
    } finally { setLoading(false); }
  };

  return (
    <div style={{ minHeight: 'calc(100vh - 64px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <div className="card fade-up" style={{ padding: '40px 44px', width: '100%', maxWidth: 420 }}>
        <h2 style={{ fontSize: 26, marginBottom: 8 }}>Reset password</h2>
        <p style={{ color: S.muted, marginBottom: 28, fontSize: 14 }}>Enter your email to receive a reset link.</p>
        <Field label="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" />
        <button className="btn-primary" onClick={handleSubmit} disabled={loading} style={{ width: '100%', padding: '13px' }}>
          {loading ? <Spinner /> : 'Send reset link'}
        </button>
        <p style={{ textAlign: 'center', marginTop: 20, fontSize: 13 }}>
          <span onClick={() => setPage('login')} style={{ color: S.accent, cursor: 'pointer' }}>Back to sign in</span>
        </p>
      </div>
    </div>
  );
}

function ResetPasswordPage({ setPage }) {
  const toast = useToast();
  const [form, setForm]     = useState({ token: '', new_password: '', confirm: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (form.new_password !== form.confirm) return toast('Passwords do not match', 'error');
    setLoading(true);
    try {
      await authAPI.resetPassword({ token: form.token, new_password: form.new_password });
      toast('Password reset successfully!');
      setPage('login');
    } catch (err) {
      toast(err.response?.data?.detail || 'Error', 'error');
    } finally { setLoading(false); }
  };

  return (
    <div style={{ minHeight: 'calc(100vh - 64px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <div className="card fade-up" style={{ padding: '40px 44px', width: '100%', maxWidth: 420 }}>
        <h2 style={{ fontSize: 26, marginBottom: 8 }}>Set new password</h2>
        <p style={{ color: S.muted, marginBottom: 28, fontSize: 14 }}>Paste the token from your email and choose a new password.</p>
        <Field label="Reset token" value={form.token} onChange={e => setForm({ ...form, token: e.target.value })} placeholder="Paste token here" style={{ fontFamily: 'monospace', fontSize: 12 }} />
        <Field label="New password" type="password" value={form.new_password} onChange={e => setForm({ ...form, new_password: e.target.value })} placeholder="••••••••" />
        <Field label="Confirm password" type="password" value={form.confirm} onChange={e => setForm({ ...form, confirm: e.target.value })} placeholder="••••••••" />
        <button className="btn-primary" onClick={handleSubmit} disabled={loading} style={{ width: '100%', padding: '13px' }}>
          {loading ? <Spinner /> : 'Reset password'}
        </button>
      </div>
    </div>
  );
}

/* ─── Doctors listing page ───────────────────────────────────────────────── */
function DoctorsPage({ setPage, setSelectedDoctor }) {
  const [doctors, setDoctors]         = useState([]);
  const [specialties, setSpecialties] = useState([]);
  const [loading, setLoading]         = useState(true);
  const [filters, setFilters]         = useState({ specialty_id: '', is_available: '', min_fee: '', max_fee: '' });
  const toast = useToast();

  useEffect(() => {
    userAPI.listSpecialties().then(r => setSpecialties(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = {};
    if (filters.specialty_id) params.specialty_id = filters.specialty_id;
    if (filters.is_available !== '') params.is_available = filters.is_available === 'true';
    if (filters.min_fee) params.min_fee = filters.min_fee;
    if (filters.max_fee) params.max_fee = filters.max_fee;
    userAPI.listDoctors(params)
      .then(r => setDoctors(r.data))
      .catch(() => toast('Failed to load doctors', 'error'))
      .finally(() => setLoading(false));
  }, [filters]);

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 24px' }}>
      <h2 style={{ fontSize: 32, marginBottom: 6 }}>Find a Doctor</h2>
      <p style={{ color: S.muted, marginBottom: 32 }}>Browse our network of verified healthcare professionals</p>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 32, flexWrap: 'wrap', background: S.white, padding: 20, borderRadius: 12, border: `1px solid ${S.border}` }}>
        <select value={filters.specialty_id} onChange={e => setFilters({ ...filters, specialty_id: e.target.value })}
          style={{ padding: '9px 14px', border: `1px solid ${S.border}`, borderRadius: 8, fontSize: 14, color: S.text, background: S.white, outline: 'none' }}>
          <option value="">All specialties</option>
          {specialties.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <select value={filters.is_available} onChange={e => setFilters({ ...filters, is_available: e.target.value })}
          style={{ padding: '9px 14px', border: `1px solid ${S.border}`, borderRadius: 8, fontSize: 14, color: S.text, background: S.white, outline: 'none' }}>
          <option value="">Any availability</option>
          <option value="true">Available now</option>
        </select>
        <input type="number" placeholder="Min fee (£)" value={filters.min_fee}
          onChange={e => setFilters({ ...filters, min_fee: e.target.value })}
          style={{ padding: '9px 14px', border: `1px solid ${S.border}`, borderRadius: 8, fontSize: 14, width: 140, outline: 'none' }} />
        <input type="number" placeholder="Max fee (£)" value={filters.max_fee}
          onChange={e => setFilters({ ...filters, max_fee: e.target.value })}
          style={{ padding: '9px 14px', border: `1px solid ${S.border}`, borderRadius: 8, fontSize: 14, width: 140, outline: 'none' }} />
        {Object.values(filters).some(v => v !== '') && (
          <button className="btn-ghost" onClick={() => setFilters({ specialty_id:'', is_available:'', min_fee:'', max_fee:'' })}>Clear</button>
        )}
      </div>

      {/* Doctor grid */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}><Spinner /></div>
      ) : doctors.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 80, color: S.muted }}>
          <p style={{ fontSize: 48, marginBottom: 16 }}>👨‍⚕️</p>
          <p style={{ fontSize: 18 }}>No doctors found</p>
          <p style={{ fontSize: 14, marginTop: 8 }}>Try adjusting your filters or run the seed script</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
          {doctors.map((doc, i) => (
            <div key={doc.id} className="card fade-up" style={{ padding: 24, animationDelay: `${i * 0.05}s` }}>
              <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
                <div style={{
                  width: 56, height: 56, borderRadius: '50%',
                  background: '#e0f2fe', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 22, flexShrink: 0,
                }}>👨‍⚕️</div>
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 2 }}>
                    Dr. {doc.first_name} {doc.last_name}
                  </h3>
                  <p style={{ color: S.muted, fontSize: 13 }}>{doc.qualification || 'General Practitioner'}</p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
                    <Stars rating={doc.rating} />
                    <span style={{ fontSize: 12, color: S.muted }}>({doc.total_reviews})</span>
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
                <Badge color={S.accent}>{doc.experience_years} yrs exp</Badge>
                {doc.is_available
                  ? <Badge color={S.success}>Available</Badge>
                  : <Badge color={S.danger}>Unavailable</Badge>}
              </div>
              {doc.bio && <p style={{ color: S.muted, fontSize: 13, marginBottom: 16, lineHeight: 1.5 }}>{doc.bio.slice(0, 100)}{doc.bio.length > 100 ? '...' : ''}</p>}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 20, fontWeight: 800, color: S.accent }}>£{doc.consultation_fee}</span>
                <button className="btn-primary" style={{ padding: '8px 18px', fontSize: 13 }}
                  onClick={() => { setSelectedDoctor(doc); setPage('doctor-profile'); }}>
                  View Profile
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─── Doctor profile page ────────────────────────────────────────────────── */
function DoctorProfilePage({ doctor, setPage }) {
  const { user } = useAuth();
  const toast    = useToast();
  const [slots, setSlots]     = useState([]);
  const [reviews, setReviews] = useState([]);

  useEffect(() => {
    if (!doctor) return;
    userAPI.getDoctorSlots(doctor.id).then(r => setSlots(r.data)).catch(() => {});
    userAPI.getDoctorReviews(doctor.id).then(r => setReviews(r.data)).catch(() => {});
  }, [doctor]);

  if (!doctor) return null;

  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '40px 24px' }}>
      <button className="btn-ghost" onClick={() => setPage('doctors')} style={{ marginBottom: 24 }}>
        ← Back to doctors
      </button>

      {/* Profile header */}
      <div className="card" style={{ padding: 32, marginBottom: 24, display: 'flex', gap: 28, alignItems: 'flex-start' }}>
        <div style={{
          width: 100, height: 100, borderRadius: '50%',
          background: '#e0f2fe', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 48, flexShrink: 0,
        }}>👨‍⚕️</div>
        <div style={{ flex: 1 }}>
          <h2 style={{ fontSize: 28, fontWeight: 800, marginBottom: 4 }}>Dr. {doctor.first_name} {doctor.last_name}</h2>
          <p style={{ color: S.muted, marginBottom: 8 }}>{doctor.qualification}</p>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
            <Badge color={S.accent}>{doctor.experience_years} years experience</Badge>
            {doctor.is_available ? <Badge color={S.success}>Available</Badge> : <Badge color={S.danger}>Unavailable</Badge>}
            {doctor.languages && <Badge color={S.warn}>{doctor.languages}</Badge>}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Stars rating={doctor.rating} />
            <span style={{ color: S.muted, fontSize: 14 }}>{doctor.rating.toFixed(1)} ({doctor.total_reviews} reviews)</span>
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <p style={{ fontSize: 32, fontWeight: 800, color: S.accent }}>£{doctor.consultation_fee}</p>
          <p style={{ color: S.muted, fontSize: 13 }}>per consultation</p>
          <button className="btn-primary" style={{ marginTop: 12 }}
            onClick={() => { if (!user) { setPage('login'); } else { toast('Appointment booking coming in Week 2!'); } }}>
            Book Appointment
          </button>
        </div>
      </div>

      {/* Bio */}
      {doctor.bio && (
        <div className="card" style={{ padding: 24, marginBottom: 24 }}>
          <h3 style={{ fontSize: 18, marginBottom: 12 }}>About</h3>
          <p style={{ color: S.muted, lineHeight: 1.7 }}>{doctor.bio}</p>
        </div>
      )}

      {/* Availability */}
      {slots.length > 0 && (
        <div className="card" style={{ padding: 24, marginBottom: 24 }}>
          <h3 style={{ fontSize: 18, marginBottom: 16 }}>Availability</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {slots.map(slot => (
              <div key={slot.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: `1px solid ${S.border}` }}>
                <span style={{ fontWeight: 600 }}>{days[slot.day_of_week]}</span>
                <span style={{ color: S.muted }}>{slot.start_time} — {slot.end_time}</span>
                <Badge color={S.accent}>{slot.slot_duration} min slots</Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reviews */}
      <div className="card" style={{ padding: 24 }}>
        <h3 style={{ fontSize: 18, marginBottom: 16 }}>Patient Reviews</h3>
        {reviews.length === 0 ? (
          <p style={{ color: S.muted }}>No reviews yet.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {reviews.map(r => (
              <div key={r.id} style={{ paddingBottom: 16, borderBottom: `1px solid ${S.border}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <Stars rating={r.rating} />
                  <span style={{ color: S.muted, fontSize: 12 }}>{new Date(r.created_at).toLocaleDateString()}</span>
                </div>
                {r.comment && <p style={{ color: S.text, fontSize: 14 }}>{r.comment}</p>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Dashboard page ─────────────────────────────────────────────────────── */
function DashboardPage({ setPage }) {
  const { user } = useAuth();
  const toast    = useToast();

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: '40px 24px' }}>
      <h2 style={{ fontSize: 32, marginBottom: 6 }}>Dashboard</h2>
      <p style={{ color: S.muted, marginBottom: 36 }}>Welcome back, {user?.email}</p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, marginBottom: 36 }}>
        {[
          { label: 'Upcoming Appointments', value: '0',   icon: '📅', color: S.accent },
          { label: 'Past Appointments',      value: '0',   icon: '✅', color: S.success },
          { label: 'Pending Payments',       value: '£0',  icon: '💳', color: S.warn },
        ].map(stat => (
          <div key={stat.label} className="card" style={{ padding: 24, display: 'flex', gap: 16, alignItems: 'center' }}>
            <div style={{ fontSize: 36 }}>{stat.icon}</div>
            <div>
              <p style={{ fontSize: 28, fontWeight: 800, color: stat.color }}>{stat.value}</p>
              <p style={{ color: S.muted, fontSize: 13 }}>{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="card" style={{ padding: 32, textAlign: 'center' }}>
        <p style={{ fontSize: 48, marginBottom: 16 }}>📅</p>
        <h3 style={{ fontSize: 20, marginBottom: 8 }}>No appointments yet</h3>
        <p style={{ color: S.muted, marginBottom: 24 }}>Book your first appointment with a doctor</p>
        <button className="btn-primary" onClick={() => setPage('doctors')}>Find a Doctor</button>
      </div>
    </div>
  );
}

/* ─── Root App ───────────────────────────────────────────────────────────── */
export default function App() {
  const [page, setPage]                   = useState('home');
  const [selectedDoctor, setSelectedDoctor] = useState(null);

  const renderPage = () => {
    switch (page) {
      case 'login':          return <AuthPage mode="login"    setPage={setPage} />;
      case 'register':       return <AuthPage mode="register" setPage={setPage} />;
      case 'verify-email':   return <VerifyEmailPage           setPage={setPage} />;
      case 'forgot-password':return <ForgotPasswordPage        setPage={setPage} />;
      case 'reset-password': return <ResetPasswordPage         setPage={setPage} />;
      case 'doctors':        return <DoctorsPage setPage={setPage} setSelectedDoctor={setSelectedDoctor} />;
      case 'doctor-profile': return <DoctorProfilePage doctor={selectedDoctor} setPage={setPage} />;
      case 'dashboard':      return <DashboardPage setPage={setPage} />;
      default:               return <HomePage setPage={setPage} />;
    }
  };

  return (
    <ToastProvider>
      <AuthProvider>
        <style>{globalCSS}</style>
        <Navbar page={page} setPage={setPage} />
        <main>{renderPage()}</main>
      </AuthProvider>
    </ToastProvider>
  );
}
