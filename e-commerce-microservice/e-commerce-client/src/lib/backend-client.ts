function compactWhitespace(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

function stripHtml(value: string): string {
  return value.replace(/<[^>]*>/g, " ");
}

async function extractErrorMessage(response: Response): Promise<string> {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    try {
      const payload = (await response.json()) as {
        error?: string;
        detail?: string;
        message?: string;
      };

      return compactWhitespace(payload.error || payload.detail || payload.message || "");
    } catch {
      return "";
    }
  }

  const raw = await response.text();
  const compactText = compactWhitespace(stripHtml(raw));
  if (!compactText) return "";
  if (compactText.length <= 180) return compactText;
  return `${compactText.slice(0, 177)}...`;
}

export async function requestBackendJson<T>(path: string, init?: RequestInit): Promise<T> {
  const safePath = path.replace(/^\/+/, "");
  const response = await fetch(`/api/backend/${safePath}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const detail = await extractErrorMessage(response);
    const message = detail ? `HTTP ${response.status}: ${detail}` : `HTTP ${response.status}: Request failed`;
    throw new Error(message);
  }

  return (await response.json()) as T;
}
