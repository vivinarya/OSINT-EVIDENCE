import { useRef, useEffect } from 'react'

export default function MagneticCursor() {
  const cursorRef = useRef(null)
  const pos = useRef({ x: 0, y: 0, cx: 0, cy: 0 })

  useEffect(() => {
    const onMouse = (e) => { pos.current.x = e.clientX; pos.current.y = e.clientY }
    const onLeave = () => { cursorRef.current.style.opacity = '0' }
    const onEnter = () => { cursorRef.current.style.opacity = '1' }
    window.addEventListener('mousemove', onMouse)
    document.addEventListener('mouseleave', onLeave)
    document.addEventListener('mouseenter', onEnter)
    return () => {
      window.removeEventListener('mousemove', onMouse)
      document.removeEventListener('mouseleave', onLeave)
      document.removeEventListener('mouseenter', onEnter)
    }
  }, [])

  useEffect(() => {
    let raf
    const tick = () => {
      const p = pos.current
      p.cx += (p.x - p.cx) * 0.12
      p.cy += (p.y - p.cy) * 0.12
      if (cursorRef.current) {
        cursorRef.current.style.transform = `translate(${p.cx - 12}px, ${p.cy - 12}px)`
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [])

  return (
    <div
      ref={cursorRef}
      className="cursor"
      style={{
        position: 'fixed',
        width: 24, height: 24,
        borderRadius: '50%',
        border: '1.5px solid var(--accent)',
        pointerEvents: 'none',
        zIndex: 9999,
        mixBlendMode: 'difference',
        transition: 'opacity 0.3s ease',
      }}
    />
  )
}
