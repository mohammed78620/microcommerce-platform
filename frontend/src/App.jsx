// frontend/src/App.js
import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './components/login';
import ProductsPage from './components/products';
import CartPage from './components/cart';
import CheckoutPage from './components/checkout';
import './App.css';
import OrdersPage from './components/orders';


function App() {
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    setToken(savedToken);
    setLoading(false);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh');
    localStorage.removeItem('user');
    setToken(null);
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!token) {
    return <LoginPage />;
  }

  return (
    <BrowserRouter>
      <div className="app">
        <header className="app-header">
          <h1>Microcommerce</h1>
          <nav className="nav-links">
            <a href="/products">Products</a>
            <a href="/cart">Cart</a>
            <a href="/orders">Orders</a>
            <button onClick={handleLogout} className="logout-button">
              Logout
            </button>
          </nav>
        </header>
        <Routes>
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/" element={<Navigate to="/products" />} />
          <Route path="/orders" element={<OrdersPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;