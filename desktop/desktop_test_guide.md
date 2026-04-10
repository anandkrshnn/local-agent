# 💻 Local Agent Desktop App - Test Guide

## Prerequisites
- Windows 10/11, macOS, or Linux
- Node.js 18+

## Test Case 1: System Tray Integration
**Steps:**
1. npm start
2. Close window.
**Expected Result:** Icon remains in tray, double-click restores window.

## Test Case 2: Global Hotkeys
**Steps:**
1. Press Ctrl+Shift+Space (Win/Linux) or Cmd+Shift+Space (Mac).
**Expected Result:** Window toggles visibility.

## Test Case 3: Native File Dialogs
**Steps:**
1. Click "Open File" from chat.
**Expected Result:** System file picker appears.
