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
    border: '1.5px solid rgba(255,255,255,0.1)',
    borderRadius: '8px',
    background: '#141319',
    color: '#EEEEF2',
    outline: 'none',
    transition: 'all 0.2s',
    fontFamily: 'inherit',
  },
  btn: {
    padding: '12px 24px',
    background: '#E25822',
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
        style={styles.input}
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
