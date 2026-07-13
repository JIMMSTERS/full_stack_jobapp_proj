import { useState } from "react";
import { toast } from "sonner";

import { createExtensionToken } from "../api";

/**
 * A small panel that mints a bearer token for the OfferFlow browser extension.
 *
 * The token is a distinct server-side session, so it can be revoked/expired
 * without affecting the web login. The user copies it into the extension's
 * settings to pair it with their account.
 */
export function ConnectExtension() {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleGenerate() {
    setLoading(true);
    try {
      const result = await createExtensionToken();
      setToken(result.token);
      toast.success("Extension token generated");
    } catch {
      toast.error("Could not generate token");
    } finally {
      setLoading(false);
    }
  }

  async function handleCopy() {
    if (!token) return;
    try {
      await navigator.clipboard.writeText(token);
      toast.success("Copied to clipboard");
    } catch {
      toast.error("Copy failed — select and copy manually");
    }
  }

  return (
    <section className="connect-extension">
      <div className="connect-extension-head">
        <h2>Browser extension</h2>
        <p>
          Save jobs from LinkedIn, Greenhouse, Lever and more with one click.
          Generate a token and paste it into the extension to connect it to your
          account.
        </p>
      </div>

      {token ? (
        <div className="connect-token-row">
          <input
            className="connect-token-input"
            readOnly
            value={token}
            onFocus={(e) => e.currentTarget.select()}
            aria-label="Extension token"
          />
          <button className="connect-copy-btn" onClick={handleCopy}>
            Copy
          </button>
          <button
            className="connect-regen-btn"
            onClick={handleGenerate}
            disabled={loading}
          >
            Regenerate
          </button>
        </div>
      ) : (
        <button
          className="connect-generate-btn"
          onClick={handleGenerate}
          disabled={loading}
        >
          {loading ? "Generating…" : "Generate extension token"}
        </button>
      )}
    </section>
  );
}
