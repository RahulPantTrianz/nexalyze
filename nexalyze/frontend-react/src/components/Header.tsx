import { Link, useLocation } from 'react-router-dom';
import { Search, MessageCircle, FileText, Home, Sparkles } from 'lucide-react';
import clsx from 'clsx';

const navItems = [
    { path: '/', label: 'Home', icon: Home },
    { path: '/search', label: 'Search', icon: Search },
    { path: '/chat', label: 'AI Chat', icon: MessageCircle },
    { path: '/reports', label: 'Reports', icon: FileText },
];

export default function Header() {
    const location = useLocation();

    return (
        <header className="fixed top-0 left-0 right-0 z-50 glass-card px-6 py-3 mx-4 mt-4 rounded-2xl">
            <div className="max-w-7xl mx-auto flex items-center justify-between">
                {/* Logo */}
                <Link to="/" className="flex items-center gap-3 group">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-600 flex items-center justify-center shadow-lg shadow-primary-500/25 group-hover:shadow-xl group-hover:shadow-primary-500/30 transition-all duration-300">
                        <Sparkles className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold gradient-text">Nexalyze</h1>
                        <p className="text-xs text-slate-500">AI Startup Intelligence</p>
                    </div>
                </Link>

                {/* Navigation */}
                <nav className="hidden md:flex items-center gap-1">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={clsx(
                                    'flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all duration-200',
                                    isActive
                                        ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/25'
                                        : 'text-slate-600 hover:bg-slate-100 hover:text-primary-600'
                                )}
                            >
                                <Icon className="w-4 h-4" />
                                <span>{item.label}</span>
                            </Link>
                        );
                    })}
                </nav>

                {/* Mobile menu button */}
                <button className="md:hidden p-2 rounded-xl hover:bg-slate-100 transition-colors">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                </button>
            </div>
        </header>
    );
}
