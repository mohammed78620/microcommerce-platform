import React, { useState, useEffect, useRef } from 'react';
import './products.css';

function ProductCard({ product, onAddToCart }) {
  const variants = product.product_variant || [];
  const [selectedVariant, setSelectedVariant] = useState(variants[0] || null);

  return (
    <div className="product-card">
      <div className="product-image">
        {product.image ? (
          <img src={product.image} alt={product.name} />
        ) : (
          <div className="placeholder">No Image</div>
        )}
      </div>
      <div className="product-details">
        <h2>{product.name}</h2>
        <p className="product-description">{product.description}</p>

        {variants.length > 0 && (
          <div className="product-variants">

            {/* Type */}
            <div className="variant-group">
              <span className="variants-label">Type:</span>
              <div className="variant-options">
                {[...new Set(variants.map((v) => v.type))].map((type) => (
                  <button
                    key={type}
                    className={`variant-btn ${selectedVariant?.type === type ? 'active' : ''}`}
                    onClick={() => {
                      const match = variants.find(
                        (v) => v.type === type &&
                        v.colour === selectedVariant?.colour &&
                        v.size === selectedVariant?.size
                      ) || variants.find((v) => v.type === type);
                      setSelectedVariant(match);
                    }}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>

            {/* Colour */}
            <div className="variant-group">
              <span className="variants-label">Colour:</span>
              <div className="variant-options">
                {[...new Set(variants.map((v) => v.colour))].map((colour) => (
                  <button
                    key={colour}
                    className={`variant-btn ${selectedVariant?.colour === colour ? 'active' : ''}`}
                    onClick={() => {
                      const match = variants.find(
                        (v) => v.colour === colour &&
                        v.type === selectedVariant?.type &&
                        v.size === selectedVariant?.size
                      ) || variants.find((v) => v.colour === colour);
                      setSelectedVariant(match);
                    }}
                    title={colour}
                  >
                    <span className="variant-swatch" style={{ backgroundColor: colour }} />
                    <span className="variant-colour-name">{colour}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Size */}
            <div className="variant-group">
              <span className="variants-label">Size:</span>
              <div className="variant-options">
                {[...new Set(variants.map((v) => v.size))].map((size) => (
                  <button
                    key={size}
                    className={`variant-btn ${selectedVariant?.size === size ? 'active' : ''}`}
                    onClick={() => {
                      const match = variants.find(
                        (v) => v.size === size &&
                        v.colour === selectedVariant?.colour &&
                        v.type === selectedVariant?.type
                      ) || variants.find((v) => v.size === size);
                      setSelectedVariant(match);
                    }}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>

            {/* SKU */}
            {selectedVariant?.sku && (
              <p className="variant-sku">SKU: {selectedVariant.sku}</p>
            )}

          </div>
        )}

        <div className="product-footer">
          <span className="product-price">
            £{selectedVariant ? selectedVariant.price : '—'}
          </span>
          <button
            onClick={() => onAddToCart(product.id, selectedVariant?.id)}
            className="add-to-cart-btn"
            disabled={!selectedVariant}
          >
            Add to Cart
          </button>
        </div>
      </div>
    </div>
  );
}

// Recursive component to render category tree
function CategoryTree({ categories, selectedSlug, onSelect, depth = 0 }) {
  return (
    <ul className={`category-list ${depth > 0 ? 'category-list--nested' : ''}`}>
      {categories.map((cat) => (
        <li key={cat.slug || cat.id} className="category-item">
          <button
            className={`category-btn ${selectedSlug === cat.slug ? 'active' : ''}`}
            onClick={() => onSelect(cat.slug)}
            style={{ paddingLeft: `${12 + depth * 14}px` }}
          >
            {selectedSlug === cat.slug && <span className="category-indicator" />}
            {cat.name}
          </button>
          {cat.children?.length > 0 && (
            <CategoryTree
              categories={cat.children}
              selectedSlug={selectedSlug}
              onSelect={onSelect}
              depth={depth + 1}
            />
          )}
        </li>
      ))}
    </ul>
  );
}

export default function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);

  // Search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [activeSearch, setActiveSearch] = useState('');

  // Pagination
  const [pageNumber, setPageNumber] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);

  // Categories & tags
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null); // slug string
  const [tags, setTags] = useState([]);
  const [selectedTags, setSelectedTags] = useState([]); // array of tag slugs/names
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const PAGE_SIZE = 10;
  const activeSearchRef = useRef('');

  useEffect(() => {
    activeSearchRef.current = activeSearch;
  }, [activeSearch]);

  // Load categories and tags once on mount
  useEffect(() => {
    fetchCategories();
    fetchTags();
  }, []);

  // Re-fetch products when filters change
  useEffect(() => {
    fetchProducts(activeSearch, pageNumber, selectedCategory, selectedTags);
  }, [activeSearch, pageNumber, selectedCategory, selectedTags]);

  const fetchCategories = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_PRODUCTS_URL}/api/products/category/?limit=100`,
        {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        }
      );
      if (!response.ok) throw new Error('Failed to fetch categories');
      const data = await response.json();
      setCategories(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      console.error('Categories error:', err);
    }
  };

  const fetchTags = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_PRODUCTS_URL}/api/products/tag/?limit=100`,
        {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        }
      );
      if (!response.ok) throw new Error('Failed to fetch tags');
      const data = await response.json();
      setTags(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      console.error('Tags error:', err);
    }
  };

  const fetchProducts = async (query = '', page = 1, categorySlug = null, activeTags = []) => {
    try {
      query ? setSearchLoading(true) : setLoading(true);

      let url, method, body;

      if (categorySlug) {
        // Category (+ optional tag) filter
        const tagParam = activeTags.length ? `&tags=${activeTags.join(',')}` : '';
        url = `${process.env.REACT_APP_PRODUCTS_URL}/api/products/category/${categorySlug}/products/?page_number=${page}&limit=${PAGE_SIZE}${tagParam}`;
        method = 'GET';
      } else if (query.trim()) {
        url = `${process.env.REACT_APP_PRODUCTS_URL}/api/products/search/?page_number=${page}&limit=${PAGE_SIZE}`;
        method = 'POST';
        body = JSON.stringify({ search: query.trim() });
      } else {
        url = `${process.env.REACT_APP_PRODUCTS_URL}/api/products/?limit=${PAGE_SIZE}&page_number=${page}`;
        method = 'GET';
      }

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        ...(body && { body }),
      });

      if (!response.ok) throw new Error('Failed to fetch products');

      const data = await response.json();

      if (data.results !== undefined) {
        setProducts(data.results);
        setHasNext(!!data.next);
        setHasPrev(!!data.previous);
      } else {
        setProducts(Array.isArray(data) ? data : []);
        setHasNext(false);
        setHasPrev(false);
      }

      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setSearchLoading(false);
    }
  };

  const handleSearch = () => {
    const trimmed = searchQuery.trim();
    setSelectedCategory(null);
    setSelectedTags([]);
    setActiveSearch(trimmed);
    setPageNumber(1);
    if (trimmed === activeSearchRef.current && pageNumber === 1) {
      fetchProducts(trimmed, 1, null, []);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSearch();
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setActiveSearch('');
    setPageNumber(1);
  };

  const handlePageChange = (newPage) => {
    setPageNumber(newPage);
  };

  const handleCategorySelect = (slug) => {
    if (slug === selectedCategory) {
      // Deselect
      setSelectedCategory(null);
    } else {
      setSelectedCategory(slug);
      setActiveSearch('');
      setSearchQuery('');
      setPageNumber(1);
    }
    setSidebarOpen(false);
  };

  const handleTagToggle = (tagName) => {
    setSelectedTags((prev) =>
      prev.includes(tagName) ? prev.filter((t) => t !== tagName) : [...prev, tagName]
    );
    setPageNumber(1);
  };

  const handleClearFilters = () => {
    setSelectedCategory(null);
    setSelectedTags([]);
    setSearchQuery('');
    setActiveSearch('');
    setPageNumber(1);
  };

  const handleAddToCart = async (productId, variantId) => {
    try {
      const url = variantId
        ? `${process.env.REACT_APP_ORDERS_URL}/api/cart/${productId}/${variantId}/`
        : `${process.env.REACT_APP_ORDERS_URL}/api/cart/${productId}/`;

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to add to cart');

      setMessage('Added to cart!');
      setTimeout(() => setMessage(null), 2000);
    } catch (err) {
      setError(err.message);
    }
  };

  const hasActiveFilters = selectedCategory || selectedTags.length > 0 || activeSearch;

  const selectedCategoryName = selectedCategory
    ? findCategoryName(categories, selectedCategory)
    : null;

  if (loading && products.length === 0) {
    return <div className="products-container"><p>Loading products...</p></div>;
  }

  if (error) {
    return <div className="products-container"><div className="error-message">{error}</div></div>;
  }

  return (
    <div className="products-container">
      <div className="products-header">
        <h1>Products</h1>
        <a href="/cart" className="cart-link">View Cart</a>
      </div>

      {/* Search bar */}
      <div className="search-bar-wrapper">
        <div className="search-bar">
          <svg className="search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z" clipRule="evenodd" />
          </svg>
          <input
            type="text"
            placeholder="Search products..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="search-input"
          />
          {searchQuery && (
            <button className="clear-search-btn" onClick={handleClearSearch} aria-label="Clear search">✕</button>
          )}
        </div>
        <button className="search-btn" onClick={handleSearch} disabled={searchLoading}>
          {searchLoading ? <span className="search-spinner" /> : 'Search'}
        </button>
        {/* Mobile: toggle sidebar */}
        <button
          className="filter-toggle-btn"
          onClick={() => setSidebarOpen((v) => !v)}
          aria-label="Toggle filters"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
            <path fillRule="evenodd" d="M2.75 4A.75.75 0 013.5 3.25h13a.75.75 0 010 1.5h-13A.75.75 0 012.75 4zM5.25 9a.75.75 0 01.75-.75h8a.75.75 0 010 1.5h-8A.75.75 0 015.25 9zm2.5 4.25a.75.75 0 000 1.5h4a.75.75 0 000-1.5h-4z" clipRule="evenodd" />
          </svg>
          Filters
          {(selectedCategory || selectedTags.length > 0) && (
            <span className="filter-badge">{selectedTags.length + (selectedCategory ? 1 : 0)}</span>
          )}
        </button>
      </div>

      {/* Active filter chips */}
      {hasActiveFilters && (
        <div className="active-filters">
          {activeSearch && (
            <span className="filter-chip">
              Search: "{activeSearch}"
              <button onClick={handleClearSearch}>✕</button>
            </span>
          )}
          {selectedCategoryName && (
            <span className="filter-chip">
              {selectedCategoryName}
              <button onClick={() => setSelectedCategory(null)}>✕</button>
            </span>
          )}
          {selectedTags.map((tag) => (
            <span key={tag} className="filter-chip">
              {tag}
              <button onClick={() => handleTagToggle(tag)}>✕</button>
            </span>
          ))}
          <button className="clear-all-btn" onClick={handleClearFilters}>
            Clear all
          </button>
        </div>
      )}

      {message && <div className="success-message">{message}</div>}

      <div className="products-layout">
        {/* Sidebar */}
        <aside className={`products-sidebar ${sidebarOpen ? 'products-sidebar--open' : ''}`}>
          {sidebarOpen && (
            <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
          )}
          <div className="sidebar-panel">
            <div className="sidebar-section">
              <h3 className="sidebar-heading">Categories</h3>
              {categories.length === 0 ? (
                <p className="sidebar-empty">No categories</p>
              ) : (
                <>
                  <button
                    className={`category-btn category-btn--all ${!selectedCategory ? 'active' : ''}`}
                    onClick={() => handleCategorySelect(null)}
                  >
                    All products
                  </button>
                  <CategoryTree
                    categories={categories}
                    selectedSlug={selectedCategory}
                    onSelect={handleCategorySelect}
                  />
                </>
              )}
            </div>

            {tags.length > 0 && (
              <div className="sidebar-section">
                <h3 className="sidebar-heading">Tags</h3>
                <div className="tag-list">
                  {tags.map((tag) => (
                    <button
                      key={tag.id || tag.name}
                      className={`tag-btn ${selectedTags.includes(tag.name) ? 'active' : ''}`}
                      onClick={() => handleTagToggle(tag.name)}
                      disabled={!selectedCategory}
                      title={!selectedCategory ? 'Select a category to filter by tag' : ''}
                    >
                      {tag.name}
                    </button>
                  ))}
                </div>
                {!selectedCategory && (
                  <p className="sidebar-hint">Choose a category to filter by tag</p>
                )}
              </div>
            )}
          </div>
        </aside>

        {/* Main content */}
        <main className="products-main">
          {loading ? (
            <p>Loading products...</p>
          ) : products.length === 0 ? (
            <p className="no-products">
              {activeSearch
                ? `No products found for "${activeSearch}"`
                : selectedCategoryName
                ? `No products in "${selectedCategoryName}"`
                : 'No products available'}
            </p>
          ) : (
            <>
              <div className="products-grid">
                {products.map((product) => (
                  <ProductCard
                    key={product.id}
                    product={product}
                    onAddToCart={handleAddToCart}
                  />
                ))}
              </div>

              <div className="pagination">
                <button
                  className="pagination-btn"
                  onClick={() => handlePageChange(pageNumber - 1)}
                  disabled={!hasPrev}
                >
                  ← Prev
                </button>
                <span className="pagination-info">Page {pageNumber}</span>
                <button
                  className="pagination-btn"
                  onClick={() => handlePageChange(pageNumber + 1)}
                  disabled={!hasNext}
                >
                  Next →
                </button>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

// Helper: find a category name by slug in a (possibly nested) list
function findCategoryName(categories, slug) {
  for (const cat of categories) {
    if (cat.slug === slug) return cat.name;
    if (cat.children?.length) {
      const found = findCategoryName(cat.children, slug);
      if (found) return found;
    }
  }
  return slug;
}