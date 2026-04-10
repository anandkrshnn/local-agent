/**
 * Local Agent Mobile App - React Native
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
  KeyboardAvoidingView,
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

const App = () => {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener(state => {
      setIsConnected(state.isConnected);
    });
    return () => unsubscribe();
  }, []);

  const sendMessage = async () => {
    if (!inputText.trim() || isLoading) return;
    const userMessage = { id: Date.now().toString(), role: 'user', content: inputText, timestamp: Date.now() };
    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const resp = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: inputText }),
      });
      if (resp.ok) {
        const data = await resp.json();
        setMessages(prev => [...prev, { id: Date.now().toString(), role: 'assistant', content: data.response, timestamp: Date.now() }]);
      }
    } catch (e) {
      Alert.alert('Error', 'Failed to connect to agent server');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Local Agent Mobile</Text>
      </View>
      <FlatList
        data={messages}
        renderItem={({ item }) => (
          <View style={[styles.bubble, item.role === 'user' ? styles.userBubble : styles.botBubble]}>
            <Text style={styles.text}>{item.content}</Text>
          </View>
        )}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.list}
      />
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.inputArea}>
        <TextInput style={styles.input} value={inputText} onChangeText={setInputText} placeholder="Ask anything..." placeholderTextColor="#888" />
        <TouchableOpacity style={styles.button} onPress={sendMessage}>
          <Text style={{color: 'white'}}>Send</Text>
        </TouchableOpacity>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0f' },
  header: { padding: 16, borderBottomWidth: 1, borderBottomColor: '#333' },
  headerTitle: { color: '#667eea', fontSize: 20, fontWeight: 'bold' },
  list: { padding: 16 },
  bubble: { padding: 12, borderRadius: 12, marginBottom: 8, maxWidth: '80%' },
  userBubble: { alignSelf: 'flex-end', backgroundColor: '#667eea' },
  botBubble: { alignSelf: 'flex-start', backgroundColor: '#1a1a2e' },
  text: { color: 'white' },
  inputArea: { flexDirection: 'row', padding: 12, borderTopWidth: 1, borderTopColor: '#333' },
  input: { flex: 1, backgroundColor: '#1a1a2e', color: 'white', borderRadius: 20, paddingHorizontal: 16, height: 40 },
  button: { marginLeft: 12, backgroundColor: '#667eea', borderRadius: 20, paddingHorizontal: 16, justifyContent: 'center' }
});

export default App;
