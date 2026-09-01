import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'

const fadeUp = {
    hidden: { opacity: 0, y: 16 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
}

const styles = {
    hero: {
        background: '#10182B',
        padding: '72px 0 48px',
        textAlign: 'center',
        width: '100%',
        borderBottom: '1px solid #26304F',
    },
    heroInner: { maxWidth: '640px', width: '90%', margin: '0 auto' },
    kicker: {
        color: '#B5643A',
        fontSize: '11px',
        fontWeight: 600,
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        marginBottom: '14px',
        display: 'block',
        fontFamily: "'DM Sans', system-ui, sans-serif",
    },
    heroTitle: {
        fontSize: '38px',
        fontWeight: 400,
        marginBottom: '16px',
        lineHeight: 1.25,
        color: '#EDEFF5',
        fontFamily: "'Source Serif 4', Georgia, serif",
        maxWidth: '540px',
        margin: '0 auto 16px auto',
    },
    heroSub: {
        color: '#8890A6',
        fontSize: '17px',
        lineHeight: 1.7,
        maxWidth: '540px',
        margin: '0 auto',
        fontFamily: "'DM Sans', system-ui, sans-serif",
    },
    section: { background: '#10182B', padding: '40px 0' },
    sectionAlt: {
        background: '#0E1525',
        padding: '60px 0',
        borderTop: '1px solid #26304F',
        borderBottom: '1px solid #26304F',
    },
    sectionInner: { maxWidth: '640px', width: '90%', margin: '0 auto' },
    h2: { fontSize: '26px', fontWeight: 700, color: '#EDEFF5', marginBottom: '16px', fontFamily: "'Eczar', Georgia, serif" },
    p: { color: '#8890A6', fontSize: '16px', lineHeight: 1.7, fontFamily: "'DM Sans', system-ui, sans-serif", marginBottom: '16px' },
    cardGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: '24px',
        maxWidth: '900px',
        width: '90%',
        margin: '40px auto',
    },
    card: {
        background: '#182240',
        border: '1px solid #26304F',
        borderRadius: '8px',
        padding: '24px',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: '0 1px 4px rgba(0,0,0,0.45)',
        transition: 'transform 0.18s, box-shadow 0.18s',
    },
    cardIcon: { marginBottom: '16px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '40px', height: '40px', borderRadius: '8px' },
    cardTitle: { fontSize: '16px', fontWeight: 700, color: '#EDEFF5', marginBottom: '8px', fontFamily: "'DM Sans', system-ui, sans-serif" },
    cardText: { fontSize: '14px', color: '#8890A6', lineHeight: 1.7, fontFamily: "'DM Sans', system-ui, sans-serif" },
    stepsGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: '24px',
        maxWidth: '900px',
        width: '90%',
        margin: '40px auto 60px',
    },
    step: {
        background: '#182240',
        border: '1px solid #26304F',
        borderRadius: '8px',
        padding: '24px',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: '0 1px 4px rgba(0,0,0,0.45)',
    },
    stepNumber: { fontSize: '12px', fontWeight: 700, color: '#B5643A', marginBottom: '8px', display: 'block', letterSpacing: '0.05em' },
    ctaBand: {
        background: '#182240',
        border: '1px solid #26304F',
        padding: '60px 40px',
        textAlign: 'center',
        maxWidth: '900px',
        width: '90%',
        margin: '40px auto 80px',
        borderRadius: '12px',
        color: '#EDEFF5',
        boxShadow: '0 0 0 1px rgba(181,100,58,0.12), 0 16px 40px rgba(0,0,0,0.5)',
    },
    btnRust: {
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#B5643A',
        color: '#fff',
        padding: '12px 28px',
        borderRadius: '4px',
        fontSize: '15px',
        fontWeight: 600,
        textDecoration: 'none',
        fontFamily: "'DM Sans', system-ui, sans-serif",
        marginTop: '24px',
        transition: 'opacity 0.2s, transform 0.15s',
    },
}

const CARD_THEMES = [
    { borderColor: '#6B8F71', tint: 'rgba(107,143,113,0.12)', color: '#8FBA96' },
    { borderColor: '#60A5FA', tint: 'rgba(96,165,250,0.12)', color: '#93B8E8' },
    { borderColor: '#F87171', tint: 'rgba(248,113,113,0.12)', color: '#F09090' },
    { borderColor: '#FBBF24', tint: 'rgba(251,191,36,0.12)', color: '#D4AA55' },
]

export default function About() {
    return (
        <div style={{ background: '#10182B', minHeight: '100vh', width: '100%', overflowX: 'hidden' }}>
            {/* Hero */}
            <motion.div
                style={styles.hero}
                variants={fadeUp}
                initial="hidden"
                animate="show"
            >
                <div style={styles.heroInner}>
                    <span style={styles.kicker}>About Suvidha</span>
                    <h1 style={styles.heroTitle}>Government schemes shouldn't be hard to find</h1>
                    <p style={styles.heroSub}>
                        Our mission is to surface verified government schemes so that no one misses out on the vital benefits and financial support they are rightfully entitled to.
                    </p>
                </div>
            </motion.div>

            {/* What Suvidha Does */}
            <div style={{ ...styles.section, paddingTop: 0 }}>
                <motion.div
                    style={styles.sectionInner}
                    variants={fadeUp}
                    initial="hidden"
                    whileInView="show"
                    viewport={{ once: true, margin: '-100px' }}
                >
                    <h2 style={styles.h2}>What Suvidha Does</h2>
                    <p style={styles.p}>
                        Suvidha seamlessly brings together essential scholarships, subsidies, and welfare grants from central and Karnataka state governments into a single, easily searchable platform.
                    </p>
                    <div style={{ height: '40px' }} />
                    <h2 style={styles.h2}>Why It Matters</h2>
                    <p style={styles.p}>
                        Scheme information is scattered across dozens of government portals. Eligibility criteria are often unclear, leaving many people to miss benefits they qualify for simply because they never found the scheme.
                    </p>
                </motion.div>
            </div>

            {/* Key Benefits */}
            <div style={styles.sectionAlt}>
                <motion.div
                    style={{ textAlign: 'center', maxWidth: '640px', margin: '0 auto 8px' }}
                    variants={fadeUp}
                    initial="hidden"
                    whileInView="show"
                    viewport={{ once: true, margin: '-100px' }}
                >
                    <h2 style={styles.h2}>Key Benefits</h2>
                </motion.div>
                <div style={styles.cardGrid}>
                    {[
                        { title: 'Verified data', text: 'Sourced directly from official government portals, not third-party aggregators.', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg> },
                        { title: 'One search, all categories', text: 'Welfare, scholarship, subsidy, loan, grant, skill programs in a single index.', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg> },
                        { title: 'Eligibility matching', text: 'Answer a few questions, get matched to schemes you actually qualify for.', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg> },
                        { title: 'Always current', text: 'Data is checked and refreshed regularly against source portals.', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" /><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" /></svg> },
                    ].map((item, idx) => (
                        <motion.div
                            key={idx}
                            style={styles.card}
                            whileHover={{ y: -4, boxShadow: '0 12px 32px rgba(0,0,0,0.55)' }}
                            transition={{ duration: 0.18 }}
                        >
                            <div style={{ position: 'absolute', top: 0, left: 0, bottom: 0, width: '4px', background: CARD_THEMES[idx].borderColor }} />
                            <div style={{ ...styles.cardIcon, background: CARD_THEMES[idx].tint, color: CARD_THEMES[idx].color }}>{item.icon}</div>
                            <div style={styles.cardTitle}>{item.title}</div>
                            <div style={styles.cardText}>{item.text}</div>
                        </motion.div>
                    ))}
                </div>
            </div>

            {/* How It Works */}
            <div style={{ ...styles.section, paddingBottom: '20px' }}>
                <motion.div
                    style={{ textAlign: 'center', maxWidth: '640px', margin: '0 auto 20px' }}
                    variants={fadeUp}
                    initial="hidden"
                    whileInView="show"
                    viewport={{ once: true, margin: '-100px' }}
                >
                    <h2 style={styles.h2}>How It Works</h2>
                </motion.div>
                <div style={styles.stepsGrid}>
                    {[
                        { step: '01', title: 'Search or browse', text: 'Find schemes by category, audience, or keyword.' },
                        { step: '02', title: 'Check eligibility', text: 'Filter schemes to see exactly which ones match your profile.' },
                        { step: '03', title: 'Apply directly', text: 'Suvidha links you out to the official portal to complete your application.' },
                    ].map((item, idx) => (
                        <motion.div
                            key={idx}
                            style={styles.step}
                            whileHover={{ y: -4, boxShadow: '0 12px 32px rgba(0,0,0,0.55)' }}
                            transition={{ duration: 0.18 }}
                        >
                            <span style={styles.stepNumber}>{item.step}</span>
                            <div style={styles.cardTitle}>{item.title}</div>
                            <div style={styles.cardText}>{item.text}</div>
                        </motion.div>
                    ))}
                </div>
            </div>

            {/* CTA Band */}
            <motion.div
                style={styles.ctaBand}
                variants={fadeUp}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true, margin: '-100px' }}
            >
                <h2 style={{ fontSize: '24px', fontFamily: "'Eczar', Georgia, serif", fontWeight: 400, marginBottom: '8px', color: '#EDEFF5' }}>
                    Ready to find your scheme?
                </h2>
                <p style={{ color: 'rgba(237,239,245,0.55)', fontSize: '15px' }}>
                    Search the directory of active government programs.
                </p>
                <Link
                    to="/schemes"
                    style={styles.btnRust}
                    onMouseEnter={e => { e.currentTarget.style.opacity = '0.9'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
                    onMouseLeave={e => { e.currentTarget.style.opacity = '1'; e.currentTarget.style.transform = 'translateY(0)'; }}
                >
                    Start exploring schemes
                </Link>
            </motion.div>
        </div>
    )
}
