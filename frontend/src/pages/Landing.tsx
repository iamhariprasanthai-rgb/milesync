import { Link } from 'react-router-dom';

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-orange-100">
      {/* Header */}
      <header className="py-6 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <h1 className="text-4xl font-bold">
            <span className="bg-gradient-to-r from-orange-500 to-red-600 bg-clip-text text-transparent">Mile</span>
            <span className="bg-gradient-to-r from-yellow-600 to-yellow-800 bg-clip-text text-transparent">Sync</span>
          </h1>
          <div className="space-x-4">
            <Link
              to="/login"
              className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-primary-600"
            >
              Login
            </Link>
            <Link
              to="/register"
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            Your AI Goal Coach
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            MileSync bridges the gap between setting goals and achieving them.
            Tell us your goal, and our AI builds your personalized roadmap with
            daily tasks and progress insights.
          </p>
          <Link
            to="/register"
            className="inline-block px-8 py-4 text-lg font-medium text-white bg-primary-600 rounded-xl hover:bg-primary-700 shadow-lg hover:shadow-xl transition-all"
          >
            Start Your Journey
          </Link>
        </div>

        {/* Features */}
        <div className="mt-24 grid md:grid-cols-3 gap-8">
          <FeatureCard
            title="Chat with AI Coach"
            description="Have a conversation about your goals. Our AI helps you define SMART goals and understand your motivations."
            icon="💬"
          />
          <FeatureCard
            title="Personalized Roadmap"
            description="Get a customized plan with milestones and daily tasks tailored to your timeline and capabilities."
            icon="🗺️"
          />
          <FeatureCard
            title="Track Progress"
            description="Visual dashboards show your progress, streaks, and keep you motivated on your journey."
            icon="📊"
          />
        </div>
      </main>
    </div>
  );
}

function FeatureCard({
  title,
  description,
  icon,
}: {
  title: string;
  description: string;
  icon: string;
}) {
  return (
    <div className="bg-white p-8 rounded-2xl shadow-lg">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}
