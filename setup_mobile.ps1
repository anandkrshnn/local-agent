# setup_mobile.ps1 - Complete Mobile Scaffolding Script

param(
    [switch]$SkipAndroid,
    [switch]$SkipiOS
)

Write-Host "📱 Setting up Local Agent Mobile App" -ForegroundColor Cyan
Write-Host "=" * 60

# Navigate to mobile directory
$mobileDir = "C:\Users\Admin\Documents\GitHub\local-agent-v4\mobile"
if (-not (Test-Path $mobileDir)) {
    New-Item -ItemType Directory -Path $mobileDir -Force
}
Set-Location $mobileDir

# 1. Initialize React Native project (if not already)
if (-not (Test-Path "android") -and -not $SkipAndroid) {
    Write-Host "`n📦 Initializing React Native project..." -ForegroundColor Yellow
    
    # Check if React Native CLI is installed
    $rnInstalled = Get-Command npx -ErrorAction SilentlyContinue
    if (-not $rnInstalled) {
        Write-Host "❌ npx not found. Please install Node.js first." -ForegroundColor Red
        exit 1
    }
    
    npx react-native init LocalAgent --template react-native-template-typescript
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ React Native init failed" -ForegroundColor Red
        exit 1
    }
}

# 2. Install dependencies
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Yellow

$dependencies = @(
    "@react-navigation/native",
    "@react-navigation/stack",
    "react-native-screens",
    "react-native-safe-area-context",
    "react-native-vector-icons",
    "@react-native-async-storage/async-storage",
    "react-native-keychain",
    "react-native-biometrics",
    "react-native-push-notification",
    "@react-native-community/netinfo"
)

foreach ($dep in $dependencies) {
    Write-Host "   Installing $dep..." -ForegroundColor Gray
    npm install $dep
}

# 3. iOS specific setup (macOS only)
if (-not $SkipiOS -and $IsMacOS) {
    Write-Host "`n🍎 Setting up iOS..." -ForegroundColor Yellow
    Set-Location ios
    pod install
    Set-Location ..
}

# 4. Android specific setup
if (-not $SkipAndroid) {
    Write-Host "`n🤖 Setting up Android..." -ForegroundColor Yellow
    Set-Location android
    
    # Clean and build
    if (Test-Path "gradlew.bat") {
        .\gradlew.bat clean
    } elseif (Test-Path "gradlew") {
        chmod +x gradlew
        ./gradlew clean
    }
    
    Set-Location ..
}

# 5. Copy App.tsx
Write-Host "`n📝 Copying App.tsx..." -ForegroundColor Yellow

$appContent = @'
/**
 * Local Agent v4.0 - React Native Mobile App
 * Complete implementation with navigation, auth, chat
 */

import React, { useEffect, useState } from 'react';
import {
    SafeAreaView,
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    FlatList,
    View,
    ActivityIndicator,
    Platform,
    Alert,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import PushNotification from 'react-native-push-notification';
import Biometrics from 'react-native-biometrics';
import Icon from 'react-native-vector-icons/Ionicons';

const API_URL = Platform.select({
    ios: 'http://localhost:8000',
    android: 'http://10.0.2.2:8000',
    default: 'http://localhost:8000',
});

const API_KEY = 'local-agent-key-2024';

interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: number;
}

const App = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isConnected, setIsConnected] = useState(true);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    useEffect(() => {
        initializeApp();
    }, []);

    const initializeApp = async () => {
        let sid = await AsyncStorage.getItem('session_id');
        if (!sid) {
            sid = generateUUID();
            await AsyncStorage.setItem('session_id', sid);
        }
        setSessionId(sid);

        const biometrics = new Biometrics();
        const { available } = await biometrics.isSensorAvailable();
        
        if (available) {
            const { success } = await biometrics.simplePrompt({
                promptMessage: 'Authenticate to access Local Agent',
            });
            setIsAuthenticated(success);
            if (success) loadConversationHistory(sid);
        } else {
            setIsAuthenticated(true);
            loadConversationHistory(sid);
        }

        setupPushNotifications();
    };

    const setupPushNotifications = () => {
        PushNotification.configure({
            onNotification: (notification) => {
                if (notification.userInteraction) {
                    console.log('Notification tapped:', notification);
                }
            },
            popInitialNotification: true,
            requestPermissions: Platform.OS === 'ios',
        });

        if (Platform.OS === 'android') {
            PushNotification.createChannel({
                channelId: 'local-agent',
                channelName: 'Local Agent Notifications',
                channelDescription: 'AI response notifications',
                importance: 4,
                vibrate: true,
            });
        }
    };

    const generateUUID = () => {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
            const r = (Math.random() * 16) | 0;
            const v = c === 'x' ? r : (r & 0x3) | 0x8;
            return v.toString(16);
        });
    };

    const loadConversationHistory = async (sid: string) => {
        try {
            const response = await fetch(`${API_URL}/api/chat/history/${sid}`, {
                headers: { 'X-API-Key': API_KEY },
            });
            if (response.ok) {
                const data = await response.json();
                setMessages(data.messages || []);
            }
        } catch (error) {
            console.error('Load history error:', error);
        }
    };

    const sendMessage = async () => {
        if (!inputText.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: inputText,
            timestamp: Date.now(),
        };
        setMessages(prev => [...prev, userMessage]);
        setInputText('');
        setIsLoading(true);

        try {
            const response = await fetch(`${API_URL}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': API_KEY,
                },
                body: JSON.stringify({
                    message: inputText,
                    session_id: sessionId,
                }),
            });

            if (response.ok) {
                const data = await response.json();
                const assistantMessage: Message = {
                    id: (Date.now() + 1).toString(),
                    role: 'assistant',
                    content: data.response,
                    timestamp: Date.now(),
                };
                setMessages(prev => [...prev, assistantMessage]);
                
                PushNotification.localNotification({
                    channelId: 'local-agent',
                    title: 'New Response',
                    message: data.response.substring(0, 100),
                });
            }
        } catch (error) {
            Alert.alert('Error', 'Failed to send message');
        } finally {
            setIsLoading(false);
        }
    };

    const renderMessage = ({ item }: { item: Message }) => (
        <View style={[styles.messageBubble, item.role === 'user' ? styles.userBubble : styles.assistantBubble]}>
            <Text style={styles.messageText}>{item.content}</Text>
            <Text style={styles.messageTime}>
                {new Date(item.timestamp).toLocaleTimeString()}
            </Text>
        </View>
    );

    if (!isAuthenticated) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#667eea" />
                <Text style={styles.loadingText}>Authenticating...</Text>
            </View>
        );
    }

    return (
        <SafeAreaView style={styles.container}>
            <View style={styles.header}>
                <Icon name="chatbubbles" size={28} color="#667eea" />
                <Text style={styles.headerTitle}>Local Agent</Text>
                <View style={styles.statusContainer}>
                    <View style={[styles.statusDot, isConnected ? styles.statusConnected : styles.statusDisconnected]} />
                    <Text style={styles.statusText}>{isConnected ? 'Online' : 'Offline'}</Text>
                </View>
            </View>

            <FlatList
                data={messages}
                renderItem={renderMessage}
                keyExtractor={item => item.id}
                contentContainerStyle={styles.messagesList}
                ref={ref => (flatListRef = ref)}
                onContentSizeChange={() => flatListRef?.scrollToEnd()}
            />

            <View style={styles.inputContainer}>
                <TextInput
                    style={styles.input}
                    value={inputText}
                    onChangeText={setInputText}
                    placeholder="Type a message..."
                    placeholderTextColor="#888"
                    multiline
                    editable={!isLoading}
                />
                <TouchableOpacity
                    style={[styles.sendButton, isLoading && styles.sendButtonDisabled]}
                    onPress={sendMessage}
                    disabled={isLoading}
                >
                    {isLoading ? (
                        <ActivityIndicator size="small" color="white" />
                    ) : (
                        <Icon name="send" size={20} color="white" />
                    )}
                </TouchableOpacity>
            </View>
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#0a0a0f' },
    loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0a0a0f' },
    loadingText: { color: '#e0e0e0', marginTop: 12 },
    header: { flexDirection: 'row', alignItems: 'center', padding: 16, backgroundColor: '#1a1a2e', borderBottomWidth: 1, borderBottomColor: '#2a2a3e' },
    headerTitle: { flex: 1, fontSize: 18, fontWeight: '600', color: '#e0e0e0', marginLeft: 12 },
    statusContainer: { flexDirection: 'row', alignItems: 'center' },
    statusDot: { width: 8, height: 8, borderRadius: 4, marginRight: 6 },
    statusConnected: { backgroundColor: '#4caf50' },
    statusDisconnected: { backgroundColor: '#f44336' },
    statusText: { fontSize: 12, color: '#888' },
    messagesList: { padding: 16 },
    messageBubble: { maxWidth: '80%', padding: 12, borderRadius: 16, marginBottom: 12 },
    userBubble: { alignSelf: 'flex-end', backgroundColor: '#667eea' },
    assistantBubble: { alignSelf: 'flex-start', backgroundColor: '#2a2a3e' },
    messageText: { color: 'white', fontSize: 14, lineHeight: 20 },
    messageTime: { fontSize: 10, color: 'rgba(255,255,255,0.6)', marginTop: 4 },
    inputContainer: { flexDirection: 'row', padding: 16, backgroundColor: '#1a1a2e', borderTopWidth: 1, borderTopColor: '#2a2a3e' },
    input: { flex: 1, backgroundColor: '#2a2a3e', borderRadius: 24, paddingHorizontal: 16, paddingVertical: 10, color: '#e0e0e0', fontSize: 14, maxHeight: 100 },
    sendButton: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#667eea', justifyContent: 'center', alignItems: 'center', marginLeft: 12 },
    sendButtonDisabled: { opacity: 0.5 },
});

export default App;
'@

# Write App.tsx
$appContent | Out-File -FilePath "App.tsx" -Encoding UTF8

Write-Host "✅ Mobile app scaffolding complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Next steps:" -ForegroundColor Cyan
Write-Host "   For Android: cd mobile/android && ./gradlew assembleRelease"
Write-Host "   For iOS: cd mobile/ios && pod install && cd .. && npx react-native run-ios"
