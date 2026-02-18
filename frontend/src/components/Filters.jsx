const styles = {
  wrapper: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    alignItems: 'center',
  },
  label: {
    fontSize: '0.85rem',
    fontWeight: 600,
    color: '#64748b',
    marginRight: '4px',
  },
  chip: {
    padding: '6px 14px',
    borderRadius: '100px',
    fontSize: '0.85rem',
    fontWeight: 500,
    border: '1.5px solid #e2e8f0',
    background: 'white',
    color: '#475569',
    cursor: 'pointer',
    transition: 'all 0.2s',
    fontFamily: 'inherit',
  },
  chipActive: {
    padding: '6px 14px',
    borderRadius: '100px',
    fontSize: '0.85rem',
    fontWeight: 500,
    border: '1.5px solid #0f4c81',
    background: '#0f4c81',
    color: 'white',
    cursor: 'pointer',
    transition: 'all 0.2s',
    fontFamily: 'inherit',
  },
}

function Filters({ categories, selected, onSelect }) {
  return (
    <div style={styles.wrapper}>
      <span style={styles.label}>Filter:</span>
      <button
        style={!selected ? styles.chipActive : styles.chip}
        onClick={() => onSelect(null)}
      >
        All
      </button>
      {categories.map((cat) => (
        <button
          key={cat.id}
          style={selected === cat.name ? styles.chipActive : styles.chip}
          onClick={() => onSelect(cat.name)}
        >
          {cat.name} ({cat.scheme_count})
        </button>
      ))}
    </div>
  )
}

export default Filters
