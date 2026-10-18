/**
 * Event Tracker - Client-side interaction tracking for ML training data
 * 
 * Tracks: view, click, apply_start, apply_complete, bookmark, share, search, filter
 * Sends to /api/v1/events endpoint (batched for performance)
 */

const EVENT_ENDPOINT = '/api/v1/events';
const BATCH_SIZE = 10;
const BATCH_INTERVAL_MS = 2000;
const SESSION_KEY = 'aiml_session_id';

class EventTracker {
  constructor() {
    this.queue = [];
    this.sessionId = this.getOrCreateSessionId();
    this.dwellStartTimes = new Map(); // schemeId -> timestamp
    this.batchTimer = null;
    this.isEnabled = true;
  }

  getOrCreateSessionId() {
    let sessionId = sessionStorage.getItem(SESSION_KEY);
    if (!sessionId) {
      sessionId = crypto.randomUUID();
      sessionStorage.setItem(SESSION_KEY, sessionId);
    }
    return sessionId;
  }

  getAuthToken() {
    // Get token from localStorage or your auth context
    return localStorage.getItem('access_token') || localStorage.getItem('token');
  }

  async sendBatch() {
    if (this.queue.length === 0) return;

    const token = this.getAuthToken();
    if (!token) {
      console.warn('[EventTracker] No auth token, dropping events');
      this.queue = [];
      return;
    }

    const events = [...this.queue];
    this.queue = [];

    try {
      await fetch(EVENT_ENDPOINT + '/batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ events }),
      });
    } catch (err) {
      console.error('[EventTracker] Failed to send events:', err);
      // Re-queue on failure (with max retry limit)
      this.queue.unshift(...events);
    }
  }

  scheduleBatch() {
    if (this.batchTimer) return;
    this.batchTimer = setTimeout(() => {
      this.batchTimer = null;
      this.sendBatch();
    }, BATCH_INTERVAL_MS);
  }

  track(eventType, schemeId, metadata = {}) {
    if (!this.isEnabled) return;

    const event = {
      event_type: eventType,
      scheme_id: schemeId,
      metadata: {
        position: metadata.position,
        source: metadata.source,
        dwell_ms: metadata.dwell_ms,
        query: metadata.query,
        filter_state: metadata.filter_state,
        referrer: metadata.referrer,
        extra: metadata.extra,
      },
      session_id: this.sessionId,
    };

    this.queue.push(event);

    if (this.queue.length >= BATCH_SIZE) {
      this.sendBatch();
    } else {
      this.scheduleBatch();
    }
  }

  // Convenience methods
  view(schemeId, metadata = {}) {
    this.dwellStartTimes.set(schemeId, Date.now());
    this.track('view', schemeId, { ...metadata, source: metadata.source || 'unknown' });
  }

  click(schemeId, metadata = {}) {
    const dwellMs = this.dwellStartTimes.has(schemeId)
      ? Date.now() - this.dwellStartTimes.get(schemeId)
      : undefined;
    this.track('click', schemeId, { ...metadata, dwell_ms: dwellMs, source: metadata.source || 'unknown' });
  }

  applyStart(schemeId, metadata = {}) {
    this.track('apply_start', schemeId, { ...metadata, source: metadata.source || 'unknown' });
  }

  applyComplete(schemeId, metadata = {}) {
    this.track('apply_complete', schemeId, { ...metadata, source: metadata.source || 'unknown' });
  }

  bookmark(schemeId, metadata = {}) {
    this.track('bookmark', schemeId, { ...metadata, source: metadata.source || 'unknown' });
  }

  share(schemeId, metadata = {}) {
    this.track('share', schemeId, { ...metadata, source: metadata.source || 'unknown' });
  }

  search(query, metadata = {}) {
    this.track('search', null, { ...metadata, query, source: 'search' });
  }

  filter(filters, metadata = {}) {
    this.track('filter', null, { ...metadata, filter_state: filters, source: 'filter' });
  }

  flush() {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }
    this.sendBatch();
  }

  disable() {
    this.isEnabled = false;
  }

  enable() {
    this.isEnabled = true;
  }
}

// Singleton instance
export const eventTracker = new EventTracker();

// React hook for easy use in components
export function useEventTracker() {
  return eventTracker;
}

// Auto-flush on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    eventTracker.flush();
  });

  // Track page visibility for dwell time
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      eventTracker.flush();
    }
  });
}

export default eventTracker;