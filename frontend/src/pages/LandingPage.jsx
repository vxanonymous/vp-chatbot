import React from 'react';
import { useNavigate } from 'react-router-dom';
import { MapPin, Calendar, DollarSign, Users, ArrowRight } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const LandingPage = () => {

  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const handleGetStarted = () => {

    navigate(isAuthenticated ? '/chat' : '/auth');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-white dark:from-gray-900 dark:to-gray-800">
      {/* Navbar */}
      <nav className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <MapPin className="h-8 w-8 text-primary-600" />
              <span className="ml-2 text-xl font-bold text-gray-900 dark:text-white">
                Vacation Planner
              </span>
            </div>
            <button
              onClick={handleGetStarted}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
            >
              {isAuthenticated ? 'Go to Chat' : 'Get Started'}
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center">
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-gray-900 dark:text-white">
            Plan Your Perfect Vacation
            <span className="block text-primary-600">With AI Assistance</span>
          </h1>
          <p className="mt-6 text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
            Let our intelligent chatbot help you plan unforgettable trips. From destination
            recommendations to budget planning, we've got you covered.
          </p>
          <div className="mt-10">
            <button
              onClick={handleGetStarted}
              className="inline-flex items-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
            >
              Start Planning Now
              <ArrowRight className="ml-2 h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-white dark:bg-gray-800 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              Everything You Need to Plan Your Trip
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="mx-auto h-12 w-12 text-primary-600">
                <MapPin className="h-12 w-12" />
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
                Destination Advice
              </h3>
              <p className="mt-2 text-gray-600 dark:text-gray-300">
                Get personalized recommendations based on your preferences
              </p>
            </div>
            <div className="text-center">
              <div className="mx-auto h-12 w-12 text-primary-600">
                <Calendar className="h-12 w-12" />
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
                Itinerary Planning
              </h3>
              <p className="mt-2 text-gray-600 dark:text-gray-300">
                Create detailed day-by-day plans for your perfect trip
              </p>
            </div>
            <div className="text-center">
              <div className="mx-auto h-12 w-12 text-primary-600">
                <DollarSign className="h-12 w-12" />
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
                Budget Estimation
              </h3>
              <p className="mt-2 text-gray-600 dark:text-gray-300">
                Get accurate cost estimates for your travel plans
              </p>
            </div>
            <div className="text-center">
              <div className="mx-auto h-12 w-12 text-primary-600">
                <Users className="h-12 w-12" />
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
                Group Travel
              </h3>
              <p className="mt-2 text-gray-600 dark:text-gray-300">
                Plan trips for solo adventures or group getaways
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-primary-600 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white">
            Ready to Start Your Adventure?
          </h2>
          <p className="mt-4 text-xl text-primary-100 dark:text-primary-200">
            Join thousands of travelers who plan smarter with AI
          </p>
          <button
            onClick={handleGetStarted}
            className="mt-8 inline-flex items-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-primary-600 bg-white hover:bg-gray-50 shadow-lg"
          >
            {isAuthenticated ? 'Continue Planning' : 'Create Free Account'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;