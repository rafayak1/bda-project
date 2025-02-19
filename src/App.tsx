import React from 'react';
import { Database, Bot, FileUp, Tractor as Transform, ChevronRight, Github, MessageSquare, BarChart, Shield } from 'lucide-react';
import { motion } from 'framer-motion';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Sphere } from '@react-three/drei';

function App() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: "spring",
        stiffness: 100
      }
    }
  };

  const featureCardVariants = {
    hidden: { scale: 0.8, opacity: 0 },
    visible: {
      scale: 1,
      opacity: 1,
      transition: {
        type: "spring",
        stiffness: 100
      }
    },
    hover: {
      scale: 1.05,
      transition: {
        type: "spring",
        stiffness: 400,
        damping: 10
      }
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
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
                Log in
              </motion.button>
            </div>
          </div>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <div className="relative bg-black overflow-hidden pt-16">
        <div className="max-w-7xl mx-auto">
          <div className="relative z-10 pb-8 bg-black sm:pb-16 md:pb-20 lg:pb-28 xl:pb-32">
            <main className="mt-10 mx-auto max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 lg:px-8 xl:mt-28">
              <div className="lg:grid lg:grid-cols-12 lg:gap-8">
                <motion.div 
                  initial="hidden"
                  animate="visible"
                  variants={containerVariants}
                  className="sm:text-center lg:text-left lg:col-span-6"
                >
                  <motion.h1 
                    variants={itemVariants}
                    className="text-4xl tracking-tight font-extrabold sm:text-5xl md:text-6xl text-white"
                  >
                    <span className="block mb-2">Transform Your Data with</span>
                    <span className="block gradient-text">AI-Powered Intelligence</span>
                  </motion.h1>
                  <motion.p 
                    variants={itemVariants}
                    className="mt-3 text-base text-gray-400 sm:mt-5 sm:text-lg sm:max-w-xl sm:mx-auto md:mt-5 md:text-xl lg:mx-0"
                  >
                    Upload datasets, perform powerful transformations, and get insights through an intuitive chatbot interface. Streamline your data processing workflow with our advanced platform.
                  </motion.p>
                  <motion.div 
                    variants={itemVariants}
                    className="mt-5 sm:mt-8 sm:flex sm:justify-center lg:justify-start"
                  >
                    <motion.div 
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="rounded-md shadow"
                    >
                      <button className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-gradient-to-r from-indigo-600 via-purple-500 to-pink-500 hover:from-indigo-700 hover:via-purple-600 hover:to-pink-600 transition-all duration-200 md:py-4 md:text-lg md:px-10">
                        Try it Now
                        <ChevronRight className="ml-2 h-5 w-5" />
                      </button>
                    </motion.div>
                    <motion.div 
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="mt-3 sm:mt-0 sm:ml-3"
                    >
                      <button className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 transition-colors duration-200 md:py-4 md:text-lg md:px-10">
                        View Demo
                      </button>
                    </motion.div>
                  </motion.div>
                </motion.div>
                <motion.div 
                  initial={{ opacity: 0, x: 100 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ type: "spring", stiffness: 50, delay: 0.2 }}
                  className="mt-12 relative sm:max-w-lg sm:mx-auto lg:mt-0 lg:max-w-none lg:mx-0 lg:col-span-6 lg:flex lg:items-center"
                >
                  <div className="relative mx-auto w-full rounded-lg shadow-lg lg:max-w-md">
                    <Canvas>
                      <ambientLight intensity={0.5} />
                      <directionalLight position={[0, 0, 5]} />
                      <OrbitControls />
                      <Sphere args={[1, 32, 32]} position={[0, 0, 0]}>
                        <meshStandardMaterial attach="material" color="hotpink" />
                      </Sphere>
                    </Canvas>
                  </div>
                </motion.div>
              </div>
            </main>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div id="features" className="py-12 bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <h2 className="text-3xl font-extrabold text-white sm:text-4xl">
              Powerful Features
            </h2>
            <p className="mt-4 text-xl text-gray-400">
              Everything you need to transform and analyze your data
            </p>
          </motion.div>

          <div className="mt-10">
            <div className="grid grid-cols-1 gap-10 sm:grid-cols-2 lg:grid-cols-3">
              <motion.div 
                variants={featureCardVariants}
                initial="hidden"
                whileInView="visible"
                whileHover="hover"
                viewport={{ once: true }}
                className="flex flex-col items-center p-6 bg-black rounded-lg shadow"
              >
                <FileUp className="h-12 w-12 text-indigo-600" />
                <h3 className="mt-4 text-xl font-medium text-white">Easy Data Upload</h3>
                <p className="mt-2 text-center text-gray-400">
                  Upload your datasets in multiple formats with our intuitive interface
                </p>
              </motion.div>

              <motion.div 
                variants={featureCardVariants}
                initial="hidden"
                whileInView="visible"
                whileHover="hover"
                viewport={{ once: true }}
                className="flex flex-col items-center p-6 bg-black rounded-lg shadow"
              >
                <Transform className="h-12 w-12 text-indigo-600" />
                <h3 className="mt-4 text-xl font-medium text-white">Smart Transformations</h3>
                <p className="mt-2 text-center text-gray-400">
                  Apply powerful transformations with predefined commands
                </p>
              </motion.div>

              <motion.div 
                variants={featureCardVariants}
                initial="hidden"
                whileInView="visible"
                whileHover="hover"
                viewport={{ once: true }}
                className="flex flex-col items-center p-6 bg-black rounded-lg shadow"
              >
                <Bot className="h-12 w-12 text-indigo-600" />
                <h3 className="mt-4 text-xl font-medium text-white">AI Chatbot</h3>
                <p className="mt-2 text-center text-gray-400">
                  Interactive chatbot interface for queries and transformations
                </p>
              </motion.div>
            </div>
          </div>
        </div>
      </div>

      {/* How it Works Section */}
      <div id="how-it-works" className="py-16 bg-black">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <h2 className="text-3xl font-extrabold text-white sm:text-4xl">
              How It Works
            </h2>
          </motion.div>

          <div className="mt-12">
            <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
              {[
                { icon: FileUp, title: "Upload Data", description: "Upload your dataset in any supported format" },
                { icon: MessageSquare, title: "Chat with AI", description: "Describe your transformation needs to the chatbot" },
                { icon: Transform, title: "Transform", description: "Apply powerful transformations to your data" },
                { icon: BarChart, title: "Analyze", description: "Get insights and visualize your results" }
              ].map((item, index) => (
                <motion.div 
                  key={item.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ scale: 1.05 }}
                  viewport={{ once: true }}
                  className="text-center"
                >
                  <div className="flex items-center justify-center w-12 h-12 mx-auto bg-indigo-100 rounded-full">
                    <item.icon className="h-6 w-6 text-indigo-600" />
                  </div>
                  <h3 className="mt-4 text-lg font-medium text-white">{item.title}</h3>
                  <p className="mt-2 text-gray-400">{item.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <motion.div 
              whileHover={{ scale: 1.05 }}
              className="flex items-center"
            >
              <Database className="h-8 w-8 text-white" />
              <span className="ml-2 text-xl font-bold text-white">DataTransform AI</span>
            </motion.div>
            <div className="flex space-x-6">
              <motion.a 
                whileHover={{ scale: 1.2, rotate: 10 }}
                href="#" 
                className="text-gray-400 hover:text-white transition-colors duration-200"
              >
                <Github className="h-6 w-6" />
              </motion.a>
              <motion.a 
                whileHover={{ scale: 1.2, rotate: -10 }}
                href="#" 
                className="text-gray-400 hover:text-white transition-colors duration-200"
              >
                <Shield className="h-6 w-6" />
              </motion.a>
            </div>
          </div>
          <motion.div 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            className="mt-8 border-t border-gray-800 pt-8"
          >
            <p className="text-center text-gray-400">&copy; 2024 DataTransform AI. All rights reserved.</p>
          </motion.div>
        </div>
      </footer>
    </div>
  );
}

export default App;