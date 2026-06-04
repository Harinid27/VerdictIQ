import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

interface InputFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  icon?: React.ReactNode;
  error?: string;
}

export const InputField: React.FC<InputFieldProps> = ({
  label,
  id,
  type = 'text',
  icon,
  error,
  className = '',
  ...props
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const isPassword = type === 'password';
  const inputType = isPassword ? (showPassword ? 'text' : 'password') : type;

  return (
    <div className="relative w-full text-left">
      {/* Outer wrapper with subtle scale animation on focus */}
      <div 
        className={`
          relative flex items-center transition-all duration-300 rounded-xl
          bg-brand-dark/30 backdrop-blur-sm border
          ${error ? 'border-red-500/50 shadow-[0_0_12px_rgba(239,68,68,0.1)]' : 'border-brand-border focus-within:border-brand-blue/50 focus-within:shadow-[0_0_15px_rgba(79,140,255,0.15),inset_0_1px_1px_rgba(255,255,255,0.05)]'}
        `}
      >
        {/* Leading Icon */}
        {icon && (
          <div className="pl-4 pr-1 text-brand-textMuted/60 transition-colors duration-300 focus-within:text-brand-blue">
            {icon}
          </div>
        )}

        {/* Input */}
        <input
          id={id}
          type={inputType}
          className={`
            peer block w-full px-4 pt-5 pb-2 text-[15px] text-white bg-transparent 
            border-none outline-none focus:ring-0 placeholder-transparent select-none
            ${icon ? 'pl-2' : ''}
            ${isPassword ? 'pr-12' : ''}
            ${className}
          `}
          placeholder={label}
          {...props}
        />

        {/* Floating Label */}
        <label
          htmlFor={id}
          className={`
            absolute text-[13px] text-brand-textMuted/50 pointer-events-none 
            transition-all duration-300 transform -translate-y-3.5 scale-90 origin-[0]
            ${icon ? 'left-11' : 'left-4'}
            peer-placeholder-shown:translate-y-0 
            peer-placeholder-shown:scale-100 
            peer-placeholder-shown:text-brand-textMuted/40
            peer-focus:-translate-y-3.5 
            peer-focus:scale-90 
            peer-focus:text-brand-blue/80
            input-has-value:-translate-y-3.5
            input-has-value:scale-90
          `}
          style={{
            // Keep the label floating if the field is not empty
            transform: props.value ? 'translateY(-14px) scale(0.9)' : undefined,
            color: props.value ? 'rgba(79, 140, 255, 0.7)' : undefined
          }}
        >
          {label}
        </label>

        {/* Password toggle icon */}
        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-4 text-brand-textMuted/40 hover:text-brand-blue transition-colors outline-none"
            tabIndex={-1}
          >
            {showPassword ? (
              <EyeOff className="w-[18px] h-[18px] animate-pulse-slow" />
            ) : (
              <Eye className="w-[18px] h-[18px]" />
            )}
          </button>
        )}
      </div>

      {/* Error message */}
      {error && (
        <span className="block mt-1.5 ml-2 text-xs text-red-400 font-medium tracking-wide">
          {error}
        </span>
      )}
    </div>
  );
};
