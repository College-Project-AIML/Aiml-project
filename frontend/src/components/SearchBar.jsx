import { useState } from 'react'

const styles = {
  form: {
    display: 'flex',
    gap: '10px',
    width: '100%',
  },
  input: {
    flex: 1,
    padding: '12px 18px',
    fontSize: '1rem',
    border: '2px solid rgba(255,255,255,0.2)',
    borderRadius: '8px',
    background: 'rgba(255,255,255,0.1)',
    color: 'white',
    outline: 'none',
    transition: 'all 0.2s',
  },
  inputLight: {
    flex: 1,
    padding: '12px 18px',
    fontSize: '1rem',
    border: '1.5px solid #e2e8f0',
    borderRadius: '8px',
    background: 'white',
    color: '#1e293b',
    outline: 'none',
    transition: 'all 0.2s',
  },
  btn: {
    padding: '12px 24px',
    background: '#0d9488',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontWeight: 600,
    fontSize: '0.95rem',
    cursor: 'pointer',
    transition: 'background 0.2s',
    fontFamily: 'inherit',
    whiteSpace: 'nowrap',
  },
}

function SearchBar({ onSearch, placeholder = 'Search schemes...', variant = 'dark' }) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (query.trim()) {
      onSearch(query.trim())
    }
  }

  return (
    <form style={styles.form} onSubmit={handleSubmit}>
      <input
        style={variant === 'dark' ? styles.input : styles.inputLight}
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
      />
      <button style={styles.btn} type="submit">
        Search
      </button>
    </form>
  )
}

export default SearchBar
