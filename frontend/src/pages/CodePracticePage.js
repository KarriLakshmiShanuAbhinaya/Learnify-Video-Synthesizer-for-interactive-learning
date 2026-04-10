import React, { useState, useEffect } from "react";
import Editor from "@monaco-editor/react";
import Confetti from "react-confetti";
import { Play, CheckCircle, XCircle, Code, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import CONFIG, { fetchAuth } from "../utils/config";

const LANGUAGES = [
    { id: "python", name: "Python", version: "*" },
    { id: "javascript", name: "JavaScript", version: "*" },
    { id: "java", name: "Java", version: "*" },
    { id: "cpp", name: "C++", version: "*" },
    { id: "sqlite3", name: "SQL (SQLite3)", version: "*" }
];

const DEFAULT_CODE = {
    python: "print('Hello, Code Practice!')",
    javascript: "console.log('Hello, Code Practice!');",
    java: "public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, Code Practice!\");\n    }\n}",
    cpp: "#include <iostream>\n\nint main() {\n    std::cout << \"Hello, Code Practice!\" << std::endl;\n    return 0;\n}",
    sqlite3: "-- Create a table and insert data\nCREATE TABLE test (id INT, message TEXT);\nINSERT INTO test VALUES (1, 'Hello, Code Practice!');\nSELECT * FROM test;"
};

function CodePracticePage() {
    const [language, setLanguage] = useState(LANGUAGES[0]);
    const [code, setCode] = useState(DEFAULT_CODE.python);
    const [output, setOutput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);
    const [hasError, setHasError] = useState(false);
    
    const [windowDimension, setWindowDimension] = useState({
        width: window.innerWidth,
        height: window.innerHeight
    });

    useEffect(() => {
        const handleResize = () => {
            setWindowDimension({ width: window.innerWidth, height: window.innerHeight });
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const handleLanguageChange = (e) => {
        const selectedLang = LANGUAGES.find(lang => lang.id === e.target.value);
        setLanguage(selectedLang);
        setCode(DEFAULT_CODE[selectedLang.id] || "");
        setOutput("");
        setIsSuccess(false);
        setHasError(false);
    };

    const handleRunCode = async () => {
        setIsLoading(true);
        setIsSuccess(false);
        setHasError(false);
        setOutput("Executing...");

        try {
            const response = await fetchAuth(`${CONFIG.API_BASE_URL}/execute_code`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    language: language.id,
                    code: code
                })
            });

            const data = await response.json();
            
            if (data.run) {
                const out = data.run.stdout || "";
                const err = data.run.stderr || "";
                
                // Piston API exit code 0 means success
                if (data.run.code === 0 && !err) {
                    setIsSuccess(true);
                    setOutput(out || "Execution succeeded with no output.");
                } else {
                    setHasError(true);
                    setOutput(err || out || `Execution failed with code ${data.run.code}`);
                }
            } else {
                setHasError(true);
                setOutput(data.message || "Failed to execute code.");
            }
        } catch (error) {
            console.error("Execution error:", error);
            setHasError(true);
            setOutput("Network error or execution engine is unavailable.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{
            padding: "2rem",
            maxWidth: "1400px",
            margin: "0 auto",
            display: "flex",
            flexDirection: "column",
            gap: "1.5rem",
            minHeight: "85vh" // Fill most of viewport but leave room for navbar
        }}>
            {isSuccess && <Confetti width={windowDimension.width} height={windowDimension.height} recycle={false} numberOfPieces={500} />}
            
            <header style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center"
            }}>
                <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                    <div style={{
                        background: 'var(--accent-gradient)',
                        padding: '0.75rem',
                        borderRadius: '0.75rem',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}>
                        <Code size={28} color="white" />
                    </div>
                    <div>
                        <h1 style={{ margin: 0, fontSize: "2rem", color: "var(--fg-main)" }}>Code Practice</h1>
                        <p style={{ margin: 0, color: "var(--text-secondary)" }}>Write, execute, and test your code algorithms in real-time.</p>
                    </div>
                </div>

                <div style={{ display: "flex", gap: "1rem" }}>
                    <select
                        className="glass"
                        style={{
                            padding: "0.75rem 1rem",
                            borderRadius: "0.75rem",
                            border: "1px solid var(--glass-border)",
                            background: "rgba(255, 255, 255, 0.05)",
                            color: "var(--fg-main)",
                            fontFamily: "inherit",
                            fontWeight: 600,
                            cursor: "pointer",
                            outline: "none"
                        }}
                        value={language.id}
                        onChange={handleLanguageChange}
                    >
                        {LANGUAGES.map(lang => (
                            <option key={lang.id} value={lang.id} style={{ color: "black" }}>
                                {lang.name}
                            </option>
                        ))}
                    </select>

                    <motion.button
                        className="btn-primary"
                        onClick={handleRunCode}
                        disabled={isLoading}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "0.5rem",
                            padding: "0.75rem 1.5rem",
                            border: "none",
                            borderRadius: "0.75rem",
                            fontWeight: 600,
                            cursor: isLoading ? "not-allowed" : "pointer",
                            opacity: isLoading ? 0.7 : 1
                        }}
                    >
                        {isLoading ? <Loader2 size={18} className="spin" /> : <Play size={18} />}
                        {isLoading ? "Running..." : "Run Code"}
                    </motion.button>
                </div>
            </header>

            <div style={{
                display: "grid",
                gridTemplateColumns: "1.5fr 1fr",
                gap: "1.5rem",
                flex: 1
            }}>
                {/* Editor Panel */}
                <motion.div 
                    className="glass panel"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{
                        borderRadius: "1rem",
                        overflow: "hidden",
                        display: "flex",
                        flexDirection: "column",
                        border: "1px solid var(--glass-border)",
                        background: "var(--nav-bg)", // semi-transparent
                        boxShadow: "0 10px 30px rgba(0,0,0,0.1)"
                    }}
                >
                    <div style={{
                        padding: "0.75rem 1.5rem",
                        background: "rgba(0,0,0,0.2)",
                        borderBottom: "1px solid var(--glass-border)",
                        fontWeight: 600,
                        color: "var(--fg-main)",
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between'
                    }}>
                        <span>Source Code</span>
                        <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{language.name}</span>
                    </div>
                    <div style={{ flex: 1, position: "relative" }}>
                        <Editor
                            height="100%"
                            theme="vs-dark" // using default vs-dark for deep aesthetics
                            language={language.id === "sqlite3" ? "sql" : (language.id === "cpp" ? "cpp" : language.id)}
                            value={code}
                            onChange={(val) => setCode(val)}
                            options={{
                                minimap: { enabled: false },
                                fontSize: 14,
                                padding: { top: 16 },
                                fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                                smoothScrolling: true,
                                cursorBlinking: 'smooth'
                            }}
                        />
                    </div>
                </motion.div>

                {/* Output Panel */}
                <motion.div 
                    className="glass panel"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    style={{
                        borderRadius: "1rem",
                        overflow: "hidden",
                        display: "flex",
                        flexDirection: "column",
                        border: "1px solid var(--glass-border)",
                        background: "var(--nav-bg)",
                        boxShadow: "0 10px 30px rgba(0,0,0,0.1)"
                    }}
                >
                    <div style={{
                        padding: "0.75rem 1.5rem",
                        background: "rgba(0,0,0,0.2)",
                        borderBottom: "1px solid var(--glass-border)",
                        fontWeight: 600,
                        color: "var(--fg-main)",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem"
                    }}>
                        <span>Execution Output</span>
                        {isSuccess && <CheckCircle size={16} color="#10b981" />}
                        {hasError && <XCircle size={16} color="#ef4444" />}
                    </div>
                    <div style={{
                        flex: 1,
                        padding: "1.5rem",
                        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                        fontSize: "0.9rem",
                        color: hasError ? "#ef4444" : (isSuccess ? "#10b981" : "var(--fg-main)"),
                        whiteSpace: "pre-wrap",
                        overflowY: "auto",
                        background: "rgba(0,0,0,0.15)"
                    }}>
                        {output || "Output will appear here after execution..."}
                    </div>
                </motion.div>
            </div>
            
            <style jsx="true">{`
                .spin {
                    animation: spin 1s linear infinite;
                }
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
}

export default CodePracticePage;
