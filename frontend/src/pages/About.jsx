import { Link } from 'react-router-dom'

const styles = {
    hero: {
        background: '#FBF8F1',
        padding: '72px 0 48px',
        textAlign: 'center',
        width: '100%',
    },
    heroInner: {
        maxWidth: '640px',
        width: '90%',
        margin: '0 auto',
    },
    kicker: {
        color: '#A9642B',
        fontSize: '13px',
        fontWeight: 'normal',
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        marginBottom: '14px',
        display: 'block',
        fontFamily: 'system-ui, -apple-system, sans-serif',
    },
    heroTitle: {
        fontSize: '38px',
        fontWeight: 400,
        marginBottom: '16px',
        lineHeight: 1.25,
        color: '#1B2A4A',
        fontFamily: "Georgia, 'Lora', 'Playfair Display', serif",
        maxWidth: '540px',
        margin: '0 auto 16px auto',
    },
    heroSub: {
        color: '#5B5748',
        fontSize: '17px',
        lineHeight: 1.7,
        marginBottom: '28px',
        maxWidth: '540px',
        margin: '0 auto',
        fontFamily: 'system-ui, -apple-system, sans-serif',
    },
    section: {
        background: '#FBF8F1',
        padding: '40px 0',
    },
    sectionInner: {
        maxWidth: '640px',
        width: '90%',
        margin: '0 auto',
    },
    h2: {
        fontSize: '26px',
        fontWeight: 700,
        color: '#1B2A4A',
        marginBottom: '16px',
        fontFamily: "Georgia, 'Lora', 'Playfair Display', serif",
    },
    p: {
        color: '#5B5748',
        fontSize: '16px',
        lineHeight: 1.7,
        fontFamily: 'system-ui, -apple-system, sans-serif',
        marginBottom: '16px',
    },
    cardGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: '24px',
        maxWidth: '900px',
        width: '90%',
        margin: '40px auto',
    },
    card: {
        background: '#FFFFFF',
        border: '1px solid #CBD5E1',
        borderRadius: '8px',
        padding: '24px',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
    },
    cardIcon: {
        marginBottom: '16px',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '40px',
        height: '40px',
        borderRadius: '8px',
    },
    cardTitle: {
        fontSize: '16px',
        fontWeight: 700,
        color: '#1B2A4A',
        marginBottom: '8px',
        fontFamily: 'system-ui, -apple-system, sans-serif',
    },
    cardText: {
        fontSize: '14px',
        color: '#5B5748',
        lineHeight: 1.7,
        fontFamily: 'system-ui, -apple-system, sans-serif',
    },
    stepsGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: '24px',
        maxWidth: '900px',
        width: '90%',
        margin: '40px auto 60px',
    },
    step: {
        background: '#FFFFFF',
        border: '1px solid #CBD5E1',
        borderRadius: '8px',
        padding: '24px',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
    },
    stepNumber: {
        fontSize: '12px',
        fontWeight: 700,
        color: '#A9642B',
        marginBottom: '8px',
        display: 'block',
        letterSpacing: '0.05em',
    },
    ctaBand: {
        background: '#1B2A4A',
        padding: '60px 40px',
        textAlign: 'center',
        maxWidth: '900px',
        width: '90%',
        margin: '40px auto 80px',
        borderRadius: '12px',
        color: '#FBF8F1',
        boxShadow: '0 10px 15px rgba(0, 0, 0, 0.08)',
    },
    btnRust: {
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#D85A30',
        color: '#FBF8F1',
        padding: '12px 28px',
        borderRadius: '4px',
        fontSize: '15px',
        fontWeight: 'normal',
        textDecoration: 'none',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        marginTop: '24px',
        transition: 'opacity 0.2s',
    }
}

export default function About() {
    return (
        <div style={{ background: '#FBF8F1', minHeight: '100vh', width: '100%', overflowX: 'hidden' }}>
            <div style={styles.hero}>
                <div style={styles.heroInner}>
                    <span style={styles.kicker}>ABOUT SUVIDHA</span>
                    <h1 style={styles.heroTitle}>
                        Government schemes shouldn't be hard to find
                    </h1>
                    <p style={styles.heroSub}>
                        Our mission is to surface verified government schemes so that no one misses out on the vital benefits and financial support they are rightfully entitled to.
                    </p>
                </div>
            </div>

            <div style={{ ...styles.section, paddingTop: 0 }}>
                <div style={styles.sectionInner}>
                    <h2 style={styles.h2}>What Suvidha Does</h2>
                    <p style={styles.p}>
                        Suvidha seamlessly brings together essential scholarships, subsidies, and welfare grants from central and Karnataka state governments into a single, easily searchable platform.
                    </p>

                    <div style={{ height: '40px' }} />

                    <h2 style={styles.h2}>Why It Matters</h2>
                    <p style={styles.p}>
                        Scheme information is scattered across dozens of government portals. Eligibility criteria are often unclear, leaving many people to miss benefits they qualify for simply because they never found the scheme.
                    </p>
                </div>
            </div>

            <div style={{ ...styles.section, background: '#FFFFFF', padding: '60px 0', borderTop: '1px solid #E2E8F0', borderBottom: '1px solid #E2E8F0' }}>
                <div style={{ textAlign: 'center', maxWidth: '640px', margin: '0 auto' }}>
                    <h2 style={styles.h2}>Key Benefits</h2>
                </div>
                <div style={styles.cardGrid}>
                    {[
                        {
                            title: 'Verified data',
                            text: 'Sourced directly from official government portals, not third-party aggregators.',
                            theme: { tint: '#ECFDF5', color: '#10B981', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg> },
                            borderColor: '#10B981'
                        },
                        {
                            title: 'One search, all categories',
                            text: 'Welfare, scholarship, subsidy, loan, grant, skill programs in a single index.',
                            theme: { tint: '#EFF6FF', color: '#3B82F6', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg> },
                            borderColor: '#3B82F6'
                        },
                        {
                            title: 'Eligibility matching',
                            text: 'Answer a few questions, get matched to schemes you actually qualify for.',
                            theme: { tint: '#FEF2F2', color: '#EF4444', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg> },
                            borderColor: '#EF4444'
                        },
                        {
                            title: 'Always current',
                            text: 'Data is checked and refreshed regularly against source portals.',
                            theme: { tint: '#FFFBEB', color: '#F59E0B', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg> },
                            borderColor: '#F59E0B'
                        }
                    ].map((item, idx) => (
                        <div key={idx} style={styles.card}>
                            <div style={{ position: 'absolute', top: 0, left: 0, bottom: 0, width: '4px', background: item.borderColor }} />
                            <div style={{ ...styles.cardIcon, background: item.theme.tint, color: item.theme.color }}>
                                {item.theme.icon}
                            </div>
                            <div style={styles.cardTitle}>{item.title}</div>
                            <div style={styles.cardText}>{item.text}</div>
                        </div>
                    ))}
                </div>
            </div>

            <div style={{ ...styles.section, paddingBottom: '20px' }}>
                <div style={{ textAlign: 'center', maxWidth: '640px', margin: '0 auto 20px' }}>
                    <h2 style={styles.h2}>How It Works</h2>
                </div>
                <div style={styles.stepsGrid}>
                    {[
                        { step: '01', title: 'Search or browse', text: 'Find schemes by category, audience, or keyword.' },
                        { step: '02', title: 'Check eligibility', text: 'Filter schemes to see exactly which ones match your profile.' },
                        { step: '03', title: 'Apply directly', text: 'Suvidha links you out to the official portal to complete your application.' }
                    ].map((item, idx) => (
                        <div key={idx} style={styles.step}>
                            <span style={styles.stepNumber}>{item.step}</span>
                            <div style={styles.cardTitle}>{item.title}</div>
                            <div style={styles.cardText}>{item.text}</div>
                        </div>
                    ))}
                </div>
            </div>

            <div style={styles.ctaBand}>
                <h2 style={{ fontSize: '24px', fontFamily: "Georgia, 'Lora', serif", fontWeight: 400, marginBottom: '8px' }}>
                    Ready to find your scheme?
                </h2>
                <p style={{ color: 'rgba(251,248,241,0.8)', fontSize: '15px' }}>
                    Search the directory of active government programs.
                </p>
                <Link
                    to="/schemes"
                    style={styles.btnRust}
                    onMouseEnter={(e) => e.target.style.opacity = '0.9'}
                    onMouseLeave={(e) => e.target.style.opacity = '1'}
                >
                    Start exploring schemes
                </Link>
            </div>
        </div>
    )
}
