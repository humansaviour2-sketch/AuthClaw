import { randomUUID } from "crypto";

export interface SessionData {
  sessionId: string;
  userId: string;
  tenantId: string;
  scopes: string[];
  apiKey: string;
  createdAt: number;
}

class SessionStore {
  private sessions = new Map<string, SessionData>();

  createSession(data: Omit<SessionData, "sessionId" | "createdAt">): SessionData {
    const sessionId = randomUUID();
    const session: SessionData = {
      ...data,
      sessionId,
      createdAt: Date.now(),
    };
    this.sessions.set(sessionId, session);
    return session;
  }

  getSession(sessionId: string): SessionData | undefined {
    const session = this.sessions.get(sessionId);
    if (!session) return undefined;

    // Check TTL (e.g. 24 hours)
    const oneDay = 24 * 60 * 60 * 1000;
    if (Date.now() - session.createdAt > oneDay) {
      this.sessions.delete(sessionId);
      return undefined;
    }

    return session;
  }

  deleteSession(sessionId: string): boolean {
    return this.sessions.delete(sessionId);
  }
}

// Global singleton to prevent hot reload clearing store in development
const globalSessionStore = global as unknown as {
  sessionStoreInstance?: SessionStore;
};

if (!globalSessionStore.sessionStoreInstance) {
  globalSessionStore.sessionStoreInstance = new SessionStore();
}

export const sessionStore = globalSessionStore.sessionStoreInstance;
