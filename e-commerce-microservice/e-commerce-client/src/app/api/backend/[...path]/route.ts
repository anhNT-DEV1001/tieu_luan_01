import { NextRequest, NextResponse } from "next/server";

const backendBaseUrl =
  process.env.ECOMMERCE_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

function normalizeBackendPath(pathname: string): string {
  const strippedPath = pathname.replace(/^\/api\/backend\//, "");
  if (!strippedPath) return "";
  return strippedPath.endsWith("/") ? strippedPath : `${strippedPath}/`;
}

async function proxy(request: NextRequest, params: { path: string[] }) {
  const backendPath = normalizeBackendPath(request.nextUrl.pathname);
  const search = request.nextUrl.search;
  const target = `${backendBaseUrl}/api/${backendPath}${search}`;

  const response = await fetch(target, {
    method: request.method,
    headers: {
      "Content-Type": request.headers.get("content-type") ?? "application/json",
    },
    body: request.method === "GET" ? undefined : await request.text(),
    cache: "no-store",
  });

  const payload = await response.text();

  return new NextResponse(payload, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("content-type") ?? "application/json",
    },
  });
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return proxy(request, await context.params);
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return proxy(request, await context.params);
}

export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return proxy(request, await context.params);
}

export async function PATCH(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return proxy(request, await context.params);
}

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return proxy(request, await context.params);
}
