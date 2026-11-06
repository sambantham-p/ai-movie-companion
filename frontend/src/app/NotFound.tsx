/** Fallback page for unknown routes. */
import { Link } from 'react-router'

export function NotFound() {
  return (
    <section className="py-16 text-center">
      <h1 className="mb-3 font-display text-3xl">Nothing playing here</h1>
      <Link to="/" className="text-gold underline-offset-4 hover:underline">
        Back to the lobby
      </Link>
    </section>
  )
}
