import { BrowserContext } from '../types';

export const DEFAULT_BACKEND_URL = 'http://127.0.0.1:8000/api';

const RESTRICTED_URL_PREFIXES = [
  'chrome://',
  'chrome-extension://',
  'devtools://',
  'edge://',
  'about:',
  'view-source:',
  'https://chromewebstore.google.com'
];

export class BrowserContextService {
  private baseUrl: string;

  constructor(baseUrl: string = DEFAULT_BACKEND_URL) {
    this.baseUrl = baseUrl;
  }

  public setBaseUrl(url: string) {
    this.baseUrl = url.replace(/\/$/, '');
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  public isRestrictedUrl(url: string): boolean {
    if (!url) return true;
    return RESTRICTED_URL_PREFIXES.some(prefix => url.startsWith(prefix));
  }

  public async checkEngineHealth(): Promise<{ connected: boolean; message?: string }> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (response.ok) {
        return { connected: true, message: 'Local Perception Engine Online' };
      }
      return { connected: false, message: `Engine returned HTTP ${response.status}` };
    } catch {
      clearTimeout(timeoutId);
      return { connected: false, message: 'Local Perception Engine Offline' };
    }
  }

  public async sendBrowserContext(context: BrowserContext): Promise<{ success: boolean; data?: any; error?: string }> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 6000);

    try {
      const response = await fetch(`${this.baseUrl}/browser/context`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(context),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Backend responded with status ${response.status}`);
      }

      const data = await response.json();
      return { success: true, data };
    } catch (err: any) {
      clearTimeout(timeoutId);
      return {
        success: false,
        error: err.name === 'AbortError' ? 'Context transmission timed out (6s)' : err.message || 'Transmission failed'
      };
    }
  }
}

export const browserContextService = new BrowserContextService();
