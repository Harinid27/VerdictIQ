import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { User, Building2, Mail, Lock, Briefcase, ArrowRight, ChevronDown } from 'lucide-react';
import { InputField } from './InputField';

interface SignupCardProps {
  onSwitchToLogin: () => void;
  onSignupSuccess?: (token: string, user: any) => void;
}

export const SignupCard: React.FC<SignupCardProps> = ({ onSwitchToLogin, onSignupSuccess }) => {
  const [fullName, setFullName] = useState('');
  const [organization, setOrganization] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('');
  const [customRole, setCustomRole] = useState('');
  const [isRoleFocused, setIsRoleFocused] = useState(false);
  
  const [errors, setErrors] = useState<{
    fullName?: string;
    organization?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
    customRole?: string;
  }>({});
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: typeof errors = {};

    if (!fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    }

    if (!organization.trim()) {
      newErrors.organization = 'Organization or Law Firm is required';
    }

    if (!email) {
      newErrors.email = 'Work email is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Please enter a valid work email';
    }

    if (role === 'other' && !customRole.trim()) {
      newErrors.customRole = 'Please specify your custom role';
    }

    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    setIsLoading(true);

    const finalRole = role === 'other' ? customRole : role;

    // Send POST query to FastAPI signup endpoint
    fetch('http://localhost:8000/api/auth/signup', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        full_name: fullName,
        organization,
        role: finalRole || 'Lawyer',
        email,
        password,
        confirm_password: confirmPassword,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        setIsLoading(false);
        if (data.success && data.token) {
          if (onSignupSuccess) {
            onSignupSuccess(data.token, data.user);
          }
        } else {
          setErrors({ email: data.message || 'Failed to provision workspace.' });
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
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-brand-purple/50 to-brand-blue/50 opacity-80" />

      {/* Top Brand Logo Section */}
      <div className="flex flex-col items-center justify-center mb-6">
        <div className="relative mb-2.5 flex items-center justify-center">
          <div className="absolute w-12 h-12 rounded-full bg-brand-purple/15 blur-md animate-pulse-slow" />
          
          <svg
            width="34"
            height="34"
            viewBox="0 0 32 32"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="relative z-10 filter drop-shadow-[0_0_8px_rgba(123,97,255,0.4)]"
          >
            <path
              d="M16 2L29.5 9.75V25.25L16 33L2.5 25.25V9.75L16 2Z"
              stroke="url(#logo-grad-signup)"
              strokeWidth="2"
              strokeLinejoin="round"
            />
            <path
              d="M9 12L16 21L23 12"
              stroke="#7B61FF"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <circle cx="16" cy="21" r="2.5" fill="#4F8CFF" />
            <circle cx="9" cy="12" r="1.5" fill="#fff" />
            <circle cx="23" cy="12" r="1.5" fill="#fff" />
            <defs>
              <linearGradient id="logo-grad-signup" x1="2.5" y1="2" x2="29.5" y2="33" gradientUnits="userSpaceOnUse">
                <stop stopColor="#7B61FF" />
                <stop offset="1" stopColor="#4F8CFF" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        
        <h1 className="text-xl font-bold tracking-tight text-white font-display flex items-center gap-1.5 m-0">
          Verdict<span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-purple to-brand-blue">IQ</span>
        </h1>
      </div>

      {/* Headings */}
      <div className="text-center mb-5">
        <h2 className="text-lg font-bold text-white tracking-wide font-display mb-1">
          Create Your Workspace
        </h2>
        <p className="text-xs text-brand-textMuted leading-relaxed max-w-[290px] mx-auto">
          Start building AI-powered legal strategies with VerdictIQ.
        </p>
      </div>

      {/* Signup Form */}
      <form onSubmit={handleSubmit} className="space-y-3.5">
        <InputField
          label="Full Name"
          id="signup-name"
          type="text"
          value={fullName}
          onChange={(e) => {
            setFullName(e.target.value);
            if (errors.fullName) setErrors({ ...errors, fullName: undefined });
          }}
          error={errors.fullName}
          icon={<User className="w-[18px] h-[18px]" />}
          disabled={isLoading}
        />

        <InputField
          label="Organization / Law Firm"
          id="signup-org"
          type="text"
          value={organization}
          onChange={(e) => {
            setOrganization(e.target.value);
            if (errors.organization) setErrors({ ...errors, organization: undefined });
          }}
          error={errors.organization}
          icon={<Building2 className="w-[18px] h-[18px]" />}
          disabled={isLoading}
        />

        <InputField
          label="Work Email"
          id="signup-email"
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

        {/* Optional Role Dropdown */}
        <div className="relative text-left w-full">
          <div 
            className={`
              relative flex items-center transition-all duration-300 rounded-xl bg-brand-dark/30 backdrop-blur-sm border
              ${isRoleFocused ? 'border-brand-blue/50 shadow-[0_0_15px_rgba(79,140,255,0.15)]' : 'border-brand-border'}
            `}
          >
            <div className="pl-4 pr-1 text-brand-textMuted/60">
              <Briefcase className="w-[18px] h-[18px]" />
            </div>

            <select
              id="signup-role"
              value={role}
              onChange={(e) => {
                setRole(e.target.value);
                if (e.target.value !== 'other') {
                  setCustomRole('');
                }
              }}
              onFocus={() => setIsRoleFocused(true)}
              onBlur={() => setIsRoleFocused(false)}
              disabled={isLoading}
              className="
                block w-full px-4 pt-5 pb-2 text-[15px] text-white bg-transparent 
                border-none outline-none focus:ring-0 appearance-none cursor-pointer pr-10
                placeholder-transparent select-none pl-2 z-10
              "
            >
              <option value="" disabled hidden className="bg-brand-dark text-brand-textMuted/60"></option>
              <option value="lawyer" className="bg-[#111827] text-white">Lawyer</option>
              <option value="researcher" className="bg-[#111827] text-white">Legal Researcher</option>
              <option value="corporate" className="bg-[#111827] text-white">Corporate Legal Team</option>
              <option value="student" className="bg-[#111827] text-white">Law Student</option>
              <option value="other" className="bg-[#111827] text-white">Other...</option>
            </select>

            {/* Custom Dropdown Arrow */}
            <div className="absolute right-4 pointer-events-none text-brand-textMuted/40 z-10">
              <ChevronDown className="w-4 h-4" />
            </div>

            {/* Float Label logic for Select */}
            <label
              htmlFor="signup-role"
              className={`
                absolute text-[13px] pointer-events-none transition-all duration-300 transform origin-[0] left-11 z-0
                ${(role || isRoleFocused)
                  ? '-translate-y-3.5 scale-90 text-brand-blue/80' 
                  : 'translate-y-0 scale-100 text-brand-textMuted/40'
                }
              `}
            >
              Role (Optional)
            </label>
          </div>
        </div>

        {/* Specify Custom Role Input Field */}
        {role === 'other' && (
          <motion.div
            initial={{ opacity: 0, y: -10, height: 0 }}
            animate={{ opacity: 1, y: 0, height: 'auto' }}
            exit={{ opacity: 0, y: -10, height: 0 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className="w-full text-left"
          >
            <InputField
              label="Specify Custom Role"
              id="signup-custom-role"
              type="text"
              value={customRole}
              onChange={(e) => {
                setCustomRole(e.target.value);
                if (errors.customRole) setErrors({ ...errors, customRole: undefined });
              }}
              error={errors.customRole}
              icon={<Briefcase className="w-[18px] h-[18px] text-brand-blue/60" />}
              disabled={isLoading}
            />
          </motion.div>
        )}

        <InputField
          label="Password"
          id="signup-password"
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

        <InputField
          label="Confirm Password"
          id="signup-confirm-password"
          type="password"
          value={confirmPassword}
          onChange={(e) => {
            setConfirmPassword(e.target.value);
            if (errors.confirmPassword) setErrors({ ...errors, confirmPassword: undefined });
          }}
          error={errors.confirmPassword}
          icon={<Lock className="w-[18px] h-[18px]" />}
          disabled={isLoading}
        />

        {/* Primary Submit Button */}
        <motion.button
          whileHover={isLoading ? {} : { y: -2 }}
          whileTap={isLoading ? {} : { scale: 0.98 }}
          type="submit"
          disabled={isLoading}
          className="relative w-full h-[48px] rounded-xl font-semibold text-sm tracking-wide text-white overflow-hidden shadow-button-glow transition-all duration-300 disabled:opacity-80 mt-2"
        >
          {/* Dynamic glowing background */}
          <div className="absolute inset-0 bg-gradient-to-r from-brand-purple to-brand-blue" />
          
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
                <span>Provisioning Node...</span>
              </>
            ) : (
              <>
                <span>Create Intelligence Workspace</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </span>
        </motion.button>
      </form>

      {/* Switch to Login bottom link */}
      <div className="mt-6 text-center">
        <p className="text-xs text-brand-textMuted">
          Already have an account?{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="text-brand-blue hover:text-brand-blue/80 transition-colors font-semibold hover:underline bg-transparent border-none p-0 cursor-pointer"
          >
            Sign In
          </button>
        </p>
      </div>
    </motion.div>
  );
};
