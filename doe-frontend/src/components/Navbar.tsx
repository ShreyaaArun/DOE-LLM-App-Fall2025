import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import doeLogo from '/images/doe-logo-final.png';

const Navbar = () => {
  const location = useLocation();

  return (
    <motion.nav 
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="bg-gradient-to-r from-gray-900 via-black to-gray-900 border-b border-violet-900/30 shadow-lg sticky top-0 z-50 backdrop-blur-sm bg-opacity-80"
    >
      <div className="container mx-auto flex justify-between items-center py-3">
          <Link to="/" className="flex items-center space-x-3">
            <img src={doeLogo} alt="DOE Logo" className="h-12 w-12 md:h-14 md:w-14" />
            <span className="text-2xl font-bold">
              DOE
            </span>
          </Link>
          <nav className="hidden md:flex space-x-1 items-center">
            <NavLink to="/" currentPath={location.pathname}>Home</NavLink>
            <NavLink to="/about" currentPath={location.pathname}>About</NavLink>
            <NavLink to="/research" currentPath={location.pathname}>Research</NavLink>
            <NavLink to="/chat" currentPath={location.pathname}>Chat</NavLink>
            <NavLink to="/contact" currentPath={location.pathname}>Contact</NavLink>
          </nav>
          <div className="md:hidden">
            {/* Mobile menu button will go here */}
          </div>
        </div>
    </motion.nav>
  );
};

const NavLink = ({ to, children, currentPath }: { to: string; children: React.ReactNode; currentPath: string }) => (
  <Link to={to}>
    <motion.div
      whileHover={{ scale: 1.05 }}
      className={`px-4 py-2 rounded-lg transition-all duration-300 ${
        currentPath === to
          ? 'bg-gradient-to-r from-violet-900 to-indigo-800 text-white shadow-lg shadow-violet-900/50'
          : 'text-gray-300 hover:bg-violet-900/30 hover:text-white'
      }`}
    >
      {children}
    </motion.div>
  </Link>
);

export default Navbar;