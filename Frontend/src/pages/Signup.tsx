import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Eye, EyeOff, UserPlus } from 'lucide-react';
import Navbar from '../components/Navbar';
import { getAuth, GoogleAuthProvider, signInWithPopup } from 'firebase/auth';
import { app } from './firebase'; // Ensure firebase.js is properly set up
//import axios from 'axios';
import  axiosInstance from '../pages/axiosConfig';
import { useNavigate } from 'react-router-dom';
 // Adjust this based on your backend deployment


  // const navigate = useNavigate();
function Signup() {
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  const validateForm = () => {
    const newErrors = {
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
    };

    if (!formData.name) {
      newErrors.name = 'Name is required';
    }

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return !Object.values(newErrors).some(error => error !== '');
  };

  
  const navigate = useNavigate();
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (validateForm()) {
      try {
        console.log("h")
        const response = await axiosInstance.post('/signup', {
          name: formData.name,
          email: formData.email,
          password: formData.password,
        });
        console.log("i")
        const token = response.data.token;
        localStorage.setItem('token', token);
        navigate('/login');
        console.log('Signup success:', response.data);
      } catch (error) {
        console.error('Signup error:', error.response?.data || error.message);
      }
    }
  };


  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name as keyof typeof errors]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const auth = getAuth(app);
  const provider = new GoogleAuthProvider();

  const handleGoogleSignup = async () => {
    console.log('Google SignUp Clicked!'); // Debugging log
    try {
      const result = await signInWithPopup(auth, provider);
      const user = result.user;
  
      console.log('Google Signup Success:', user);
  
      // Send user data to backend
      const response = await axiosInstance.post('/google-signup', {
        name: user.displayName,
        email: user.email,
        uid: user.uid, // or token: await user.getIdToken() if your backend verifies Firebase tokens
      });
  
      const token = response.data.token;
      localStorage.setItem('token', token);
      console.log('Google Signup Backend Success:', response.data);
  
      // navigate('/dashboard'); // if needed
    } catch (error) {
      if (error instanceof Error) {
        console.error('Google Signup Error:', error.message);
      } else {
        console.error('Google Signup Error:', error);
      }
    }
  };  

  
  return (
    <div>
        <Navbar/>
    
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
    
      <div className="max-w-md w-full backdrop-blur-xl bg-black/40 p-8 rounded-2xl shadow-[0_8px_32px_0_rgba(0,0,0,0.5)] border border-zinc-800/50">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold bg-gradient-to-r from-white via-zinc-400 to-zinc-500 text-transparent bg-clip-text">Create your account</h2>
          <p className="mt-2 text-sm text-zinc-400">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-white hover:text-zinc-300 transition-colors">
              Sign in
            </Link>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-zinc-300">
                Full name
              </label>
              <div className="mt-1">
                <input
                  id="name"
                  name="name"
                  type="text"
                  autoComplete="name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  className={`appearance-none block w-full px-3 py-2 border ${
                    errors.name ? 'border-red-500' : 'border-zinc-800'
                  } bg-black/50 backdrop-blur-sm rounded-lg shadow-sm placeholder-zinc-500 text-white focus:outline-none focus:ring-2 focus:ring-white/25 focus:border-black transition-colors`}
                  placeholder="Enter your full name"
                />
                {errors.name && <p className="mt-1 text-sm text-red-500">{errors.name}</p>}
              </div>
            </div>

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
                  value={formData.email}
                  onChange={handleChange}
                  className={`appearance-none block w-full px-3 py-2 border ${
                    errors.email ? 'border-red-500' : 'border-zinc-800'
                  } bg-black/50 backdrop-blur-sm rounded-lg shadow-sm placeholder-zinc-500 text-white focus:outline-none focus:ring-2 focus:ring-white/25 focus:border-black transition-colors`}
                  placeholder="Enter your email"
                />
                {errors.email && <p className="mt-1 text-sm text-red-500">{errors.email}</p>}
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-zinc-300">
                Password
              </label>
              <div className="mt-1 relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className={`appearance-none block w-full px-3 py-2 border ${
                    errors.password ? 'border-red-500' : 'border-zinc-800'
                  } bg-black/50 backdrop-blur-sm rounded-lg shadow-sm placeholder-zinc-500 text-white focus:outline-none focus:ring-2 focus:ring-white/25 focus:border-black transition-colors`}
                  placeholder="Create a password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-zinc-500 hover:text-zinc-300 transition-colors" />
                  ) : (
                    <Eye className="h-5 w-5 text-zinc-500 hover:text-zinc-300 transition-colors" />
                  )}
                </button>
                {errors.password && <p className="mt-1 text-sm text-red-500">{errors.password}</p>}
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-zinc-300">
                Confirm password
              </label>
              <div className="mt-1">
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className={`appearance-none block w-full px-3 py-2 border ${
                    errors.confirmPassword ? 'border-red-500' : 'border-zinc-800'
                  } bg-black/50 backdrop-blur-sm rounded-lg shadow-sm placeholder-zinc-500 text-white focus:outline-none focus:ring-2 focus:ring-white/25 focus:border-black transition-colors`}
                  placeholder="Confirm your password"
                />
                {errors.confirmPassword && (
                  <p className="mt-1 text-sm text-red-500">{errors.confirmPassword}</p>
                )}
              </div>
            </div>
          </div>

          <div>
            <button
              type="submit"
              className="mb-2 w-full flex items-center justify-center px-8 py-3 border border-black text-base font-medium rounded-md text-white bg-gradient-to-r from-indigo-600 via-purple-500 to-pink-500 hover:from-indigo-700 hover:via-purple-600 hover:to-pink-600 transition-all duration-200 md:py-4 md:text-lg md:px-10"
            >
           
              Sign up
            </button>

            <button type="button" onClick={handleGoogleSignup} className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-red-500 hover:bg-red-600 transition-all duration-200 md:py-4 md:text-lg md:px-10">
              Sign up with Google
            </button>

          </div>
        </form>
      </div>
    </div>
    </div>
  );
}

export default Signup;
