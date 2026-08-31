import express, { Request, Response } from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { GoogleGenAI, Type, FunctionDeclaration, GenerateContentResponse } from '@google/genai';
import path from 'path';
import { createServer as createViteServer } from 'vite';
import fs from 'fs';
import { exec } from 'child_process';
import util from 'util';
import os from 'os';

dotenv.config();

const execPromise = util.promisify(exec);
const app = express();
const PORT = 3000;

// Initialize Google Gen AI Client
const aiApiKey = process.env.GEMINI_API_KEY;
const ai = aiApiKey ? new GoogleGenAI({ apiKey: aiApiKey }) : null;

app.use(cors());
app.use(express.json());

const dbPath = path.resolve(process.cwd(), 'braink_memory.json');
const evolutionPath = path.resolve(process.cwd(), 'braink_evolution.json');

function readHistory() {
    try {
        if (!fs.existsSync(dbPath)) {
            fs.writeFileSync(dbPath, JSON.stringify([]));
            return [];
        }
        const data = fs.readFileSync(dbPath, 'utf-8');
        return JSON.parse(data);
    } catch (e) {
        console.error("Storage read error:", e);
        return [];
    }
}

function writeHistory(history: any[]) {
    try {
        fs.writeFileSync(dbPath, JSON.stringify(history, null, 2));
    } catch (e) {
        console.error("Storage write error:", e);
    }
}

function readEvolution() {
    try {
        if (!fs.existsSync(evolutionPath)) {
            fs.writeFileSync(evolutionPath, JSON.stringify({ coreDirectives: [], learnedFacts: [] }));
            return { coreDirectives: [], learnedFacts: [] };
        }
        return JSON.parse(fs.readFileSync(evolutionPath, 'utf-8'));
    } catch (e) {
        return { coreDirectives: [], learnedFacts: [] };
    }
}

function writeEvolution(data: any) {
    try {
        fs.writeFileSync(evolutionPath, JSON.stringify(data, null, 2));
    } catch (e) {
        console.error("Evolution write error:", e);
    }
}

const executeBash: FunctionDeclaration = {
    name: 'execute_bash',
    description: 'Execute a bash command on the host Linux system. Useful for navigating the file system, installing dependencies, checking processes, or running scripts. Use standard bash syntax.',
    parameters: {
        type: Type.OBJECT,
        properties: {
            command: { type: Type.STRING, description: 'The exact bash command to execute.' }
        },
        required: ['command']
    }
};

const readFile: FunctionDeclaration = {
    name: 'read_file',
    description: 'Read the contents of a file.',
    parameters: {
        type: Type.OBJECT,
        properties: {
            path: { type: Type.STRING, description: 'The absolute or relative path to the file.' }
        },
        required: ['path']
    }
};

const writeFile: FunctionDeclaration = {
    name: 'write_file',
    description: 'Write contents to a file, overwriting if it exists.',
    parameters: {
        type: Type.OBJECT,
        properties: {
            path: { type: Type.STRING, description: 'The absolute or relative path to the file.' },
            content: { type: Type.STRING, description: 'The string content to write.' }
        },
        required: ['path', 'content']
    }
};

const updateEvolution: FunctionDeclaration = {
    name: 'update_evolution',
    description: 'Save a learned fact or core directive to the persistent BrainK evolution memory. Use this to remember user preferences or important project context across sessions.',
    parameters: {
        type: Type.OBJECT,
        properties: {
            category: { type: Type.STRING, description: 'Either "coreDirectives" or "learnedFacts"' },
            content: { type: Type.STRING, description: 'The text content to save permanently.' }
        },
        required: ['category', 'content']
    }
};

const deployWorkload: FunctionDeclaration = {
    name: 'deploy_workload',
    description: 'Spin up a virtualized hardware environment or subsystem. Supported types: "linux" (Alpine Desktop), "android" (AOSP Subsystem), "browser" (Headless Chromium), "llm" (Local Inferencing Node).',
    parameters: {
        type: Type.OBJECT,
        properties: {
            type: { type: Type.STRING, description: 'The environment type (linux, android, browser, llm).' },
            name: { type: Type.STRING, description: 'A custom display name for this workload instance.' }
        },
        required: ['type', 'name']
    }
};

let activeWorkloads: any[] = [];


app.post('/api/chat', async (req: Request, res: Response) => {
    const { sessionId, message } = req.body;

    if (!sessionId || !message) {
        return res.status(400).json({ error: "Missing sessionId or message payload." });
    }
    
    if (!ai) {
        return res.status(500).json({ error: "GEMINI_API_KEY is not configured." });
    }

    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    try {
        const allHistory = readHistory();
        
        // Add user message to history
        allHistory.push({
            session_id: sessionId,
            role: 'user',
            parts: [{ text: message }],
            timestamp: new Date().toISOString()
        });
        writeHistory(allHistory);

        let agentLoop = true;
        let iterationCount = 0;
        const maxIterations = 15;

        while (agentLoop && iterationCount < maxIterations) {
            iterationCount++;
            
            const sessionHistory = allHistory
                .filter((h: any) => h.session_id === sessionId)
                .map((h: any) => ({ role: h.role, parts: h.parts || [{ text: h.text }] }));

            const responseStream = await ai.models.generateContentStream({
                model: 'gemini-2.5-flash',
                contents: sessionHistory,
                config: {
                    systemInstruction: "You are BRAINK, an advanced AI assistant operating within a highly technical cybernetic console interface. You have full access to the user's local filesystem and terminal. You can write code, run commands, deploy virtual workloads/environments (like desktops, browsers, or LLMs), and accomplish tasks directly on the host machine. You can also persist core directives or learned facts using update_evolution. Always explain what you are doing before executing tools. If a command fails, try an alternative approach. Once you finish your overall task, provide a final summary message to the user.",
                    tools: [{ functionDeclarations: [executeBash, readFile, writeFile, updateEvolution, deployWorkload] }],
                    temperature: 0.2
                }
            });

            let currentModelParts: any[] = [];
            let functionCalls: any[] = [];
            let textOutput = "";

            for await (const chunk of responseStream) {
                if (chunk.text) {
                    textOutput += chunk.text;
                    res.write(`data: ${JSON.stringify({ text: chunk.text })}\n\n`);
                }
                if (chunk.functionCalls) {
                    functionCalls.push(...chunk.functionCalls);
                }
            }

            if (textOutput) {
                currentModelParts.push({ text: textOutput });
            }

            if (functionCalls.length > 0) {
                for (const call of functionCalls) {
                    res.write(`data: ${JSON.stringify({ toolCall: { name: call.name, args: call.args } })}\n\n`);
                    currentModelParts.push({ functionCall: call });
                }

                allHistory.push({
                    session_id: sessionId,
                    role: 'model',
                    parts: currentModelParts,
                    timestamp: new Date().toISOString()
                });

                const functionResponses = [];
                for (const call of functionCalls) {
                    let result = "";
                    try {
                        if (call.name === 'execute_bash') {
                            const { stdout, stderr } = await execPromise(call.args.command as string, { cwd: process.cwd() });
                            result = stdout + (stderr ? `\nSTDERR:\n${stderr}` : '');
                            if (!result.trim()) result = "Command executed successfully with no output.";
                        } else if (call.name === 'read_file') {
                            result = fs.readFileSync(path.resolve(process.cwd(), call.args.path as string), 'utf8');
                        } else if (call.name === 'write_file') {
                            fs.writeFileSync(path.resolve(process.cwd(), call.args.path as string), call.args.content as string);
                            result = "File written successfully.";
                        } else if (call.name === 'update_evolution') {
                            const evo = readEvolution();
                            if (call.args.category === 'coreDirectives') {
                                evo.coreDirectives.push(call.args.content as string);
                            } else {
                                evo.learnedFacts.push(call.args.content as string);
                            }
                            writeEvolution(evo);
                            result = "Evolution memory updated successfully.";
                        } else if (call.name === 'deploy_workload') {
                            const newWorkload = {
                                id: Math.random().toString(36).substring(2, 9),
                                type: call.args.type,
                                name: call.args.name,
                                status: 'booting',
                                logs: ['Initializing hypervisor bindings...', 'Allocating memory regions...']
                            };
                            activeWorkloads.push(newWorkload);
                            // Simulate boot sequence
                            setTimeout(() => {
                                const w = activeWorkloads.find(x => x.id === newWorkload.id);
                                if (w) {
                                    w.status = 'running';
                                    w.logs.push('Kernel panic averted.', 'Virtual Environment fully operational.');
                                }
                            }, 5000);
                            result = `Workload deployed. ID: ${newWorkload.id}, Name: ${newWorkload.name}. It is currently booting.`;
                        } else {
                            result = `Unknown function: ${call.name}`;
                        }
                    } catch(e: any) {
                        result = `Error executing ${call.name}: ${e.message}`;
                    }
                    
                    // Truncate overly long outputs to prevent context limits
                    if (result.length > 15000) {
                        result = result.substring(0, 15000) + "\n...[TRUNCATED]";
                    }

                    functionResponses.push({
                        functionResponse: {
                            name: call.name,
                            response: { result }
                        }
                    });
                    
                    res.write(`data: ${JSON.stringify({ toolResult: { name: call.name, result } })}\n\n`);
                }

                allHistory.push({
                    session_id: sessionId,
                    role: 'user',
                    parts: functionResponses,
                    timestamp: new Date().toISOString()
                });
                writeHistory(allHistory);
                
                // Agent loop continues to process the function responses
            } else {
                allHistory.push({
                    session_id: sessionId,
                    role: 'model',
                    parts: currentModelParts,
                    timestamp: new Date().toISOString()
                });
                writeHistory(allHistory);
                agentLoop = false;
            }
        }
        
        if (iterationCount >= maxIterations) {
            res.write(`data: ${JSON.stringify({ text: "\n\n*Agent reached maximum action iterations.*" })}\n\n`);
        }

        res.write('data: [DONE]\n\n');
        res.end();

    } catch (error: any) {
        console.error("API ERROR:", error);
        let errorMsg = error.message || "Internal processing error.";
        if (errorMsg.includes("429") || errorMsg.includes("quota") || errorMsg.includes("RESOURCE_EXHAUSTED")) {
            errorMsg = "\n\n[BRAINK COGNITIVE OVERLOAD] Primary neural link saturated (Rate Limit 429). The Gemini sub-cortex is cooling down. Please hold for a moment before issuing further directives.";
            res.write(`data: ${JSON.stringify({ text: errorMsg })}\n\n`);
        } else {
            res.write(`data: ${JSON.stringify({ error: errorMsg })}\n\n`);
        }
        res.end();
    }
});

app.post('/api/chat/history', async (req: Request, res: Response) => {
    const { sessionId } = req.body;
    if (!sessionId) return res.status(400).json({ error: "Missing sessionId." });

    const allHistory = readHistory();
    const sessionHistory = allHistory.filter((h: any) => h.session_id === sessionId);
    
    // Flatten parts for the UI
    const uiHistory = sessionHistory.map((h: any) => {
        let content = "";
        if (h.role === 'model') {
            if (h.parts) {
                const texts = h.parts.filter((p: any) => p.text).map((p: any) => p.text);
                content = texts.join('');
            } else if (h.text) {
                content = h.text;
            }
        } else if (h.role === 'user') {
            if (h.parts) {
                const texts = h.parts.filter((p: any) => p.text).map((p: any) => p.text);
                content = texts.join('');
                if (!content && h.parts.some((p: any) => p.functionResponse)) {
                    content = "[Tool Execution Result]";
                }
            } else if (h.text) {
                content = h.text;
            }
        }
        return { role: h.role, content };
    }).filter((h: any) => h.content !== "[Tool Execution Result]");
    
    res.json({ history: uiHistory });
});

app.post('/api/chat/clear', (req: Request, res: Response) => {
    const { sessionId } = req.body;
    if (!sessionId) return res.status(400).json({ error: "Missing sessionId." });

    const allHistory = readHistory();
    const filteredHistory = allHistory.filter((h: any) => h.session_id !== sessionId);
    writeHistory(filteredHistory);
    
    res.json({ status: "SUCCESS", message: "Conversation log buffer reset successfully." });
});

app.get('/api/system', (req: Request, res: Response) => {
    res.json({
        platform: os.platform(),
        release: os.release(),
        uptime: os.uptime(),
        totalmem: os.totalmem(),
        freemem: os.freemem(),
        cpus: os.cpus(),
        processMemory: process.memoryUsage()
    });
});

app.get('/api/fs', (req: Request, res: Response) => {
    try {
        const targetPath = req.query.path as string || '.';
        const absolutePath = path.resolve(process.cwd(), targetPath);
        
        // Basic security to prevent escaping workspace
        if (!absolutePath.startsWith(process.cwd())) {
            return res.status(403).json({ error: "Access denied." });
        }
        
        const items = fs.readdirSync(absolutePath, { withFileTypes: true });
        const list = items.map(item => ({
            name: item.name,
            isDirectory: item.isDirectory(),
            path: path.relative(process.cwd(), path.join(absolutePath, item.name))
        }));
        
        // Sort directories first
        list.sort((a, b) => {
            if (a.isDirectory && !b.isDirectory) return -1;
            if (!a.isDirectory && b.isDirectory) return 1;
            return a.name.localeCompare(b.name);
        });
        
        res.json({ currentPath: targetPath, items: list });
    } catch (e: any) {
        res.status(500).json({ error: e.message });
    }
});

app.get('/api/evolution', (req: Request, res: Response) => {
    res.json(readEvolution());
});

app.get('/api/workloads', (req: Request, res: Response) => {
    res.json(activeWorkloads);
});

app.delete('/api/workloads/:id', (req: Request, res: Response) => {
    activeWorkloads = activeWorkloads.filter(w => w.id !== req.params.id);
    res.json({ success: true });
});

async function startServer() {
    if (process.env.NODE_ENV !== "production") {
      const vite = await createViteServer({
        server: { middlewareMode: true },
        appType: "spa",
      });
      app.use(vite.middlewares);
    } else {
      const distPath = path.join(process.cwd(), 'dist');
      app.use(express.static(distPath));
      app.get('*all', (req, res) => {
        res.sendFile(path.join(distPath, 'index.html'));
      });
    }
  
    app.listen(PORT, "0.0.0.0", () => {
      console.log(`[BRAINK_CORE] Agent backend listening at http://localhost:${PORT}`);
    });
}
  
startServer();
