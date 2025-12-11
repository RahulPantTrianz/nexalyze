import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
    ArrowLeft, Building2, MapPin, Calendar, DollarSign, Users,
    Globe, TrendingUp, Shield, AlertTriangle, Lightbulb,
    Loader2
} from 'lucide-react';
import { getCompanyDetails, analyzeCompany } from '../services/api';
import type { Company, CompanyAnalysis } from '../types';

export default function CompanyPage() {
    const { id } = useParams<{ id: string }>();
    const [company, setCompany] = useState<Company | null>(null);
    const [analysis, setAnalysis] = useState<CompanyAnalysis | null>(null);
    const [loading, setLoading] = useState(true);
    const [analyzing, setAnalyzing] = useState(false);

    useEffect(() => {
        const fetchCompany = async () => {
            if (!id) return;

            setLoading(true);
            try {
                const response = await getCompanyDetails(parseInt(id));
                if (response.success && response.data) {
                    setCompany(response.data);
                }
            } catch (error) {
                console.error('Failed to fetch company:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchCompany();
    }, [id]);

    const handleAnalyze = async () => {
        if (!company) return;

        setAnalyzing(true);
        try {
            const response = await analyzeCompany(company.name, true);
            if (response.success && response.data) {
                setAnalysis(response.data);
            }
        } catch (error) {
            console.error('Analysis failed:', error);
        } finally {
            setAnalyzing(false);
        }
    };

    if (loading) {
        return (
            <div className="px-4 py-16 text-center">
                <Loader2 className="w-12 h-12 animate-spin text-primary-500 mx-auto" />
                <p className="mt-4 text-slate-500">Loading company details...</p>
            </div>
        );
    }

    if (!company) {
        return (
            <div className="px-4 py-16 text-center">
                <Building2 className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-slate-800 mb-2">Company Not Found</h2>
                <Link to="/search" className="text-primary-500 hover:underline">
                    ← Back to Search
                </Link>
            </div>
        );
    }

    return (
        <div className="px-4 py-8 max-w-6xl mx-auto">
            {/* Back Button */}
            <Link
                to="/search"
                className="inline-flex items-center gap-2 text-slate-600 hover:text-primary-600 mb-6 transition-colors"
            >
                <ArrowLeft className="w-4 h-4" />
                Back to Search
            </Link>

            {/* Company Header */}
            <div className="glass-card p-8 mb-6 animate-fadeIn">
                <div className="flex flex-col md:flex-row gap-6">
                    {/* Logo/Initial */}
                    <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-primary-400 to-secondary-500 flex items-center justify-center text-white text-4xl font-bold shrink-0 shadow-xl">
                        {company.name?.charAt(0) || 'C'}
                    </div>

                    <div className="flex-1">
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <h1 className="text-3xl font-bold text-slate-800 mb-2">{company.name}</h1>
                                <div className="flex flex-wrap gap-2">
                                    {company.yc_batch && (
                                        <span className="px-3 py-1 bg-orange-100 text-orange-700 font-medium rounded-lg">
                                            YC {company.yc_batch}
                                        </span>
                                    )}
                                    {company.stage && (
                                        <span className="px-3 py-1 bg-blue-100 text-blue-700 font-medium rounded-lg">
                                            {company.stage}
                                        </span>
                                    )}
                                    {company.is_active !== undefined && (
                                        <span className={`px-3 py-1 rounded-lg font-medium ${company.is_active
                                            ? 'bg-green-100 text-green-700'
                                            : 'bg-slate-100 text-slate-600'
                                            }`}>
                                            {company.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    )}
                                </div>
                            </div>

                            {company.website && (
                                <a
                                    href={company.website}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="btn-secondary flex items-center gap-2"
                                >
                                    <Globe className="w-4 h-4" />
                                    Visit Website
                                </a>
                            )}
                        </div>

                        <p className="text-slate-600 mt-4 text-lg">
                            {company.long_description || company.description || 'No description available'}
                        </p>

                        {/* Quick Stats */}
                        <div className="flex flex-wrap gap-6 mt-6 text-slate-600">
                            {company.industry && (
                                <div className="flex items-center gap-2">
                                    <Building2 className="w-5 h-5 text-primary-500" />
                                    <span>{company.industry}</span>
                                </div>
                            )}
                            {company.location && (
                                <div className="flex items-center gap-2">
                                    <MapPin className="w-5 h-5 text-primary-500" />
                                    <span>{company.location}</span>
                                </div>
                            )}
                            {company.founded_year && company.founded_year > 0 && (
                                <div className="flex items-center gap-2">
                                    <Calendar className="w-5 h-5 text-primary-500" />
                                    <span>Founded {company.founded_year}</span>
                                </div>
                            )}
                            {company.funding && (
                                <div className="flex items-center gap-2">
                                    <DollarSign className="w-5 h-5 text-primary-500" />
                                    <span>{company.funding}</span>
                                </div>
                            )}
                            {company.employees && (
                                <div className="flex items-center gap-2">
                                    <Users className="w-5 h-5 text-primary-500" />
                                    <span>{company.employees} employees</span>
                                </div>
                            )}
                        </div>

                        {/* Tags */}
                        {company.tags && company.tags.length > 0 && (
                            <div className="flex flex-wrap gap-2 mt-6">
                                {company.tags.map((tag, i) => (
                                    <span key={i} className="px-3 py-1 bg-slate-100 text-slate-600 text-sm rounded-lg">
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Analysis Section */}
            <div className="glass-card p-6 mb-6">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-slate-800">AI Analysis</h2>
                    {!analysis && (
                        <button
                            onClick={handleAnalyze}
                            disabled={analyzing}
                            className="btn-primary flex items-center gap-2"
                        >
                            {analyzing ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Analyzing...
                                </>
                            ) : (
                                <>
                                    <TrendingUp className="w-5 h-5" />
                                    Analyze Company
                                </>
                            )}
                        </button>
                    )}
                </div>

                {!analysis && !analyzing && (
                    <p className="text-slate-500 text-center py-8">
                        Click "Analyze Company" to get AI-powered insights, SWOT analysis, and competitor information.
                    </p>
                )}

                {analysis?.swot && (
                    <div className="grid md:grid-cols-2 gap-4">
                        {/* Strengths */}
                        <div className="p-4 bg-green-50 rounded-xl border border-green-200">
                            <h3 className="font-semibold text-green-800 flex items-center gap-2 mb-3">
                                <Shield className="w-5 h-5" />
                                Strengths
                            </h3>
                            <ul className="space-y-2">
                                {analysis.swot.strengths.map((item, i) => (
                                    <li key={i} className="text-green-700 text-sm">• {item}</li>
                                ))}
                            </ul>
                        </div>

                        {/* Weaknesses */}
                        <div className="p-4 bg-red-50 rounded-xl border border-red-200">
                            <h3 className="font-semibold text-red-800 flex items-center gap-2 mb-3">
                                <AlertTriangle className="w-5 h-5" />
                                Weaknesses
                            </h3>
                            <ul className="space-y-2">
                                {analysis.swot.weaknesses.map((item, i) => (
                                    <li key={i} className="text-red-700 text-sm">• {item}</li>
                                ))}
                            </ul>
                        </div>

                        {/* Opportunities */}
                        <div className="p-4 bg-blue-50 rounded-xl border border-blue-200">
                            <h3 className="font-semibold text-blue-800 flex items-center gap-2 mb-3">
                                <Lightbulb className="w-5 h-5" />
                                Opportunities
                            </h3>
                            <ul className="space-y-2">
                                {analysis.swot.opportunities.map((item, i) => (
                                    <li key={i} className="text-blue-700 text-sm">• {item}</li>
                                ))}
                            </ul>
                        </div>

                        {/* Threats */}
                        <div className="p-4 bg-amber-50 rounded-xl border border-amber-200">
                            <h3 className="font-semibold text-amber-800 flex items-center gap-2 mb-3">
                                <AlertTriangle className="w-5 h-5" />
                                Threats
                            </h3>
                            <ul className="space-y-2">
                                {analysis.swot.threats.map((item, i) => (
                                    <li key={i} className="text-amber-700 text-sm">• {item}</li>
                                ))}
                            </ul>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
