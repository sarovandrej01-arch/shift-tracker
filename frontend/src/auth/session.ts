type SessionListener = () => void;

const unauthorizedListeners = new Set<SessionListener>();

export function subscribeUnauthorized(listener: SessionListener): () => void {
  unauthorizedListeners.add(listener);
  return () => {
    unauthorizedListeners.delete(listener);
  };
}

export function notifyUnauthorized(): void {
  for (const listener of unauthorizedListeners) {
    listener();
  }
}
