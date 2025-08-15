#!/usr/bin/env python3
"""
Test script for password reset functionality
"""
import asyncio
import sys
import os
import httpx
import json

BASE_URL = "http://144.172.100.198:7007/clicktromics/v1"

async def test_password_reset_flow():
    """Test the complete password reset flow"""
    print("🔐 Testing Password Reset Flow")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Request password reset for existing user
        print("\n1. 📧 Testing password reset request...")
        reset_request_data = {
            "email": "user1@example.com"  # Use an existing user email
        }
        
        try:
            response = await client.post(f"{BASE_URL}/auth/password-reset", json=reset_request_data)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            
            if response.status_code == 200:
                print("   ✅ Password reset request successful!")
                print("   📝 Check your application logs for the reset token")
            else:
                print(f"   ❌ Password reset request failed: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 2: Request password reset for non-existing user (should not reveal if user exists)
        print("\n2. 📧 Testing password reset for non-existing user...")
        non_existing_reset_data = {
            "email": "nonexisting@example.com"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/auth/password-reset", json=non_existing_reset_data)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            
            if response.status_code == 200:
                print("   ✅ Correctly handled non-existing user (doesn't reveal existence)")
            else:
                print(f"   ❌ Unexpected response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 3: Confirm password reset with invalid token
        print("\n3. 🔑 Testing password reset confirmation with invalid token...")
        invalid_confirm_data = {
            "token": "invalid_reset_token",
            "new_password": "NewPassword123!"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/auth/password-reset/confirm", json=invalid_confirm_data)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            
            if response.status_code == 400:
                print("   ✅ Correctly rejected invalid reset token")
            else:
                print(f"   ❌ Should have rejected invalid token: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 4: Confirm password reset with valid token (you need to get this from logs)
        print("\n4. 🔑 Testing password reset confirmation with valid token...")
        print("   📝 To test this, you need to:")
        print("   1. Request a password reset for an existing user")
        print("   2. Check your application logs for the reset token")
        print("   3. Use that token in the confirmation request")
        print("   4. Replace 'YOUR_RESET_TOKEN_HERE' with the actual token")
        
        # Example with placeholder token
        valid_confirm_data = {
            "token": "YOUR_RESET_TOKEN_HERE",  # Replace with actual token from logs
            "new_password": "NewPassword123!"
        }
        
        print(f"   Example request data: {json.dumps(valid_confirm_data, indent=2)}")
        print("   Expected: 200 OK if token is valid and not expired")

def print_manual_test_instructions():
    """Print manual testing instructions"""
    print("\n" + "=" * 60)
    print("📋 MANUAL TESTING INSTRUCTIONS")
    print("=" * 60)
    
    print("\n🔧 Step 1: Request Password Reset")
    print("curl -X POST 'http://144.172.100.198:7007/clicktromics/v1/auth/password-reset' \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{")
    print('    "email": "user1@example.com"')
    print("  }'")
    
    print("\n📝 Step 2: Get Reset Token from Logs")
    print("Check your application logs for a line like:")
    print("Email would be sent to user1@example.com: Password Reset Request")
    print("The reset token will be in the email body URL")
    
    print("\n🔑 Step 3: Confirm Password Reset")
    print("curl -X POST 'http://144.172.100.198:7007/clicktromics/v1/auth/password-reset/confirm' \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{")
    print('    "token": "YOUR_RESET_TOKEN_HERE",')
    print('    "new_password": "NewPassword123!"')
    print("  }'")
    
    print("\n🔍 Step 4: Test Login with New Password")
    print("curl -X POST 'http://144.172.100.198:7007/clicktromics/v1/auth/login' \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{")
    print('    "email": "user1@example.com",')
    print('    "password": "NewPassword123!"')
    print("  }'")
    
    print("\n⚠️  Important Notes:")
    print("- Reset tokens expire after 1 hour")
    print("- Each token can only be used once")
    print("- After password reset, all refresh tokens are revoked")
    print("- The email sending is currently logged but not actually sent")

def print_swagger_test_instructions():
    """Print Swagger UI testing instructions"""
    print("\n" + "=" * 60)
    print("🌐 SWAGGER UI TESTING")
    print("=" * 60)
    
    print("\n1. 📧 Test Password Reset Request:")
    print("   - Go to: http://144.172.100.198:7007/docs")
    print("   - Find the POST /auth/password-reset endpoint")
    print("   - Click 'Try it out'")
    print("   - Enter JSON:")
    print("     {")
    print('       "email": "user1@example.com"')
    print("     }")
    print("   - Click 'Execute'")
    print("   - Check logs for reset token")
    
    print("\n2. 🔑 Test Password Reset Confirmation:")
    print("   - Find the POST /auth/password-reset/confirm endpoint")
    print("   - Click 'Try it out'")
    print("   - Enter JSON:")
    print("     {")
    print('       "token": "TOKEN_FROM_LOGS",')
    print('       "new_password": "NewPassword123!"')
    print("     }")
    print("   - Click 'Execute'")
    
    print("\n3. 🔐 Test Login with New Password:")
    print("   - Find the POST /auth/login endpoint")
    print("   - Click 'Try it out'")
    print("   - Enter JSON:")
    print("     {")
    print('       "email": "user1@example.com",')
    print('       "password": "NewPassword123!"')
    print("     }")
    print("   - Click 'Execute'")

if __name__ == "__main__":
    print("Password Reset Testing Guide")
    print("=" * 50)
    
    # Run automated tests
    asyncio.run(test_password_reset_flow())
    
    # Print manual instructions
    print_manual_test_instructions()
    print_swagger_test_instructions()
