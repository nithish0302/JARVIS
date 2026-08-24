import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import './PinAuthModal.css';

interface PinAuthModalProps {
  onCancel: () => void;
  // eslint-disable-next-line no-unused-vars
  onConfirm: (val: string) => Promise<void>;
  isOpen: boolean;
  // What the description line says is being deleted, e.g. "conversation" or
  // "memory". Defaults to "conversation" so the existing call site is unaffected.
  itemLabel?: string;
}

export function PinAuthModal({ onCancel, onConfirm, isOpen, itemLabel = "conversation" }: PinAuthModalProps) {
  const [pin, setPin] = useState('');
  const [error, setError] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setPin('');
      setError(false);
      setIsDeleting(false);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: globalThis.KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === 'Escape') {
        onCancel();
      } else if (e.key === 'Enter' && pin.length === 4 && !isDeleting) {
        handleConfirm();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, pin, isDeleting, onCancel]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (error) setError(false);
    const val = e.target.value.replace(/\D/g, '').slice(0, 4);
    setPin(val);
  };

  const handleConfirm = async () => {
    if (pin.length !== 4 || isDeleting) return;
    setIsDeleting(true);
    try {
      await onConfirm(pin);
    } catch {
      // Trigger error animation
      setError(true);
      setTimeout(() => {
        setPin('');
        setError(false);
        setIsDeleting(false);
      }, 500);
    }
  };

  if (!isOpen) return null;

  return createPortal(
    <div className="pin-modal-backdrop" onClick={onCancel}>
      <div className="pin-modal-container" onClick={(e) => e.stopPropagation()}>
        <div className={`pin-modal ${error ? 'shake' : ''}`}>
          <div className="pin-corner tl"></div>
          <div className="pin-corner tr"></div>
          <div className="pin-corner bl"></div>
          <div className="pin-corner br"></div>
          <div className="pin-scanline"></div>
          
          <div className="pin-header">
            <div className="pin-header-left">
              <div className="pin-lock-icon">🔒</div>
              <div className="pin-header-text">
                <h2>AUTHENTICATION REQUIRED</h2>
                <span>SECURITY CHECKPOINT</span>
              </div>
            </div>
            <button className="pin-close-btn" onClick={onCancel}>✕</button>
          </div>
          
          <div className="pin-divider"></div>
          
          <p className="pin-desc">
            Please enter the security PIN to <b>delete this {itemLabel}</b>.
          </p>
          
          <div className="pin-label-text">4-Digit PIN</div>
          
          <div className="pin-boxes">
            <input
              type="tel"
              inputMode="numeric"
              maxLength={4}
              autoFocus
              className="pin-hidden-input"
              value={pin}
              onChange={handleChange}
              disabled={isDeleting || error}
            />
            {[0, 1, 2, 3].map((index) => {
              const isFilled = pin.length > index;
              const isActive = pin.length === index;
              let className = 'pin-box';
              if (isFilled) className += ' filled';
              if (isActive) className += ' active';
              if (error) className += ' error';

              return (
                <div key={index} className={className}>
                  {isFilled && <span className="dot"></span>}
                  {isActive && !error && <span className="cursor"></span>}
                </div>
              );
            })}
          </div>
          
          <div className="pin-progress-dots">
            {[0, 1, 2, 3].map((index) => {
              const isDone = pin.length > index;
              return (
                <div 
                  key={index} 
                  className={`seg ${isDone ? 'done' : ''} ${error ? 'error' : ''}`}
                ></div>
              );
            })}
          </div>
          
          <div className="pin-hint">
            Numeric keys 0–9 · Backspace to clear · Esc to cancel
          </div>
          
          <div className="pin-btn-row">
            <button className="pin-btn pin-btn-cancel" onClick={onCancel} disabled={isDeleting}>
              Cancel
            </button>
            <button 
              className="pin-btn pin-btn-delete" 
              disabled={pin.length !== 4 || isDeleting || error}
              onClick={handleConfirm}
            >
              {isDeleting ? 'Verifying...' : 'Delete'}
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
