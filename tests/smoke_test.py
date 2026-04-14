from localagent.agent import LocalAgent
try:
    agent = LocalAgent()
    print('=== v0.2 Final Smoke Test ===')
    response = agent.chat('Hello, remember I like dark mode')
    print('Chat response preview:', response[:150] + '...' if response else 'No response')
    
    ctx = agent.memory_service.get_governed_context('dark mode preference', {'session_id': 'test'})
    print('Governed context reason:', ctx.get('reason'))
    print('Retrieved memories count:', len(ctx.get('memories', [])))
    for m in ctx.get('memories', []):
        print('- Body:', m.get('body'))
except Exception as global_e:
    print(f"Global error: {global_e}")
