import { useEffect, useRef } from 'react'

// ── Config ───────────────────────────────────────────────────────────────────
const COUNT = 30           // total nodes
const HUB_COUNT = 5            // larger "hub" nodes with extra rings
const LINK_DIST = 160          // px — draw line if nodes are within this
const SPEED = 0.06         // px/frame baseline (very slow drift)
const FPS_CAP = 30

// Node appearance
const NODE_R_SMALL = 3            // small node core radius
const NODE_R_HUB = 5            // hub node core radius
const RING1_SCALE = 2.4          // first ring radius = core * scale
const RING2_SCALE = 4.2          // second ring radius

// Colours (RGB strings for rgba())
const ACCENT = '181,100,58'   // #B5643A terracotta
const LINE_COL = '181,100,58'   // line colour — same accent, kept subtle

// Opacity levels
const NODE_ALPHA = 0.55          // core fill opacity
const HUB_ALPHA = 0.75
const RING1_ALPHA = 0.18
const RING2_ALPHA = 0.08
const LINE_ALPHA = 0.22          // max line opacity at closest distance
const PULSE_SPEED = 1.2           // rad/sec for hub pulse

// Mouse interaction
const MOUSE_BOOST_DIST = 180       // px — cursor brightens nearby nodes
const MOUSE_BOOST = 0.45      // extra line opacity boost near cursor

function rand(min, max) { return min + Math.random() * (max - min) }

function makeNode(w, h, isHub) {
    const angle = rand(0, Math.PI * 2)
    const speed = SPEED * rand(0.5, 1.5)
    return {
        x: rand(0, w),
        y: rand(0, h),
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        r: isHub ? NODE_R_HUB : NODE_R_SMALL,
        isHub,
        pulsePhase: rand(0, Math.PI * 2),
    }
}

export default function ParticleCanvas() {
    const canvasRef = useRef(null)
    const mouseRef = useRef({ x: -9999, y: -9999 })

    useEffect(() => {
        const canvas = canvasRef.current
        if (!canvas) return
        const ctx = canvas.getContext('2d')

        const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches

        let W = 0, H = 0, nodes = []

        function resize() {
            const rect = canvas.parentElement.getBoundingClientRect()
            W = rect.width
            H = rect.height
            canvas.width = W
            canvas.height = H
            nodes = Array.from({ length: COUNT }, (_, i) => makeNode(W, H, i < HUB_COUNT))
        }

        resize()
        const ro = new ResizeObserver(resize)
        ro.observe(canvas.parentElement)

        // Track mouse position relative to canvas
        function onMouseMove(e) {
            const rect = canvas.getBoundingClientRect()
            mouseRef.current = { x: e.clientX - rect.left, y: e.clientY - rect.top }
        }
        function onMouseLeave() {
            mouseRef.current = { x: -9999, y: -9999 }
        }
        canvas.parentElement.addEventListener('mousemove', onMouseMove)
        canvas.parentElement.addEventListener('mouseleave', onMouseLeave)

        // Pause when scrolled out
        let visible = true
        const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting }, { threshold: 0 })
        io.observe(canvas)

        let rafId = null
        let lastTime = 0
        const interval = 1000 / FPS_CAP

        function draw(now) {
            rafId = requestAnimationFrame(draw)
            if (!visible) return
            const delta = now - lastTime
            if (delta < interval) return
            lastTime = now - (delta % interval)

            ctx.clearRect(0, 0, W, H)

            const t = now / 1000
            const mx = mouseRef.current.x
            const my = mouseRef.current.y

            // Move nodes
            if (!prefersReduced) {
                for (const n of nodes) {
                    n.x += n.vx
                    n.y += n.vy
                    if (n.x < 0) { n.x = 0; n.vx = Math.abs(n.vx) }
                    if (n.x > W) { n.x = W; n.vx = -Math.abs(n.vx) }
                    if (n.y < 0) { n.y = 0; n.vy = Math.abs(n.vy) }
                    if (n.y > H) { n.y = H; n.vy = -Math.abs(n.vy) }
                }
            }

            // ── Draw lines ────────────────────────────────────────────────────────
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const a = nodes[i], b = nodes[j]
                    const dx = a.x - b.x, dy = a.y - b.y
                    const dist = Math.sqrt(dx * dx + dy * dy)
                    if (dist >= LINK_DIST) continue

                    // Proximity fade
                    let alpha = LINE_ALPHA * (1 - dist / LINK_DIST)

                    // Mouse boost — brighten lines near the cursor
                    const midX = (a.x + b.x) / 2, midY = (a.y + b.y) / 2
                    const mdx = midX - mx, mdy = midY - my
                    const mDist = Math.sqrt(mdx * mdx + mdy * mdy)
                    if (mDist < MOUSE_BOOST_DIST) {
                        alpha += MOUSE_BOOST * (1 - mDist / MOUSE_BOOST_DIST)
                    }
                    alpha = Math.min(alpha, 0.75)

                    ctx.lineWidth = 1
                    ctx.strokeStyle = `rgba(${LINE_COL},${alpha.toFixed(3)})`
                    ctx.beginPath()
                    ctx.moveTo(a.x, a.y)
                    ctx.lineTo(b.x, b.y)
                    ctx.stroke()
                }
            }

            // ── Draw nodes ────────────────────────────────────────────────────────
            for (const n of nodes) {
                const pulse = Math.sin(t * PULSE_SPEED + n.pulsePhase) * 0.5 + 0.5 // 0→1

                // Mouse proximity glow for all nodes
                const ndx = n.x - mx, ndy = n.y - my
                const nmd = Math.sqrt(ndx * ndx + ndy * ndy)
                const mouseGlow = nmd < MOUSE_BOOST_DIST
                    ? (1 - nmd / MOUSE_BOOST_DIST) * 0.4
                    : 0

                const baseAlpha = (n.isHub ? HUB_ALPHA : NODE_ALPHA) + mouseGlow
                const coreR = n.r + (n.isHub ? pulse * 1.5 : pulse * 0.6)

                // Outer ring 2 (faintest)
                ctx.beginPath()
                ctx.arc(n.x, n.y, coreR * RING2_SCALE, 0, Math.PI * 2)
                ctx.strokeStyle = `rgba(${ACCENT},${(RING2_ALPHA + mouseGlow * 0.12).toFixed(3)})`
                ctx.lineWidth = 0.8
                ctx.stroke()

                // Ring 1
                ctx.beginPath()
                ctx.arc(n.x, n.y, coreR * RING1_SCALE, 0, Math.PI * 2)
                ctx.strokeStyle = `rgba(${ACCENT},${(RING1_ALPHA + mouseGlow * 0.2).toFixed(3)})`
                ctx.lineWidth = n.isHub ? 1 : 0.8
                ctx.stroke()

                // Core fill
                ctx.beginPath()
                ctx.arc(n.x, n.y, coreR, 0, Math.PI * 2)
                ctx.fillStyle = `rgba(${ACCENT},${Math.min(baseAlpha, 0.9).toFixed(3)})`
                ctx.fill()

                // Small bright centre highlight
                ctx.beginPath()
                ctx.arc(n.x, n.y, coreR * 0.45, 0, Math.PI * 2)
                ctx.fillStyle = `rgba(255,220,190,${(baseAlpha * 0.6).toFixed(3)})`
                ctx.fill()
            }
        }

        rafId = requestAnimationFrame(draw)

        return () => {
            cancelAnimationFrame(rafId)
            ro.disconnect()
            io.disconnect()
            canvas.parentElement.removeEventListener('mousemove', onMouseMove)
            canvas.parentElement.removeEventListener('mouseleave', onMouseLeave)
        }
    }, [])

    return (
        <canvas
            ref={canvasRef}
            aria-hidden="true"
            style={{
                position: 'absolute',
                inset: 0,
                width: '100%',
                height: '100%',
                pointerEvents: 'none',
                zIndex: 0,
            }}
        />
    )
}
