/**
 * Ollama Auto-Installer for Local Agent Desktop
 * Handles installation, model pulling, and health checks
 */

const { exec, spawn, execSync } = require('child_process');
const { promisify } = require('util');
const fs = require('fs');
const path = require('path');
const https = require('https');
const os = require('os');
const { dialog } = require('electron');

const execAsync = promisify(exec);

class OllamaInstaller {
    constructor() {
        this.platform = os.platform();
        this.ollamaPath = this.getOllamaPath();
        this.downloadProgress = 0;
    }

    getOllamaPath() {
        switch (this.platform) {
            case 'win32': return 'C:\\Program Files\\Ollama\\ollama.exe';
            case 'darwin': return '/usr/local/bin/ollama';
            case 'linux': return '/usr/bin/ollama';
            default: return null;
        }
    }

    getDownloadUrl() {
        switch (this.platform) {
            case 'win32':
                return 'https://ollama.com/download/OllamaSetup.exe';
            case 'darwin':
                return 'https://ollama.com/download/Ollama-darwin.zip';
            case 'linux':
                return 'https://ollama.com/download/ollama-linux-amd64.tgz';
            default:
                throw new Error(`Unsupported platform: ${this.platform}`);
        }
    }

    async isInstalled() {
        try {
            await execAsync('ollama --version');
            return true;
        } catch {
            return false;
        }
    }

    async isRunning() {
        try {
            const response = await fetch('http://localhost:11434/api/tags');
            return response.ok;
        } catch {
            return false;
        }
    }

    async startService() {
        console.log('🔄 Starting Ollama service...');
        
        switch (this.platform) {
            case 'win32':
                exec('net start Ollama', (error) => {
                    if (error) console.error('Failed to start Ollama service:', error);
                });
                break;
            case 'darwin':
            case 'linux':
                exec('ollama serve &', (error) => {
                    if (error) console.error('Failed to start Ollama:', error);
                });
                break;
        }
        
        // Wait for service to be ready
        for (let i = 0; i < 30; i++) {
            if (await this.isRunning()) {
                console.log('✅ Ollama service started');
                return true;
            }
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        return false;
    }

    async downloadFile(url, dest, onProgress) {
        return new Promise((resolve, reject) => {
            const file = fs.createWriteStream(dest);
            let receivedBytes = 0;
            
            https.get(url, (response) => {
                const totalBytes = parseInt(response.headers['content-length'], 10);
                
                response.on('data', (chunk) => {
                    receivedBytes += chunk.length;
                    if (onProgress) {
                        const progress = (receivedBytes / totalBytes) * 100;
                        onProgress(progress);
                    }
                });
                
                response.pipe(file);
                
                file.on('finish', () => {
                    file.close();
                    resolve();
                });
            }).on('error', (err) => {
                fs.unlink(dest, () => {});
                reject(err);
            });
        });
    }

    async installWithProgress(onProgress) {
        console.log('📦 Installing Ollama...');
        
        const downloadUrl = this.getDownloadUrl();
        const installerPath = path.join(os.tmpdir(), `ollama_installer_${Date.now()}${path.extname(downloadUrl)}`);
        
        await this.downloadFile(downloadUrl, installerPath, onProgress);
        await this.runInstaller(installerPath);
        await this.cleanup(installerPath);
        await this.startService();
        
        console.log('✅ Ollama installed successfully');
        return true;
    }

    async runInstaller(installerPath) {
        return new Promise((resolve, reject) => {
            let installer;
            
            switch (this.platform) {
                case 'win32':
                    installer = spawn(installerPath, ['/S'], { stdio: 'inherit' });
                    break;
                case 'darwin':
                    installer = spawn('unzip', [installerPath, '-d', '/usr/local/bin'], { stdio: 'inherit' });
                    break;
                case 'linux':
                    installer = spawn('tar', ['-xzf', installerPath, '-C', '/usr/local/bin'], { stdio: 'inherit' });
                    break;
                default:
                    reject(new Error('Unsupported platform'));
                    return;
            }
            
            installer.on('close', (code) => {
                if (code === 0) resolve();
                else reject(new Error(`Installer exited with code ${code}`));
            });
        });
    }

    async pullModel(modelName = 'phi3:mini', onProgress) {
        console.log(`📥 Pulling model: ${modelName}...`);
        
        return new Promise((resolve, reject) => {
            const pull = spawn('ollama', ['pull', modelName]);
            
            pull.stdout.on('data', (data) => {
                const output = data.toString();
                console.log(output);
                
                // Parse progress from output
                const progressMatch = output.match(/(\d+)%/);
                if (progressMatch && onProgress) {
                    onProgress(parseInt(progressMatch[1]));
                }
            });
            
            pull.stderr.on('data', (data) => {
                console.error(data.toString());
            });
            
            pull.on('close', (code) => {
                if (code === 0) {
                    console.log(`✅ Model ${modelName} pulled successfully`);
                    resolve();
                } else {
                    reject(new Error(`Failed to pull model: ${code}`));
                }
            });
        });
    }

    async getInstalledModels() {
        try {
            const { stdout } = await execAsync('ollama list');
            const lines = stdout.split('\n').slice(1);
            return lines.filter(l => l.trim()).map(l => l.split(' ')[0]);
        } catch {
            return [];
        }
    }

    async ensureReady(modelName = 'phi3:mini', onProgress) {
        // Check if Ollama is installed
        if (!await this.isInstalled()) {
            const shouldInstall = await dialog.showMessageBox({
                type: 'question',
                title: 'Ollama Required',
                message: 'Local Agent requires Ollama to run AI models.',
                detail: 'Ollama is a free, open-source tool for running AI models locally. Would you like to install it now?',
                buttons: ['Install', 'Cancel'],
                defaultId: 0,
                cancelId: 1
            });
            
            if (shouldInstall.response === 0) {
                await this.installWithProgress(onProgress);
            } else {
                throw new Error('Ollama installation cancelled');
            }
        }
        
        // Check if Ollama is running
        if (!await this.isRunning()) {
            await this.startService();
        }
        
        // Check if model is available
        const models = await this.getInstalledModels();
        if (!models.includes(modelName)) {
            const shouldPull = await dialog.showMessageBox({
                type: 'question',
                title: 'Model Required',
                message: `The ${modelName} model is required for AI responses.`,
                detail: 'This model will be downloaded (approximately 2.2GB). Continue?',
                buttons: ['Download', 'Skip'],
                defaultId: 0,
                cancelId: 1
            });
            
            if (shouldPull.response === 0) {
                await this.pullModel(modelName, onProgress);
            } else {
                throw new Error('Model download cancelled');
            }
        }
        
        return true;
    }

    async cleanup(filePath) {
        try {
            if (fs.existsSync(filePath)) {
                fs.unlinkSync(filePath);
            }
        } catch (error) {
            console.error('Cleanup error:', error);
        }
    }
}

module.exports = OllamaInstaller;
