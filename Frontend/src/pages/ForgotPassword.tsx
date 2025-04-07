import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import  axiosInstance from '../pages/axiosConfig';
import { useNavigate } from 'react-router-dom';



function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();
  // const handleSubmit = async(e: { preventDefault: () => void; }) => {
  //   e.preventDefault();
  //   setError('');
  //   setMessage('');

  //   if (!email) {
  //     setError('Email is required');
  //     return;
  //   }
  //   if (!/\S+@\S+\.\S+/.test(email)) {
  //     setError('Please enter a valid email');
  //     return;
  //   }
  //   try {
  //     const response = await axiosInstance.post('/forgot-password', {
  //       email: email,
      
  //     });
  //     // Store the JWT
  //     navigate('/login');
  //     console.log("success")
  //     // Redirect to another page, e.g., dashboard
  //     // Change '/dashboard' to your desired path
  //   } catch (error) {
  //     console.error('Login error:', error.response?.data || error.message);
  //   }
  //   // Simulate password reset logic
  //   setMessage('A password reset link has been sent to your email.');
  // };

  const handleSubmit = async (e: { preventDefault: () => void }) => {
    e.preventDefault();
    setError('');
    setMessage('');
  
    if (!email) {
      setError('Email is required');
      return;
    }
    if (!/\S+@\S+\.\S+/.test(email)) {
      setError('Please enter a valid email');
      return;
    }
  
    try {
      const response = await axiosInstance.post('/forgot-password', { email });
      if (response.status === 200) {
        const userId = response.data.user_id;
        navigate('/reset-password', { state: { userId } });
      }
    } catch (error: any) {
      console.error('Error:', error.response?.data || error.message);
      setError("Email not found. Please try again.");
    }
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
        <div className="max-w-md w-full backdrop-blur-xl bg-black/40 p-8 rounded-2xl shadow-[0_8px_32px_0_rgba(0,0,0,0.5)] border border-zinc-800/50">
          <div className="text-center">
            <h2 className="mt-6 text-3xl font-extrabold bg-gradient-to-r from-white via-zinc-400 to-zinc-500 text-transparent bg-clip-text">
              Forgot Password?
            </h2>
            <p className="mt-2 text-sm text-zinc-400">
              Enter your email, and we'll send you a reset link.
            </p>
          </div>

          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-zinc-300">
                  Email address
                </label>
                <div className="mt-1">
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      setError('');
                      setMessage('');
                    }}
                    className={`appearance-none block w-full px-3 py-2 border ${
                      error ? 'border-red-500' : 'border-zinc-800'
                    } bg-black/50 backdrop-blur-sm rounded-lg shadow-sm placeholder-zinc-500 text-white focus:outline-none focus:ring-2 focus:ring-white/25 focus:border-transparent transition-colors`}
                    placeholder="Enter your email"
                  />
                  {error && <p className="mt-1 text-sm text-red-500">{error}</p>}
                  {message && <p className="mt-1 text-sm text-green-500">{message}</p>}
                </div>
              </div>
            </div>

            <div>
              <button
                type="submit"
                className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-gradient-to-r from-indigo-600 via-purple-500 to-pink-500 hover:from-indigo-700 hover:via-purple-600 hover:to-pink-600 transition-all duration-200 md:py-4 md:text-lg md:px-10"
              >
                Reset Password
              </button>
            </div>
          </form>

          <div className="mt-4 text-center">
            <Link to="/login" className="text-sm text-white hover:text-zinc-300 transition-colors">
              Back to Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ForgotPassword;