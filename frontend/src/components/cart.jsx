import React, { useState, useEffect } from 'react';
import './cart.css';

export default function CartPage() {
  const [cartItems, setCartItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    fetchCart();
  }, []);

  useEffect(() => {
    calculateTotal();
  }, [cartItems]);

  const fetchCart = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_ORDERS_URL}/api/cart/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch cart');
      }

      const data = await response.json();
      setCartItems(data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const calculateTotal = () => {
    const sum = cartItems.reduce((acc, item) => {
      return acc + (item.price * item.quantity);
    }, 0);
    setTotal(sum);
  };

  const handleRemoveItem = async (productId) => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_ORDERS_URL}/api/cart/${productId}/`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to remove item');
      }

      setCartItems(prev =>
        prev
          .map(item => item.product_id === productId ? { ...item, quantity: item.quantity - 1 } : item)
          .filter(item => item.quantity > 0)
      );
    } catch (err) {
      setError(err.message);
    }
  };

  
  const handleCheckout = () => {
    window.location.href = '/checkout';
  };

  if (loading) {
    return <div className="cart-container"><p>Loading cart...</p></div>;
  }

  return (
    <div className="cart-container">
      <div className="cart-header">
        <h1>Shopping Cart</h1>
        <a href="/products" className="continue-shopping">← Continue Shopping</a>
      </div>

      {error && <div className="error-message">{error}</div>}

      {cartItems.length === 0 ? (
        <div className="empty-cart">
          <p>Your cart is empty</p>
          <a href="/products" className="shop-button">Start Shopping</a>
        </div>
      ) : (
        <>
          <div className="cart-items">
            <div className="cart-header-row">
              <div>Product</div>
              <div>Price</div>
              <div>Quantity</div>
              <div>Total</div>
              <div>Action</div>
            </div>

            {cartItems.map((item) => (
              <div key={item.product_id} className="cart-item">
                <div className="item-name">{item.name}</div>
                <div className="item-price">£{item.price.toFixed(2)}</div>
                <div className="item-quantity">{item.quantity}</div>
                <div className="item-total">£{(item.price * item.quantity).toFixed(2)}</div>
                <button
                  onClick={() => handleRemoveItem(item.product_id)}
                  className="remove-btn"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>

          <div className="cart-summary">
            <div className="summary-row">
              <span>Subtotal:</span>
              <span>£{total.toFixed(2)}</span>
            </div>
            <div className="summary-row">
              <span>Shipping:</span>
              <span>£0.00</span>
            </div>
            <div className="summary-row total-row">
              <span>Total:</span>
              <span>£{total.toFixed(2)}</span>
            </div>

            <button
              onClick={handleCheckout}
              className="checkout-btn"
            >
              Proceed to Checkout
            </button>
          </div>
        </>
      )}
    </div>
  );
}