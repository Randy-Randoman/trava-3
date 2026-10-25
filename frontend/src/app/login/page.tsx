'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/lib/auth'
import { safeNextPath } from '@/lib/oauth'

export default function LoginPage() {
  const router = useRouter()
  const { signIn } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const { error } = await signIn(email, password)
      if (error) {
        setError(error.message)
      } else {
        router.push(safeNextPath(new URLSearchParams(window.location.search).get('next')))
      }
    } catch (err) {
      setError('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        {/* Logo */}
        <div className="flex justify-center mb-6">
          <img
            src="/trava-logo.png"
            alt="Trava Logo"
            className="w-24 h-auto object-contain scale-x-[-1] drop-shadow-[4px_4px_0px_rgba(26,26,27,0.2)]"
          />
        </div>
        <h2 className="mt-2 text-center text-3xl font-black uppercase tracking-tighter text-trava-black">
          Sign in to TRAVA
        </h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 border-4 border-trava-black shadow-brutal sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-50 border-2 border-red-500 text-red-700 px-4 py-3 text-sm font-bold">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-bold text-trava-black uppercase tracking-wide">
                Email address
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full appearance-none border-2 border-trava-black px-3 py-2 text-trava-black placeholder-gray-400 focus:outline-none focus:shadow-brutal transition-all sm:text-sm font-medium"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-bold text-trava-black uppercase tracking-wide">
                Password
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full appearance-none border-2 border-trava-black px-3 py-2 text-trava-black placeholder-gray-400 focus:outline-none focus:shadow-brutal transition-all sm:text-sm font-medium"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="flex w-full justify-center border-2 border-trava-black bg-adventure-orange py-2 px-4 text-sm font-bold text-trava-black hover:shadow-brutal hover:translate-x-[-2px] hover:translate-y-[-2px] transition-all focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none disabled:translate-x-0 disabled:translate-y-0"
              >
                {loading ? 'Signing in...' : 'Sign in'}
              </button>
            </div>
          </form>
          <p className="text-center mt-4 text-sm text-gray-600">
            Don&apos;t have an account?{' '}
            <Link href="/signup" className="font-bold text-adventure-orange hover:underline">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
