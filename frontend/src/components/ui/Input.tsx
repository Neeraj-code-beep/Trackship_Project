import React from 'react';
import './Input.css';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  leftIcon,
  rightIcon,
  className = '',
  id,
  ...props
}) => {
  const inputId = id || (label ? `input-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined);

  return (
    <div className={`sc-input-group ${className}`}>
      {label && (
        <label htmlFor={inputId} className="sc-input__label text-label">
          {label}
        </label>
      )}
      <div className="sc-input__wrapper">
        {leftIcon && <span className="sc-input__icon sc-input__icon--left">{leftIcon}</span>}
        <input
          id={inputId}
          className={`sc-input ${leftIcon ? 'sc-input--has-left' : ''} ${rightIcon ? 'sc-input--has-right' : ''} ${error ? 'sc-input--error' : ''}`}
          {...props}
        />
        {rightIcon && <span className="sc-input__icon sc-input__icon--right">{rightIcon}</span>}
      </div>
      {error && <span className="sc-input__error text-micro">{error}</span>}
    </div>
  );
};

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: Array<{ value: string; label: string }>;
  error?: string;
}

export const Select: React.FC<SelectProps> = ({
  label,
  options,
  error,
  className = '',
  id,
  ...props
}) => {
  const selectId = id || (label ? `select-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined);

  return (
    <div className={`sc-input-group ${className}`}>
      {label && (
        <label htmlFor={selectId} className="sc-input__label text-label">
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={`sc-input sc-select ${error ? 'sc-input--error' : ''}`}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <span className="sc-input__error text-micro">{error}</span>}
    </div>
  );
};
