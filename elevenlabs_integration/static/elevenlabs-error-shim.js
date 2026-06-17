/**
 * elevenlabs-error-shim.js
 *
 * Defensive shim for @elevenlabs/client@1.8.x.
 *
 * The SDK's handleErrorEvent() assumes every "error" message is the structured
 * shape { type:"error", error_event:{ error_type, message, ... } }. But the
 * backend also sends FLAT protocol errors — e.g. quota/rate-limit close frames:
 *
 *   { "type":"error", "message":"... This request exceeds your quota limit." }
 *
 * On those, the SDK throws `Cannot read properties of undefined (reading
 * 'error_type')` INSIDE its own message handler — before the consumer's
 * onError fires — which tears down the WebRTC session with no usable signal.
 * (This single crash is what masked a quota error as a mysterious "voice cuts
 * off after 1-2 words" disconnect for a long time.)
 *
 * This shim wraps BaseConversation.prototype.handleErrorEvent so flat errors
 * are normalized and routed through the SDK's normal onError path instead of
 * crashing. Load it AFTER the @elevenlabs/client script and BEFORE app.js.
 *
 * Remove if/when the project upgrades to an SDK version that handles flat
 * error frames natively.
 */
(function () {
  try {
    const C = window.ElevenLabsClient;
    const VC = C && C.VoiceConversation;
    if (!VC || !VC.prototype) {
      console.warn('[el-shim] VoiceConversation not found; error shim not applied');
      return;
    }
    const Base = Object.getPrototypeOf(VC.prototype); // BaseConversation.prototype
    if (!Base || typeof Base.handleErrorEvent !== 'function') {
      console.warn('[el-shim] handleErrorEvent not found; error shim not applied');
      return;
    }

    const orig = Base.handleErrorEvent;
    Base.handleErrorEvent = function (event) {
      // Structured error → let the SDK handle it as designed.
      if (event && event.error_event) {
        return orig.call(this, event);
      }
      // Flat / unexpected error → surface it instead of crashing.
      const message = (event && (event.message || event.reason)) || 'Unknown error';
      try {
        // this.onError(message, context) → forwards to options.onError
        this.onError(`Server error: ${message}`, { raw: event });
      } catch (e) {
        console.error('[el-shim] error reporting failed:', e, 'original event:', event);
      }
      // Don't rethrow: the backend closes the connection itself, and the SDK's
      // disconnect handler will run normal teardown.
    };

    console.info('[el-shim] handleErrorEvent guard installed');
  } catch (e) {
    console.error('[el-shim] failed to install error shim:', e);
  }
})();
