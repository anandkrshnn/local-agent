/**
 * Local Agent v4.0 - React Native Mobile App
 * SECURE: No hardcoded API keys - user must authenticate
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
    Modal,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import PushNotification from 'react-native-push-notification';
import Biometrics from 'react-native-biometrics';
import Icon from 'react-native-vector-icons/Ionicons';

// NO HARDCODED API KEYS - MUST BE PROVIDED BY USER
const DEFAULT_API_URL = Platform.select({
    ios: 'http://localhost:8000',
    android: 'http://10.0.2.2:8000',
    default: 'http://localhost:8000',
});

interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: number;
}

interface AuthConfig {
    apiUrl: string;
    apiKey: string;
}

const App = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isConnected, setIsConnected] = useState(true);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [showAuthModal, setShowAuthModal] = useState(true);
    const [apiUrl, setApiUrl] = useState(DEFAULT_API_URL);
    const [apiKey, setApiKey] = useState('');
    const [isConnecting, setIsConnecting] = useState(false);

    useEffect(() => {
        loadSavedConfig();
    }, []);

    const loadSavedConfig = async () => {
        try {
            const savedUrl = await AsyncStorage.getItem('api_url');
            const savedKey = await AsyncStorage.getItem('api_key');
            const savedSessionId = await AsyncStorage.getItem('session_id');
            
            if (savedUrl && savedKey) {
                setApiUrl(savedUrl);
                setApiKey(savedKey);
                setShowAuthModal(false);
                
                if (savedSessionId) {
                    setSessionId(savedSessionId);
                    await authenticateAndConnect(savedUrl, savedKey, savedSessionId);
                } else {
                    const newSessionId = generateUUID();
                    await AsyncStorage.setItem('session_id', newSessionId);
                    setSessionId(newSessionId);
                    await authenticateAndConnect(savedUrl, savedKey, newSessionId);
                }
            }
        } catch (error) {
            console.error('Load config error:', error);
        }
    };

    const authenticateAndConnect = async (url: string, key: string, sid: string) => {
        setIsConnecting(true);
        
        try {
            // Test connection with provided credentials
            const response = await fetch(`${url}/api/status`, {
                headers: { 'X-API-Key': key },
            });
            
            if (response.ok) {
                setIsAuthenticated(true);
                setShowAuthModal(false);
                await loadConversationHistory(sid, url, key);
                setupPushNotifications();
            } else {
                Alert.alert('Connection Failed', 'Invalid API key or server unreachable');
                setShowAuthModal(true);
            }
        } catch (error) {
            Alert.alert('Connection Error', 'Cannot reach server. Check URL and try again.');
            setShowAuthModal(true);
        } finally {
            setIsConnecting(false);
        }
    };

    const saveConfigAndConnect = async () => {
        if (!apiUrl.trim() || !apiKey.trim()) {
            Alert.alert('Missing Information', 'Please enter both API URL and API Key');
            return;
        }
        
        await AsyncStorage.setItem('api_url', apiUrl);
        await AsyncStorage.setItem('api_key', apiKey);
        
        const newSessionId = generateUUID();
        await AsyncStorage.setItem('session_id', newSessionId);
        setSessionId(newSessionId);
        
        await authenticateAndConnect(apiUrl, apiKey, newSessionId);
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

    const loadConversationHistory = async (sid: string, url: string, key: string) => {
        try {
            const response = await fetch(`${url}/api/chat/history/${sid}`, {
                headers: { 'X-API-Key': key },
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
            const response = await fetch(`${apiUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': apiKey,
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

    // Auth Modal
    if (showAuthModal) {
        return (
            <Modal visible={true} animationType="slide">
                <SafeAreaView style={styles.authContainer}>
                    <View style={styles.authHeader}>
                        <Icon name="chatbubbles" size={48} color="#667eea" />
                        <Text style={styles.authTitle}>Local Agent</Text>
                        <Text style={styles.authSubtitle}>Enter your server details</Text>
                    </View>
                    
                    <View style={styles.authForm}>
                        <Text style={styles.inputLabel}>API URL</Text>
                        <TextInput
                            style={styles.authInput}
                            value={apiUrl}
                            onChangeText={setApiUrl}
                            placeholder="http://localhost:8000"
                            placeholderTextColor="#666"
                            autoCapitalize="none"
                        />
                        
                        <Text style={styles.inputLabel}>API Key</Text>
                        <TextInput
                            style={styles.authInput}
                            value={apiKey}
                            onChangeText={setApiKey}
                            placeholder="Enter your API key"
                            placeholderTextColor="#666"
                            secureTextEntry
                            autoCapitalize="none"
                        />
                        
                        <TouchableOpacity
                            style={styles.authButton}
                            onPress={saveConfigAndConnect}
                            disabled={isConnecting}
                        >
                            {isConnecting ? (
                                <ActivityIndicator color="white" />
                            ) : (
                                <Text style={styles.authButtonText}>Connect</Text>
                            )}
                        </TouchableOpacity>
                    </View>
                    
                    <Text style={styles.authFooter}>
                        API key can be found in your server's .env file
                    </Text>
                </SafeAreaView>
            </Modal>
        );
    }

    if (isConnecting) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#667eea" />
                <Text style={styles.loadingText}>Connecting to server...</Text>
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
    // Auth Modal Styles
    authContainer: { flex: 1, backgroundColor: '#0a0a0f', justifyContent: 'center', padding: 20 },
    authHeader: { alignItems: 'center', marginBottom: 40 },
    authTitle: { fontSize: 28, fontWeight: 'bold', color: '#e0e0e0', marginTop: 16 },
    authSubtitle: { fontSize: 14, color: '#888', marginTop: 8 },
    authForm: { backgroundColor: '#1a1a2e', borderRadius: 16, padding: 20 },
    inputLabel: { color: '#e0e0e0', fontSize: 14, marginBottom: 8 },
    authInput: { backgroundColor: '#2a2a3e', borderRadius: 8, padding: 12, color: '#e0e0e0', marginBottom: 16, fontSize: 14 },
    authButton: { backgroundColor: '#667eea', borderRadius: 8, padding: 14, alignItems: 'center', marginTop: 8 },
    authButtonText: { color: 'white', fontSize: 16, fontWeight: '600' },
    authFooter: { textAlign: 'center', color: '#666', fontSize: 12, marginTop: 20 },
});

export default App;
