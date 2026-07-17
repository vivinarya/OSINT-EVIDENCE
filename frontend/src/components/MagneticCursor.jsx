import { useRef, useEffect } from 'react'
import { gsap } from '../lib/gsap'

export default function MagneticCursor() {
  const cursorRef = useRef(null)
  const pos = useRef({ x: 0, y: 0, cx: 0, cy: 0 })

  useEffect(() => {
    const onMouse = (e) => {
      pos.current.x = e.clientX
      pos.current.y = e.clientY
    }
    const onLeave = () => { if (cursorRef.current) cursorRef.current.style.opacity = '0' }
    const onEnter = () => { if (cursorRef.current) cursorRef.current.style.opacity = '1' }

    window.addEventListener('mousemove', onMouse, { passive: true })
    document.addEventListener('mouseleave', onLeave)
    document.addEventListener('mouseenter', onEnter)

    // Drive cursor via GSAP ticker — shares the same RAF loop, no extra overhead
    const tick = () => {
      const p = pos.current
      p.cx += (p.x - p.cx) * 0.12
      p.cy += (p.y - p.cy) * 0.12
      if (cursorRef.current) {
        cursorRef.current.style.transform = `translate(${p.cx - 12}px, ${p.cy - 12}px)`
      }
    }
    gsap.ticker.add(tick)

    return () => {
      window.removeEventListener('mousemove', onMouse)
      document.removeEventListener('mouseleave', onLeave)
      document.removeEventListener('mouseenter', onEnter)
      gsap.ticker.remove(tick)
    }
  }, [])

  return (
    <div
      ref={cursorRef}
      style={{
        position: 'fixed',
        width: 24,
        height: 24,
        borderRadius: '50%',
        border: '1.5px solid var(--accent)',
        pointerEvents: 'none',
        zIndex: 9999,
        mixBlendMode: 'difference',
        transition: 'opacity 0.3s ease',
        top: 0,
        left: 0,
      }}
    />
  )
}
