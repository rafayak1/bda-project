import { Database } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
function Navbar() {


  return (
    <div className="">
      {/* Navigation */}
      <motion.nav 
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ type: "spring", stiffness: 100 }}
        className="bg-black border-b border-gray-800 fixed w-full top-0 z-50"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <motion.div 
              whileHover={{ scale: 1.05 }}
              className="flex items-center"
            >
              <Database className="h-8 w-8 text-white" />
              <span className="ml-2 text-xl font-bold text-white">DataTransform AI</span>
            </motion.div>
            <div className="flex items-center space-x-8">
              <motion.a 
                whileHover={{ scale: 1.1 }}
                href="#features" 
                className="text-gray-400 hover:text-white transition-colors duration-200"
              >
                Features
              </motion.a>
              <motion.a 
                whileHover={{ scale: 1.1 }}
                href="#how-it-works" 
                className="text-gray-400 hover:text-white transition-colors duration-200"
              >
                How it Works
              </motion.a>
              <motion.button 
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition-colors duration-200"
              >
                Get Started
              </motion.button>
              <motion.button 
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="border border-indigo-600 text-indigo-600 px-4 py-2 rounded-md hover:bg-indigo-50 transition-colors duration-200"
              >
           
                <Link to="/login" className="font-medium text-white hover:text-zinc-300 transition-colors">
                Log in
            </Link>
              </motion.button>
            </div>
          </div>
        </div>
      </motion.nav>

     
    </div>
  );
}

export default Navbar;