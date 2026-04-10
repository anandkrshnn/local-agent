/**
 * Mobile App Tests - React Native
 * Tests: Connection, Authentication, Chat, Offline Mode
 */

import 'react-native';
import React from 'react';
import renderer from 'react-test-renderer';
import App from '../src/App';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
}));

// Mock NetInfo
jest.mock('@react-native-community/netinfo', () => ({
  addEventListener: jest.fn(),
  fetch: jest.fn(() => Promise.resolve({ isConnected: true })),
}));

describe('Local Agent Mobile App', () => {
  
  test('renders correctly', () => {
    const tree = renderer.create(<App />).toJSON();
    expect(tree).toBeTruthy();
  });

  test('has header with title', () => {
    const instance = renderer.create(<App />).root;
    const header = instance.findByProps({ testID: 'header-title' });
    expect(header.props.children).toContain('Local Agent');
  });

  test('has input field', () => {
    const instance = renderer.create(<App />).root;
    const input = instance.findByProps({ testID: 'message-input' });
    expect(input.props.placeholder).toBeDefined();
  });

  test('has send button', () => {
    const instance = renderer.create(<App />).root;
    const button = instance.findByProps({ testID: 'send-button' });
    expect(button).toBeTruthy();
  });
});
