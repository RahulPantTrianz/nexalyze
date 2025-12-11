import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search as SearchIcon, Filter, Building2, MapPin, Calendar, DollarSign, Users, ExternalLink } from 'lucide-react';
import { searchCompanies } from '../services/api';
import { useAppStore } from '../store';
import type { Company } from '../types';
import clsx from 'clsx';

const industries = ['All', 'AI', 'FinTech', 'Healthcare', 'EdTech', 'SaaS', 'E-commerce', 'Developer Tools', 'Security'];

export default function Search() {
    const navigate = useNavigate();
    const { searchQuery, setSearchQuery, searchResults, setSearchResults, isSearching, setIsSearching } = useAppStore();
    const [selectedIndustry, setSelectedIndustry] = useState('All');
    const [showFilters, setShowFilters] = useState(false);

    const handleSearch = useCallback(async () => {
        if (!searchQuery.trim()) return;

        setIsSearching(true);
        try {
            const response = await searchCompanies(searchQuery, 20);
            if (response.success && response.data) {
                let filtered = response.data;
                if (selectedIndustry !== 'All') {
                    filtered = filtered.filter(c =>
                        c.industry?.toLowerCase().includes(selectedIndustry.toLowerCase()) ||
                        c.tags?.some(t => t.toLowerCase().includes(selectedIndustry.toLowerCase()))
                    );
                }
                setSearchResults(filtered);
            }
        } catch (error) {
            console.error('Search failed:', error);
        } finally {
            setIsSearching(false);
        }
    }, [searchQuery, selectedIndustry, setIsSearching, setSearchResults]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') handleSearch();
    };

    return (
        <div className="px-4 py-8 max-w-7xl mx-auto">
            {/* Search Header */}
            <div className="text-center mb-8 animate-fadeIn">
                <h1 className="text-4xl font-bold text-slate-800 mb-4">
                    Discover <span className="gradient-text">Startups</span>
                </h1>
                <p className="text-slate-600 max-w-xl mx-auto">
                    Search our database of 3,500+ companies from Y Combinator, Product Hunt, and more.
                </p>
            </div>

            {/* Search Bar */}
            <div className="glass-card p-6 mb-6 animate-slideUp">
                <div className="flex flex-col md:flex-row gap-4">
                    <div className="relative flex-1">
                        <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Search companies by name, industry, or description..."
                            className="input-field pl-12"
                        />
                    </div>
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        className={clsx(
                            'flex items-center gap-2 px-4 py-3 rounded-xl border-2 transition-all',
                            showFilters ? 'bg-primary-50 border-primary-300 text-primary-600' : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                        )}
                    >
                        <Filter className="w-5 h-5" />
                        Filters
                    </button>
                    <button
                        onClick={handleSearch}
                        disabled={isSearching}
                        className="btn-primary"
                    >
                        {isSearching ? (
                            <span className="flex items-center gap-2">
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                Searching...
                            </span>
                        ) : (
                            <span className="flex items-center gap-2">
                                <SearchIcon className="w-5 h-5" />
                                Search
                            </span>
                        )}
                    </button>
                </div>

                {/* Filters */}
                {showFilters && (
                    <div className="mt-4 pt-4 border-t border-slate-200 animate-slideUp">
                        <div className="flex flex-wrap gap-2">
                            {industries.map((industry) => (
                                <button
                                    key={industry}
                                    onClick={() => setSelectedIndustry(industry)}
                                    className={clsx(
                                        'px-4 py-2 rounded-full text-sm font-medium transition-all',
                                        selectedIndustry === industry
                                            ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/25'
                                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                                    )}
                                >
                                    {industry}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Results */}
            {searchResults.length > 0 && (
                <div className="mb-4 text-slate-600">
                    Found <span className="font-semibold text-slate-800">{searchResults.length}</span> companies
                </div>
            )}

            <div className="grid gap-4">
                {searchResults.map((company, index) => (
                    <CompanyCard
                        key={company.id || index}
                        company={company}
                        onClick={() => navigate(`/company/${company.id}`)}
                        delay={index * 50}
                    />
                ))}
            </div>

            {/* Empty state */}
            {!isSearching && searchResults.length === 0 && searchQuery && (
                <div className="text-center py-12 text-slate-500">
                    <Building2 className="w-16 h-16 mx-auto mb-4 text-slate-300" />
                    <p className="text-lg">No companies found for "{searchQuery}"</p>
                    <p className="text-sm mt-2">Try adjusting your search terms or filters</p>
                </div>
            )}
        </div>
    );
}

function CompanyCard({ company, onClick, delay }: { company: Company; onClick: () => void; delay?: number }) {
    return (
        <div
            onClick={onClick}
            className="glass-card p-6 cursor-pointer card-hover animate-slideUp"
            style={{ animationDelay: `${delay}ms` }}
        >
            <div className="flex flex-col md:flex-row md:items-start gap-4">
                {/* Company Icon */}
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-400 to-secondary-500 flex items-center justify-center text-white text-xl font-bold shrink-0">
                    {company.name?.charAt(0) || 'C'}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                        <div>
                            <h3 className="text-xl font-bold text-slate-800 group-hover:text-primary-600">
                                {company.name}
                            </h3>
                            {company.yc_batch && (
                                <span className="inline-block mt-1 px-2 py-0.5 bg-orange-100 text-orange-700 text-xs font-medium rounded">
                                    YC {company.yc_batch}
                                </span>
                            )}
                        </div>
                        {company.website && (
                            <a
                                href={company.website}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(e) => e.stopPropagation()}
                                className="text-slate-400 hover:text-primary-500 transition-colors"
                            >
                                <ExternalLink className="w-5 h-5" />
                            </a>
                        )}
                    </div>

                    <p className="text-slate-600 mt-2 line-clamp-2">
                        {company.description || company.long_description || 'No description available'}
                    </p>

                    <div className="flex flex-wrap gap-4 mt-4 text-sm text-slate-500">
                        {company.industry && (
                            <div className="flex items-center gap-1">
                                <Building2 className="w-4 h-4" />
                                {company.industry}
                            </div>
                        )}
                        {company.location && (
                            <div className="flex items-center gap-1">
                                <MapPin className="w-4 h-4" />
                                {company.location}
                            </div>
                        )}
                        {company.founded_year && company.founded_year > 0 && (
                            <div className="flex items-center gap-1">
                                <Calendar className="w-4 h-4" />
                                Founded {company.founded_year}
                            </div>
                        )}
                        {company.funding && (
                            <div className="flex items-center gap-1">
                                <DollarSign className="w-4 h-4" />
                                {company.funding}
                            </div>
                        )}
                        {company.employees && (
                            <div className="flex items-center gap-1">
                                <Users className="w-4 h-4" />
                                {company.employees} employees
                            </div>
                        )}
                    </div>

                    {/* Tags */}
                    {company.tags && company.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-3">
                            {company.tags.slice(0, 5).map((tag, i) => (
                                <span key={i} className="px-2 py-1 bg-slate-100 text-slate-600 text-xs rounded-lg">
                                    {tag}
                                </span>
                            ))}
                            {company.tags.length > 5 && (
                                <span className="px-2 py-1 text-slate-400 text-xs">
                                    +{company.tags.length - 5} more
                                </span>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
