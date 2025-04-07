import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import  axiosInstance from '../pages/axiosConfig';
import { useNavigate } from 'react-router-dom';
import { useLocation } from 'react-router-dom';

function ResetPassword() {
  const [formData, setFormData] = useState({
    newPassword: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState({
    newPassword: '',
    confirmPassword: '',
  });
  const [message, setMessage] = useState('');

  const validateForm = () => {
    const newErrors = {
      newPassword: '',
      confirmPassword: '',
    };

    if (!formData.newPassword) {
      newErrors.newPassword = 'New password is required';
    } else if (formData.newPassword.length < 6) {
      newErrors.newPassword = 'Password must be at least 6 characters';
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Confirm password is required';
    } else if (formData.newPassword !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return !newErrors.newPassword && !newErrors.confirmPassword;
  };
  const navigate = useNavigate();
  const location = useLocation();
  const userId = location.state?.userId;
  // const handleSubmit = async (e: { preventDefault: () => void; }) => {
  //   e.preventDefault();
  //   setMessage('');

  //   if (validateForm()) {
  //     try {
  //       const response = await axiosInstance.post('/resetpassword', {
  //         newPassword: formData.newPassword,
  //         confirmPassword: formData.confirmPassword,
  //       });
  //       // Store the JWT
  //       navigate('/login');
  //       console.log("success")
  //       // Redirect to another page, e.g., dashboard
  //       // Change '/dashboard' to your desired path
  //     } catch (error) {
  //       console.error('Login error:', error.response?.data || error.message);
  //     }

  //     setMessage('Your password has been successfully reset.');
  //     setFormData({ newPassword: '', confirmPassword: '' }); // Clear fields
  //   }
  // };

  const handleSubmit = async (e: { preventDefault: () => void; }) => {
    e.preventDefault();
    setMessage('');
  
    if (validateForm()) {
      try {
        const response = await axiosInstance.post('/reset-password', {
          user_id: userId,
          newPassword: formData.newPassword
        });
        navigate('/login');
      } catch (error) {
        console.error('Reset error:', error.response?.data || error.message);
        setMessage('Something went wrong. Please try again.');
      }
    }
  };
 
  const handleChange = (e: { target: { name: any; value: any; }; }) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: '' })); // Clear error when user starts typing
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
        <div className="max-w-md w-full backdrop-blur-xl bg-black/40 p-8 rounded-2xl shadow-[0_8px_32px_0_rgba(0,0,0,0.5)] border border-zinc-800/50">
          <div className="text-center">
            <h2 className="mt-6 text-3xl font-extrabold bg-gradient-to-r from-white via-zinc-400 to-zinc-500 text-transparent bg-clip-text">
              Reset Password
            </h2>
            <p className="mt-2 text-sm text-zinc-400">
              Enter your new password below.
            </p>
          </div>

          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-4">
              {/* New Password */}
              <div>
                <label htmlFor="newPassword" className="block text-sm font-medium text-zinc-300">
                  New Password
                </label>
                <div className="mt-1">
                  <input
                    id="newPassword"
                    name="newPassword"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={formData.newPassword}
                    onChange={handleChange}
                    className={`appearance-none block w-full px-3 py-2 border ${
                      errors.newPassword ? 'border-red-500' : 'border-zinc-800'
                    } bg-black/50 backdrop-blur-sm rounded-lg shadow-sm placeholder-zinc-500 text-white focus:outline-none focus:ring-2 focus:ring-white/25 focus:border-transparent transition-colors`}
                    placeholder="Enter new password"
                  />
                  {errors.newPassword && <p className="mt-1 text-sm text-red-500">{errors.newPassword}</p>}
                </div>
              </div>

              {/* Confirm Password */}
              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-zinc-300">
                  Confirm Password
                </label>
                <div className="mt-1">
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className={`appearance-none block w-full px-3 py-2 border ${
                      errors.confirmPassword ? 'border-red-500' : 'border-zinc-800'
                    } bg-black/50 backdrop-blur-sm rounded-lg shadow-sm placeholder-zinc-500 text-white focus:outline-none focus:ring-2 focus:ring-white/25 focus:border-transparent transition-colors`}
                    placeholder="Confirm new password"
                  />
                  {errors.confirmPassword && <p className="mt-1 text-sm text-red-500">{errors.confirmPassword}</p>}
                </div>
              </div>
            </div>

            {/* Success Message */}
            {message && <p className="mt-2 text-sm text-green-500 text-center">{message}</p>}

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-gradient-to-r from-indigo-600 via-purple-500 to-pink-500 hover:from-indigo-700 hover:via-purple-600 hover:to-pink-600 transition-all duration-200 md:py-4 md:text-lg md:px-10"
              >
                Reset Password
              </button>
            </div>
          </form>

          {/* Back to Login Link */}
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

export default ResetPassword;