import React, { useState, useEffect } from 'react';
import './orders.css';

export default function OrdersPage() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      setError(null);

      const userStr = localStorage.getItem('user');
      const token = localStorage.getItem('token');

      if (!userStr || !token) {
        throw new Error('User not authenticated');
      }

      const user = JSON.parse(userStr);
      const userId = user?.id;

      if (!userId) {
        throw new Error('Invalid user data');
      }

      const response = await fetch(
        `${process.env.REACT_APP_ORDERS_URL}/api/orders/${userId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || 'Failed to fetch orders');
      }

      const data = await response.json();
      setOrders(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="orders-container">
        <p>Loading orders...</p>
      </div>
    );
  }

  return (
    <div className="orders-container">
      <div className="orders-header">
        <h1>My Orders</h1>
        <a href="/products" className="continue-shopping">
          Continue Shopping
        </a>
      </div>

      {error && <div className="error-message">{error}</div>}

      {orders.length === 0 ? (
        <div className="empty-orders">
          <p>No orders yet</p>
          <a href="/products" className="shop-button">
            Start Shopping
          </a>
        </div>
      ) : (
        <div className="orders-list">
          {orders.map((order) => {
            const orderId = order.order_id;
            const items = Array.isArray(order.items) ? order.items : [];

            const orderTotal = items.reduce(
              (sum, item) =>
                sum + ((item.price || 0) * (item.quantity || 0)),
              0
            );

            const itemCount = items.reduce(
              (sum, item) => sum + (item.quantity || 0),
              0
            );

            return (
              <div key={orderId} className="order-card">
                <div className="order-header">
                  <div className="order-info">
                    <h2>Order #{orderId}</h2>
                    <p className="order-status">{order.status}</p>
                    <p className="order-items">
                      {itemCount} item{itemCount !== 1 ? 's' : ''}
                    </p>
                  </div>
                  <div className="order-total">
                    <span className="label">Total:</span>
                    <span className="amount">
                      £{orderTotal.toFixed(2)}
                    </span>
                  </div>
                </div>

                <div className="order-items-list">
                  <div className="items-header">
                    <div>Product</div>
                    <div>Quantity</div>
                    <div>Price</div>
                    <div>Subtotal</div>
                  </div>

                  {items.map((item) => {
                    const price = item.price || 0;
                    const quantity = item.quantity || 0;
                    const subtotal = price * quantity;

                    return (
                      <div key={item.id} className="order-item-row">
                        <div className="item-name">{item.name}</div>
                        <div className="item-quantity">{quantity}</div>
                        <div className="item-price">
                          £{price.toFixed(2)}
                        </div>
                        <div className="item-subtotal">
                          £{subtotal.toFixed(2)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}