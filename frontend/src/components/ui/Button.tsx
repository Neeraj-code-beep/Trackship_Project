import React from 'react';
import { Loader2 } from 'lucide-react';
import './Button.css';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'icon' | 'pill';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  children?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  children,
  disabled,
  className = '',
  ...props
}) => {
  const baseClass = `sc-button sc-button--${variant} sc-button--${size} ${className}`;

  return (
    <button
      className={baseClass}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="sc-button__spinner" size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16} />
      ) : (
        leftIcon && <span className="sc-button__icon sc-button__icon--left">{leftIcon}</span>
      )}
      {children && <span className="sc-button__label">{children}</span>}
      {!isLoading && rightIcon && (
        <span className="sc-button__icon sc-button__icon--right">{rightIcon}</span>
      )}
    </button>
  );
};

export default Button;
