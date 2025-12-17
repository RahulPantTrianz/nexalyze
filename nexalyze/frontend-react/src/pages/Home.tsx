import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
    Search, MessageCircle, FileText, TrendingUp,
    Zap, Database, BarChart3, ArrowRight, Sparkles
} from 'lucide-react';
import { getStats, getHealthStatus } from '../services/api';
import type { SystemStats, HealthStatus } from '../types';

const features = [
    {
        icon: Search,
        title: 'Company Search',
        description: 'Search 3,500+ startups from Y Combinator, Product Hunt, and more.',
        link: '/search',
        color: 'from-blue-500 to-cyan-500'
    },
    {
        icon: MessageCircle,
        title: 'AI Chat',
        description: 'Ask questions about companies, markets, and competitive landscapes.',
        link: '/chat',
        color: 'from-purple-500 to-pink-500'
    },
    {
        icon: FileText,
        title: 'Report Generation',
        description: 'Generate comprehensive PDF reports with AI-powered analysis.',
        link: '/reports',
        color: 'from-orange-500 to-red-500'
    },
    {
        icon: TrendingUp,
        title: 'Competitive Intelligence',
        description: 'Discover competitors, market trends, and strategic insights.',
        link: '/search',
        color: 'from-green-500 to-emerald-500'
    }
];

export default function Home() {
    const [stats, setStats] = useState<SystemStats | null>(null);
    const [health, setHealth] = useState<HealthStatus | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, healthRes] = await Promise.all([
                    getStats(),
                    getHealthStatus()
                ]);
                if (statsRes.success && statsRes.data) setStats(statsRes.data);
                setHealth(healthRes);
            } catch (error) {
                console.error('Failed to fetch data:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    return (
        <div className="px-4 py-8 max-w-7xl mx-auto">
            {/* Hero Section */}
            <section className="text-center py-16 animate-fadeIn">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100 text-primary-700 rounded-full text-sm font-medium mb-6">
                    <Sparkles className="w-4 h-4" />
                    Powered by Claude Sonnet
                </div>

                <h1 className="text-5xl md:text-6xl font-bold mb-6">
                    <span className="gradient-text">AI-Powered</span>
                    <br />
                    <span className="text-slate-800">Startup Intelligence</span>
                </h1>

                <p className="text-xl text-slate-600 max-w-2xl mx-auto mb-10">
                    Transform your startup research with AI. Search companies, analyze markets,
                    and generate professional reports in seconds.
                </p>

                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Link to="/search" className="btn-primary flex items-center justify-center gap-2">
                        <Search className="w-5 h-5" />
                        Start Searching
                    </Link>
                    <Link to="/chat" className="btn-secondary flex items-center justify-center gap-2">
                        <MessageCircle className="w-5 h-5" />
                        Chat with AI
                    </Link>
                </div>
            </section>

            {/* Stats Section */}
            <section className="py-12">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                        { label: 'Companies', value: stats?.total_companies || 0, icon: Database },
                        { label: 'Data Sources', value: stats?.data_sources || 6, icon: Zap },
                        { label: 'AI Queries', value: stats?.total_queries || 0, icon: MessageCircle },
                        { label: 'Reports', value: stats?.total_reports || 0, icon: BarChart3 }
                    ].map((stat, index) => {
                        const Icon = stat.icon;
                        return (
                            <div
                                key={stat.label}
                                className="glass-card p-6 text-center card-hover animate-slideUp"
                                style={{ animationDelay: `${index * 100}ms` }}
                            >
                                <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-primary-100 to-primary-200 rounded-xl mb-4">
                                    <Icon className="w-6 h-6 text-primary-600" />
                                </div>
                                <div className="text-3xl font-bold text-slate-800">
                                    {loading ? '...' : stat.value.toLocaleString()}
                                </div>
                                <div className="text-sm text-slate-500">{stat.label}</div>
                            </div>
                        );
                    })}
                </div>
            </section>

            {/* Features Section */}
            <section className="py-12">
                <h2 className="text-3xl font-bold text-center mb-12 text-slate-800">
                    Powerful Features
                </h2>

                <div className="grid md:grid-cols-2 gap-6">
                    {features.map((feature, index) => {
                        const Icon = feature.icon;
                        return (
                            <Link
                                key={feature.title}
                                to={feature.link}
                                className="glass-card p-6 card-hover group animate-slideUp"
                                style={{ animationDelay: `${index * 100}ms` }}
                            >
                                <div className={`inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.color} mb-4 shadow-lg group-hover:scale-110 transition-transform`}>
                                    <Icon className="w-7 h-7 text-white" />
                                </div>
                                <h3 className="text-xl font-bold text-slate-800 mb-2 group-hover:text-primary-600 transition-colors">
                                    {feature.title}
                                </h3>
                                <p className="text-slate-600 mb-4">{feature.description}</p>
                                <div className="flex items-center text-primary-600 font-medium">
                                    Learn more
                                    <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-2 transition-transform" />
                                </div>
                            </Link>
                        );
                    })}
                </div>
            </section>

            {/* System Status */}
            {health && (
                <section className="py-8">
                    <div className="glass-card p-6">
                        <h3 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
                            <div className={`w-3 h-3 rounded-full ${health.status === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'} animate-pulse`} />
                            System Status
                        </h3>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                            <div className="flex items-center gap-2">
                                <span className={`w-2 h-2 rounded-full ${health.services.postgres.connected ? 'bg-green-500' : 'bg-red-500'}`} />
                                <span className="text-slate-600">PostgreSQL</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className={`w-2 h-2 rounded-full ${health.services.redis.connected ? 'bg-green-500' : 'bg-red-500'}`} />
                                <span className="text-slate-600">Redis</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className={`w-2 h-2 rounded-full ${health.services.ai.status === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'}`} />
                                <span className="text-slate-600">{health.services.ai.model}</span>
                            </div>
                        </div>
                    </div>
                </section>
            )}
        </div>
    );
}
