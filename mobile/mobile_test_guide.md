# 📱 Local Agent Mobile App - Test Guide

## Prerequisites
- iOS Simulator (Xcode) or Android Emulator (Android Studio)
- Backend server running on http://localhost:8000
- AGENT_API_KEY set in .env

## Test Case 1: App Launch & Connection
**Steps:**
1. npx react-native run-ios OR run-android
**Expected Result:** App launches, shows "● Connected" instantly.

## Test Case 2: Authentication (Biometric)
**Steps:**
1. Enable FaceID/Fingerprint in simulator settings.
2. Launch app.
**Expected Result:** Biometric prompt appears before chat enters main state.

## Test Case 3: Offline Mode
**Steps:**
1. Disable internet on host.
2. Send "Hello".
**Expected Result:** Message stored locally, status indicator changes to "Offline".
