import { useState, useRef, useEffect } from 'react';
import { FileText, Download, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { generateReportBackground, getReportTaskStatus, downloadReport } from '../services/api';
import clsx from 'clsx';

const reportTypes = [
    {
        id: 'comprehensive',
        name: 'Comprehensive Analysis',
        description: 'Full market overview with industry trends, competitive landscape, and strategic insights'
    },
    {
        id: 'competitive_analysis',
        name: 'Competitive Analysis',
        description: 'Deep dive into competitors, market positioning, and differentiation strategies'
    },
    {
        id: 'market_research',
        name: 'Market Research',
        description: 'Industry size, growth projections, trends, and opportunities'
    },
];

const formats = [
    { id: 'pdf', name: 'PDF', icon: '📄' },
    { id: 'docx', name: 'Word', icon: '📝' },
];

interface GeneratedReport {
    filename: string;
    topic: string;
    type: string;
    generatedAt: Date;
}

export default function Reports() {
    const [topic, setTopic] = useState('');
    const [reportType, setReportType] = useState('comprehensive');
    const [format, setFormat] = useState('pdf');
    const [isGenerating, setIsGenerating] = useState(false);
    const [pollingStatus, setPollingStatus] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const [generatedReports, setGeneratedReports] = useState<GeneratedReport[]>([]);
    const pollingIntervalRef = useRef<number | null>(null);

    // Cleanup interval on unmount
    useEffect(() => {
        return () => {
            if (pollingIntervalRef.current) {
                window.clearInterval(pollingIntervalRef.current);
            }
        };
    }, []);

    const handleGenerate = async () => {
        if (!topic.trim()) {
            setError('Please enter a topic');
            return;
        }

        setIsGenerating(true);
        setError(null);
        setPollingStatus('Initializing report generation...');

        try {
            const response = await generateReportBackground({
                topic: topic.trim(),
                report_type: reportType,
                format,
                use_langgraph: true
            });

            if (response.success && response.data && response.data.task_id) {
                pollStatus(response.data.task_id);
            } else {
                setError('Failed to start report generation. Please try again.');
                setIsGenerating(false);
            }
        } catch (err: any) {
            console.error('Report generation failed:', err);
            setError(err.response?.data?.detail || 'Failed to generate report');
            setIsGenerating(false);
        }
    };

    const pollStatus = (taskId: string) => {
        // Clear any existing interval
        if (pollingIntervalRef.current) {
            window.clearInterval(pollingIntervalRef.current);
        }

        pollingIntervalRef.current = window.setInterval(async () => {
            try {
                const response = await getReportTaskStatus(taskId);
                const task = response.data;

                if (!task) return;

                if (task.status === 'completed') {
                    if (pollingIntervalRef.current) window.clearInterval(pollingIntervalRef.current);
                    setIsGenerating(false);
                    setPollingStatus('');

                    if (task.result?.report_filename) {
                        setGeneratedReports(prev => [{
                            filename: task.result!.report_filename,
                            topic: task.result!.topic || topic,
                            type: task.result!.report_type || reportType,
                            generatedAt: new Date()
                        }, ...prev]);
                        setTopic('');
                    }
                } else if (task.status === 'failed') {
                    if (pollingIntervalRef.current) window.clearInterval(pollingIntervalRef.current);
                    setIsGenerating(false);
                    setPollingStatus('');
                    setError(task.error || 'Report generation failed');
                } else {
                    // Still processing
                    setPollingStatus(task.message || 'Processing...');
                }
            } catch (e) {
                console.error("Polling error", e);
                // Don't stop polling on transient errors
            }
        }, 10000); // Poll every 10 seconds
    };

    return (
        <div className="px-4 py-8 max-w-4xl mx-auto">
            {/* Header */}
            <div className="text-center mb-8 animate-fadeIn">
                <h1 className="text-4xl font-bold text-slate-800 mb-4">
                    Generate <span className="gradient-text">Reports</span>
                </h1>
                <p className="text-slate-600 max-w-xl mx-auto">
                    Create professional AI-powered reports on any topic. Our AI analyzes multiple sources
                    to generate comprehensive insights.
                </p>
            </div>

            {/* Report Generator */}
            <div className="glass-card p-6 mb-8 animate-slideUp">
                <h2 className="text-lg font-semibold text-slate-800 mb-4">New Report</h2>

                {/* Topic Input */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                        Topic
                    </label>
                    <input
                        type="text"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        placeholder="e.g., AI startups in healthcare, Fintech market analysis..."
                        className="input-field"
                        disabled={isGenerating}
                    />
                </div>

                {/* Report Type */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                        Report Type
                    </label>
                    <div className="grid sm:grid-cols-3 gap-3">
                        {reportTypes.map((type) => (
                            <button
                                key={type.id}
                                onClick={() => setReportType(type.id)}
                                disabled={isGenerating}
                                className={clsx(
                                    'p-4 rounded-xl border-2 text-left transition-all',
                                    reportType === type.id
                                        ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-200'
                                        : 'border-slate-200 hover:border-slate-300 bg-white'
                                )}
                            >
                                <div className="font-semibold text-slate-800 text-sm mb-1">
                                    {type.name}
                                </div>
                                <div className="text-xs text-slate-500 line-clamp-2">
                                    {type.description}
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Format */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                        Format
                    </label>
                    <div className="flex gap-3">
                        {formats.map((f) => (
                            <button
                                key={f.id}
                                onClick={() => setFormat(f.id)}
                                disabled={isGenerating}
                                className={clsx(
                                    'flex items-center gap-2 px-4 py-2 rounded-xl border-2 transition-all',
                                    format === f.id
                                        ? 'border-primary-500 bg-primary-50 text-primary-700'
                                        : 'border-slate-200 text-slate-600 hover:border-slate-300'
                                )}
                            >
                                <span>{f.icon}</span>
                                <span className="font-medium">{f.name}</span>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Error */}
                {error && (
                    <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3 text-red-700">
                        <AlertCircle className="w-5 h-5 shrink-0" />
                        <span>{error}</span>
                    </div>
                )}

                {/* Generate Button */}
                <button
                    onClick={handleGenerate}
                    disabled={isGenerating || !topic.trim()}
                    className="btn-primary w-full flex items-center justify-center gap-2"
                >
                    {isGenerating ? (
                        <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            {pollingStatus || 'Generating Report...'}
                        </>
                    ) : (
                        <>
                            <FileText className="w-5 h-5" />
                            Generate Report
                        </>
                    )}
                </button>

                {isGenerating && (
                    <p className="text-sm text-slate-500 text-center mt-4">
                        This may take a few minutes. You can wait here or check back later.
                    </p>
                )}
            </div>

            {/* Generated Reports */}
            {generatedReports.length > 0 && (
                <div className="animate-slideUp">
                    <h2 className="text-lg font-semibold text-slate-800 mb-4">
                        Generated Reports
                    </h2>
                    <div className="space-y-3">
                        {generatedReports.map((report, index) => (
                            <div
                                key={report.filename}
                                className="glass-card p-4 flex items-center justify-between"
                                style={{ animationDelay: `${index * 100}ms` }}
                            >
                                <div className="flex items-center gap-4">
                                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center">
                                        <CheckCircle className="w-5 h-5 text-white" />
                                    </div>
                                    <div>
                                        <div className="font-semibold text-slate-800">{report.topic}</div>
                                        <div className="text-sm text-slate-500">
                                            {report.type.replace('_', ' ')} • {report.generatedAt.toLocaleTimeString()}
                                        </div>
                                    </div>
                                </div>
                                <a
                                    href={downloadReport(report.filename)}
                                    className="flex items-center gap-2 px-4 py-2 bg-primary-50 text-primary-600 rounded-xl hover:bg-primary-100 transition-colors font-medium"
                                >
                                    <Download className="w-4 h-4" />
                                    Download
                                </a>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
