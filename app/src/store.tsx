import React, { createContext, useContext, useEffect, useState } from "react";

export interface Session {
  adminToken?: string;      // guards admin endpoints (unset = dev-open backend)
  tenantId?: string;        // the tenant currently being operated on
  tenantName?: string;
  tenantToken?: string;     // that tenant's write token
}

interface Ctx {
  session: Session;
  setSession: (s: Session) => void;
  clear: () => void;
}

const SessionContext = createContext<Ctx | null>(null);
const KEY = "pdi.session";

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [session, setState] = useState<Session>(() => {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "{}");
    } catch {
      return {};
    }
  });
  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(session));
  }, [session]);
  const setSession = (s: Session) => setState((p) => ({ ...p, ...s }));
  const clear = () => {
    setState({});
    localStorage.removeItem(KEY);
  };
  return (
    <SessionContext.Provider value={{ session, setSession, clear }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession(): Ctx {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}
