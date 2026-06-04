import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, Lock, ArrowRight } from 'lucide-react';
import { InputField } from './InputField';

interface LoginCardProps {
  onSwitchToSignup: () => void;
  onLoginSuccess?: (token: string, user: any) => void;
}

export const LoginCard: React.FC<LoginCardProps> = ({ onSwitchToSignup, onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: { email?: string; password?: string } = {};

    if (!email) {
      newErrors.email = 'Email address is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Please enter a valid work email';
    }

    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    setIsLoading(true);

    // Send POST query to FastAPI login endpoint
    fetch('http://localhost:8000/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    })
      .then((res) => res.json())
      .then((data) => {
        setIsLoading(false);
        if (data.success && data.token) {
          if (onLoginSuccess) {
            onLoginSuccess(data.token, data.user);
          }
        } else {
          setErrors({ email: data.message || 'Authentication handshake failed.' });
        }
      })
      .catch(() => {
        setIsLoading(false);
        setErrors({ email: 'Failed to communicate with auth nodes. Check backend connection.' });
      });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -30, scale: 0.98 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className="w-full max-w-[420px] rounded-[24px] glass-card shadow-premium-card border border-brand-border glow-border-hover p-8 md:p-9 relative overflow-hidden"
    >
      {/* Decorative top corner gradient line */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-brand-blue/50 to-brand-purple/50 opacity-80" />

      {/* Top Brand Logo Section */}
      <div className="flex flex-col items-center justify-center mb-7">
        <div className="relative mb-3 flex items-center justify-center">
          {/* Futuristic ambient back-glow behind logo */}
          <div className="absolute w-12 h-12 rounded-full bg-brand-blue/20 blur-md animate-pulse-slow" />
          
          <svg
            width="40"
            height="40"
            viewBox="0 0 32 32"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="relative z-10 filter drop-shadow-[0_0_8px_rgba(79,140,255,0.4)]"
          >
            {/* Outer Hexagon node outline */}
            <path
              d="M16 2L29.5 9.75V25.25L16 33L2.5 25.25V9.75L16 2Z"
              stroke="url(#logo-grad)"
              strokeWidth="2"
              strokeLinejoin="round"
              className="animate-pulse-slow"
            />
            {/* Stylized V and Neural Node Scale */}
            <path
              d="M9 12L16 21L23 12"
              stroke="#4F8CFF"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <circle cx="16" cy="21" r="2.5" fill="#7B61FF" />
            <circle cx="9" cy="12" r="1.5" fill="#fff" />
            <circle cx="23" cy="12" r="1.5" fill="#fff" />
            <defs>
              <linearGradient id="logo-grad" x1="2.5" y1="2" x2="29.5" y2="33" gradientUnits="userSpaceOnUse">
                <stop stopColor="#4F8CFF" />
                <stop offset="1" stopColor="#7B61FF" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        
        <h1 className="text-2xl font-bold tracking-tight text-white font-display flex items-center gap-1.5 m-0">
          Verdict<span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-blue to-brand-purple">IQ</span>
        </h1>
        <p className="text-[11px] uppercase tracking-[0.18em] text-brand-blue font-medium mt-1">
          Legal Intelligence OS
        </p>
      </div>

      {/* Headings */}
      <div className="text-center mb-6">
        <h2 className="text-xl font-bold text-white tracking-wide font-display mb-1.5">
          Welcome Back
        </h2>
        <p className="text-xs text-brand-textMuted leading-relaxed max-w-[280px] mx-auto">
          Access your AI-powered legal intelligence workspace.
        </p>
      </div>

      {/* Auth Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <InputField
          label="Email Address"
          id="login-email"
          type="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (errors.email) setErrors({ ...errors, email: undefined });
          }}
          error={errors.email}
          icon={<Mail className="w-[18px] h-[18px]" />}
          disabled={isLoading}
        />

        <InputField
          label="Password"
          id="login-password"
          type="password"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            if (errors.password) setErrors({ ...errors, password: undefined });
          }}
          error={errors.password}
          icon={<Lock className="w-[18px] h-[18px]" />}
          disabled={isLoading}
        />

        {/* Remember Me & Forgot Password */}
        <div className="flex items-center justify-between text-xs mt-1 px-1">
          <label className="flex items-center gap-2 text-brand-textMuted cursor-pointer select-none">
            <input
              type="checkbox"
              id="remember-me"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              disabled={isLoading}
              className="
                appearance-none w-3.5 h-3.5 rounded bg-brand-dark/80 border border-white/20
                hover:border-brand-blue/50 checked:bg-brand-blue checked:border-brand-blue 
                focus:ring-0 focus:outline-none relative cursor-pointer transition-all 
                flex items-center justify-center
                after:content-['✓'] after:text-white after:text-[9px] after:font-bold after:hidden checked:after:block
              "
            />
            <span>Remember Me</span>
          </label>
          <a
            href="#forgot-password"
            onClick={(e) => {
              e.preventDefault();
              alert('Password reset link simulated. Please check email in staging.');
            }}
            className="text-brand-blue hover:text-brand-blue/80 transition-colors font-medium hover:underline"
          >
            Forgot Password?
          </a>
        </div>

        {/* Primary Submit Button */}
        <motion.button
          whileHover={isLoading ? {} : { y: -2 }}
          whileTap={isLoading ? {} : { scale: 0.98 }}
          type="submit"
          disabled={isLoading}
          className="relative w-full h-[48px] rounded-xl font-semibold text-sm tracking-wide text-white overflow-hidden shadow-button-glow transition-all duration-300 disabled:opacity-80"
        >
          {/* Dynamic glowing background */}
          <div className="absolute inset-0 bg-gradient-to-r from-brand-blue to-brand-purple" />
          
          {/* Shine Sweep Animation effect */}
          {!isLoading && (
            <div className="absolute top-0 bottom-0 left-[-100%] w-[50%] bg-gradient-to-r from-transparent via-white/25 to-transparent skew-x-[-20deg] animate-shine-sweep" />
          )}

          {/* Button Text / Hologram Loader */}
          <span className="relative z-10 flex items-center justify-center gap-2">
            {isLoading ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>Decrypting Creds...</span>
              </>
            ) : (
              <>
                <span>Access VerdictIQ</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </span>
        </motion.button>
      </form>

      {/* Divider */}
      <div className="relative my-6 flex items-center justify-center">
        <div className="absolute left-0 right-0 h-[1px] bg-brand-border" />
        <span className="relative z-10 px-3 text-[10px] uppercase tracking-wider text-brand-textMuted/50 bg-[#161d2b] rounded-full border border-brand-border">
          or continue with
        </span>
      </div>

      {/* Social Auth Buttons */}
      <div className="grid grid-cols-2 gap-3.5">
        <button
          onClick={() => alert('Redirecting to Google authentication portal...')}
          className="flex items-center justify-center gap-2 h-11 px-4 rounded-xl border border-brand-border bg-brand-dark/20 hover:bg-brand-dark/50 text-xs text-white transition-all duration-300 font-medium"
        >
          {/* Google Icon */}
          <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          <span>Google</span>
        </button>

        <button
          onClick={() => alert('Redirecting to Microsoft authentication portal...')}
          className="flex items-center justify-center gap-2 h-11 px-4 rounded-xl border border-brand-border bg-brand-dark/20 hover:bg-brand-dark/50 text-xs text-white transition-all duration-300 font-medium"
        >
          {/* Microsoft Icon */}
          <svg className="w-4 h-4 shrink-0" viewBox="0 0 23 23" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M0 0h11v11H0z" fill="#F25022"/>
            <path d="M12 0h11v11H12z" fill="#7FBA00"/>
            <path d="M0 12h11v11H0z" fill="#00A4EF"/>
            <path d="M12 12h11v11H12z" fill="#FFB900"/>
          </svg>
          <span>Microsoft</span>
        </button>
      </div>

      {/* Switch to Signup bottom link */}
      <div className="mt-8 text-center">
        <p className="text-xs text-brand-textMuted">
          Don’t have an account?{' '}
          <button
            type="button"
            onClick={onSwitchToSignup}
            className="text-brand-blue hover:text-brand-blue/80 transition-colors font-semibold hover:underline bg-transparent border-none p-0 cursor-pointer"
          >
            Create Account
          </button>
        </p>
      </div>
    </motion.div>
  );
};
