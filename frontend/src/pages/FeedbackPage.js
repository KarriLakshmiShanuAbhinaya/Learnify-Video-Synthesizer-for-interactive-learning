import React, { useState } from "react";
import { MessageSquare, Star, Send, ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";
import { toast } from "react-hot-toast";
import CONFIG, { fetchAuth } from "../utils/config";
import { useNavigate } from "react-router-dom";

function FeedbackPage() {
    const [content, setContent] = useState("");
    const [rating, setRating] = useState(5);
    const [submitting, setSubmitting] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (content.length < 5) {
            toast.error("Feedback must be at least 5 characters long");
            return;
        }

        setSubmitting(true);
        try {
            const res = await fetchAuth(`${CONFIG.API_BASE_URL}/feedback`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ content, rating }),
            });

            if (res.ok) {
                toast.success("Thank you for your feedback!");
                setContent("");
                setRating(5);
                setTimeout(() => navigate(-1), 2000);
            } else {
                toast.error("Failed to submit feedback");
            }
        } catch (err) {
            toast.error("An error occurred");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="container" 
            style={{ maxWidth: '600px', padding: '2rem 0' }}
        >
            <div className="glass-card" style={{ padding: '3rem' }}>
                <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
                    <div style={{ 
                        width: '64px', 
                        height: '64px', 
                        background: 'rgba(139, 92, 246, 0.1)', 
                        borderRadius: '1.25rem', 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center',
                        margin: '0 auto 1.5rem',
                        border: '1px solid rgba(139, 92, 246, 0.2)'
                    }}>
                        <MessageSquare size={32} className="text-gradient" />
                    </div>
                    <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem', fontWeight: 800 }}>Your <span className="text-gradient">Feedback</span></h1>
                    <p style={{ color: 'var(--fg-muted)', fontSize: '1.1rem' }}>
                        Help us make Learnify even more interactive and useful for you.
                    </p>
                </div>

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <label style={{ fontWeight: 600, color: 'var(--fg-main)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem' }}>
                            <Star size={18} className="text-gradient" /> How would you rate your experience?
                        </label>
                        <div style={{ 
                            display: 'flex', 
                            gap: '1rem', 
                            justifyContent: 'center', 
                            padding: '1.5rem', 
                            background: 'rgba(255,255,255,0.02)', 
                            borderRadius: '1.25rem', 
                            border: '1px solid var(--glass-border)' 
                        }}>
                            {[1, 2, 3, 4, 5].map((star) => (
                                <motion.button
                                    key={star}
                                    type="button"
                                    whileHover={{ scale: 1.2, rotate: 5 }}
                                    whileTap={{ scale: 0.9 }}
                                    onClick={() => setRating(star)}
                                    style={{ 
                                        background: 'transparent', 
                                        border: 'none', 
                                        cursor: 'pointer',
                                        color: star <= rating ? '#f59e0b' : 'var(--glass-border)',
                                        transition: 'color 0.2s',
                                        padding: 0
                                    }}
                                >
                                    <Star size={36} fill={star <= rating ? "#f59e0b" : "none"} />
                                </motion.button>
                            ))}
                        </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <label style={{ fontWeight: 600, color: 'var(--fg-main)', fontSize: '1.1rem' }}>Your Suggestions & Comments</label>
                        <textarea
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            placeholder="Tell us what you like or what we can improve..."
                            style={{
                                width: '100%',
                                minHeight: '180px',
                                padding: '1.5rem',
                                borderRadius: '1.25rem',
                                background: 'rgba(255,255,255,0.04)',
                                border: '1px solid var(--glass-border)',
                                color: 'var(--fg-main)',
                                fontSize: '1.05rem',
                                resize: 'none',
                                outline: 'none',
                                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                lineHeight: '1.6'
                            }}
                            onFocus={(e) => {
                                e.target.style.borderColor = '#8b5cf6';
                                e.target.style.background = 'rgba(255,255,255,0.06)';
                                e.target.style.boxShadow = '0 0 20px rgba(139, 92, 246, 0.1)';
                            }}
                            onBlur={(e) => {
                                e.target.style.borderColor = 'var(--glass-border)';
                                e.target.style.background = 'rgba(255,255,255,0.04)';
                                e.target.style.boxShadow = 'none';
                            }}
                        />
                    </div>

                    <motion.button 
                        type="submit" 
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="btn-primary" 
                        disabled={submitting}
                        style={{ 
                            width: '100%', 
                            height: '64px', 
                            fontSize: '1.15rem',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '0.75rem',
                            borderRadius: '1.25rem',
                            fontWeight: 700,
                            marginTop: '1rem'
                        }}
                    >
                        {submitting ? (
                            <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                            >
                                <Star size={24} />
                            </motion.div>
                        ) : (
                            <>
                                <Send size={20} /> Post Feedback
                            </>
                        )}
                    </motion.button>
                </form>

                <div style={{ 
                    marginTop: '2.5rem', 
                    textAlign: 'center', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    gap: '0.6rem', 
                    color: 'var(--fg-muted)', 
                    fontSize: '0.95rem',
                    opacity: 0.7
                }}>
                    <ShieldCheck size={18} /> Verified feedback collection for Learnify.
                </div>
            </div>
        </motion.div>
    );
}

export default FeedbackPage;
