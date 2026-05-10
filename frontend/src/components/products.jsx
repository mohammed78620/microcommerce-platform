import React, { useState, useEffect } from 'react';
import './products.css';

export default function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_PRODUCTS_URL}/api/products/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch products');
      }

      const data = await response.json();
      setProducts(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
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

      if (!response.ok) {
        throw new Error('Failed to add to cart');
      }

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

      {message && <div className="success-message">{message}</div>}

      {products.length === 0 ? (
        <p className="no-products">No products available</p>
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