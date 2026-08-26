import { useState } from 'react'
import { Link } from 'react-router-dom'
import { checkEligibility } from '../api/api'
import SchemeCard from '../components/SchemeCard'

const styles = {
  content: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '0 24px 60px',
  },
  layout: {
    display: 'grid',
    gridTemplateColumns: '380px 1fr',
    gap: '32px',
    alignItems: 'start',
  },
  form: {
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: '12px',
    padding: '28px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
    position: 'sticky',
    top: '88px',
  },
  formTitle: {
    fontSize: '1.15rem',
    fontWeight: 700,
    color: '#0f172a',
    marginBottom: '4px',
  },
  formSub: {
    fontSize: '0.85rem',
    color: '#64748b',
    marginBottom: '24px',
  },
  field: {
    marginBottom: '18px',
  },
  row: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '12px',
  },
  results: {
    minHeight: '300px',
  },
  resultHeader: {
    marginBottom: '20px',
  },
  resultTitle: {
    fontSize: '1.25rem',
    fontWeight: 700,
    color: '#0f172a',
    marginBottom: '4px',
  },
  resultSub: {
    fontSize: '0.9rem',
    color: '#64748b',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '1fr',
    gap: '16px',
  },
  matchCard: {
    border: '1px solid #e2e8f0',
    borderRadius: '10px',
    overflow: 'hidden',
  },
  matchReason: {
    background: '#f0fdf4',
    padding: '10px 20px',
    fontSize: '0.85rem',
    color: '#15803d',
    fontWeight: 500,
    borderTop: '1px solid #dcfce7',
  },
  emptyResults: {
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: '12px',
    padding: '60px 24px',
    textAlign: 'center',
  },
  emptyIcon: {
    fontSize: '3rem',
    marginBottom: '16px',
  },
  emptyTitle: {
    fontSize: '1.1rem',
    fontWeight: 600,
    color: '#334155',
    marginBottom: '8px',
  },
  emptyText: {
    fontSize: '0.9rem',
    color: '#64748b',
    maxWidth: '400px',
    margin: '0 auto',
    lineHeight: 1.6,
  },
  privacy: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginTop: '16px',
    padding: '12px',
    background: '#f0fdf4',
    borderRadius: '8px',
    fontSize: '0.8rem',
    color: '#15803d',
  },
}

function Eligibility() {
  const [form, setForm] = useState({
    age: '',
    income: '',
    gender: '',
    caste: '',
    state: '',
    education_level: '',
  })
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setSubmitted(true)
    try {
      const profile = {}
      if (form.age) profile.age = parseInt(form.age)
      if (form.income) profile.income = parseFloat(form.income)
      if (form.gender) profile.gender = form.gender
      if (form.caste) profile.caste = form.caste
      if (form.state) profile.state = form.state
      if (form.education_level) profile.education_level = form.education_level
      const data = await checkEligibility(profile)
      setResults(data)
    } catch (err) {
      console.error('Eligibility check failed:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h1>Check Eligibility</h1>
          <p>Enter your profile to find matching government schemes</p>
        </div>
      </div>

      <div style={styles.content}>
        <div style={styles.layout}>
          <form style={styles.form} onSubmit={handleSubmit}>
            <div style={styles.formTitle}>Your Profile</div>
            <div style={styles.formSub}>Fill in any fields that apply to you</div>

            <div style={styles.row}>
              <div style={styles.field}>
                <label>Age</label>
                <input
                  type="number"
                  name="age"
                  value={form.age}
                  onChange={handleChange}
                  placeholder="e.g. 20"
                  min="0"
                  max="100"
                />
              </div>
              <div style={styles.field}>
                <label>Annual Income (₹)</label>
                <input
                  type="number"
                  name="income"
                  value={form.income}
                  onChange={handleChange}
                  placeholder="e.g. 200000"
                  min="0"
                />
              </div>
            </div>

            <div style={styles.row}>
              <div style={styles.field}>
                <label>Gender</label>
                <select name="gender" value={form.gender} onChange={handleChange}>
                  <option value="">Any</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="others">Others</option>
                </select>
              </div>
              <div style={styles.field}>
                <label>Category</label>
                <select name="caste" value={form.caste} onChange={handleChange}>
                  <option value="">Any</option>
                  <option value="SC">SC</option>
                  <option value="ST">ST</option>
                  <option value="OBC">OBC</option>
                  <option value="general">General</option>
                </select>
              </div>
            </div>

            <div style={styles.field}>
              <label>State</label>
              <select name="state" value={form.state} onChange={handleChange}>
                <option value="">Any / All India</option>
                <option value="KA">Karnataka</option>
                <option value="MH">Maharashtra</option>
                <option value="TN">Tamil Nadu</option>
                <option value="AP">Andhra Pradesh</option>
                <option value="DL">Delhi</option>
                <option value="UP">Uttar Pradesh</option>
              </select>
            </div>

            <div style={styles.field}>
              <label>Education Level</label>
              <select name="education_level" value={form.education_level} onChange={handleChange}>
                <option value="">Any</option>
                <option value="7th_pass">7th Pass</option>
                <option value="8th_pass">8th Pass</option>
                <option value="10th_pass">10th Pass</option>
                <option value="12th_pass">12th Pass</option>
                <option value="graduate">Graduate</option>
                <option value="post_graduate">Post Graduate</option>
              </select>
            </div>

            <button
              type="submit"
              className="btn btn-accent"
              style={{ width: '100%', padding: '12px', fontSize: '1rem' }}
              disabled={loading}
            >
              {loading ? 'Checking...' : 'Check Eligibility'}
            </button>

            <div style={styles.privacy}>
              🔒 Privacy-first: No data is stored or shared
            </div>
          </form>

          <div style={styles.results}>
            {!submitted ? (
              <div style={styles.emptyResults}>
                <div style={styles.emptyIcon}>🎯</div>
                <div style={styles.emptyTitle}>Ready to check your eligibility</div>
                <div style={styles.emptyText}>
                  Fill in your profile on the left and click "Check Eligibility" to discover
                  matching government schemes, scholarships, and welfare programs.
                </div>
              </div>
            ) : loading ? (
              <div className="loading" style={{ minHeight: '300px' }}>
                <div className="spinner" />
                Finding matching schemes...
              </div>
            ) : results && results.matches.length > 0 ? (
              <>
                <div style={styles.resultHeader}>
                  <div style={styles.resultTitle}>
                    {results.total_matches} Matching Schemes Found
                  </div>
                  <div style={styles.resultSub}>
                    Based on your profile, you may be eligible for these schemes
                  </div>
                </div>
                <div style={styles.grid}>
                  {results.matches.map((match, i) => (
                    <div key={i} style={styles.matchCard}>
                      <div style={{ padding: '0' }}>
                        <SchemeCard scheme={match.scheme} />
                      </div>
                      <div style={styles.matchReason}>
                        ✓ {match.match_reason}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div style={styles.emptyResults}>
                <div style={styles.emptyIcon}>🔍</div>
                <div style={styles.emptyTitle}>No exact matches found</div>
                <div style={styles.emptyText}>
                  Try adjusting your profile details or leave some fields empty
                  for broader results.
                </div>
                <Link to="/schemes" className="btn btn-outline" style={{ marginTop: '16px' }}>
                  Browse All Schemes
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Eligibility
