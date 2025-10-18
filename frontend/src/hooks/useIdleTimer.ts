import { useState, useEffect, useRef } from 'react';

const useIdleTimer = (timeout: number, onIdle: () => void) => {
  const [isIdle, setIsIdle] = useState(false);
  const timeoutId = useRef<number | null>(null);
  const onIdleRef = useRef(onIdle);

  // Actualizar la referencia cuando onIdle cambie, sin provocar re-render
  useEffect(() => {
    onIdleRef.current = onIdle;
  }, [onIdle]);

  useEffect(() => {
    const resetTimer = () => {
      if (timeoutId.current) {
        window.clearTimeout(timeoutId.current);
      }
      timeoutId.current = window.setTimeout(() => {
        setIsIdle(true);
        onIdleRef.current();
      }, timeout);
    };

    const events = ['mousemove', 'keydown', 'mousedown', 'touchstart'];

    const handleActivity = () => {
      setIsIdle(false);
      resetTimer();
    };

    events.forEach(event => {
      window.addEventListener(event, handleActivity);
    });

    resetTimer();

    return () => {
      if (timeoutId.current) {
        window.clearTimeout(timeoutId.current);
      }
      events.forEach(event => {
        window.removeEventListener(event, handleActivity);
      });
    };
  }, [timeout]); // Solo depende de timeout, no de onIdle

  return isIdle;
};

export default useIdleTimer;
