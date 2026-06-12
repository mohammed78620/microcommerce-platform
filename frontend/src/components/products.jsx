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
                    <span
                      className="variant-swatch"
                      style={{ backgroundColor: colour }}
                    />
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

export default function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [activeSearch, setActiveSearch] = useState('');
  const [pageNumber, setPageNumber] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);

  const PAGE_SIZE = 10;
  const activeSearchRef = useRef('');

  useEffect(() => {
    activeSearchRef.current = activeSearch;
  }, [activeSearch]);

  useEffect(() => {
    fetchProducts(activeSearch, pageNumber);
  }, [activeSearch, pageNumber]);

  const fetchProducts = async (query = '', page = 1) => {
    try {
      query ? setSearchLoading(true) : setLoading(true);

      let url, method, body;

      if (query.trim()) {
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
        setProducts(data);
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
    setActiveSearch(trimmed);
    setPageNumber(1);
    if (trimmed === activeSearchRef.current && pageNumber === 1) {
      fetchProducts(trimmed, 1);
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
    fetchProducts(activeSearchRef.current, newPage);
    setPageNumber(newPage);
  };

  // Now accepts optional variantId
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

  if (loading) {
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
      </div>

      {message && <div className="success-message">{message}</div>}

      {products.length === 0 ? (
        <p className="no-products">
          {activeSearch ? `No products found for "${activeSearch}"` : 'No products available'}
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
            <button className="pagination-btn" onClick={() => handlePageChange(pageNumber - 1)} disabled={!hasPrev}>
              ← Prev
            </button>
            <span className="pagination-info">Page {pageNumber}</span>
            <button className="pagination-btn" onClick={() => handlePageChange(pageNumber + 1)} disabled={!hasNext}>
              Next →
            </button>
          </div>
        </>
      )}
    </div>
  );
}