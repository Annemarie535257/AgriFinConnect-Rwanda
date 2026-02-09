import { useState } from 'react';
import Header from '../components/Header';
import Hero from '../components/Hero';
import GetStartedModal from '../components/GetStartedModal';
import AboutSection from '../components/AboutSection';
import OurServicesSection from '../components/OurServicesSection';
import ContactSection from '../components/ContactSection';
import Footer from '../components/Footer';
import BackToTop from '../components/BackToTop';
import '../App.css';

const ROLE_TO_PATH = {
  farmers: '/dashboard/farmer',
  microfinances: '/dashboard/microfinance',
  admin: '/dashboard/admin',
};

export default function LandingPage({ onLoginToDashboard }) {
  const [getStartedOpen, setGetStartedOpen] = useState(false);

  return (
    <div className="app">
      <Header onOpenGetStarted={() => setGetStartedOpen(true)} />
      <Hero onOpenGetStarted={() => setGetStartedOpen(true)} />
      <GetStartedModal
        isOpen={getStartedOpen}
        onClose={() => setGetStartedOpen(false)}
        onLogin={(role) => {
          setGetStartedOpen(false);
          onLoginToDashboard?.(ROLE_TO_PATH[role]);
        }}
      />
      <AboutSection />
      <OurServicesSection />
      <ContactSection />
      <Footer />
      <BackToTop />
    </div>
  );
}
