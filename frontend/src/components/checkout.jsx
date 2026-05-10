import React, { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { CardElement, Elements, useStripe, useElements } from '@stripe/react-stripe-js';
import './checkout.css';

const stripePromise = loadStripe(`${process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY}`);

export default function CheckoutPage() {
  return (
    <Elements stripe={stripePromise}>
      <CheckoutForm />
    </Elements>
  );
}

function CheckoutForm() {
  const stripe = useStripe();
  const elements = useElements();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [orderId, setOrderId] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // 1. Call your checkout endpoint
      const checkoutResponse = await fetch(`${process.env.REACT_APP_ORDERS_URL}/api/cart/checkout/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!checkoutResponse.ok) {
        throw new Error('Checkout failed');
      }

      const { order_id, client_secret } = await checkoutResponse.json();
      setOrderId(order_id);

      // 2. Confirm payment with Stripe
      const result = await stripe.confirmCardPayment(client_secret, {
        payment_method: {
          card: elements.getElement(CardElement),
          billing_details: {
            name: 'Test User',
          },
        },
      });

      if (result.error) {
        setError(result.error.message);
      } else if (result.paymentIntent.status === 'succeeded') {
        setSuccess(true);
        // Wait a moment for webhook to process
        setTimeout(() => {
          window.location.href = '/products';
        }, 2000);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="success-message">
        <h2>Payment Successful!</h2>
        <p>Order #{orderId} created. Redirecting...</p>
      </div>
    );
  }

  return (
    <div className="checkout-container">
      <h1>Checkout</h1>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Card Details</label>
          <CardElement
            options={{
              style: {
                base: {
                  fontSize: '16px',
                  color: '#424770',
                  '::placeholder': {
                    color: '#aab7c4',
                  },
                },
                invalid: {
                  color: '#fa755a',
                },
              },
            }}
          />
        </div>

        {error && <div className="error-message">{error}</div>}

        <button
          type="submit"
          disabled={!stripe || loading}
          className="pay-button"
        >
          {loading ? 'Processing...' : 'Pay Now'}
        </button>
      </form>

      <div className="test-cards">
        <h3>Test Cards:</h3>
        <ul>
          <li>Success: 4242 4242 4242 4242</li>
          <li>Fail: 4000 0000 0000 0002</li>
          <li>Any future expiry, any 3-digit CVC</li>
        </ul>
      </div>
    </div>
  );
}