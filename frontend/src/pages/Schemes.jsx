import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getSchemes, searchSchemes, getCategories } from '../api/api'
import SchemeCard from '../components/SchemeCard'
import SearchBar from '../components/SearchBar'
import Filters from '../components/Filters'

const styles = {
  content: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '0 24px 40px',
  },
  toolbar: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
    marginBottom: '24px',
  },
  searchRow: {
    maxWidth: '600px',
  },
  statusFilters: {
    display: 'flex',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: '8px',
  },
  statusLabel: {
    fontSize: '0.85rem',
    fontWeight: 600,
    color: '#6B6F7E',
    marginRight: '4px',
  },
  statusButton: {
    padding: '6px 14px',
    borderRadius: '100px',
    fontSize: '0.85rem',
    fontWeight: 500,
    border: '1.5px solid rgba(255,255,255,0.1)',
    background: '#141319',
    color: '#9A988F',
    cursor: 'pointer',
    fontFamily: 'inherit',
  },
  statusButtonActive: {
    padding: '6px 14px',
    borderRadius: '100px',
    fontSize: '0.85rem',
    fontWeight: 600,
    border: '1.5px solid #E25822',
    background: 'rgba(226,88,34,0.15)',
    color: '#E25822',
    cursor: 'pointer',
    fontFamily: 'inherit',
  },
  results: {
    fontSize: '0.9rem',
    color: '#6B6F7E',
    marginBottom: '16px',
  },
  sortRow: {
    display: 'flex',
    justifyContent: 'flex-end',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '16px',
  },
  sortLabel: {
    fontSize: '0.85rem',
    fontWeight: 600,
    color: '#6B6F7E',
  },
  sortSelect: {
    padding: '8px 12px',
    borderRadius: '8px',
    border: '1.5px solid rgba(255,255,255,0.1)',
    background: '#141319',
    color: '#EEEEF2',
    fontSize: '0.85rem',
    fontFamily: 'inherit',
    cursor: 'pointer',
    outline: 'none',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
    gap: '20px',
  },
  pagination: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '12px',
    marginTop: '32px',
  },
  pageBtn: {
    padding: '8px 18px',
    borderRadius: '6px',
    border: '1.5px solid rgba(255,255,255,0.12)',
    background: '#141319',
    color: '#EEEEF2',
    fontWeight: 600,
    fontSize: '0.85rem',
    cursor: 'pointer',
    fontFamily: 'inherit',
    transition: 'all 0.2s',
  },
  pageBtnDisabled: {
    padding: '8px 18px',
    borderRadius: '6px',
    border: '1.5px solid rgba(255,255,255,0.06)',
    background: '#0F0F14',
    color: '#45485A',
    fontWeight: 600,
    fontSize: '0.85rem',
    cursor: 'not-allowed',
    fontFamily: 'inherit',
  },
  pageInfo: {
    fontSize: '0.9rem',
    color: '#6B6F7E',
  },
}

function Schemes() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [schemes, setSchemes] = useState([])
  const [categories, setCategories] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '')
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get('category') || null)
  const [sort, setSort] = useState(searchParams.get('sort') === 'recently_updated' ? 'recently_updated' : 'default')
  const [status, setStatus] = useState(['ACTIVE', 'INACTIVE'].includes(searchParams.get('status')) ? searchParams.get('status') : '')

  const limit = 12

  useEffect(() => {
    getCategories().then(cats => setCategories(cats.filter(c => c.name !== 'Training Program'))).catch(console.error)
  }, [])

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        if (searchQuery) {
          const res = await searchSchemes(searchQuery)
          setSchemes(res.results)
          setTotal(res.total)
        } else {
          const res = await getSchemes({
            page,
            limit,
            category: selectedCategory,
            status: status || undefined,
            sort: sort === 'recently_updated' ? 'recently_updated' : undefined,
          })
          setSchemes(res.schemes)
          setTotal(res.total)
        }
      } catch (err) {
        console.error('Failed to load schemes:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [page, selectedCategory, searchQuery, sort, status])

  const updateStatusParam = (nextStatus) => {
    const params = new URLSearchParams(searchParams)
    if (nextStatus) params.set('status', nextStatus)
    else params.delete('status')
    setSearchParams(params)
  }

  const handleStatusChange = (nextStatus) => {
    setStatus(nextStatus)
    setPage(1)
    updateStatusParam(nextStatus)
  }

  const handleSearch = (query) => {
    setSearchQuery(query)
    setSelectedCategory(null)
    setPage(1)
    setSearchParams(query ? { q: query } : {})
  }

  const handleCategorySelect = (catName) => {
    setSelectedCategory(catName)
    setSearchQuery('')
    setPage(1)
    setSearchParams(catName ? { category: catName } : {})
  }

  const handleSortChange = (value) => {
    setSort(value)
    setPage(1)
    setSearchParams(value === 'recently_updated' ? { sort: 'recently_updated' } : {})
  }

  const totalPages = Math.ceil(total / limit)

  return (
    <div>
      <div className="page-header">
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h1>Government Schemes</h1>
          <p>Browse {total} schemes from central and state government sources</p>
        </div>
      </div>

      <div style={styles.content}>
        <div style={styles.toolbar}>
          <div style={styles.searchRow}>
            <SearchBar
              onSearch={handleSearch}
              placeholder="Search by name, description..."
              variant="dark"
            />
          </div>
          {categories.length > 0 && (
            <Filters
              categories={categories}
              selected={selectedCategory}
              onSelect={handleCategorySelect}
            />
          )}
          <div style={styles.statusFilters}>
            <span style={styles.statusLabel}>Status:</span>
            {[
              { value: '', label: 'All' },
              { value: 'ACTIVE', label: 'Active' },
              { value: 'INACTIVE', label: 'Inactive' },
            ].map((option) => (
              <button
                key={option.value || 'all'}
                type="button"
                style={status === option.value ? styles.statusButtonActive : styles.statusButton}
                onClick={() => handleStatusChange(option.value)}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div style={styles.sortRow}>
          <span style={styles.sortLabel}>Sort:</span>
          <select
            style={{ ...styles.sortSelect, opacity: searchQuery ? 0.5 : 1, cursor: searchQuery ? 'not-allowed' : 'pointer' }}
            value={sort}
            onChange={(e) => handleSortChange(e.target.value)}
            disabled={!!searchQuery}
            title={searchQuery ? 'Clear your search to sort' : 'Sort schemes'}
          >
            <option value="default">Default (best match)</option>
            <option value="recently_updated">Recently updated</option>
          </select>
        </div>

        {searchQuery && (
          <div style={styles.results}>
            Showing {total} results for "<strong>{searchQuery}</strong>"
            <button
              onClick={() => handleSearch('')}
              style={{
                marginLeft: '12px',
                background: 'none',
                border: 'none',
                color: '#E25822',
                cursor: 'pointer',
                fontWeight: 600,
                fontFamily: 'inherit',
                fontSize: '0.85rem',
              }}
            >
              Clear
            </button>
          </div>
        )}

        {loading ? (
          <div className="loading">
            <div className="spinner" />
            Loading schemes...
          </div>
        ) : schemes.length === 0 ? (
          <div className="empty-state">
            <h3>No schemes found</h3>
            <p>Try a different search or filter</p>
          </div>
        ) : (
          <>
            <div style={styles.grid}>
              {schemes.map((s) => (
                <SchemeCard key={s.id} scheme={s} />
              ))}
            </div>

            {!searchQuery && totalPages > 1 && (
              <div style={styles.pagination}>
                <button
                  style={page <= 1 ? styles.pageBtnDisabled : styles.pageBtn}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                >
                  ← Previous
                </button>
                <span style={styles.pageInfo}>
                  Page {page} of {totalPages}
                </span>
                <button
                  style={page >= totalPages ? styles.pageBtnDisabled : styles.pageBtn}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                >
                  Next →
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default Schemes
