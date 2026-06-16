import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;
  
  // 1. Define public and asset paths
  const isPublicPath = path === "/login" || path.startsWith("/api/auth");
  const isAssetPath =
    path.startsWith("/_next") ||
    path.startsWith("/favicon.ico") ||
    path.startsWith("/api/"); // skip standard middleware for internal APIs (handled in routes)

  if (isAssetPath) {
    return NextResponse.next();
  }

  // 2. Extract session cookie
  const sessionCookie = request.cookies.get("authclaw_session")?.value;

  // 3. Handle redirects
  if (!sessionCookie && !isPublicPath) {
    // Redirect unauthenticated user to login
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (sessionCookie && path === "/login") {
    // Redirect authenticated user away from login to overview dashboard
    return NextResponse.redirect(new URL("/overview", request.url));
  }

  if (sessionCookie && path === "/") {
    // Redirect root to overview dashboard
    return NextResponse.redirect(new URL("/overview", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
};
