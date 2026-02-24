import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  // Redirect bare "/" to "/dashboard" so we don't load the heavy
  // Excalidraw bundle just to redirect client-side.
  if (request.nextUrl.pathname === '/' && !request.nextUrl.searchParams.has('trip')) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }
}

export const config = {
  matcher: ['/'],
}
