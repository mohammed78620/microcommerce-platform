import React, { useState, useEffect } from 'react';
import './products.css';

export default function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [activeSearch, setActiveSearch] = useState('');

  useEffect(() => {
    fetchProducts('');
  }, []);

  const fetchProducts = async (query = '') => {
    try {
      query ? setSearchLoading(true) : setLoading(true);

      let url, method, body;

      if (query.trim()) {
        url = `${process.env.REACT_APP_PRODUCTS_URL}/api/products/search/`;
        method = 'POST';
        body = JSON.stringify({ search: query.trim() });
      } else {
        url = `${process.env.REACT_APP_PRODUCTS_URL}/api/products/?limit=10`;
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
      setProducts(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setSearchLoading(false);
    }
  };

  const handleSearch = () => {
    setActiveSearch(searchQuery);
    fetchProducts(searchQuery);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSearch();
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setActiveSearch('');
    fetchProducts('');
  };

  const handleAddToCart = async (productId) => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_ORDERS_URL}/api/cart/${productId}/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

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
            <button className="clear-search-btn" onClick={handleClearSearch} aria-label="Clear search">
              ✕
            </button>
          )}
        </div>
        <button
          className="search-btn"
          onClick={handleSearch}
          disabled={searchLoading}
        >
          {searchLoading ? <span className="search-spinner" /> : 'Search'}
        </button>
      </div>

      {message && <div className="success-message">{message}</div>}

      {products.length === 0 ? (
        <p className="no-products">
          {activeSearch ? `No products found for "${activeSearch}"` : 'No products available'}
        </p>
      ) : (
        <div className="products-grid">
          {products.map((product) => (
            <div key={product.id} className="product-card">
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
                <div className="product-footer">
                  <span className="product-price">£{product.price}</span>
                  <button
                    onClick={() => handleAddToCart(product.id)}
                    className="add-to-cart-btn"
                  >
                    Add to Cart
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}